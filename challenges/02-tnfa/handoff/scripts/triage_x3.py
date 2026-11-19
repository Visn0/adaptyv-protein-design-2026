#!/usr/bin/env python3
"""Triage the X3 RFdiffusion3 designs (trimmed patch target).

The X3 runs use a target trimmed to the neighbourhood of a hotspot set, so the
outputs differ from the Tamarind X2 layout:

* the binder is **chain A** (not the smallest chain);
* the whole target arrives as **one chain B**, renumbered 1..N in the order the
  residues appear in the patch PDB.

That order is the mapping this script needs, and it reads it from the patch PDB
itself — never from a guess.

Per design it reports: binder length, minimum heavy-atom distance, interface
size (binder atoms within 4 A), contacts to each hotspot residue, the site flags
(loop group + neighbour group, by residue identity, so "cross-protomer" is judged
from the input structure, not from the output chain), and the generator's own
metrics from the sidecar JSON.

`--trimer` adds the loophole check: the design's target chain is superimposed on
the full trimer (Kabsch), then the binder's distance to every residue that the
trim removed is measured. A binder that sits where the absent protomer sits is
discarded, whatever its other numbers say.

Usage:
    python triage_x3.py --root ~/c2-work/x3/x3a-rbs \
        --patch ../../handoff/rfd3/target-x3a-rbs.pdb \
        --site A83,A87,A89 --neighbour B147 \
        --trimer ../../data/epitope-analysis/1TNF.pdb \
        --out ~/c2-work/x3/x3a-rbs-triage.csv
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import pathlib
from collections import OrderedDict

import numpy as np
from Bio.PDB import MMCIFParser

THREE2ONE = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
             "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
             "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
             "TYR": "Y", "VAL": "V"}


def patch_order(patch: pathlib.Path) -> list[tuple[str, int]]:
    """[(chain, resnum), ...] in file order — equals the output chain B numbering."""
    order: list[tuple[str, int]] = []
    for line in patch.read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            item = (line[21], int(line[22:26]))
            if item not in order:
                order.append(item)
    return order


def read_trimer(path: pathlib.Path) -> dict[tuple[str, int], dict[str, np.ndarray]]:
    """{(chain, resnum): {atom_name: xyz}} — heavy atoms only."""
    residues: dict[tuple[str, int], dict[str, np.ndarray]] = {}
    for line in path.read_text().splitlines():
        if line.startswith("ATOM") and line[76:78].strip() != "H":
            key = (line[21], int(line[22:26]))
            name = line[12:16].strip()
            residues.setdefault(key, {})[name] = np.array(
                [float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return residues


def design_atoms(cif_gz: pathlib.Path) -> tuple[dict, dict, list[str]]:
    """(binder residues, target residues, binder sequence) from a design file.

    residues: {resnum: {"xyz": ndarray[n,3], "name": str, "atoms": [names]}}
    """
    parser = MMCIFParser(QUIET=True)
    with gzip.open(cif_gz, "rt") as fh:
        structure = parser.get_structure("design", fh)
    model = structure[0]
    out: dict[str, dict] = {}
    for chain_id in ("A", "B"):
        chain = model[chain_id] if chain_id in model else None
        residues = OrderedDict()
        if chain is not None:
            for res in chain:
                xyz = np.array([atom.coord for atom in res.get_atoms()
                                if atom.element != "H"])
                if len(xyz) == 0:
                    continue
                residues[res.id[1]] = {
                    "xyz": xyz,
                    "name": res.resname.strip(),
                    "atoms": [atom.get_name() for atom in res.get_atoms()
                              if atom.element != "H"],
                }
        out[chain_id] = residues
    sequence = "".join(THREE2ONE.get(r["name"], "X") for r in out["A"].values())
    return out["A"], out["B"], sequence


def minimum_distance(binder: dict, target: dict) -> tuple[float, int]:
    """(minimum heavy-atom distance, binder atoms within 4 A of the target)."""
    binder_xyz = np.vstack([r["xyz"] for r in binder.values()])
    target_xyz = np.vstack([r["xyz"] for r in target.values()])
    mind, count4 = float("inf"), 0
    for i in range(0, len(binder_xyz), 400):
        block = binder_xyz[i:i + 400]
        d = np.linalg.norm(block[:, None, :] - target_xyz[None, :, :], axis=2)
        mind = min(mind, float(d.min()))
        count4 += int((d <= 4.0).sum())
    return mind, count4


def hotspot_contacts(binder: dict, target: dict, target_index: dict[int, tuple[str, int]],
                     hotspots: list[tuple[str, int]], cutoff: float = 4.5) -> dict:
    """{hotspot: minimum distance} — only for the hotspots the target still holds."""
    output_numbers = {key: num for num, key in target_index.items()}
    binder_xyz = np.vstack([r["xyz"] for r in binder.values()])
    result = {}
    for key in hotspots:
        num = output_numbers.get(key)
        if num is None or num not in target:
            result[key] = None
            continue
        d = np.linalg.norm(binder_xyz[:, None, :] - target[num]["xyz"][None, :, :], axis=2)
        result[key] = float(d.min())
    return result


def kabsch(mobile: np.ndarray, fixed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rotation and translation that map `mobile` onto `fixed`."""
    centre_m, centre_f = mobile.mean(0), fixed.mean(0)
    a, b = mobile - centre_m, fixed - centre_f
    u, _s, vt = np.linalg.svd(a.T @ b)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ np.diag([1.0, 1.0, d]) @ u.T
    return rotation, centre_f - rotation @ centre_m


