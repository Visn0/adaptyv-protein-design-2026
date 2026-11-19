"""Prepare the design carousel structures for the Blender render.

For every design of the campaign that has a co-fold on disk against the HUMAN
TNF-alpha construct, superpose its target chains onto one common reference
target and write the binder in that frame.  One PDB per design + one shared
target PDB + a manifest, all in `--outdir`.

The set is rebuilt from the campaign records each run (no stale lists):

- scores: `challenges/02-tnfa/notes/genie3/genie3-all-scores.csv`
- folds:  `~/c2-work/genie3/folds/<design>/boltz_results_<design>/predictions/<design>/`
- keep:   at_site == True and best ipSAE >= --min-ipsae (0.6 = the calibrated
          discard line), one entry per unique binder sequence
- name:   the submitted name when the sequence is in the submission set, else
          the shortest known name
- order:  best ipSAE, descending

Run with the repo venv:  .venv/bin/python .../prep_carousel.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import warnings
from pathlib import Path

from Bio.PDB import MMCIFParser, PDBIO, Superimposer
from Bio.PDB.PDBExceptions import PDBConstructionWarning

warnings.simplefilter("ignore", PDBConstructionWarning)

HUMAN = ("RTPSDKPVAHVVANPQAEGQLQWLNRRANALLANGVELRDNQLVVPSEGLYLIYSQVLFKGQGC"
         "PSTHVLLTHTISRIAVSYQTKVNLLSAIKSPCQRETPEGAEAKPWYEPIYLGGVFQLEKGDRLS"
         "AEINRPDYLLFAESGQVYFGIIAL")

SUBMITTED = {
    "sr2-ds-mce-14-v6-r2c", "sr2-ds2-mce-14-v7-v1-r2a", "sr2-ds-mce-14-v6-r2a",
    "sr6-r37", "sr1-mce-14-b", "ds-mce-14-v6", "ds2-mce-14-v7-v1",
    "e1b-d7x-t3-3-v6",
}

FOLDS = Path.home() / "c2-work/genie3/folds"
SCORES = (Path(__file__).resolve().parents[2] / "notes/genie3"
          / "genie3-all-scores.csv")

TARGET_CHAINS = ("B", "C", "D")
BINDER_CHAIN = "A"


def read_fold(path: Path) -> dict | None:
    """Binder chain/sequence and human-target flag from a fold YAML."""
    try:
        txt = path.read_text()
    except OSError:
        return None
    chains = dict(re.findall(r"id: ([A-Z])\n\s+sequence: ([A-Z]+)", txt))
    if not chains:
        return None
    binder = min(chains, key=lambda c: len(chains[c]))
    human = any(chains.get(c, "") == HUMAN for c in TARGET_CHAINS)
    return dict(binder=binder, seq=chains[binder], human=human)


def build_set(min_ipsae: float) -> list[dict]:
    rows = list(csv.DictReader(SCORES.open()))
    best: dict[str, tuple[float, int, bool]] = {}
    for r in rows:
        try:
            s = float(r["ipsae"] or 0)
        except ValueError:
            continue
        d = r["design"]
        if d not in best or s > best[d][0]:
            best[d] = (s, int(r["sample"]), r["at_site"] == "True")

    folds = {p.stem: read_fold(p) for p in sorted(FOLDS.glob("*.yaml"))
             if p.with_suffix("").is_dir()}
    folds = {k: v for k, v in folds.items() if v}

    # per unique binder sequence: best score, all names, human fold dirs
    by_seq: dict[str, dict] = {}
    for name, f in folds.items():
        if not f["human"]:
            continue
        e = by_seq.setdefault(f["seq"], dict(score=0.0, at_site=False,
                                             names=set(), dirs=[]))
        e["names"].add(name)
        e["dirs"].append(name)
        if name in best:
            s, _, at = best[name]
            e["score"] = max(e["score"], s)
            e["at_site"] = e["at_site"] or at
    # names that scored but whose own fold is mouse-only still belong to the seq
    for name, (s, _, at) in best.items():
        f = folds.get(name)
        if f and not f["human"]:
            e = by_seq.get(f["seq"])
            if e is not None:
                e["names"].add(name)
                e["score"] = max(e["score"], s)
                e["at_site"] = e["at_site"] or at

    entries = []
    for seq, e in by_seq.items():
        if not e["at_site"] or e["score"] < min_ipsae:
            continue
        subs = sorted(n for n in e["names"] if n in SUBMITTED)
        display = subs[0] if subs else min(e["names"], key=lambda n: (len(n), n))
        # structure: the human fold with the display name, else the best dir
        src = display if display in e["dirs"] else max(
            e["dirs"], key=lambda n: best.get(n, (0, 0, False))[0])
        sample = best.get(src, (e["score"], 0, False))[1]
        entries.append(dict(name=display, score=round(e["score"], 3),
                            dir=src, sample=sample, seq=seq))
    entries.sort(key=lambda x: (-x["score"], x["name"]))
    return entries


def cif_path(design_dir: str, sample: int) -> Path:
    d = (FOLDS / design_dir / f"boltz_results_{design_dir}" / "predictions"
         / design_dir)
    return d / f"{design_dir}_model_{sample}.cif"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-ipsae", type=float, default=0.6)
    ap.add_argument("--outdir",
                    default=str(Path.home() / "c2-work/mn-anim/carousel"))
    args = ap.parse_args()
    out = Path(args.outdir) / "structures"
    out.mkdir(parents=True, exist_ok=True)

    entries = build_set(args.min_ipsae)
    print(f"[prep] {len(entries)} designs at_site >= {args.min_ipsae}")

    parser = MMCIFParser(QUIET=True)
    io = PDBIO()

    ref_model = None
    ref_ca = None
    manifest = []
    for i, e in enumerate(entries, 1):
        path = cif_path(e["dir"], e["sample"])
        if not path.exists():
            print(f"[prep] MISSING {path}")
            continue
        model = parser.get_structure("m", str(path))[0]
        if any(c not in model for c in TARGET_CHAINS + (BINDER_CHAIN,)):
            print(f"[prep] chain layout unexpected in {path}: "
                  f"{[c.id for c in model]} — skipped")
            continue
        target_ca = [a for c in TARGET_CHAINS for a in model[c].get_atoms()
                     if a.name == "CA"]
        if ref_ca is None:
            ref_model, ref_ca = model, target_ca
        if len(target_ca) != len(ref_ca):
            print(f"[prep] CA count mismatch for {e['name']}: "
                  f"{len(target_ca)} vs {len(ref_ca)} — skipped")
            continue
        sup = Superimposer()
        sup.set_atoms(ref_ca, target_ca)
        sup.apply(model.get_atoms())

        p = out / f"binder_{i:02d}_{e['name']}.pdb"
        io.set_structure(model[BINDER_CHAIN])
        io.save(str(p))
        n_ca = sum(1 for a in model[BINDER_CHAIN].get_atoms() if a.name == "CA")
        manifest.append(dict(idx=i, name=e["name"], score=e["score"],
                             src=e["dir"], sample=e["sample"],
                             binder_file=p.name, n_ca=n_ca))
        print(f"[prep] {i:2d}. {e['name']:28s} {e['score']:.3f} "
              f"<- {e['dir']} model_{e['sample']}  ({n_ca} aa)")

    if ref_model is not None:
        ref_model.detach_child(BINDER_CHAIN)
        io.set_structure(ref_model)
        io.save(str(out / "target.pdb"))
        print(f"[prep] target.pdb written from {entries[0]['dir']} "
              f"model_{entries[0]['sample']}")
    (Path(args.outdir) / "manifest.json").write_text(
        json.dumps(manifest, indent=1))
    print(f"[prep] manifest: {len(manifest)} designs -> "
          f"{Path(args.outdir) / 'manifest.json'}")


if __name__ == "__main__":
    main()
