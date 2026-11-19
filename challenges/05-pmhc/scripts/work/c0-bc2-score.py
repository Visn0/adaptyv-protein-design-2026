#!/usr/bin/env python3
"""C0 third instrument: BindCraft2 `bindcraft score` over the C0 folds.

Runs the geometry pass on every boltz model of every arm and writes
records/bc2-score.csv. The BC2 output is one JSON object followed by a "#"
comment line, so the parser truncates at the comment.

Chain map in the C0 folds: A,B = TCR chains (binder); C,D,E = pMHC;
hotspots = the peptide ridge E4-E8 (10-mer register). The peptide-free arm
has no E chain and takes no hotspots.

Usage: .venv/bin/python c0-bc2-score.py
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[4]
RECORDS = REPO / "challenges/05-pmhc/campaigns/c0-instrument-calibration/records"
WORK = pathlib.Path.home() / "c5-work" / "c0t"
BC2 = pathlib.Path.home() / ".venvs/bindcraft2/bin/bindcraft"

ARMS = {
    "pos-g12d": ("A,B", "C,D,E", "E4,E5,E6,E7,E8"),
    "pos-wt": ("A,B", "C,D,E", "E4,E5,E6,E7,E8"),
    "neg-peptidefree": ("A,B", "C,D", ""),
    "neg-shuffled": ("A,B", "C,D,E", "E4,E5,E6,E7,E8"),
}
FIELDS = ["arm", "sample", "Hotspot_Contact_Fraction",
          "Off_Epitope_Contact_Fraction", "Interface_Residues",
          "Interface_BuriedArea", "All_Atom_Clashes"]


def bc2_score(cif: pathlib.Path, binder: str, target: str, hotspots: str):
    cmd = [str(BC2), "score", str(cif), "--binder", binder, "--target", target]
    if hotspots:
        cmd += ["--hotspots", hotspots]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = r.stdout
    cut = text.find("\n#")
    if cut >= 0:
        text = text[:cut]
    try:
        return json.loads(text)
    except Exception:
        return None


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    out = RECORDS / "bc2-score.csv"
    done: set[tuple[str, str]] = set()
    if out.exists():
        for r in csv.DictReader(out.open()):
            done.add((r["arm"], r["sample"]))
    fresh = not out.exists()
    # append per row: a killed run keeps its finished rows, and re-runs resume
    with out.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if fresh:
            w.writeheader()
        n = 0
        for arm, (binder, target, hotspots) in ARMS.items():
            preds = sorted((WORK / "folds" / arm).glob("boltz_results_*/predictions/*"))
            if not preds:
                continue
            for cif in sorted(preds[0].glob("*_model_*.cif")):
                if (arm, cif.stem) in done:
                    continue
                d = bc2_score(cif, binder, target, hotspots)
                if d is None:
                    print("FAILED", arm, cif.name, flush=True)
                    continue
                w.writerow({"arm": arm, "sample": cif.stem,
                            **{f: d.get(f) for f in FIELDS[2:]}})
                fh.flush()
                n += 1
                print(f"[{len(done) + n}] {arm} {cif.stem} hotspot "
                      f"{d.get('Hotspot_Contact_Fraction')} off-epitope "
                      f"{d.get('Off_Epitope_Contact_Fraction')}", flush=True)
    print(f"appended {n} rows to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
