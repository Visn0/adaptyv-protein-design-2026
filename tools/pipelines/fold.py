"""Fold pipeline: import a Boltz-2 co-fold and score every sample with IPSAE.

Stages:
    import   score each predicted sample (IPSAE + pDockQ2), write the metric
             table, embed the best model and the input backbone in the viewer,
             and carry the reference numbers (Tamarind) for comparison.

The fold itself runs outside this repo (Boltz-2 on a CUDA machine, or the
Tamarind service). This stage makes the result a first-class run: one run
folder, one report, one verdict — the same shape as every other experiment.

Params (spec `params:`):
    source          directory with the Boltz-2 outputs (the run's `boltz_results_*`
                    parent, or the `predictions/` directory itself)
    design          design id, used in labels and file names
    binder_chain    chain of the designed binder (default A)
    target_chains   the target chains (default B,C,D)
    input_pdb       optional: the RFD3 backbone the fold started from
    reference_csv   optional: per-model metrics of the comparison fold
                    (handoff/records/x2-fold-metrics.csv from Tamarind)
    reference_label name of that comparison (default Tamarind)
"""
from __future__ import annotations

import glob as _globmod
import shutil
import sys
from pathlib import Path

import pandas as pd

from tools import common
from tools.insights import BARS

DEFAULTS = {
    "source": "",
    "design": "",
    "binder_chain": "A",
    "target_chains": "B,C,D",
    "input_pdb": "",
    "reference_csv": "handoff/records/x2-fold-metrics.csv",
    "reference_label": "Tamarind",
    "ipsae_script": "~/tools/IPSAE/ipsae.py",
    "pae_cutoff": 10,
    "dist_cutoff": 10,
}

# The pre-registered acceptance line for a docked complex (AGENT.md rule 19).
# The numbers and the sentence live in tools/insights.py so the pass count and
# the verdict text can never disagree.
DOCK_BAR = BARS["dock"]


def _param(ctx: common.RunContext, key: str):
    value = ctx.param(key)
    if value in (None, ""):
        return DEFAULTS[key]
    return value


def _find_predictions(source: Path) -> Path:
    """Accept the boltz_results_* parent, the run dir, or the predictions dir."""
    if (source / "predictions").is_dir():
        return source / "predictions"
    hits = sorted(_globmod.glob(str(source / "boltz_results_*" / "predictions" / "*")))
    if hits:
        return Path(hits[-1])
    hits = sorted(_globmod.glob(str(source / "predictions" / "*")))
    if hits:
        return Path(hits[-1])
    raise common.WaitingInputsError(f"no Boltz-2 predictions under {source}")


def _copy_sample_inputs(ctx: common.RunContext, predictions: Path,
                        model: Path) -> tuple[Path, Path, Path, int]:
    """Copy one sample's four Boltz files into the run under their ORIGINAL names.

    IPSAE finds the pLDDT file by replacing "pae" with "plddt" in the PAE path,
    and the confidence JSON by replacing "pae"->"confidence" and ".npz"->".json".
    Renaming any of them makes IPSAE read no pLDDT and report pDockQ/pDockQ2 at
    their floor (0.018 / 0.005) with ipSAE unchanged — a silent wrong number.
    """
    stem, index = model.stem.rsplit("_model_", 1)
    names = {
        model.name: model,
        f"pae_{stem}_model_{index}.npz": predictions / f"pae_{stem}_model_{index}.npz",
        f"plddt_{stem}_model_{index}.npz": predictions / f"plddt_{stem}_model_{index}.npz",
        f"confidence_{stem}_model_{index}.json":
            predictions / f"confidence_{stem}_model_{index}.json",
    }
    copied: dict[str, Path] = {}
    for name, source in names.items():
        target = ctx.artifact(f"ipsae/{name}")
        if not source.exists():
            if name.startswith("plddt_"):
                ctx.log(f"warning: no {name} — pDockQ/pDockQ2 will read 0 for this sample")
            continue
        try:  # copy, do not pre-check: the Boltz directory may still be written to
            shutil.copy2(source, target)
        except FileNotFoundError as exc:
            raise common.WaitingInputsError(f"missing fold input {source}: {exc}") from exc
        copied[name] = target
    pae_name = f"pae_{stem}_model_{index}.npz"
    if pae_name not in copied:
        raise common.WaitingInputsError(f"no PAE matrix for {model.name}")
    confidence = copied.get(f"confidence_{stem}_model_{index}.json")
    return copied[model.name], copied[pae_name], confidence, int(index)


def _run_ipsae(ctx: common.RunContext, script: Path, model: Path, pae: Path,
               pae_cutoff: int, dist_cutoff: int) -> Path:
    """Run ipsae.py on one sample; returns the written report text file.

    The copied structure keeps its extension: ipsae.py picks its parser from the
    suffix, and a file without one is read as PDB (a mmCIF then fails with
    "invalid literal for int()").
    """
    common.run_cmd(ctx, [sys.executable, str(script), str(pae), str(model),
                         str(pae_cutoff), str(dist_cutoff)], cwd=model.parent)
    report = model.parent / (f"{model.stem}_{int(pae_cutoff):02d}"
                             f"_{int(dist_cutoff):02d}.txt")
    if not report.exists():
        raise RuntimeError(f"IPSAE wrote no report for {model.name}")
    return report


