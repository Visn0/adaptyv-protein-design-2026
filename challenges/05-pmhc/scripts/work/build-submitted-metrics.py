#!/usr/bin/env python3
"""Write the metrics table of the nineteen submitted designs.

One row per submitted design, in submission order (which is the ranking of
record).  Every number is read, not computed here:

    score              records/selection-scores-05-pmhc.csv
    peptide_read_g12d  the gate instrument - mean peptide ipSAE over the five
                       boltz models.  The clean two-state panel of 2026-11-08
                       where the design ran there, otherwise the design's own
                       campaign `s1-summary.csv`.  Lowest reading when a design
                       was folded more than once in the chosen source.
    ipdae_pep_g12d     mean interface pDAE against the peptide, from the same
                       row as the read above - the metric the 2026-10-30
                       benchmark ranks first
    e_score            the Coulomb E-score against the P6 aspartate
    gate               pass when peptide_read_g12d >= 0.61

Wild-type reads are deliberately absent: the recorded WT folds come from
several different batches, and mixing them would put separations on the record
that no single panel measured.  The four below-gate entries carry their
clean-panel WT reads in `records/final-cut-2026-11-08.md` instead.

    .venv/bin/python challenges/05-pmhc/scripts/work/build-submitted-metrics.py
"""
from __future__ import annotations

import csv
import glob
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CH5 = REPO / "challenges/05-pmhc"
WORK = Path.home() / "c5-work"
OUT = CH5 / "records/submitted-19-metrics-2026-11-08.csv"
GATE = 0.61

FAMILY = {"pep": "PEP hotspot set", "peprim": "PEPRIM hotspot set",
          "mini": "MINI hotspot set", "nat": "NATURAL hotspot set",
          "nim": "wave-3 NIM set"}


def summary_reads() -> dict[str, list[tuple[float, float | None, str]]]:
    """design -> [(peptide ipSAE, peptide i_pDAE, source)] from the *summary* files.

    Both numbers come off one row, so the panel never mixes two fold batches.
    """
    reads: dict[str, list[tuple[float, float | None, str]]] = {}
    for path in sorted(glob.glob(str(WORK / "**/*summary*.csv"), recursive=True)):
        with open(path, newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "peptide_read" not in reader.fieldnames:
                continue
            for row in reader:
                design = (row.get("design") or "").strip()
                try:
                    value = float(row["peptide_read"])
                except (TypeError, ValueError):
                    continue
                try:
                    ipdae = float(row.get("ipdae_pep", ""))
                except (TypeError, ValueError):
                    ipdae = None
                if design:
                    reads.setdefault(design, []).append(
                        (value, ipdae, os.path.relpath(path, WORK)))
    return reads


def e_scores() -> dict[str, set[float]]:
    """design -> every recorded E-score, from the work tables and the records."""
    out: dict[str, set[float]] = {}
    paths = glob.glob(str(WORK / "**/*.csv"), recursive=True)
    paths += glob.glob(str(CH5 / "**/*.csv"), recursive=True)
    for path in paths:
        try:
            rows = list(csv.DictReader(open(path, newline="")))
        except OSError:
            continue
        if not rows:
            continue
        columns = list(rows[0])
        e_col = next((c for c in columns if c in ("E", "E_D6")), None)
        d_col = next((c for c in columns if c in ("design", "name")), None)
        if not (e_col and d_col):
            continue
        for row in rows:
            try:
                out.setdefault(row[d_col], set()).add(float(row[e_col]))
            except (TypeError, ValueError, KeyError):
                pass
    return out


def candidate_keys(name: str) -> list[str]:
    """The names a fold batch may have used: the evolution prefix and the state."""
    bases = [name] + ([name[3:]] if name.startswith("evo") else [])
    return [base + suffix for base in bases for suffix in ("", "__g12d")]


def chosen_row(name: str, reads: dict) -> tuple[float, float | None] | None:
    """The reading of record: the clean panel where it ran, else the campaign."""
    hits = [h for key in candidate_keys(name) for h in reads.get(key, [])]
    panel = [h for h in hits if h[2].startswith("wt-panel")]
    use = panel or hits
    if not use:
        return None
    best = min(use, key=lambda h: h[0])
    return best[0], best[1]


def family(name: str) -> str:
    """The generator line, read from the design name alone."""
    base = re.sub(r"^(evo|evorepair-|repair-)+", "", name)
    match = re.match(r"([a-z]+)-wave(\d)", base) or re.match(r"wave(\d)-([a-z]+)", base)
    if not match:
        tag, wave = "", "?"
    elif base.startswith("wave"):
        wave, tag = match.group(1), match.group(2)
    else:
        tag, wave = match.group(1), match.group(2)
    label = FAMILY.get(tag.lower(), f"{tag or 'unknown'} set")
    line = f"RFdiffusion4 (NIM) · {label}, wave {wave}"
    if name.startswith(("evorepair", "repair-")):
        return line + " · charge-repair child"
    if name.startswith("evo"):
        return line + " · evolution-loop child"
    return line


def main() -> None:
    reads, e_table = summary_reads(), e_scores()
    scores = {r["design"]: r["score"] for r in
              csv.DictReader(open(CH5 / "records/selection-scores-05-pmhc.csv"))}
    rows = []
    for rank, row in enumerate(csv.DictReader(
            open(CH5 / "submission/submission-05-pmhc.csv")), start=1):
        name = row["name"]
        chosen = chosen_row(name, reads)
        read, ipdae = chosen if chosen else (None, None)
        bare = name[3:] if name.startswith("evo") else name
        e_values = e_table.get(name) or e_table.get(bare) or set()
        mutation = name.split("__g12d")[-1].lstrip("-")
        rows.append({
            "rank": rank,
            "design": name,
            "score": scores.get(name, ""),
            "peptide_read_g12d": f"{read:.3f}" if read is not None else "",
            "ipdae_pep_g12d": f"{ipdae:.3f}" if ipdae is not None else "",
            "e_score": f"{max(e_values):.2f}" if e_values else "",
            "gate": "pass" if (read is not None and read >= GATE) else "below",
            "length_aa": len(row["sequence"]),
            "molecule_class": row["molecule_class"],
            "family": family(name),
            "mutation": mutation if mutation and not mutation.startswith("_") else "",
        })
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(f"{r['rank']:2d} {r['design'][-42:]:<42} score={r['score']:>5} "
              f"read={r['peptide_read_g12d']:>5} E={r['e_score']:>6} "
              f"{r['gate']:<5} {r['family']}")
    assert len(rows) == 19, len(rows)
    assert sum(r["gate"] == "pass" for r in rows) == 16, "the gate count moved"
    print(f"\nwrote {OUT.relative_to(REPO)} ({len(rows)} designs, "
          f"{sum(r['gate'] == 'pass' for r in rows)} above the gate)")


if __name__ == "__main__":
    main()
