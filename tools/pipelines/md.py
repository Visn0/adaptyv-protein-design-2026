"""All-atom molecular-dynamics pipeline (OpenMM, implicit solvent).

Real physics for one designed complex. The pipeline simulates the predicted
target-binder complex twice: once with the designed switch histidine
protonated (the low-pH state) and once with it neutral (the high-pH state).
The comparison shows whether the designed His-carboxylate contact behaves
differently in the two states, and whether the predicted pose holds.

Stages (any subset, executed in this order):
    prepare  fix the fold and set the histidine states -> prepared_<ph>.pdb
    low      MD at the low-pH state (switch His protonated, +1)
    high     MD at the high-pH state (switch His neutral)
    compare  both timelines -> md_compare.csv, charts, player page, viewer files

Chain convention, same as the challenge pipelines: binder = chain B,
target = chain A. Distances in Angstrom. OpenMM reports in kJ/mol and nm.

Honesty rules for every caption this pipeline produces:
- A short run like this is a physics test of the predicted pose. It is not
  a binding assay, and it is not a free-energy calculation.
- The template force field cannot change protonation during a run. The two
  runs differ only in the histidine state set at the start.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from tools import common
from tools.md import analyze, player, prepare
from tools.md.simulate import run_md

DEFAULTS = {
    "design": "egfr_ph_l95_s898818_mpnn12_H47",
    "folds_dir": "data/colabfold/result",
    "switch_his": 47,
    "ph_low": 6.5,
    "ph_high": 7.4,
    "length_ps": 1000.0,
    "save_every_ps": 5.0,
    "equil_ps": 60.0,
    "temperature_k": 300.0,
    "ionic_strength": 0.15,
    "movie_frames": 48,
    "player_frames": 24,
    "seed": 7,
}

STATES = {
    "low": {"ph_key": "ph_low", "resname": "HIP",
            "label": "pH 6.5 · His protonated (+1)"},
    "high": {"ph_key": "ph_high", "resname": None,  # None -> the picked tautomer
             "label": "pH 7.4 · His neutral"},
}


def _params(ctx: common.RunContext) -> dict:
    return {key: ctx.param(key, value) for key, value in DEFAULTS.items()}


def _state_ph(params: dict, state: str) -> float:
    return float(params[STATES[state]["ph_key"]])


def _prepared_path(ctx: common.RunContext, params: dict, state: str) -> Path:
    return ctx.artifact(f"md/prepared_{_state_ph(params, state):g}.pdb")


def _load_pairs(ctx: common.RunContext) -> dict:
    pairs_path = ctx.artifact("md/md_pairs.json")
    if not pairs_path.exists():
        raise common.WaitingInputsError(
            "md_pairs.json is missing. Run the prepare stage first: "
            "pdt exp run <an md spec>")
    return common.read_json(pairs_path)


# ------------------------------------------------------------------ stages

def stage_prepare(ctx: common.RunContext) -> dict:
    params = _params(ctx)
    design = str(params["design"])
    folds_dir = ctx.resolve(str(params["folds_dir"]))
    fold = prepare.find_fold(folds_dir, design)
    if fold is None:
        raise common.WaitingInputsError(
            f"no fold file for {design} in {folds_dir} (restore with: pdt fetch-data)")

    base_path = ctx.artifact("md/prepared_base.pdb")
    fix_report = prepare.complete_structure(fold, base_path)
    ctx.log(f"prepared {base_path.name}: {fix_report['atoms']} atoms from {fold.name}")

    switch_his = int(params["switch_his"])
    pairs = prepare.nearest_carboxylate_pairs(base_path, "B", switch_his)
    tautomer = prepare.pick_neutral_tautomer(pairs)
    tracked = [entry for entry in pairs if entry["distance"] <= 4.6] or pairs
    nearest = tracked[0] if tracked else None
    if nearest is None:
        raise ValueError(
            f"no carboxylate within reach of {design} chain B residue {switch_his}. "
            "Check the switch_his parameter.")

    text = base_path.read_text()
    low_text, n_low = prepare.set_his_state(text, "B", switch_his, "HIP")
    high_text, n_high = prepare.set_his_state(text, "B", switch_his, tautomer)
    if n_low == 0 or n_high == 0:
        raise ValueError(
            f"chain B residue {switch_his} is not a histidine in {fold.name}")
    low_path = _prepared_path(ctx, params, "low")
    high_path = _prepared_path(ctx, params, "high")
    low_path.write_text(low_text)
    high_path.write_text(high_text)
    ctx.log(f"switch His B{switch_his}: low state HIP, high state {tautomer} "
            f"({n_low} atoms renamed per state)")

    target_label = f"{nearest['target_resname']}{nearest['target_resnum']}"
    pairs_doc = {
        "design": design,
        "fold": str(fold),
        "switch_his": switch_his,
        "switch_target": target_label,
        "min_distance_A": nearest["distance"],
        "within_hbond_range": nearest["distance"] <= 4.0,
        "states": {
            "low": {"ph": _state_ph(params, "low"), "resname": "HIP"},
            "high": {"ph": _state_ph(params, "high"), "resname": tautomer},
        },
        "pairs": tracked,
    }
    common.write_json(ctx.artifact("md/md_pairs.json"), pairs_doc)

    from tools.analysis.contacts import interface_contacts

    iface = interface_contacts(base_path, ["B"], ["A"])
    ctx.log(f"interface: {len(iface['binder_resi'])} design residues + "
            f"{len(iface['target_resi'])} target residues, "
            f"{iface['n_atom_pairs']} atom pairs within 4.5 A")

    viewer_entry = {
        "path": "md/prepared_base.pdb",
        "label": f"{design} · start pose · His{switch_his}-{target_label} "
                 f"{nearest['distance']} A",
        "highlights": [
            {"selections": ["A"], "color": "#60a5fa", "repr": "cartoon", "opacity": 0.98},
            {"selections": ["B"], "color": "#e879f9", "repr": "cartoon", "opacity": 0.98},
            {"selections": [f"{switch_his}:B", f"{nearest['target_resnum']}:A"],
             "color": "#fbbf24", "repr": "ball+stick"},
        ],
        "note": "Blue = target. Pink = the designed binder. Amber = the designed "
                "switch: the grafted histidine and its partner carboxylate. "
                "This is the AlphaFold pose before any dynamics.",
    }
    return {
        "stage": "prepare",
        "md_prepared_atoms": int(fix_report["atoms"]),
        "md_switch_his": f"B{switch_his} → {target_label}",
        "md_start_distance_A": float(nearest["distance"]),
        "md_interface_residues": int(len(iface["binder_resi"]) + len(iface["target_resi"])),
        "states": pairs_doc["states"],
        "viewer": {
            "select": True,
            "files": [viewer_entry],
            "note": "The prepared start pose. The two MD runs start from exactly "
                    "this structure and differ only in the histidine state.",
        },
    }


def _state_stage(ctx: common.RunContext, state: str) -> dict:
    params = _params(ctx)
    doc = _load_pairs(ctx)
    prepared = _prepared_path(ctx, params, state)
    if not prepared.exists():
        raise common.WaitingInputsError(
            "prepared structure is missing. Run the prepare stage first: "
            "pdt exp run <an md spec>")

    ph = _state_ph(params, state)
    resname = doc["states"][state]["resname"]
    ctx.log(f"stage {state}: pH {ph}, switch histidine as {resname}")

    prefix = ctx.artifact(f"md/{state}")
    run_info = run_md(
        prepared, prefix,
        length_ps=float(params["length_ps"]),
        save_every_ps=float(params["save_every_ps"]),
        equil_ps=float(params["equil_ps"]),
        temperature_k=float(params["temperature_k"]),
        ionic_strength_molar=float(params["ionic_strength"]),
        seed=int(params["seed"]),
        log=ctx.log,
    )

    stats = analyze.analyze_trajectory(
        run_info["dcd"], run_info["topology_pdb"], doc["pairs"],
        state=state, his_resnum=int(doc["switch_his"]),
        save_every_ps=float(params["save_every_ps"]),
        movie_frames=int(params["movie_frames"]),
        out_csv=ctx.artifact(f"md/{state}_timeseries.csv"),
        out_frames=ctx.artifact(f"md/{state}_frames.pdb"),
        log=ctx.log,
    )
    stats.update({key: run_info[key] for key in
                  ("platform", "n_atoms", "production_ps", "wall_s", "ps_per_day_ns")})
    common.write_json(ctx.artifact(f"md/{state}_stats.json"), stats)

    target_label = doc["switch_target"]
    note = (
        f"Real molecular dynamics, {stats['duration_ns']:g} ns at 300 K "
        f"(AMBER14 + GBn2 implicit solvent, {run_info['platform']} platform). "
        f"The design keeps His{doc['switch_his']}-{target_label} contact in "
        f"{stats['presence_3p6'] * 100:.0f} % of frames. Frames are superposed "
        "on the target chain. This is a physics test of the predicted pose, "
        "not a binding assay."
    )
    viewer_entry = {
        "path": f"md/{state}_frames.pdb",
        "label": f"{doc['design']} · {STATES[state]['label']} · "
                 f"{stats['duration_ns']:g} ns MD",
        "trajectory": True,
        "highlights": [
            {"selections": ["A"], "color": "#60a5fa", "repr": "cartoon", "opacity": 0.98},
            {"selections": ["B"], "color": "#e879f9", "repr": "cartoon", "opacity": 0.98},
            {"selections": [f"{doc['switch_his']}:B", f"{doc['pairs'][0]['target_resnum']}:A"],
             "color": "#fbbf24", "repr": "ball+stick"},
        ],
        "note": note,
    }
    summary = {
        "stage": state,
        "md_ns": float(stats["duration_ns"]),
        "md_ns_day": float(stats["ps_per_day_ns"]),
        "md_platform": str(stats["platform"]),
        "md_presence": float(stats["presence_3p6"]),
        "md_contacts_mean": float(stats["contacts_mean"]),
        "md_binder_rmsd": float(stats["binder_rmsd_mean_A"]),
        "md_min_distance_A": float(stats["min_N_O_mean_A"]),
        "tables": [f"{state}_timeseries.csv"],
        "charts": [
            {"kind": "line", "source": f"md/{state}_timeseries.csv",
             "x": "time_ns", "y": "min_N_O_A",
             "label": f"His{doc['switch_his']}–{target_label} (pH {ph:g})",
             "title": f"His{doc['switch_his']}–{target_label} distance, {stats['duration_ns']:g} ns "
                      f"(Å, cutoff 3.6 Å = hydrogen bond)",
             "note": "the designed pH switch contact, frame by frame"},
            {"kind": "line", "source": f"md/{state}_timeseries.csv",
             "x": "time_ns", "y": "contacts_4p5",
             "label": "interface contacts",
             "title": "interface residue contacts over time (pairs under 4.5 Å)",
             "note": "does the predicted interface hold in real dynamics?"},
        ],
        "viewer": {
            "select": True,
            "files": [viewer_entry],
            "note": "Playback: open the run's MD player page, or make a movie "
                    "with: pdt movie <run_dir> --mode trajectory",
        },
    }
    return summary


def stage_low(ctx: common.RunContext) -> dict:
    return _state_stage(ctx, "low")


def stage_high(ctx: common.RunContext) -> dict:
    return _state_stage(ctx, "high")


def _subsample_multimodel_text(text: str, wanted: int) -> str:
    """Keep a subset of MODEL blocks from a multi-model PDB text."""
    blocks = text.split("MODEL")
    if len(blocks) <= 1:
        return text
    header = blocks[0]
    models = ["MODEL" + block for block in blocks[1:]]
    picks = analyze.subsample_indices(len(models), wanted)
    return header + "".join(models[index] for index in picks)


def stage_compare(ctx: common.RunContext) -> dict:
    paths = {state: ctx.artifact(f"md/{state}_timeseries.csv") for state in STATES}
    stats = {}
    for state, path in list(paths.items()):
        if not path.exists():
            raise common.WaitingInputsError(
                f"{path.name} is missing. Run the low and high stages first: "
                "pdt exp run <an md spec>")
        stats[state] = common.read_json(ctx.artifact(f"md/{state}_stats.json"))

    frames = {state: pd.read_csv(path) for state, path in paths.items()}
    merged = pd.concat(frames.values(), ignore_index=True)
    merged["state_label"] = merged["state"].map(
        {"low": f"pH {_state_ph(_params(ctx), 'low'):g}",
         "high": f"pH {_state_ph(_params(ctx), 'high'):g}"})
    merged.to_csv(ctx.artifact("md/md_compare.csv"), index=False)

    doc = _load_pairs(ctx)
    design = doc["design"]
    target_label = doc["switch_target"]
    low, high = stats["low"], stats["high"]
    presence_delta = float(low["presence_3p6"]) - float(high["presence_3p6"])

    compare_doc = {
        "design": design,
        "switch": f"His{doc['switch_his']}–{target_label}",
        "start_distance_A": doc["min_distance_A"],
        "low": {key: low[key] for key in
                ("presence_3p6", "presence_4p0", "min_N_O_mean_A", "contacts_mean",
                 "binder_rmsd_mean_A", "duration_ns", "platform", "ps_per_day_ns")},
        "high": {key: high[key] for key in
                 ("presence_3p6", "presence_4p0", "min_N_O_mean_A", "contacts_mean",
                  "binder_rmsd_mean_A", "duration_ns", "platform", "ps_per_day_ns")},
        "presence_delta": round(presence_delta, 3),
        "note": "Same structure, two protonation states. The only difference "
                "between the runs is the histidine state set at the start.",
    }
    common.write_json(ctx.artifact("md/md_summary.json"), compare_doc)

    # The chat deliverable: one self-contained player page with both states.
    player_states = []
    for state in STATES:
        frames_path = ctx.artifact(f"md/{state}_frames.pdb")
        light = ctx.artifact(f"md/{state}_player.pdb")
        light.write_text(_subsample_multimodel_text(
            frames_path.read_text(), int(_params(ctx)["player_frames"])))
        entry = stats[state]
        player_states.append({
            "key": state,
            "label": STATES[state]["label"],
            "pdb": light.read_text(),
            "stat": (f"{design} · {STATES[state]['label']} · "
                     f"{entry['duration_ns']:g} ns · contact present "
                     f"{entry['presence_3p6'] * 100:.0f}% of frames · "
                     f"mean interface contacts {entry['contacts_mean']:g}"),
        })
    config = {
        "title": f"Real physics: {design} on EGFR domain III",
        "eyebrow": "Real physics · OpenMM all-atom MD (not an animation)",
        "note": (
            f"Two all-atom molecular-dynamics runs of the designed complex "
            f"({low['duration_ns']:g} ns each, 300 K, AMBER14 + GBn2 implicit solvent). "
            f"His{doc['switch_his']}–{target_label} starts at {doc['min_distance_A']} Å. "
            f"The contact is present in {low['presence_3p6'] * 100:.0f}% of frames at "
            f"pH 6.5 (protonated, +1) and {high['presence_3p6'] * 100:.0f}% at pH 7.4 "
            f"(neutral). Blue = target, pink = design, amber = the switch pair. "
            "Short simulations test the predicted pose. They are not a binding assay."
        ),
        "footer": (f"OpenMM on the {low['platform']} platform · "
                   f"{low['ps_per_day_ns']:.0f} ns/day · frames every "
                   f"{float(_params(ctx)['save_every_ps']):g} ps, superposed on the target"),
        "hints": [
            {"sels": [{"chain": "A"}], "color": "#60a5fa", "repr": "cartoon"},
            {"sels": [{"chain": "B"}], "color": "#e879f9", "repr": "cartoon"},
            {"sels": [{"resi": int(doc["switch_his"]), "chain": "B"},
                      {"resi": int(doc["pairs"][0]["target_resnum"]), "chain": "A"}],
             "color": "#fbbf24", "repr": "ball+stick"},
        ],
        "states": player_states,
    }
    document = player.player_document(config, Path(__file__).parent.parent / "serve/static/3Dmol-min.js")
    player_path = ctx.artifact("md/md_player.html")
    player_path.write_text(document)
    ctx.log(f"player page: {player_path.name} ({player_path.stat().st_size / 1e6:.1f} MB)")

    viewer_files = []
    for state in STATES:
        viewer_files.append({
            "path": f"md/{state}_frames.pdb",
            "trajectory": True,
            "label": f"{design} · {STATES[state]['label']} · "
                     f"{stats[state]['duration_ns']:g} ns · contact "
                     f"{stats[state]['presence_3p6'] * 100:.0f}%",
            "highlights": [
                {"selections": ["A"], "color": "#60a5fa", "repr": "cartoon", "opacity": 0.98},
                {"selections": ["B"], "color": "#e879f9", "repr": "cartoon", "opacity": 0.98},
                {"selections": [f"{doc['switch_his']}:B",
                                f"{doc['pairs'][0]['target_resnum']}:A"],
                 "color": "#fbbf24", "repr": "ball+stick"},
            ],
            "note": ("Multi-model file: one model per saved frame. The viewer "
                     "plays the frames. Real MD, superposed on the target chain."),
        })

    summary = {
        "stage": "compare",
        "md_ns": float(low["duration_ns"]),
        "md_presence": float(low["presence_3p6"]),
        "md_presence_high": float(high["presence_3p6"]),
        "md_presence_delta": round(presence_delta, 3),
        "md_contacts_mean": float(low["contacts_mean"]),
        "md_contacts_high": float(high["contacts_mean"]),
        "md_binder_rmsd": float(low["binder_rmsd_mean_A"]),
        "md_binder_rmsd_high": float(high["binder_rmsd_mean_A"]),
        "md_min_distance_A": float(low["min_N_O_mean_A"]),
        "md_min_distance_high_A": float(high["min_N_O_mean_A"]),
        "tables": ["md_compare.csv"],
        "charts": [
            {"kind": "line", "source": "md/md_compare.csv",
             "x": "time_ns", "y": "min_N_O_A", "series": "state_label",
             "title": f"His{doc['switch_his']}–{target_label} distance: pH 6.5 vs pH 7.4",
             "note": "the designed switch contact under real dynamics"},
            {"kind": "line", "source": "md/md_compare.csv",
             "x": "time_ns", "y": "contacts_4p5", "series": "state_label",
             "title": "interface contacts over time: pH 6.5 vs pH 7.4",
             "note": "does the binder stay on?"},
            {"kind": "line", "source": "md/md_compare.csv",
             "x": "time_ns", "y": "binder_rmsd_A", "series": "state_label",
             "title": "binder RMSD from the start pose (Å)", "note": ""},
        ],
        "viewer": {
            "select": True,
            "files": viewer_files,
            "note": "Two real trajectories, one per protonation state. Open the "
                    "MD player page for cartoon/cloud/surface playback in the browser.",
        },
    }
    return summary


STAGES = {"prepare": stage_prepare, "low": stage_low, "high": stage_high,
          "compare": stage_compare}


def run(ctx: common.RunContext) -> dict:
    stages = ctx.spec.get("stages") or list(STAGES)
    unknown = [name for name in stages if name not in STAGES]
    if unknown:
        raise ValueError(f"unknown md stages: {unknown} (have: {sorted(STAGES)})")
    stage_summaries = []
    for name in stages:
        ctx.log(f"stage: {name}")
        part = STAGES[name](ctx)
        part["stage"] = name
        stage_summaries.append(part)
    return {"stages": stage_summaries}