def _parse_ipsae(report: Path, binder: str, target: str) -> dict:
    """Pull the binder-vs-target rows out of an IPSAE report."""
    header, rows = None, []
    for line in report.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "Chn1":
            header = parts
        elif header and len(parts) == len(header):
            rows.append(dict(zip(header, parts)))
    out = {}
    for row in rows:
        if row.get("Chn1") == binder and row.get("Chn2") == target and row.get("Type") == "asym":
            out["ipsae_ab"] = float(row["ipSAE"])
            out["pdockq2_ab"] = float(row["pDockQ2"])
        if row.get("Chn1") == target and row.get("Chn2") == binder and row.get("Type") == "asym":
            out["ipsae_ba"] = float(row["ipSAE"])
            out["pdockq2_ba"] = float(row["pDockQ2"])
    if "ipsae_ab" in out and "ipsae_ba" in out:
        out["ipsae_min"] = min(out["ipsae_ab"], out["ipsae_ba"])
    return out


def stage_import(ctx: common.RunContext) -> dict:
    source = ctx.resolve(_param(ctx, "source"))
    if not source.exists():
        raise common.WaitingInputsError(f"fold output directory not found: {source}")
    design = str(_param(ctx, "design") or source.name)
    binder = str(_param(ctx, "binder_chain"))
    target = str(_param(ctx, "target_chains")).split(",")[0].strip()
    script = ctx.resolve(_param(ctx, "ipsae_script"))
    if not script.exists():
        raise common.WaitingInputsError(f"IPSAE script not found: {script}")
    pae_cutoff = int(_param(ctx, "pae_cutoff"))
    dist_cutoff = int(_param(ctx, "dist_cutoff"))

    predictions = _find_predictions(source)
    ctx.log(f"fold import: {design} from {predictions}")
    models = sorted(predictions.glob("*_model_*.cif")) or sorted(predictions.glob("*_model_*.pdb"))
    if not models:
        raise common.WaitingInputsError(f"no model files under {predictions}")

    rows = []
    for model in models:
        # The boltz input name itself can contain "_model_1", so split at the LAST
        # "_model_" (AGENT.md mistake 1: a loose prefix match reads the wrong file).
        work_model, work_pae, confidence, index = _copy_sample_inputs(ctx, predictions, model)
        report = _run_ipsae(ctx, script, work_model, work_pae, pae_cutoff, dist_cutoff)
        scores = _parse_ipsae(report, binder, target)
        if "ipsae_ab" not in scores:
            continue
        entry = {
            "sample": int(index),
            "ipsae_ab": scores["ipsae_ab"],
            "ipsae_ba": scores.get("ipsae_ba"),
            "ipsae_min": scores.get("ipsae_min"),
            "pdockq2_ab": scores["pdockq2_ab"],
            "model_file": model.name,
        }
        if confidence is not None and confidence.exists():
            conf = common.read_json(confidence)
            entry["iptm"] = conf.get("iptm")
            entry["ptm"] = conf.get("ptm")
        rows.append(entry)

    if not rows:
        raise RuntimeError("no sample could be scored")
    rows.sort(key=lambda item: item["sample"])
    table = pd.DataFrame(rows)
    table["passes_bar"] = ((table["ipsae_ab"] >= DOCK_BAR["ipsae"])
                           & (table["pdockq2_ab"] >= DOCK_BAR["pdockq2"]))
    metrics_csv = ctx.artifact("fold_metrics.csv")
    table.to_csv(metrics_csv, index=False)

    best = max(rows, key=lambda item: item["ipsae_ab"])
    suffix = Path(best["model_file"]).suffix
    viewer_model = ctx.artifact(f"viewer/{design}_model_{best['sample']}{suffix}")
    shutil.copy2(predictions / best["model_file"], viewer_model)
    viewer_files = [{
        "path": f"viewer/{design}_model_{best['sample']}{suffix}",
        "label": f"{design} — sample {best['sample']} (ipSAE {best['ipsae_ab']:.2f})",
        "note": f"Boltz-2 sample {best['sample']}: ipSAE({binder}-{target}) "
                f"{best['ipsae_ab']:.3f}, pDockQ2 {best['pdockq2_ab']:.3f}, "
                f"ipTM {best.get('iptm', float('nan')):.3f}",
    }]
    highlights = [{
        "file": 0, "selections": [binder], "color": "#e879f9", "repr": "cartoon",
        "label": "designed binder",
    }, {
        "file": 0, "selections": [" or ".join(str(_param(ctx, "target_chains")).split(","))],
        "color": "#60a5fa", "repr": "cartoon", "label": "target (TNF-alpha protomers)",
    }]
    input_pdb = ctx.resolve(str(_param(ctx, "input_pdb"))) if _param(ctx, "input_pdb") else None
    if input_pdb is not None and input_pdb.exists():
        target_copy = ctx.artifact(f"viewer/{design}_input.pdb")
        shutil.copy2(input_pdb, target_copy)
        viewer_files.append({
            "path": f"viewer/{design}_input.pdb",
            "label": f"{design} — the RFdiffusion3 backbone this fold started from",
            "note": "The generator output before folding: binder chain A, renumbered target.",
        })

    n_pass = int(table["passes_bar"].sum())
    reference_rows, reference_label = _reference_rows(ctx)
    comparison_csv = _write_comparison(ctx, rows, reference_rows, reference_label, binder, target)
    stage = {
        "n_samples": len(rows),
        "design": design,
        "ipsae": round(best["ipsae_ab"], 3),
        "ipsae_min": round(best.get("ipsae_min") or 0.0, 3),
        "pdockq2": round(best["pdockq2_ab"], 3),
        "iptm": round(best.get("iptm") or 0.0, 3),
        "n_pass": n_pass,
        "bar": DOCK_BAR["rule"],
        "tables": ["fold_metrics.csv"],
        "charts": _charts(comparison_csv, reference_rows, reference_label, binder, target),
        "viewer": {
            "files": viewer_files,
            "highlights": highlights,
            "note": "Blue = target trimer, pink = the designed binder. The viewer opens "
                    "on the best-scoring sample.",
        },
    }
    if reference_rows:
        stage["reference_fold"] = {
            "label": reference_label,
            "ipsae": max(row["ipsae_ab"] for row in reference_rows),
        }
    ctx.log(f"fold import: {len(rows)} samples, best ipSAE {best['ipsae_ab']:.3f}, "
            f"{n_pass} pass the bar")
    return stage


