#!/usr/bin/env python3
"""Fold a third party's designs through OUR funnel, on OUR instrument.

The archive AethronPhantom/KRAS-G12D-pMHC-Designs-64 holds 64 designs made with
the same generator we use (pretrained RFD4-Proteina) and evaluated with the same
folder (Boltz-2 across mutant, wild-type and peptide-free). To compare the two
sets on one instrument, their binder sequences are folded here in both states,
one sequence source per design, and scored with the campaign's s1 scorer.

Selected scope: the designs they put forward for competition (status "selected
for pending submission" or "confirmed prior submission"). That is their chosen
set, so it compares like-for-like with our twenty.

Sources: ~/c5-work/rival-64/candidates.json (sequences live in the records).
HLA and b2m, with MSAs, are copied from the campaign template yaml.

Usage: PYTHONPATH= .venv/bin/python rival-panel-build.py
"""

from __future__ import annotations

import json
import pathlib

import yaml

RIVAL = pathlib.Path.home() / "c5-work" / "rival-64"
WORK = pathlib.Path.home() / "c5-work" / "rival-panel"
FOLDS = WORK / "folds"
TEMPLATE = pathlib.Path.home() / "c5-work" / "pr-batch" / "folds" / "pr-000.yaml"
WT_PEPTIDE = "VVVGAGGVGK"
G12D_PEPTIDE = "VVVGADGVGK"


def template_blocks() -> tuple[dict, dict]:
    doc = yaml.safe_load(TEMPLATE.read_text())
    ch = {e["protein"]["id"]: e["protein"] for e in doc["sequences"]}
    return ch["A"], ch["B"]


def chosen(cands: list[dict]) -> list[dict]:
    """Their competition entries, in archive order."""
    out = []
    for r in cands:
        status = (r.get("competition_status") or "").lower()
        if status.startswith("not "):
            continue
        if "submission" in status:
            out.append(r)
    return out


def write_panel(design: str, seq: str, hla: dict, b2m: dict) -> None:
    for tag, peptide in (("g12d", G12D_PEPTIDE), ("wt", WT_PEPTIDE)):
        doc = {"version": 1, "sequences": [
            {"protein": dict(hla)},
            {"protein": dict(b2m)},
            {"protein": {"id": "C", "sequence": peptide, "msa": "empty"}},
            {"protein": {"id": "D", "sequence": seq, "msa": "empty"}},
        ]}
        (FOLDS / f"rival-{design}__{tag}.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False))


def main() -> int:
    FOLDS.mkdir(parents=True, exist_ok=True)
    cands = json.loads((RIVAL / "candidates.json").read_text())
    hla, b2m = template_blocks()
    sel = chosen(cands)
    made = 0
    for r in sel:
        seq = (r.get("sequence") or "").strip()
        if not seq:
            print(f"  no sequence for {r.get('id')}")
            continue
        write_panel(r["id"], seq, hla, b2m)
        made += 2
        print(f"  {r['id']:8s} {len(seq):3d} aa  {(r.get('competition_status') or '')[:46]}")
    print(f"wrote {made} yamls for {len(sel)} designs into {FOLDS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
