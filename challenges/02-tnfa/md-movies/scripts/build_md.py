#!/usr/bin/env python
"""Prepare, simulate and package an MD binding movie for one C2 design.

Chain convention of the Boltz folds: binder = chain A, target = chains B, C, D
(three TNF-alpha protomers). Reuses the repo MD stack unchanged:
tools.md.prepare (PDBFixer), tools.md.simulate (OpenMM, AMBER14 + GBn2).

    prep   cif -> pdb, PDBFixer completes heavy atoms and terminals
    run    one OpenMM trajectory; writes dcd + topology + run json
    pack   trajectory -> superposed multi-model PDB + stats + summary.json,
           the layout tools.report.movie expects (trajectory mode)

Usage with the project venv, from anywhere:
    .venv/bin/python build_md.py prep --design d7x-t3-3 --cif X.cif --run-dir R
    .venv/bin/python build_md.py run  --design d7x-t3-3 --run-dir R --length-ps 300
    .venv/bin/python build_md.py pack --design d7x-t3-3 --run-dir R --movie-frames 80
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
sys.path.insert(0, str(REPO))
from tools.md import prepare as md_prepare  # noqa: E402
from tools.md import simulate as md_simulate  # noqa: E402
from tools.md.analyze import subsample_indices  # noqa: E402
from tools import common  # noqa: E402

BINDER = "A"
CONTACT_CUTOFF_A = 4.5
BINDER_PINK = "#e879f9"
TARGET_BLUE = "#60a5fa"
INTERFACE_AMBER = "#fbbf24"
HIGHLIGHT_CAP = 24


def _art(run_dir: Path) -> Path:
    path = Path(run_dir) / "artifacts" / "md"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cmd_prep(args) -> None:
    import mdtraj

    art = _art(args.run_dir)
    traj = mdtraj.load(str(args.cif))
    chains = {chain.chain_id: len(list(chain.residues)) for chain in traj.top.chains}
    assert chains.get(BINDER), f"no binder chain {BINDER} in {chain_info(chains)}"
    raw = art / f"{args.design}_raw.pdb"
    traj.save_pdb(str(raw))
    prepared = art / f"{args.design}_prepared.pdb"
    report = md_prepare.complete_structure(raw, prepared)
    common.write_json(art / f"{args.design}_prep.json",
                      {"chains": chains, "atoms": report["atoms"],
                       "missing_residues": {k: len(v) for k, v in report["missing_residues"].items()},
                       "missing_atoms": {k: len(v) for k, v in report["missing_atoms"].items()}})
    print(json.dumps({"chains": chains, "atoms": report["atoms"],
                      "missing_residues": report["missing_residues"],
                      "missing_atoms": report["missing_atoms"]}, indent=1, default=str))


def cmd_run(args) -> None:
    art = _art(args.run_dir)
    prepared = art / f"{args.design}_prepared.pdb"
    info = md_simulate.run_md(
        prepared, art / f"{args.design}_md",
        length_ps=args.length_ps, save_every_ps=args.save_every_ps,
        equil_ps=args.equil_ps, seed=args.seed)
    info.update({"design": args.design, "binder_chain": BINDER,
                 "target_chains": args.target_chains.split(","),
                 "seed": args.seed, "save_every_ps": args.save_every_ps})
    common.write_json(art / f"{args.design}_md_run.json", info)
    print(json.dumps(info, indent=1))


def _heavy_residue_coords(traj, frame: int, subset) -> tuple:
    coords, residues = [], []
    for residue in subset:
        for atom in residue.atoms:
            if atom.element is not None and atom.element.symbol == "H":
                continue
            coords.append(traj.xyz[frame, atom.index])
            residues.append(residue)
    return np.asarray(coords), residues


def _interface(traj, frame: int = 0) -> dict:
    """Residue pairs in contact at `frame` (heavy atoms < cutoff)."""
    from scipy.spatial import cKDTree

    binder_residues = [r for r in traj.top.residues if r.chain.chain_id == BINDER]
    target_residues = [r for r in traj.top.residues if r.chain.chain_id != BINDER]
    b_xyz, b_res = _heavy_residue_coords(traj, frame, binder_residues)
    t_xyz, t_res = _heavy_residue_coords(traj, frame, target_residues)
    tree = cKDTree(t_xyz)
    neighbours = tree.query_ball_point(b_xyz, r=CONTACT_CUTOFF_A / 10.0)
    pairs: dict = {}
    for index, near in enumerate(neighbours):
        for other in near:
            key = (b_res[index].index, t_res[other].index)
            distance = float(np.linalg.norm(b_xyz[index] - t_xyz[other]))
            if key not in pairs or distance < pairs[key]:
                pairs[key] = distance
    binder_side: dict = {}
    target_side: dict = {}
    for (b_index, t_index), distance in pairs.items():
        binder_side[b_index] = min(binder_side.get(b_index, 99.0), distance)
        target_side[t_index] = min(target_side.get(t_index, 99.0), distance)
    return {"pairs": pairs, "binder_side": binder_side, "target_side": target_side,
            "residues": {r.index: r for r in traj.top.residues}}


def _token(residue) -> str:
    return f"{residue.resSeq}:{residue.chain.chain_id}"


def cmd_pack(args) -> None:
    import mdtraj

    run = Path(args.run_dir)
    art = _art(run)
    info = json.loads((art / f"{args.design}_md_run.json").read_text())
    traj = mdtraj.load(str(info["dcd"]), top=str(info["topology_pdb"]))
    n_frames = traj.n_frames
    print(f"pack {args.design}: {n_frames} frames, {traj.n_atoms} atoms")

    iface = _interface(traj, 0)
    chains = list(traj.top.chains)
    binder_pos = chains.index([c for c in chains if c.chain_id == BINDER][0])
    caps = sorted(iface["binder_side"].items(), key=lambda item: item[1])[:HIGHLIGHT_CAP]
    tact = sorted(iface["target_side"].items(), key=lambda item: item[1])[:HIGHLIGHT_CAP]
    tokens = ([_token(iface["residues"][i]) for i, _d in caps]
              + [_token(iface["residues"][i]) for i, _d in tact])

    # contacts over the whole run: the frame-0 pairs, counted per frame
    pair_list = np.asarray(sorted(iface["pairs"].keys()), dtype=int)
    contacts = np.zeros(n_frames)
    closest = np.full(n_frames, np.nan)
    if len(pair_list):
        distances = mdtraj.compute_contacts(traj, contacts=pair_list, scheme="closest-heavy",
                                            periodic=False)[0] * 10.0
        contacts = (distances < CONTACT_CUTOFF_A).sum(axis=1).astype(float)
        closest = distances.min(axis=1)

    binder_ca = traj.top.select(f"chainid {binder_pos} and name CA")
    target_ca = traj.top.select(" or ".join([f"chainid {chains.index(c)} and name CA"
                                             for c in chains if c.chain_id != BINDER]))
    sup = traj[:]  # full copy; superpose every frame onto frame 0 via the target
    sup.superpose(traj[0], atom_indices=target_ca)
    # binder drift relative to the (fixed) target: plain RMSD after superposition
    binder_xyz = sup.xyz[:, binder_ca, :]
    delta = binder_xyz - binder_xyz[0]
    binder_rmsd = np.sqrt((delta ** 2).sum(axis=2).mean(axis=1)) * 10.0

    picks = subsample_indices(n_frames, args.movie_frames)
    heavy = [atom.index for atom in traj.top.atoms
             if atom.element is None or atom.element.symbol != "H"]
    heavy_map = {old: new for new, old in enumerate(heavy)}
    frames = traj[picks].atom_slice(heavy)
    reference = sup[0].atom_slice(heavy)
    anchor = [heavy_map[int(index)] for index in target_ca if int(index) in heavy_map]
    frames.superpose(reference, atom_indices=anchor)
    out_frames = art / f"{args.design}_frames.pdb"
    frames.save_pdb(str(out_frames))

    duration_ns = round(info["production_ps"] / 1000.0, 3)
    half = slice(n_frames // 2, None)
    stats = {
        "design": args.design,
        "n_frames": n_frames,
        "duration_ns": duration_ns,
        "movie_frames": len(picks),
        "platform": info["platform"],
        "n_atoms": info["n_atoms"],
        "seed": info["seed"],
        "ps_per_day_ns": info["ps_per_day_ns"],
        "wall_s": info["wall_s"],
        "interface_pairs_frame0": len(pair_list),
        "interface_binder_residues": len(caps),
        "interface_target_residues": len(tact),
        "contacts_mean": round(float(contacts.mean()), 1),
        "contacts_last_half": round(float(contacts[half].mean()), 1),
        "closest_approach_mean_A": round(float(np.nanmean(closest)), 2),
        "binder_rmsd_mean_A": round(float(binder_rmsd.mean()), 2),
        "binder_rmsd_last_half_A": round(float(binder_rmsd[half].mean()), 2),
        "binder_chain": BINDER,
        "target_chains": [c.chain_id for c in traj.top.chains if c.chain_id != BINDER],
    }
    common.write_json(art / f"{args.design}_stats.json", stats)

    # top interface pairs (closest first) for the zoom inset's dashed lines
    top = sorted(iface["pairs"].items(), key=lambda item: item[1])[:12]
    stats["top_contacts"] = [
        {"a": _token(iface["residues"][b]), "b": _token(iface["residues"][t]),
         "d": round(float(dist), 2)}
        for (b, t), dist in top
    ]

    # target-side residues within 8 A of the binder: the surface hotspot patch
    from scipy.spatial import cKDTree

    binder_xyz = [traj.xyz[0, atom.index] for atom in traj.top.atoms
                  if atom.residue.chain.chain_id == BINDER
                  and (atom.element is None or atom.element.symbol != "H")]
    tree = cKDTree(np.asarray(binder_xyz))
    patch = []
    for residue in traj.top.residues:
        if residue.chain.chain_id == BINDER:
            continue
        for atom in residue.atoms:
            if atom.element is not None and atom.element.symbol == "H":
                continue
            if tree.query(traj.xyz[0, atom.index])[0] <= 0.8:  # 8 A in nm
                patch.append(_token(residue))
                break
    stats["patch_tokens"] = patch
    common.write_json(art / f"{args.design}_stats.json", stats)

    save_every = float(info.get("save_every_ps") or args.save_every_ps)
    lines = ["frame,state,time_ns,contacts_4p5,pairs_total,closest_A,binder_rmsd_A"]
    for index in range(n_frames):
        lines.append(f"{index},{args.design},{index * save_every / 1000.0:.3f},"
                     f"{contacts[index]:.0f},{len(pair_list)},{closest[index]:.2f},"
                     f"{binder_rmsd[index]:.2f}")
    (art / f"{args.design}_timeseries.csv").write_text("\n".join(lines) + "\n")

    note = (
        f"Real all-atom molecular dynamics, {duration_ns:g} ns at 300 K "
        f"(AMBER14 + GBn2 implicit solvent, {info['platform']} platform, seed {info['seed']}). "
        f"The predicted interface holds {stats['contacts_mean']:.0f} of "
        f"{len(pair_list)} residue-pair contacts on average "
        f"({stats['contacts_last_half']:.0f} in the second half). Frames are superposed "
        "on the target chains. A short run like this is a physics test of the "
        "predicted pose. It is not a binding assay."
    )
    summary = {
        "design": args.design,
        "stages": [{
            "stage": "md",
            "md_ns": duration_ns,
            "md_ns_day": info["ps_per_day_ns"],
            "md_platform": info["platform"],
            "viewer": {
                "note": note,
                "files": [{
                    "path": f"md/{args.design}_frames.pdb",
                    "label": f"{args.design} \u00b7 {duration_ns:g} ns MD \u00b7 binder chain {BINDER}",
                    "trajectory": True,
                    "highlights": [
                        {"selections": [BINDER], "color": BINDER_PINK, "repr": "cartoon", "opacity": 0.98},
                        {"selections": stats["target_chains"], "color": TARGET_BLUE, "repr": "cartoon", "opacity": 0.98},
                        {"selections": tokens, "color": INTERFACE_AMBER, "repr": "ball+stick"},
                    ],
                }],
            },
        }],
    }
    common.write_json(run / "summary.json", summary)
    print(json.dumps(stats, indent=1))
    print("movie run dir ready:", run)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prep")
    p.add_argument("--design", required=True)
    p.add_argument("--cif", required=True)
    p.add_argument("--run-dir", required=True)
    p.set_defaults(func=cmd_prep)

    p = sub.add_parser("run")
    p.add_argument("--design", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--length-ps", type=float, default=300.0)
    p.add_argument("--equil-ps", type=float, default=40.0)
    p.add_argument("--save-every-ps", type=float, default=2.0)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--target-chains", default="B,C,D")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("pack")
    p.add_argument("--design", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--movie-frames", type=int, default=80)
    p.add_argument("--save-every-ps", type=float, default=2.0)
    p.set_defaults(func=cmd_pack)

    args = parser.parse_args()
    args.func(args)


def chain_info(chains: dict) -> str:
    return ", ".join(f"{key}: {value} residues" for key, value in chains.items())


if __name__ == "__main__":
    main()
