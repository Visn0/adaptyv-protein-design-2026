#!/usr/bin/env python3
"""Build the final challenge-3 candidate list in the selection order.

Reads the ranked selection (selection-top20.csv), pulls each design's sequence
from its fold yaml, and writes the candidates CSV that
make_competition_csv.py turns into the upload file. Run after the c9 pipeline.
"""
import collections
import csv
import pathlib

W = pathlib.Path.home() / "c3-work"
seqs = {}
for y in (W / "folds").glob("*.yaml"):
    txt = y.read_text().splitlines()
    for i, line in enumerate(txt):
        if line.strip() == "id: A":
            seqs[y.stem] = txt[i + 1].split("sequence:")[1].strip()
            break

# Selection lives entirely in select-top20.py. The family map, the cap and the
# near-duplicate filter used to be duplicated here and silently produced a
# different twenty; this script only attaches sequences to that script's result.

ranked = list(csv.DictReader(open(W / "c8-agonism/selection-top20.csv")))
rows = []
for r in ranked:
    seq = seqs.get(r["design"], "")
    if not seq:
        print(f"missing sequence for {r['design']}")
        continue
    rows.append({"design": r["design"], "sequence": seq,
                 "family": r["family"], "score": r["score"]})

out = W / "final-candidates.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["design", "score", "sequence", "family"])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {out}: {len(rows)} designs, in select-top20.py's order")
for i, r in enumerate(rows, 1):
    print(f"  {i:2d}. {r['design']:26s} {float(r['score']):5.1f}  {r['family']}")
print("families:", dict(collections.Counter(r["family"] for r in rows)))
