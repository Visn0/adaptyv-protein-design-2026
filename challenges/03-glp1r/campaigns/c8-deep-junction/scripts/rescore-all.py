#!/usr/bin/env python3
"""Rescore every folded design with the activation-geometry gate (robust parse).

Parses the scorer's report lines with regexes, so column padding cannot shift
fields. Writes one row per (design, sample) plus a per-design summary.
"""
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

WORK = Path.home() / "c3-work"
PY = WORK / "c8-agonism/.venv/bin/python"
SCORER = WORK / "c8-agonism/scorers/activation_geometry.py"

LINE = re.compile(
    r"len=\s*(\d+)\s+depth=\s*(-?\d+\.\d+)\s+"
    r"ecd/tmd/ic=\s*(\d+)/\s*(\d+)/\s*(\d+)\s+"
    r"met=(\d+)/6\s+(\w+)\s+"
    r"anion=\s*([\d.]+|-)\s+aromatic=\s*([\d.]+|-)\s+small=\s*([\d.]+|-)\s+"
    r"hbond=\s*([\d.]+|-)\s+hydrophobe=\s*([\d.]+|-)\s+ecl3=\s*([\d.]+|-)"
)

ROWS_CSV = WORK / "c8-agonism/rescore-rows.csv"
FORCE = "--rescore" in sys.argv

rows = []
if ROWS_CSV.is_file() and not FORCE:
    # The per-sample scores are the expensive half: one scorer subprocess per
    # model, thousands of cold starts. They only change when the folds or the
    # scorer change, so reuse them and re-derive just the per-design pick.
    # Pass --rescore to force the full run.
    with ROWS_CSV.open() as handle:
        for r in csv.DictReader(handle):
            r["depth"] = float(r["depth"])
            r["met"] = int(r["met"])
            rows.append(r)
    print(f"reusing {len(rows)} cached rows from {ROWS_CSV.name} "
          f"({len({r['design'] for r in rows})} designs); --rescore to redo")

designs = sorted({r.split(",")[0] for r in open(WORK / "folds-screen.csv").read().splitlines()[1:]})

# Incremental: score only the designs the cache does not already cover. A new
# campaign, or designs the screen picked up late, then cost one short run
# instead of redoing every model.
have = {r["design"] for r in rows}
todo = [d for d in designs if d not in have]
if rows and todo:
    print(f"scoring {len(todo)} design(s) missing from the cache: "
          f"{', '.join(todo[:8])}{' ...' if len(todo) > 8 else ''}")
elif rows:
    print("cache already covers every screened design")

for d in todo:
    pdir = WORK / "folds" / d / f"boltz_results_{d}" / "predictions" / d
    if not pdir.is_dir():
        continue
    for cif in sorted(pdir.glob("*_model_*.cif")):
        s = cif.stem.rsplit("_model_", 1)[1]
        out = subprocess.run(
            [str(PY), str(SCORER), str(cif), "--receptor-chain", "B",
             "--ligand-chain", "A", "--offset", "24"],
            capture_output=True, text=True, timeout=300,
        ).stdout
        m = LINE.search(out)
        if not m:
            continue
        g = m.groups()
        rows.append({
            "design": d, "sample": s, "len": g[0], "depth": float(g[1]),
            "ecd": g[2], "tmd": g[3], "ic": g[4], "met": int(g[5]), "tier": g[6],
            "anion": g[7], "aromatic": g[8], "small": g[9],
            "hbond": g[10], "hydrophobe": g[11], "ecl3": g[12],
        })
    # progress for the log
    print(f"{d}: {sum(1 for r in rows if r['design'] == d)} samples", flush=True)

if FORCE or not ROWS_CSV.is_file() or todo:
    with ROWS_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

by = defaultdict(list)
for r in rows:
    by[r["design"]].append(r)

ORDER = {"deep": 0, "shelf": 1, "groove": 2, "wrong_face": 3}
WRAP_DEPTH = 30.0  # select-top20.py: "Depth > 30 A (a wrapping pose) costs 1"


def rank_key(r):
    """Best tier, then the penalised feature count, then the shallower pose.

    The old key ended in `-r["depth"]`, which MAXIMISED insertion depth - the
    exact quantity the project's own rubric penalises as a wrapping pose. That
    promoted the deepest sample of each design, so designs recorded at depths
    far past the 30 A line were published as the full agonist pattern. This key
    applies the documented penalty instead of rewarding the thing it penalises.
    """
    met = r["met"] - (1 if r["depth"] > WRAP_DEPTH else 0)
    return (ORDER[r["tier"]], -met, r["depth"])


summary = []
for d, rs in by.items():
    b = min(rs, key=rank_key)
    deep = sum(1 for r in rs if r["tier"] == "deep")
    shelf = sum(1 for r in rs if r["tier"] == "shelf")
    summary.append({
        "design": d, "best_tier": b["tier"], "features": b["met"],
        "depth": b["depth"], "contacts": f"{b['ecd']}/{b['tmd']}/{b['ic']}",
        "deep_samples": deep, "shelf_samples": shelf, "samples": len(rs),
    })
summary.sort(key=lambda r: (ORDER[r["best_tier"]],
                            -(r["features"] - (1 if r["depth"] > WRAP_DEPTH else 0)),
                            r["depth"]))
with (WORK / "c8-agonism/rescore-summary.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0]))
    w.writeheader()
    w.writerows(summary)

tiers = defaultdict(int)
for r in summary:
    tiers[r["best_tier"]] += 1
print(f"\n{len(rows)} samples, {len(by)} designs; best-tier counts: {dict(tiers)}")
print("\nThe deep tier ranked by features then depth:")
for r in [s for s in summary if s["best_tier"] == "deep"][:20]:
    print(f"  {r['design']:36s} {r['features']}/6 d={r['depth']:5.1f} "
          f"deep {r['deep_samples']}/{r['samples']} shelf {r['shelf_samples']}/{r['samples']} "
          f"contacts {r['contacts']}")
