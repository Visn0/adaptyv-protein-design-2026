#!/usr/bin/env python3
"""Build a clean two-state panel from SUBMITTED sequences.

The swap question was answered with readings drawn from several fold batches,
which is not comparable, and the `evo` prefix means a name can belong to a
different generation than the arm measured. This builds one panel from one
source per design, so both states are folded from the same sequence in the
same batch:

  <design>__g12d.yaml   A=HLA, B=b2m, C=VVVGADGVGK, D=binder
  <design>__wt.yaml     A=HLA, B=b2m, C=VVVGAGGVGK, D=binder

Sources:
  --sub <csv>       binder sequence from a submission CSV (name,sequence)
  --gen4 <name>     binder sequence from the chain-D block of a gen-4 yaml

The HLA and b2m blocks, including their MSA paths, are copied from a template
yaml so the panel uses exactly the campaign's target definition.

Usage: PYTHONPATH= .venv/bin/python wt-panel-build.py
"""

from __future__ import annotations

import csv
import pathlib

import yaml

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


WORK = pathlib.Path.home() / "c5-work/wt-panel"
FOLDS = WORK / "folds"
TEMPLATE = pathlib.Path.home() / "c5-work/pr-batch/folds/pr-000.yaml"
SUB = _repo_root() / "challenges/05-pmhc/submission/submission-05-pmhc.csv"
GEN4 = pathlib.Path.home() / "c5-work/evo/gen4/folds"
WT_PEPTIDE = "VVVGAGGVGK"
G12D_PEPTIDE = "VVVGADGVGK"

# The entries below the organizer gate, per the 2026-11-08 review. Names are
# exactly as the submission CSV carries them: the 'evo' prefix is present on
# some entries and absent on others. Do not normalise it.
BELOW_GATE = [
    "peprim-wave1__run-012__design_0006__g12d__c3",
    "peprim-wave1__run-007__design_0004__g12d",
    "wave2-pep__run-054__design_0005__g12d",
    "wave2-pep__run-049__design_0002__g12d",
    "evorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K",
    "evonim-wave3__run-013__design_0003__g12d-E23K",
]
# The three the review proposed to restore. Their gen-4 parent yamls are gone
# from the tree (only -combo descendants remain), so each sequence is taken
# from chain D of that design's own G12D fold - the design that was measured.
RESTORE = [
    ("peprim-wave1__run-001__design_0002__g12d-W57K",
     "GSLERALALLEKLKAQLSDPDKVAVVEEAIARVQAAQAAKEAGDEEAYLTELTRANKGIAAVLRMLGVPESELSPILYASDPEAALVALVDMLEKKLA"),
    ("repair-nat-wave1__run-011__design_0004__g12d-N71K",
     "ALEARAAELIASSGSPYTAALIEAAVYGVSPALKEKLSVYLSAEEIAALEAAPTVEERLEVAIAIAKAQGKLVTARMLEELLALDK"),
    ("mini-wave1__run-011__design_0001__g12d__c5",
     "AADVEAAAASLEALYGIPIDLSKLTEKEKQLLVIISRVSGVAGSVGNAEAEALAKEALVALVVEKDYEKAVALTREAIAALEPAAPEAAAALKAELDALT"),
]


def template_blocks() -> tuple[dict, dict]:
    doc = yaml.safe_load(TEMPLATE.read_text())
    ch = {e["protein"]["id"]: e["protein"] for e in doc["sequences"]}
    return ch["A"], ch["B"]


def sub_sequences() -> dict[str, str]:
    out = {}
    with SUB.open(newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["name"]] = row["sequence"].strip()
    return out


def gen4_sequence(name: str) -> str | None:
    y = GEN4 / f"{name}.yaml"
    if not y.exists():
        return None
    doc = yaml.safe_load(y.read_text())
    for e in doc["sequences"]:
        p = e.get("protein") or {}
        if p.get("id") == "D":
            return p["sequence"].strip()
    return None


def write_panel(design: str, seq: str, hla: dict, b2m: dict) -> None:
    short = design.replace("evo", "", 1)
    for tag, peptide in (("g12d", G12D_PEPTIDE), ("wt", WT_PEPTIDE)):
        doc = {"version": 1, "sequences": [
            {"protein": dict(hla)},
            {"protein": dict(b2m)},
            {"protein": {"id": "C", "sequence": peptide, "msa": "empty"}},
            {"protein": {"id": "D", "sequence": seq, "msa": "empty"}},
        ]}
        (FOLDS / f"{short}__{tag}.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False))


def main() -> int:
    FOLDS.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists():
        print(f"no template: {TEMPLATE}")
        return 1
    hla, b2m = template_blocks()
    subs = sub_sequences()
    made, missing = 0, []
    for name in BELOW_GATE:
        seq = subs.get(name)
        if not seq:
            missing.append(name)
            continue
        write_panel(name, seq, hla, b2m)
        made += 2
        print(f"  sub  {name.replace('evo','',1)[:52]:52s} {len(seq)} aa")
    for name, seq in RESTORE:
        write_panel(name, seq, hla, b2m)
        made += 2
        print(f"  fold {name[:52]:52s} {len(seq)} aa")
    print(f"wrote {made} yamls into {FOLDS}")
    if missing:
        print(f"MISSING sequences for: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