def loophole(binder: dict, target: dict, target_index: dict[int, tuple[str, int]],
             trimer: dict, cutoff: float = 4.0) -> tuple[float, int]:
    """Superimpose on the shared residues, then measure against what the trim cut.

    Returns (minimum distance to an absent residue, count of binder atoms closer
    than the cutoff). Zero atoms means the design stays in the designed space.
    """
    mobile, fixed = [], []
    for num, key in target_index.items():
        residue = target.get(num)
        reference = trimer.get(key)
        if not residue or not reference:
            continue
        for name, xyz in zip(residue["atoms"], residue["xyz"]):
            if name in reference:
                mobile.append(xyz)
                fixed.append(reference[name])
    if len(mobile) < 30:
        return float("nan"), -1
    rotation, translation = kabsch(np.asarray(mobile), np.asarray(fixed))

    absent = {key: res for key, res in trimer.items() if key not in set(target_index.values())}
    absent_xyz = np.vstack([xyz for res in absent.values() for xyz in res.values()])
    binder_xyz = np.vstack([r["xyz"] for r in binder.values()])
    binder_xyz = binder_xyz @ rotation.T + translation
    mind, count = float("inf"), 0
    for i in range(0, len(binder_xyz), 400):
        block = binder_xyz[i:i + 400]
        d = np.linalg.norm(block[:, None, :] - absent_xyz[None, :, :], axis=2)
        mind = min(mind, float(d.min()))
        count += int((d <= cutoff).sum())
    return mind, count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--patch", type=pathlib.Path, required=True)
    parser.add_argument("--site", required=True, help="site hotspots, e.g. A83,A87,A89")
    parser.add_argument("--neighbour", default="", help="the neighbour-protomer hotspot, e.g. B147")
    parser.add_argument("--trimer", type=pathlib.Path, help="full trimer, enables the loophole check")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    index = patch_order(args.patch)
    target_index = dict(enumerate(index, start=1))
    site_group = [(t[0], int(t[1:])) for t in args.site.split(",")]
    neighbour_group = [(t[0], int(t[1:])) for t in args.neighbour.split(",") if t]
    trimer = read_trimer(args.trimer) if args.trimer else None

    rows = []
    for design in sorted(args.root.glob("*_model_*.cif.gz")):
        binder, target, sequence = design_atoms(design)
        if not binder or not target:
            continue
        mind, atoms4 = minimum_distance(binder, target)
        contacts = hotspot_contacts(binder, target, target_index, site_group + neighbour_group)
        site_hit = any(v is not None and v <= 4.5 for k, v in contacts.items() if k in site_group)
        neighbour_hit = any(v is not None and v <= 4.5 for k, v in contacts.items()
                            if k in neighbour_group)
        metrics = {}
        sidecar = design.with_suffix("").with_suffix(".json")
        if sidecar.exists():
            metrics = json.loads(sidecar.read_text()).get("metrics", {})
        row = {
            "design": design.name.replace(".cif.gz", ""),
            "binder_len": len(binder),
            "min_d": round(mind, 2),
            "atoms4": atoms4,
            "site_hit": site_hit,
            "neighbour_hit": neighbour_hit,
            "site_any": bool(site_hit and neighbour_hit) if neighbour_group else bool(site_hit),
            "contacts": " ".join(f"{c[0]}{c[1]}={contacts[c]:.2f}" if contacts[c] is not None
                                 else f"{c[0]}{c[1]}=-" for c in site_group + neighbour_group),
            "helix_frac": round(float(metrics.get("helix_fraction", 0.0)), 2),
            "clashes": metrics.get("n_clashing.interresidue_clashes_w_sidechain", ""),
            "chainbreaks": metrics.get("n_chainbreaks", ""),
            "sequence": sequence,
        }
        if trimer is not None:
            hole_d, hole_atoms = loophole(binder, target, target_index, trimer)
            row["loophole_d"] = "" if np.isnan(hole_d) else round(hole_d, 2)
            row["loophole_atoms"] = hole_atoms
            row["loophole_ok"] = hole_atoms == 0
        rows.append(row)

    rows.sort(key=lambda r: (r["site_any"], r["neighbour_hit"], r["atoms4"]), reverse=True)
    for position, row in enumerate(rows, 1):
        row["rank"] = position
    fields = ["rank", "design", "binder_len", "min_d", "atoms4", "site_hit", "neighbour_hit",
              "site_any", "contacts", "helix_frac", "clashes", "chainbreaks", "sequence"]
    if trimer is not None:
        fields += ["loophole_d", "loophole_atoms", "loophole_ok"]
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} designs -> {args.out}")
    if rows:
        site = sum(r["site_any"] for r in rows)
        clean = sum(r["site_any"] and r["min_d"] >= 2.0 and r["atoms4"] >= 80 for r in rows)
        print(f"at the site: {site} | clean shortlist (site, no clash, >=80 atoms): {clean}")
        if trimer is not None:
            ok = sum(bool(r.get("loophole_ok")) for r in rows)
            print(f"loophole-clean: {ok} of {len(rows)}")


if __name__ == "__main__":
    main()
