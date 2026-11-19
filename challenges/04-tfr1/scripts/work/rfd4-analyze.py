#!/usr/bin/env python3
"""Aggregate RFD4-Proteina hosted runs: per-design metrics + at-site geometry.

Reads every ~/c4-work/rfd4/<set>/run-*/summary.json (skips dryrun dirs),
parses the design CIF, and reports: binder chain/length, hotspot distances in
the returned pose, and the service metrics. Writes logs/rfd4-batch.csv and a
per-set summary to stdout. Auth numbering for hotspots matches the target CIF.
"""
import csv
import json
import math
import pathlib
import sys

WORK = pathlib.Path.home() / "c4-work/rfd4"
OUT = pathlib.Path.home() / "c4-work/logs/rfd4-batch.csv"
HOTSPOTS = {
    "E0": (204, 208, 210, 211, 348, 371),
    "E1": (206, 207, 209, 374),
    "E2": (343, 344, 347, 350, 351),
    "E12": (344, 374),
}


def parse_cif(path):
    txt = path.read_text().splitlines()
    start = next(i for i, l in enumerate(txt) if l.startswith("_atom_site."))
    cols, i = [], start
    while txt[i].startswith("_atom_site."):
        cols.append(txt[i].strip())
        i += 1
    idx = {c.split(".")[1]: j for j, c in enumerate(cols)}
    atoms = []
    for l in txt[i:]:
        if l.startswith("ATOM") or l.startswith("HETATM"):
            p = l.split()
            if len(p) < len(cols):
                continue
            atoms.append((
                p[idx["auth_asym_id"]], p[idx["label_comp_id"]],
                int(p[idx["auth_seq_id"]]), p[idx["label_atom_id"]],
                float(p[idx["Cartn_x"]]), float(p[idx["Cartn_y"]]), float(p[idx["Cartn_z"]]),
            ))
    chains = {}
    for a in atoms:
        chains.setdefault(a[0], []).append(a)
    return chains


AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def main():
    rows = []
    for setdir in sorted(WORK.glob("E*")):
        setname = setdir.name
        if setname not in HOTSPOTS:
            continue
        for run in sorted(setdir.glob("run-*")):
            summary = run / "summary.json"
            if not summary.exists():
                continue
            s = json.loads(summary.read_text())
            if s.get("status") != "completed":
                print(f"{setname}/{run.name}: status {s.get('status')} - skipped", file=sys.stderr)
                continue
            for d in s.get("designs", []):
                cif = run / d["structure_file"]
                chains = parse_cif(cif)
                if len(chains) < 2:
                    continue
                tgt = max(chains, key=lambda c: len(chains[c]))
                bnd = next(c for c in chains if c != tgt)
                binder = [a for a in chains[bnd] if a[3] != "H"]
                batoms = [a for a in binder]
                res = {}
                for a in binder:
                    res.setdefault(a[2], a[1])
                seq = "".join(AA3.get(res[k], "X") for k in sorted(res))
                dists = []
                for hs in HOTSPOTS[setname]:
                    t = [a for a in chains[tgt] if a[2] == hs and a[3] != "H"]
                    dm = min((math.dist(a[4:7], b[4:7]) for a in t for b in batoms), default=float("nan"))
                    dists.append(dm)
                near = set()
                for hs in HOTSPOTS[setname]:
                    for b in batoms:
                        for a in chains[tgt]:
                            if a[2] == hs and a[3] != "H" and math.dist(a[4:7], b[4:7]) <= 5.0:
                                near.add(b[2])
                m = d.get("metrics", {})
                rows.append({
                    "set": setname, "run": run.name, "design": d["design_id"],
                    "seed": d.get("seed"), "binder_chain": bnd, "binder_len": len(res),
                    "binder_seq": seq,
                    "min_dist_A": round(min(dists), 2) if dists else None,
                    "max_min_dist_A": round(max(dists), 2) if dists else None,
                    "binder_res_at_site": len(near),
                    "hotspot_obedience": m.get("hotspot_obedience.hotspot_obedience"),
                    "motif_rmsd": m.get("design_motif_allatom_rmsd.rmsd"),
                    "clash_frac": m.get("clash_metrics.frac_atoms_clashing_1p5A"),
                    "seq_adherence": m.get("sequence_adherence.sequence_adherence"),
                })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} designs)")
    per = {}
    for r in rows:
        per.setdefault(r["set"], []).append(r)
    for setname in ("E0", "E1", "E2", "E12"):
        rs = per.get(setname, [])
        if not rs:
            continue
        lens = [r["binder_len"] for r in rs]
        ob = [r["hotspot_obedience"] for r in rs if r["hotspot_obedience"] is not None]
        touches = [r for r in rs if r["max_min_dist_A"] is not None and r["max_min_dist_A"] <= 5.0]
        print(f"{setname}: {len(rs)} designs | binder {min(lens)}-{max(lens)} aa "
              f"(median {sorted(lens)[len(lens)//2]}) | contact ALL hotspots in pose: "
              f"{len(touches)}/{len(rs)} | hotspot_obedience mean "
              f"{sum(ob)/len(ob):.2f}" if ob else "")


if __name__ == "__main__":
    main()
