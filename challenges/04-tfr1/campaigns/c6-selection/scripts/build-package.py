#!/usr/bin/env python3
"""Build the challenge-4 submission package, in the challenge-3 layout.

Mirrors challenge 3's `submission-package-*.zip`: the upload CSV, the
methodology, the design method, the prescreen report, the final candidates and
the self-evaluation. The candidates and the prescreen report are generated
from the committed records; nothing here is hand-maintained.

Usage:  .venv/bin/python campaigns/c6-selection/scripts/build-package.py [date]
        (date defaults to 2026-10-30, the day the twenty were frozen)

The submission folder holds exactly three files, as in challenge 3: the upload
CSV, methodology.md and design-method.md. Everything else this script produces
lands in records/ (candidates, prescreen report), notes/ (self-evaluation) or
the package zip at the challenge root.
"""
import csv
import pathlib
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
CH4 = HERE.parents[2]        # challenges/04-tfr1
SUB = CH4 / "submission"
RECORDS = CH4 / "records"
DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-10-30"

SUBMISSION = SUB / "submission-04-tfr1.csv"
METHODOLOGY = SUB / "methodology.md"
DESIGN_METHOD = SUB / "design-method.md"
SELF_EVAL = CH4 / "notes/self-evaluation.md"
CANDIDATES = CH4 / "records" / f"final-candidates-{DATE}.csv"
PRESCREEN = CH4 / "records" / f"prescreen-report-{DATE}.csv"
PACKAGE = CH4 / f"submission-package-{DATE}.zip"

# The prescreen report lives in the work area (the tool runs there); copy it in.
PRESCREEN_SRC = pathlib.Path.home() / "c4-work/c6/prescreen-out4/report.csv"


def build_candidates():
    """final-candidates: the twenty in selection order, with every read."""
    top20 = RECORDS / f"selection-top20-{DATE}.csv"
    rows = list(csv.DictReader(open(top20)))
    assert len(rows) == 20, f"expected 20 designs, found {len(rows)}"
    assert len({r["design"] for r in rows}) == 20, "duplicate design names"
    fields = ["design", "total", "score", "S", "X", "B", "E", "iptm", "mouse",
              "plddt", "hydro", "ipsae", "pdockq2", "family", "prescreen", "reason"]
    with CANDIDATES.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {CANDIDATES.name}: {len(rows)} designs, selection order")


def copy_prescreen():
    """Copy the prescreen run's report, reordered to the submission's row order.

    The run screened the same twenty designs in an earlier ordering (before the
    liability repairs swapped in). The rows are identical; only their order is
    made to match the upload file.
    """
    if not PRESCREEN_SRC.exists():
        print(f"WARNING: prescreen report not found at {PRESCREEN_SRC}; skipped")
        return False
    rows = list(csv.DictReader(open(PRESCREEN_SRC)))
    order = {r["name"]: i for i, r in enumerate(csv.DictReader(open(SUBMISSION)))}
    rows.sort(key=lambda r: order.get(r["id"], 10**6))
    with PRESCREEN.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {PRESCREEN.name}: {len(rows)} rows, submission order")
    return True


def build_zip():
    members = [SUBMISSION, METHODOLOGY, DESIGN_METHOD, CANDIDATES, PRESCREEN, SELF_EVAL]
    missing = [m for m in members if not m.exists()]
    if missing:
        raise SystemExit(f"missing package members: {[str(m) for m in missing]}")
    with zipfile.ZipFile(PACKAGE, "w", zipfile.ZIP_DEFLATED) as z:
        for m in members:
            z.write(m, m.name)
    print(f"wrote {PACKAGE.name}:")
    with zipfile.ZipFile(PACKAGE) as z:
        for n in z.namelist():
            print(f"  {z.getinfo(n).file_size:7d}  {n}")


if __name__ == "__main__":
    build_candidates()
    copy_prescreen()
    build_zip()
