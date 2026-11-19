"""Restrained-fold screening: score a directory of folded complexes.

Every challenge-4 campaign ran the same screen by hand from its own copy of
one script (eight copies of a CIF parser and an O(n^2) distance loop lived in
`challenges/04-tfr1/scripts/work/*-restrained-scores.py`). This is that screen
as one pipeline stage, driven by a spec instead of an edited constant block.

Spec params:

    designs: ~/c4-work/chai/designs   # <design>/out/pred.model_idx_<n>.cif + scores npz
    hotspots:                         # design-name prefix -> target positions
      e0:  [83, 87, 89, 90, 227, 250] # (label_seq_id, i.e. FASTA numbering)
      e12: [223, 253]
    models: 5
    cutoff: 5.0                       # A, binder residue counts as "at site"
    gate_max_dist: 8.0                # worst hotspot further than this = not engaged
    gate_min_residues: 1
    skip: ["_r2", "_s2"]              # name substrings to exclude

The gate is the point: ipTM alone promotes off-site poses (challenge 4
measured 0.696 for a binder sitting ~55 A from its epitope), so a read counts
only when the geometry agrees. `mean_iptm` is the engagement-gated mean --
the number campaign selection consumes.
"""
from __future__ import annotations

import csv

import numpy as np

from tools import common
from tools.analysis.contacts import cif_atoms, hotspot_engagement


def _hotspots_for(name: str, table: dict) -> list | None:
    for prefix, positions in table.items():
        if name.startswith(f"{prefix}_"):
            return list(positions)
    return None


def stage_score(ctx: common.RunContext) -> dict:
    designs_dir = ctx.resolve(ctx.param("designs", "designs"))
    if not designs_dir.is_dir():
        raise common.WaitingInputsError(f"no folded designs at {designs_dir}")
    table = ctx.param("hotspots") or {}
    if not table:
        raise ValueError("spec needs params.hotspots: {name_prefix: [positions]}")

    n_models = int(ctx.param("models", 5))
    cutoff = float(ctx.param("cutoff", 5.0))
    max_dist = float(ctx.param("gate_max_dist", 8.0))
    min_residues = int(ctx.param("gate_min_residues", 1))
    skip = list(ctx.param("skip", []))

    rows = []
    for design in sorted(p for p in designs_dir.iterdir() if p.is_dir()):
        if any(token in design.name for token in skip):
            continue
        hotspots = _hotspots_for(design.name, table)
        if hotspots is None:
            continue
        for model in range(n_models):
            cif = design / "out" / f"pred.model_idx_{model}.cif"
            npz = design / "out" / f"scores.model_idx_{model}.npz"
            if not cif.exists() or not npz.exists():
                continue
            read = hotspot_engagement(cif_atoms(cif), hotspots, cutoff=cutoff)
            scores = np.load(npz, allow_pickle=True)
            engaged = (read["worst_min_dist"] is not None
                       and read["worst_min_dist"] <= max_dist
                       and read["binder_residues"] >= min_residues)
            rows.append({
                "design": design.name,
                "model": model,
                "iptm": round(float(np.asarray(scores["iptm"]).reshape(-1)[0]), 3),
                "worst_hotspot_min_dist": read["worst_min_dist"],
                "binder_res_at_site": read["binder_residues"],
                "engaged": engaged,
            })

    if not rows:
        raise common.WaitingInputsError(
            f"{designs_dir} has no design matching params.hotspots keys {sorted(table)}")

    samples_csv = ctx.artifact("restrained-samples.csv")
    with samples_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    per_design = {}
    for row in rows:
        per_design.setdefault(row["design"], []).append(row)
    designs = []
    for name, samples in sorted(per_design.items()):
        gated = [s["iptm"] for s in samples if s["engaged"]]
        designs.append({
            "design": name,
            "n_samples": len(samples),
            "n_engaged": len(gated),
            # gated mean: an unengaged sample has no interface to score
            "mean_iptm": round(float(np.mean(gated)), 3) if gated else None,
            "best_iptm": max(s["iptm"] for s in samples),
        })

    designs_csv = ctx.artifact("restrained-designs.csv")
    with designs_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(designs[0]))
        writer.writeheader()
        writer.writerows(designs)

    engaged_designs = [d for d in designs if d["n_engaged"]]
    ctx.log(f"{len(rows)} samples over {len(designs)} designs; "
            f"{len(engaged_designs)} engage the site in at least one sample")
    return {
        "n_samples": len(rows),
        "n_designs": len(designs),
        "n_designs_engaged": len(engaged_designs),
        "gate": {"max_worst_dist": max_dist, "min_binder_residues": min_residues},
        "samples_csv": str(samples_csv),
        "designs_csv": str(designs_csv),
        "top": sorted((d for d in engaged_designs),
                      key=lambda d: -d["mean_iptm"])[:10],
    }


STAGES = {"score": stage_score}


def run(ctx: common.RunContext) -> dict:
    stages = ctx.spec.get("stages") or list(STAGES)
    unknown = [s for s in stages if s not in STAGES]
    if unknown:
        raise ValueError(f"unknown screen stages: {unknown} (have: {sorted(STAGES)})")
    summaries = []
    for name in stages:
        ctx.log(f"stage: {name}")
        part = STAGES[name](ctx)
        part["stage"] = name
        summaries.append(part)
    return {"stages": summaries}
