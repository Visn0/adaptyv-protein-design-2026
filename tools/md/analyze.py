"""Trajectory metrics (mdtraj) and the movie frame files.

`analyze_trajectory` loads one DCD plus its topology PDB and writes:

    <state>_timeseries.csv   one row per saved frame
    <state>_frames.pdb       a subsampled multi-model PDB for viewers and movies

The frames are superposed on the target chain. The target must look steady
in a movie about the binder. Distances stay the same under superposition.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

NM_TO_ANGSTROM = 10.0
HBOND_CUTOFF_A = 3.6
CONTACT_CUTOFF_A = 4.5


def _select(topology, chain_index: int, resseq: int, name: str) -> int | None:
    matches = topology.select(f"chainid {chain_index} and resSeq {int(resseq)} and name {name}")
    return int(matches[0]) if len(matches) else None


def subsample_indices(n_frames: int, wanted: int) -> list[int]:
    """Evenly spaced frame indices. The first and the last frame stay."""
    n = int(n_frames)
    wanted = max(2, min(int(wanted), n))
    if n <= wanted:
        return list(range(n))
    picks = np.linspace(0, n - 1, wanted)
    return sorted({int(round(value)) for value in picks})


def load_trajectory(dcd, topology_pdb):
    import mdtraj

    return mdtraj.load(str(dcd), top=str(topology_pdb))


def analyze_trajectory(dcd, topology_pdb, pairs: list[dict], *, state: str,
                       his_resnum: int, save_every_ps: float,
                       binder_chain: str = "B", target_chain: str = "A",
                       movie_frames: int = 48, out_csv=None, out_frames=None,
                       log=print) -> dict:
    """One pass over the trajectory. Returns the summary statistics."""
    import mdtraj

    traj = load_trajectory(dcd, topology_pdb)
    n_frames = traj.n_frames
    chain_ids = [chain.chain_id for chain in traj.top.chains]
    binder_index = chain_ids.index(binder_chain)
    target_index = chain_ids.index(target_chain)
    log(f"analyze {state}: {n_frames} frames, {traj.n_atoms} atoms")

    times_ns = np.arange(n_frames) * (save_every_ps / 1000.0)

    # tracked contact distances (heavy atoms only)
    series = {}
    for entry in pairs:
        his_atom = _select(traj.top, binder_index, his_resnum, entry["his_atom"])
        oxygen = _select(traj.top, target_index, entry["target_resnum"], entry["target_atom"])
        if his_atom is None or oxygen is None:
            continue
        label = (f"{entry['his_atom']}-{entry['target_resname']}"
                 f"{entry['target_resnum']}:{entry['target_atom']}")
        delta = traj.xyz[:, his_atom, :] - traj.xyz[:, oxygen, :]
        series[label] = np.linalg.norm(delta, axis=1) * NM_TO_ANGSTROM
    if series:
        min_n_o = np.min(np.vstack(list(series.values())), axis=0)
    else:
        min_n_o = np.full(n_frames, np.nan)

    # the same contact including the hydrogen, when this state has one
    nitrogen_hydrogens = {"NE2": "HE2", "ND1": "HD1"}
    hydrogen_values = []
    for entry in pairs:
        hydrogen_name = nitrogen_hydrogens.get(entry["his_atom"])
        if hydrogen_name is None:
            continue
        hydrogen = _select(traj.top, binder_index, his_resnum, hydrogen_name)
        oxygen = _select(traj.top, target_index, entry["target_resnum"], entry["target_atom"])
        if hydrogen is None or oxygen is None:
            continue
        delta = traj.xyz[:, hydrogen, :] - traj.xyz[:, oxygen, :]
        hydrogen_values.append(np.linalg.norm(delta, axis=1) * NM_TO_ANGSTROM)
    min_h_o = (np.min(np.vstack(hydrogen_values), axis=0)
               if hydrogen_values else np.full(n_frames, np.nan))

    # interface contacts: residue pairs that touch at the first frame
    def heavy_residue_pairs(frame_index: int):
        from scipy.spatial import cKDTree

        def gather(chain_position: int):
            coords, resids = [], []
            for residue in traj.top.chain(chain_position).residues:
                for atom in residue.atoms:
                    if atom.element is not None and atom.element.symbol == "H":
                        continue
                    coords.append(traj.xyz[frame_index, atom.index])
                    resids.append(residue.index)
            return np.asarray(coords), np.asarray(resids)

        binder_xyz, binder_res = gather(binder_index)
        target_xyz, target_res = gather(target_index)
        tree = cKDTree(target_xyz)
        neighbours = tree.query_ball_point(binder_xyz, r=CONTACT_CUTOFF_A / NM_TO_ANGSTROM)
        found = set()
        for index, near in enumerate(neighbours):
            for other in near:
                found.add((int(binder_res[index]), int(target_res[other])))
        return np.asarray(sorted(found), dtype=int)

    contact_pairs = heavy_residue_pairs(0)
    contacts_4p5 = np.zeros(n_frames)
    if len(contact_pairs):
        distances = mdtraj.compute_contacts(traj, contacts=contact_pairs,
                                            scheme="closest-heavy", periodic=False)[0]
        contacts_4p5 = (distances * NM_TO_ANGSTROM < CONTACT_CUTOFF_A).sum(axis=1).astype(float)
    log(f"analyze {state}: {len(contact_pairs)} interface residue pairs tracked")

    # RMSD of both chains against the first frame
    binder_ca = traj.top.select(f"chainid {binder_index} and name CA")
    target_ca = traj.top.select(f"chainid {target_index} and name CA")
    binder_rmsd = mdtraj.rmsd(traj, traj[0], atom_indices=binder_ca) * NM_TO_ANGSTROM
    target_rmsd = mdtraj.rmsd(traj, traj[0], atom_indices=target_ca) * NM_TO_ANGSTROM

    if out_csv is not None:
        out_csv = Path(out_csv)
        lines = ["frame,state,time_ns,min_N_O_A,min_H_O_A,contacts_4p5,binder_rmsd_A,target_rmsd_A"]
        for index in range(n_frames):
            lines.append(
                f"{index},{state},{times_ns[index]:.3f},{min_n_o[index]:.3f},"
                f"{min_h_o[index]:.3f},{contacts_4p5[index]:.0f},"
                f"{binder_rmsd[index]:.3f},{target_rmsd[index]:.3f}")
        out_csv.write_text("\n".join(lines) + "\n")

    if out_frames is not None:
        picks = subsample_indices(n_frames, movie_frames)
        heavy = [atom.index for atom in traj.top.atoms
                 if atom.element is None or atom.element.symbol != "H"]
        heavy_map = {old: new for new, old in enumerate(heavy)}
        frames = traj[picks].atom_slice(heavy)
        reference = traj[0].atom_slice(heavy)
        anchor = [heavy_map[int(index)] for index in target_ca if int(index) in heavy_map]
        frames.superpose(reference, atom_indices=anchor)
        out_frames = Path(out_frames)
        frames.save_pdb(str(out_frames))
        log(f"analyze {state}: wrote {len(picks)} movie frames -> {out_frames.name}")

    half = slice(len(contacts_4p5) // 2, None)
    return {
        "state": state,
        "n_frames": int(n_frames),
        "duration_ns": round(float(times_ns[-1]) if n_frames else 0.0, 3),
        "min_N_O_mean_A": round(float(np.nanmean(min_n_o)), 2),
        "min_N_O_best_A": round(float(np.nanmin(min_n_o)), 2),
        "min_H_O_mean_A": (round(float(np.nanmean(min_h_o)), 2)
                           if np.isfinite(min_h_o).any() else None),
        "presence_3p6": round(float(np.mean(min_n_o < HBOND_CUTOFF_A)), 3),
        "presence_4p0": round(float(np.mean(min_n_o < 4.0)), 3),
        "contacts_mean": round(float(np.mean(contacts_4p5)), 1),
        "contacts_last_half": round(float(np.mean(contacts_4p5[half])), 1),
        "binder_rmsd_mean_A": round(float(np.mean(binder_rmsd)), 2),
        "binder_rmsd_last_half_A": round(float(np.mean(binder_rmsd[half])), 2),
        "target_rmsd_mean_A": round(float(np.mean(target_rmsd)), 2),
        "pair_means_A": {label: round(float(np.mean(values)), 2)
                         for label, values in series.items()},
    }
