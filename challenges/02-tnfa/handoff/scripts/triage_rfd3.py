#!/usr/bin/env python3
"""Triage RFdiffusion3 binder-design outputs (Tamarind or local run).

One row per design model. The binder is the smallest polymer chain; the
target is every other chain. Reports: binder length, minimum heavy-atom
distance, interface size (binder atoms within 4 A), and per-residue
contacts to the requested hotspot positions.

Example (the C2 X2 run; 1TNF input residues 6-157 are renumbered 1-152
in the output, so the original hotspot numbers get -5):

    python triage_rfd3.py \
        --root ../../../data/tamarind/x2/extracted/c2-x2-rfd3-s1-groove \
        --site 65 67 75 --offset -5 \
        --out ../../../data/tamarind/x2/x2-triage.csv

Site rule: a design is "at the site" when it contacts at least one loop
position (65/67) and at least one neighbour position (75). It is "cross"
when those contacts come from different protomers.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib

import numpy as np

AA3 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}
LOOP_SITE = (65, 67)  # 60s loop positions in the original numbering


def read_pdb(path):
    """Return {chain: {"res": {num: xyz ndarray}, "xyz": ndarray, "seq": [(num, aa)]}}."""
    chains = collections.OrderedDict()
    for line in open(path):
        if not line.startswith("ATOM"):
            continue
        ch = line[21]
        entry = chains.setdefault(ch, {"res": collections.defaultdict(list), "xyz": [], "seq": {}})
        xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        num = int(line[22:26])
        entry["res"][num].append(xyz)
        entry["xyz"].append(xyz)
        if line[12:16].strip() == "CA":
            entry["seq"][num] = AA3.get(line[17:20].strip(), "X")
    for ch in chains:
        chains[ch]["xyz"] = np.asarray(chains[ch]["xyz"])
        chains[ch]["res"] = {n: np.asarray(v) for n, v in chains[ch]["res"].items()}
        chains[ch]["sequence"] = "".join(aa for _, aa in sorted(chains[ch]["seq"].items()))
    return chains


def contact_metrics(binder_xyz, target_xyz):
    """Minimum distance and count of binder atoms within 4 A of the target."""
    mind, count4 = float("inf"), 0
    for i in range(0, len(binder_xyz), 300):
        block = binder_xyz[i:i + 300]
        d = np.linalg.norm(block[:, None, :] - target_xyz[None, :, :], axis=2)
        mind = min(mind, float(d.min()))
        count4 += int((d <= 4.0).sum())
    return mind, count4


def hotspot_hits(binder_xyz, targets, loop_out, nb_out, cutoff=4.5):
    """{chain: {"loop": bool, "nb": bool}} for residues within the cutoff."""
    hits = {}
    for ch, entry in targets.items():
        hit_loop = hit_nb = False
        for num, xyz in entry["res"].items():
            if num not in loop_out and num not in nb_out:
                continue
            d = np.linalg.norm(binder_xyz[:, None, :] - xyz[None, :, :], axis=2).min()
            if d <= cutoff:
                if num in loop_out:
                    hit_loop = True
                else:
                    hit_nb = True
        hits[ch] = {"loop": hit_loop, "nb": hit_nb}
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory that holds the per-child design folders")
    ap.add_argument("--out", required=True, help="output CSV path")
    ap.add_argument("--site", nargs="+", type=int, required=True, help="hotspot residues, original numbering")
    ap.add_argument("--offset", type=int, default=0, help="added to the site numbers to match the output numbering")
    ap.add_argument("--glob", default="*_model_*.pdb")
    args = ap.parse_args()

    loop_out = {n + args.offset for n in args.site if n in LOOP_SITE}
    nb_out = {n + args.offset for n in args.site if n not in LOOP_SITE}
    root = pathlib.Path(args.root)
    rows = []
    for pdb in sorted(root.glob(f"*/{args.glob}")) + sorted(root.glob(args.glob)):
        chains = read_pdb(pdb)
        if not chains:
            continue
        binder_key = min(chains, key=lambda c: len(chains[c]["res"]))
        binder = chains[binder_key]
        targets = {c: e for c, e in chains.items() if c != binder_key}
        target_xyz = np.vstack([e["xyz"] for e in targets.values()])
        mind, count4 = contact_metrics(binder["xyz"], target_xyz)
        hits = hotspot_hits(binder["xyz"], targets, loop_out, nb_out)
        loop_chains = sorted(c for c, h in hits.items() if h["loop"])
        nb_chains = sorted(c for c, h in hits.items() if h["nb"])
        metrics = {}
        sidecar = pdb.with_suffix(".json")
        if sidecar.exists():
            metrics = json.loads(sidecar.read_text()).get("metrics", {})
        rows.append({
            "design": pdb.name,
            "child": pdb.parent.name,
            "pdb": str(pdb.relative_to(root)),
            "binder_chain": binder_key,
            "binder_len": len(binder["res"]),
            "min_d": round(mind, 2),
            "atoms4": count4,
            "hits": len(loop_chains) + len(nb_chains),
            "loop_chains": " ".join(loop_chains),
            "nb_chains": " ".join(nb_chains),
            "site_any": bool(loop_chains and nb_chains),
            "site_cross": bool(loop_chains and nb_chains and not set(loop_chains) == set(nb_chains)),
            "helix_frac": round(float(metrics.get("helix_fraction", 0.0)), 2),
            "clashes": metrics.get("n_clashing.interresidue_clashes_w_sidechain", ""),
            "chainbreaks": metrics.get("n_chainbreaks", ""),
            "sequence": binder["sequence"],
        })

    rows.sort(key=lambda r: (r["site_any"], r["atoms4"]), reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    fields = ["rank", "design", "child", "pdb", "binder_chain", "binder_len", "min_d",
              "atoms4", "hits", "loop_chains", "nb_chains", "site_any", "site_cross",
              "helix_frac", "clashes", "chainbreaks", "sequence"]
    out = pathlib.Path(args.out)
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    site = sum(r["site_any"] for r in rows)
    cross = sum(r["site_cross"] for r in rows)
    clean = sum(r["site_any"] and r["min_d"] >= 2.0 and r["atoms4"] >= 80 for r in rows)
    print(f"{n} designs | site: {site} | cross-protomer: {cross} | clean shortlist: {clean}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