def _reference_rows(ctx: common.RunContext) -> tuple[list[dict], str]:
    """The comparison fold's per-sample numbers (Tamarind), when available."""
    path = Path(str(_param(ctx, "reference_csv")))
    if not path.is_absolute():
        path = ctx.challenge_dir / path
    if not path.exists():
        return [], str(_param(ctx, "reference_label"))
    frame = pd.read_csv(path)
    missing = [column for column in ("ipSAE_AB", "pDockQ2_AB") if column not in frame.columns]
    if missing:
        ctx.log(f"warning: {path.name} has no {missing} — no comparison numbers")
        return [], str(_param(ctx, "reference_label"))
    rows = []
    for index, row in frame.iterrows():
        try:
            rows.append({
                "sample": int(row.get("model", index)),
                "ipsae_ab": float(row["ipSAE_AB"]),
                "pdockq2_ab": float(row["pDockQ2_AB"]),
            })
        except (TypeError, ValueError) as exc:
            ctx.log(f"warning: {path.name} row {index} skipped: {exc}")
    if not rows:
        ctx.log(f"warning: {path.name} produced no comparison rows")
    return rows, str(_param(ctx, "reference_label"))


def _write_comparison(ctx: common.RunContext, rows: list[dict], reference_rows: list[dict],
                      reference_label: str, binder: str, target: str) -> str:
    """One table with both folds: the chart groups it by the `series` column."""
    records = [{
        "series": f"this run ({binder}-{target})",
        "sample": row["sample"],
        "ipsae_ab": round(row["ipsae_ab"], 4),
        "pdockq2_ab": round(row["pdockq2_ab"], 4),
        "source": "local GPU (Boltz-2)",
    } for row in rows]
    records += [{
        "series": f"{reference_label} (reference)",
        "sample": row["sample"],
        "ipsae_ab": round(row["ipsae_ab"], 4),
        "pdockq2_ab": round(row.get("pdockq2_ab") or 0.0, 4),
        "source": reference_label,
    } for row in sorted(reference_rows, key=lambda item: item["sample"])]
    path = ctx.artifact("fold_vs_reference.csv")
    pd.DataFrame(records).to_csv(path, index=False)
    return path.name


def _charts(comparison_csv: str, reference_rows: list[dict],
            reference_label: str, binder: str, target: str) -> list[dict]:
    """ipSAE per sample: this run against the comparison fold, one line each.

    A design the comparison never folded gets a single series — no invented
    reference line.
    """
    return [{
        "kind": "line", "source": comparison_csv, "x": "sample", "y": "ipsae_ab",
        "series": "series",
        "hlines": [[DOCK_BAR["ipsae"], f"acceptance {DOCK_BAR['ipsae']}"]],
        "title": f"ipSAE per sample — {binder} against {target}, this run vs {reference_label}",
        "note": "One point per Boltz-2 sample. Sample indices are independent draws "
                "when the seeds differ; compare the spread, not the row order.",
    }]


STAGES = {
    "import": stage_import,
}


def run(ctx: common.RunContext) -> dict:
    stages = ctx.spec.get("stages") or list(STAGES)
    unknown = [name for name in stages if name not in STAGES]
    if unknown:
        raise ValueError(f"unknown fold stages: {unknown} (have: {sorted(STAGES)})")
    stage_summaries = []
    for name in stages:
        ctx.log(f"stage: {name}")
        part = STAGES[name](ctx)
        part["stage"] = name
        stage_summaries.append(part)
    return {"stages": stage_summaries}
