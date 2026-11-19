#!/usr/bin/env python3
"""Build the figure pages for the complete-history document.

Two figures, three panels each:
  fig-jdi:      the JDI receptor on the mutant display, the healthy display,
                and the display with the peptide removed. Source: the C0
                built complexes (~/c5-work/c0/pdb/jdi-*.pdb), which keep the
                crystal chain letters A = HLA, B = b2m, C = peptide,
                D and E = the two receptor chains.
  fig-tristate: one submitted design (the A58K variant) folded in the three
                states. Source: its Boltz-2 folds; layout A = HLA, B = b2m,
                C = peptide, D = binder.

Pages land in viewers/multiview/fig-*.html; screenshot with headless
Chromium, then stitch with the paired shell steps.
"""

from __future__ import annotations

import io
import pathlib
import sys

import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "challenges" / "05-pmhc" / "viewers" / "scripts"))

from Bio.PDB import PDBIO, PDBParser  # noqa: E402

from tools.serve import molstar_viewer  # noqa: E402
import make_molstar_multiview as mm  # noqa: E402

CH = REPO / "challenges" / "05-pmhc"
OUT = CH / "viewers" / "multiview"
W = pathlib.Path.home() / "c5-work"

HLA = 0x60a5fa      # blue
B2M = 0x9ca3af      # gray
PEP = 0xf59e0b      # amber
TCR = 0xe879f9      # magenta (both receptor chains)
BINDER = 0xe879f9   # magenta


def focus_on(structure, center_chains, near_chains=(), radius_extra=16.0):
    """Centroid + radius of center_chains, optionally restricted to atoms
    within 15 A of near_chains."""
    pts = [a.get_coord() for c in structure if c.id in center_chains
           for a in c.get_atoms()]
    if near_chains:
        ref = [a.get_coord() for c in structure if c.id in near_chains
               for a in c.get_atoms()]
        if ref:
            near = [p for p in pts
                    if min(float(np.linalg.norm(p - q)) for q in ref) <= 15.0]
            pts = near or pts
    center = np.mean(pts, axis=0)
    rad = float(np.max(np.linalg.norm(pts - center, axis=1))) + radius_extra
    return {"center": [round(float(v), 2) for v in center],
            "radius": round(rad, 1)}


def pdb_text(structure):
    buf = io.StringIO()
    io_ = PDBIO()
    io_.set_structure(structure)
    io_.save(buf)
    return buf.getvalue()


def build_page(slug, title, pdb, chains, colors, focus):
    items = [{
        "id": "complex", "label": title, "color": colors.get(chains[0], TCR),
        "pdb": pdb, "chains": chains, "chainColors": colors, "interface": [],
        "focus": focus, "on": True, "scores": {},
    }]
    html = molstar_viewer.render_viewer_page(
        items, title=title, label=title, slug=slug, binder_chain="D")
    (OUT / f"{slug}.html").write_text(html)
    print(f"wrote {slug}.html")


def main() -> int:
    # ---- figure 1: the JDI in its three states --------------------------
    jdi = [
        ("fig-jdi-g12d", "JDI + mutant display", "jdi-g12d",
         ["A", "B", "C", "D", "E"], ["D", "E"], ["C"]),
        ("fig-jdi-wt", "JDI + healthy display", "jdi-wt",
         ["A", "B", "C", "D", "E"], ["D", "E"], ["C"]),
        ("fig-jdi-free", "JDI + display, no peptide", "jdi-peptidefree",
         ["A", "B", "D", "E"], ["D", "E"], ["A"]),
    ]
    for slug, title, src, chains, center, near in jdi:
        st = PDBParser(QUIET=True).get_structure("m", str(W / "c0" / "pdb" / f"{src}.pdb"))[0]
        colors = {"A": HLA, "B": B2M, "C": PEP, "D": TCR, "E": TCR}
        build_page(slug, title, pdb_text(st), chains, colors,
                   focus_on(st, center, near))

    # ---- figure 2: one design in the three states ------------------------
    design = "repair-wave4-pep__run-007__design_0002__g12d-A58K"
    tri = [
        ("fig-tri-g12d", "binder + mutant flag", W / "repair2" / "folds" / design),
        ("fig-tri-wt", "binder + healthy flag",
         W / "repair2" / "tristate" / "folds" / f"{design}__wt"),
        ("fig-tri-free", "binder + no flag",
         W / "repair2" / "tristate" / "folds" / f"{design}__free"),
    ]
    for slug, title, d in tri:
        cif = sorted(d.glob("boltz_results_*/predictions/*/*_model_0.cif"))
        if not cif:
            print(f"no fold for {slug}")
            continue
        st = mm.MMCIFParser(QUIET=True).get_structure("m", str(cif[0]))[0]
        rms, nfit, mode = mm.superpose_onto_crystal(st)
        chains = [c.id for c in st]
        colors = {"A": HLA, "B": B2M, "C": PEP, "D": BINDER}
        focus = (focus_on(st, ["D"], ["C"]) if "C" in chains
                 else focus_on(st, ["D"]))
        build_page(slug, title, pdb_text(st), chains, colors, focus)
        print(f"   (fit {mode} on {nfit} CA, RMSD {rms:.2f} A)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
