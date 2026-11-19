#!/usr/bin/env python3
"""Two-for-two swap on measured evidence, 2026-11-08.

The clean two-state panel (one sequence source per design, one fold batch)
measured these reads on the organizer gate and the wild-type arm:

    OUT  peprim-wave1__run-007__design_0004__g12d     gate 0.486  WT 0.429  sep 0.057
    OUT  peprim-wave1__run-012__design_0006__g12d__c3 gate 0.411  WT 0.113  sep 0.298
    IN   repair-nat-wave1__run-011__design_0004__g12d-N71K  gate 0.676  WT 0.006  sep 0.670
    IN   peprim-wave1__run-001__design_0002__g12d-W57K     gate 0.641  WT 0.223  sep 0.418

Both additions pass the gate AND separate mutant from wild type better than
both removals, so each swap is a strict improvement on both criteria. Gate
compliance rises from 14 of 20 to 16 of 20.

NOT swapped: mini-wave1__run-011__design_0001__g12d__c5. It passes the gate
(0.635) but its wild-type read is 0.519, a separation of 0.116 - cross-reactive.
Swapping it in would trade the criterion that decides the challenge for a
better gate count.

The score column is left empty for the two additions. That column is already
known to mix two formulas (review, 2026-11-08); their composite inputs were not
recomputed, and inventing a third formula would make it worse, not better.

Usage: PYTHONPATH= .venv/bin/python swap-gate-restore.py
"""
from __future__ import annotations

import csv
import pathlib

C5 = pathlib.Path(__file__).resolve().parents[2]
SUB = C5 / "submission" / "submission-05-pmhc.csv"
FASTA = C5 / "records" / "final2" / "submission-top20.fasta"
SCORES = C5 / "records" / "selection-scores-05-pmhc.csv"

OUT = [
    "peprim-wave1__run-007__design_0004__g12d",
    "peprim-wave1__run-012__design_0006__g12d__c3",
]
IN = [
    ("evorepair-nat-wave1__run-011__design_0004__g12d-N71K",
     "ALEARAAELIASSGSPYTAALIEAAVYGVSPALKEKLSVYLSAEEIAALEAAPTVEERLEVAIAIAKAQGKLVTARMLEELLALDK"),
    ("evopeprim-wave1__run-001__design_0002__g12d-W57K",
     "GSLERALALLEKLKAQLSDPDKVAVVEEAIARVQAAQAAKEAGDEEAYLTELTRANKGIAAVLRMLGVPESELSPILYASDPEAALVALVDMLEKKLA"),
]


def matches(name: str, target: str) -> bool:
    """Same design, with or without the 'evo' prefix."""
    return name == target or name == "evo" + target or "evo" + name == target


def main() -> int:
    # ---- submission CSV: replace each OUT row in place with an IN row
    rows = list(csv.reader(SUB.open()))
    header, body = rows[0], rows[1:]
    queue = list(IN)
    new_body, dropped = [], []
    for r in body:
        if any(matches(r[0], o) for o in OUT):
            dropped.append(r[0])
            if queue:
                name, seq = queue.pop(0)
                new_body.append([name, seq, "single_chain"])
            continue
        new_body.append(r)
    with SUB.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(new_body)
    print(f"CSV: dropped {len(dropped)}, added {len(IN)}, rows now {len(new_body)}")

    # ---- FASTA: same order as the CSV
    lines = []
    for r in new_body:
        lines.append(f">{r[0]}")
        lines.append(r[1])
    FASTA.write_text("\n".join(lines) + "\n")
    n_fa = sum(1 for l in lines if l.startswith(">"))
    print(f"FASTA: {n_fa} records")

    # ---- selection scores: same operations, score left empty for the additions
    srows = list(csv.reader(SCORES.open()))
    s_head, s_body = srows[0], srows[1:]
    squeue = [n for n, _ in IN]
    s_new = []
    for r in s_body:
        if any(matches(r[0], o) for o in OUT):
            if squeue:
                s_new.append([squeue.pop(0), ""])
            continue
        s_new.append(r)
    with SCORES.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(s_head)
        w.writerows(s_new)
    print(f"scores: {len(s_new)} rows (empty score on the two additions)")

    # ---- verify
    names_csv = [r[0] for r in new_body]
    names_fa = [l[1:] for l in lines if l.startswith(">")]
    names_sc = [r[0] for r in s_new]
    ok = len(names_csv) == len(names_fa) == len(names_sc) == 20
    same = names_csv == names_fa == names_sc
    print(f"counts 20/20/20: {ok}; orders identical: {same}")
    for n, s in IN:
        print(f"  present: {n} -> csv {n in names_csv}, fasta {n in names_fa}, scores {n in names_sc}")
    for o in OUT:
        print(f"  removed: {o} -> csv {not any(matches(x, o) for x in names_csv)}")
    return 0 if (ok and same) else 1


if __name__ == "__main__":
    raise SystemExit(main())
