#!/usr/bin/env python
"""Render Mol* viewpoint images of a protein complex (proteinbase-style).

For every view mode — cartoon, surface, pLDDT, hydrophobicity, interface — the
tool renders three viewpoints of the complex with headless Chrome, using the
same Mol* page as the interactive explorers. Use the images to inspect binding
geometry, the interface, confidence and hydrophobicity from several angles.

    .venv/bin/python tools/report/molstar_views.py --complex fold.cif \
        --name e1b-d7x-t3-3-v6 --out outdir --explorer

Inputs: one complex file (PDB or mmCIF), or --binder plus --target files.
The binder chains are pink; target chains use the cyan family. The interface
mode marks residues in heavy-atom contact (4.5 A) between binder and target.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import glob
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GENERATOR = REPO / "challenges" / "02-tnfa" / "viewers" / "scripts" / "make_molstar_explorer.py"
DEFAULT_BUNDLE = REPO / "challenges" / "02-tnfa" / "viewers" / "molstar-bundle.js"

MODES = ["cartoon", "surface", "plddt", "hydrophobicity", "interface"]
MODE_NOTES = {
    "cartoon": "ribbon cartoon; binder pink, target chains cyan family",
    "surface": "molecular surface (quality medium); same chain colours",
    "plddt": "cartoon coloured by the B-factor column (Boltz-2 folds carry pLDDT; blue = high)",
    "hydrophobicity": "cartoon coloured by residue hydrophobicity",
    "interface": "cartoon plus interface residues as amber ball-and-stick (4.5 A heavy-atom contact)",
}
PALETTE = [0xE879F9, 0x0099FF, 0x00D2FF, 0x03FFFF, 0x60A5FA, 0x34D399]


def display_path(path: Path) -> str:
    """Home-relative (~/...) form for the manifest, so it stays portable."""
    resolved = path.resolve()
    try:
        return "~/" + str(resolved.relative_to(Path.home()))
    except ValueError:
        return str(resolved)


def load_generator():
    spec = importlib.util.spec_from_file_location("make_molstar_explorer", GENERATOR)
    if spec is None or spec.loader is None:
        raise SystemExit(f"generator not found: {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_structure(path: Path):
    """Parse a PDB or mmCIF file into a Bio.PDB Structure."""
    from Bio.PDB import MMCIFParser, PDBParser

    if path.suffix.lower() in (".cif", ".mmcif"):
        return MMCIFParser(QUIET=True).get_structure(path.stem, str(path))
    return PDBParser(QUIET=True).get_structure(path.stem, str(path))


def to_pdb_text(structure) -> str:
    from Bio.PDB import PDBIO

    handle = io.StringIO()
    writer = PDBIO()
    writer.set_structure(structure)
    writer.save(handle)
    return handle.getvalue()


def remap_chains(pdb_text: str, mapping: dict) -> str:
    """Rewrite the chain-ID column (index 21) of ATOM/HETATM records."""
    lines = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")) and len(line) > 21 and line[21] in mapping:
            line = line[:21] + mapping[line[21]] + line[22:]
        lines.append(line)
    return "\n".join(lines) + "\n"


def chain_ids(structure) -> list:
    return sorted({chain.id.strip() for chain in structure.get_chains()})


def build_complex(binder_path: Path, target_path: Path, binder_chains: list):
    """Merge binder and target files; rename target chains that clash."""
    binder = read_structure(binder_path)
    target = read_structure(target_path)
    binder_text = to_pdb_text(binder)
    target_text = to_pdb_text(target)
    free = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in binder_chains]
    mapping = {}
    for cid in chain_ids(target):
        if cid in binder_chains:
            mapping[cid] = free.pop(0)
    if mapping:
        target_text = remap_chains(target_text, mapping)
    return binder_text + target_text


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--complex", type=Path, help="one complex file (PDB or mmCIF)")
    parser.add_argument("--binder", type=Path, help="binder file (with --target)")
    parser.add_argument("--target", type=Path, help="target file (with --binder)")
    parser.add_argument("--binder-chain", default="A",
                        help="binder chain ID(s), comma-separated (default: A)")
    parser.add_argument("--name", help="design name (default: complex file stem)")
    parser.add_argument("--out", type=Path, help="output directory")
    parser.add_argument("--modes", default=",".join(MODES),
                        help=f"comma-separated subset of: {','.join(MODES)}")
    parser.add_argument("--views", type=int, default=3, help="viewpoints per mode (default: 3)")
    parser.add_argument("--explorer", action="store_true",
                        help="also write the interactive explorer HTML")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE,
                        help="Mol* bundle to copy next to the page")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-ms", type=int, default=20000,
                        help="headless Chrome virtual-time budget per shot (surface needs the longest)")
    return parser.parse_args(argv)


def find_chrome() -> str:
    env = os.environ.get("PDT_CHROME")
    if env and Path(env).exists():
        return env
    for pattern in ("~/.cache/ms-playwright/*/chrome-linux64/chrome",
                    "~/.cache/ms-playwright/*/chrome-linux/chrome"):
        hits = sorted(glob.glob(str(Path(pattern).expanduser())))
        if hits:
            return hits[-1]
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(mac).exists():
        return mac
    raise SystemExit("no Chrome found; set PDT_CHROME")


def render_shot(chrome: str, page: Path, png: Path, mode: str, view: int,
                width: int, height: int, timeout_ms: int) -> tuple:
    url = f"file://{page}?shot=1&mode={mode}&view={view}"
    last_error = ""
    for _ in range(3):
        if png.exists():
            png.unlink()
        try:
            subprocess.run(
                [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--use-gl=swiftshader", "--enable-unsafe-swiftshader",
                 "--run-all-compositor-stages-before-draw",
                 f"--window-size={width},{height}", f"--virtual-time-budget={timeout_ms}",
                 f"--screenshot={png}", "--hide-scrollbars", url],
                check=True, capture_output=True, timeout=timeout_ms / 1000 + 60,
            )
            if png.exists() and png.stat().st_size > 20000:
                return (mode, view, png, "")
            last_error = f"png too small ({png.stat().st_size if png.exists() else 0} bytes)"
        except Exception as exc:  # noqa: BLE001 - retry any chrome failure
            last_error = str(exc)[:200]
    return (mode, view, png, last_error)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.complex and not (args.binder and args.target):
        raise SystemExit("give --complex FILE, or --binder FILE --target FILE")

    if args.complex:
        complex_path = args.complex.resolve()
        name = args.name or args.complex.stem
        source = [display_path(complex_path)]
        structure_text = to_pdb_text(read_structure(complex_path))
    else:
        name = args.name or args.binder.stem
        source = [display_path(args.binder), display_path(args.target)]
        structure_text = build_complex(args.binder.resolve(), args.target.resolve(),
                                       binder_chains=[c.strip() for c in args.binder_chain.split(",")])

    from Bio.PDB import PDBParser

    structure = PDBParser(QUIET=True).get_structure(name, io.StringIO(structure_text))[0]
    binder_chains = [c.strip() for c in args.binder_chain.split(",")]
    all_chains = chain_ids(structure)
    target_chains = [c for c in all_chains if c not in binder_chains]

    generator = load_generator()
    interface = generator.compute_interface(structure, binder_chains=set(binder_chains))
    colors = {}
    for ch in binder_chains:
        colors[ch] = PALETTE[0]
    for i, ch in enumerate(target_chains):
        colors[ch] = PALETTE[1 + (i % (len(PALETTE) - 1))]

    out = (args.out or Path.cwd() / "molstar_views" / name).resolve()
    out.mkdir(parents=True, exist_ok=True)
    caption = (f"{name} \u00b7 structure rendered from {Path(source[0]).name} \u00b7 "
               "a fold is a model, not a binding measurement")
    page_text = generator.build_page(
        structure=structure_text, interface=interface, colors=colors, design=name,
        caption=caption, binder_chains=binder_chains,
        pdblabel=f"{name} \u00b7 local structure \u2197")
    page = out / f"{name}_page.html"
    page.write_text(page_text)
    bundle_src = args.bundle if args.bundle.exists() else None
    if bundle_src is None:
        raise SystemExit(f"Mol* bundle not found: {args.bundle}")
    shutil.copy(bundle_src, out / "molstar-bundle.js")
    if args.explorer:
        (out / f"{name}_explorer.html").write_text(page_text)

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    chrome = find_chrome()
    jobs = [(m, v) for m in modes for v in range(args.views)]
    print(f"{name}: {len(jobs)} shots ({len(modes)} modes x {args.views} views), "
          f"{len(interface)} interface residues, chains {all_chains}")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(render_shot, chrome, page, out / f"{name}_{m}_view{v}.png",
                               m, v, args.width, args.height, args.timeout_ms)
                   for m, v in jobs]
        for fut in concurrent.futures.as_completed(futures):
            mode, view, png, error = fut.result()
            results.append((mode, view, png, error))
            print(f"  {png.name}: {'ok' if not error else 'FAILED ' + error}")

    results.sort(key=lambda r: (modes.index(r[0]), r[1]))
    failures = [r for r in results if r[3]]
    manifest = {
        "name": name,
        "source": source,
        "binder_chains": binder_chains,
        "target_chains": target_chains,
        "interface_residues": [list(t) for t in interface],
        "interface_count": len(interface),
        "modes": modes,
        "views": args.views,
        "view_note": "viewpoints 0/1/2 are 120-degree azimuth steps at 15-degree elevation",
        "mode_notes": {m: MODE_NOTES[m] for m in modes},
        "files": [r[2].name for r in results if not r[3]],
        "failures": [f"{r[0]}_view{r[1]}: {r[3]}" for r in failures],
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "note": ("Rendered from a predicted structure with Mol*; a fold is a model, "
                 "not a binding measurement."),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {out} ({len(manifest['files'])} images, "
          f"{len(failures)} failed)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
