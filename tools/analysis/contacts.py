"""Protein-protein interface contacts, and the viewer hints that show them.

`interface_contacts` gives the contact residue lists (KD-tree over atom
coordinates, one Bio.PDB parse). `complex_viewer_hints` turns a complex into
the standard highlight set used by every viewer in this workspace:

    blue  = target chain(s)
    pink  = the designed binder
    amber = interface residues (ball+stick) on both sides of the contact
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, PDBParser
from scipy.spatial import cKDTree

DEFAULT_CUTOFF = 4.5


def _parse(path: Path):
    text = str(path).lower()
    if text.endswith(".cif") or text.endswith(".mmcif"):
        return MMCIFParser(QUIET=True).get_structure("s", str(path))
    return PDBParser(QUIET=True).get_structure("s", str(path))


def interface_contacts(path, binder_chains, target_chains, cutoff: float = DEFAULT_CUTOFF) -> dict:
    """Atom contacts between the binder chains and the target chains.

    Returns:
        binder_resi:  sorted residue numbers of the binder in contact,
        target_resi:  sorted residue numbers of the target in contact,
        n_atom_pairs: number of atom pairs within `cutoff` Angstrom.
    """
    model = _parse(Path(path))[0]

    def gather(chains):
        coords, resi = [], []
        for chain_id in chains:
            if chain_id not in model:
                continue
            for residue in model[chain_id]:
                if residue.id[0] != " ":
                    continue
                for atom in residue:
                    coords.append(atom.coord)
                    resi.append(residue.id[1])
        return np.asarray(coords, dtype=float), np.asarray(resi)

    binder_xyz, binder_resi = gather(binder_chains)
    target_xyz, target_resi = gather(target_chains)
    if len(binder_xyz) == 0 or len(target_xyz) == 0:
        return {"binder_resi": [], "target_resi": [], "n_atom_pairs": 0}

    tree = cKDTree(target_xyz)
    neighbours = tree.query_ball_point(binder_xyz, r=cutoff)
    n_pairs = 0
    binder_hit, target_hit = set(), set()
    for index, near in enumerate(neighbours):
        if not near:
            continue
        n_pairs += len(near)
        binder_hit.add(int(binder_resi[index]))
        for neighbour in near:
            target_hit.add(int(target_resi[neighbour]))
    return {
        "binder_resi": sorted(binder_hit),
        "target_resi": sorted(target_hit),
        "n_atom_pairs": int(n_pairs),
    }


def complex_viewer_hints(path, binder_chain: str, target_chains) -> dict:
    """Viewer hints + note: blue target, pink design, amber binding interface."""
    target_chains = list(target_chains)
    iface = interface_contacts(path, [binder_chain], target_chains)
    hints = [
        {"selections": target_chains, "color": "#60a5fa",
         "repr": "cartoon", "opacity": 0.98},
        {"selections": [binder_chain], "color": "#e879f9",
         "repr": "cartoon", "opacity": 0.98},
    ]
    if iface["binder_resi"]:
        hints.append({
            "selections": [f"{resi}:{binder_chain}" for resi in iface["binder_resi"]],
            "color": "#fbbf24", "repr": "ball+stick",
        })
    if iface["target_resi"]:
        hints.append({
            "selections": [f"{resi}:{chain}" for chain in target_chains
                           for resi in iface["target_resi"]],
            "color": "#fbbf24", "repr": "ball+stick",
        })
    note = (
        f"Blue = target (chain{'' if len(target_chains) == 1 else 's'} "
        f"{','.join(target_chains)}). Pink = your design (chain {binder_chain}). "
        f"Amber = binding interface: {len(iface['binder_resi'])} design residues + "
        f"{len(iface['target_resi'])} target residues, "
        f"{iface['n_atom_pairs']} atom contacts within 4.5 A."
    )
    return {"highlights": hints, "note": note}


# ---------------------------------------------------------------- hotspots
# Campaign screens score engagement against named target positions, not just
# "is there an interface". They also index the target by label_seq_id (the
# FASTA position the restraint files use), which Bio.PDB's auth numbering does
# not give, so this path reads _atom_site directly instead of reusing _parse.

def cif_atoms(path) -> list[tuple]:
    """(chain, label_seq_id, atom_name, x, y, z) per non-hydrogen atom.

    Indexed by label_seq_id so hotspot positions match the FASTA/restraint
    numbering the fold inputs were built with.
    """
    lines = Path(path).read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("_atom_site."))
    names, i = [], start
    while lines[i].startswith("_atom_site."):
        names.append(lines[i].strip().split(".")[1])
        i += 1
    atoms = []
    for line in lines[i:]:
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        parts = line.split()
        if len(parts) < len(names):
            continue
        row = dict(zip(names, parts))
        if row["label_atom_id"] == "H":
            continue
        try:
            seq = int(row["label_seq_id"])
        except ValueError:
            continue
        atoms.append((row["label_asym_id"], seq, row["label_atom_id"],
                      float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"])))
    return atoms


def split_binder_target(atoms) -> tuple[str, str]:
    """(target_chain, binder_chain): the target is the chain with most atoms."""
    counts: dict[str, int] = {}
    for atom in atoms:
        counts[atom[0]] = counts.get(atom[0], 0) + 1
    if len(counts) < 2:
        raise ValueError(f"expected 2+ chains, found {sorted(counts)}")
    target = max(counts, key=lambda c: counts[c])
    binder = max((c for c in counts if c != target), key=lambda c: counts[c])
    return target, binder


def hotspot_engagement(atoms, hotspots, cutoff: float = 5.0) -> dict:
    """How well the binder engages the named target positions.

    worst_min_dist is the largest per-hotspot minimum distance, so one missed
    hotspot shows up however good the others are; binder_residues counts the
    distinct binder residues within `cutoff` of any hotspot. A read is
    "engaged" only when both are good - ipTM alone promotes off-site poses
    (challenge 4 measured 0.696 for a binder sitting ~55 A away).
    """
    target, binder = split_binder_target(atoms)
    binder_xyz = np.asarray([a[3:6] for a in atoms if a[0] == binder], dtype=float)
    binder_resi = [a[1] for a in atoms if a[0] == binder]
    tree = cKDTree(binder_xyz)

    per_hotspot, near = {}, set()
    for hotspot in hotspots:
        target_xyz = np.asarray([a[3:6] for a in atoms
                                 if a[0] == target and a[1] == hotspot], dtype=float)
        if not len(target_xyz):
            continue
        dist, _ = tree.query(target_xyz)
        per_hotspot[hotspot] = round(float(dist.min()), 2)
        for neighbours in tree.query_ball_point(target_xyz, r=cutoff):
            near.update(binder_resi[index] for index in neighbours)

    return {
        "target_chain": target,
        "binder_chain": binder,
        "per_hotspot": per_hotspot,
        "worst_min_dist": max(per_hotspot.values()) if per_hotspot else None,
        "binder_residues": len(near),
    }
