#!/usr/bin/env python3
"""Check a Chai-1 fold of the control pair against the native apical footprint.

Chain A = 11RN VP1u RBD (62 aa), chain B = 11QC protomer (639 aa, fold
numbering = author - 121). The native footprint in fold numbering is
{81,82,83,87,88,89,90,91,227,250}; the dimer-interface patch that Boltz-2
kept choosing is fold 182-207. Prints min distances and contact counts.
"""
import math
import pathlib
import sys


def parse_cif(path):
    txt = pathlib.Path(path).read_text().splitlines()
    start = next(i for i, l in enumerate(txt) if l.startswith("_atom_site."))
    cols, i = [], start
    while txt[i].startswith("_atom_site."):
        cols.append(txt[i].strip())
        i += 1
    key = {}
    for c in cols:
        bare = c.split(".")[1]
        key[bare] = len(key)
    # mmCIF order is fixed per file; map by header name
    names = [c.split(".")[1] for c in cols]
    atoms = []
    for l in txt[i:]:
        if l.startswith("ATOM") or l.startswith("HETATM"):
            p = l.split()
            if len(p) < len(cols):
                continue
            d = dict(zip(names, p))
            atoms.append((d["label_asym_id"], d["label_comp_id"],
                          int(d["label_seq_id"]), d["label_atom_id"],
                          float(d["Cartn_x"]), float(d["Cartn_y"]), float(d["Cartn_z"]),
                          d.get("auth_seq_id", "")))
    return atoms


def main(cif_path):
    atoms = parse_cif(cif_path)
    chains = {}
    for a in atoms:
        chains.setdefault(a[0], []).append(a)
    print("chains:", {k: len(v) for k, v in chains.items()})
    a_chain = min(chains, key=lambda c: len(chains[c]))  # RBD = smaller
    b_chain = max(chains, key=lambda c: len(chains[c]))
    rbd = [a for a in chains[a_chain] if a[3] != "H"]
    tgt = [a for a in chains[b_chain] if a[3] != "H"]
    footprint = (81, 82, 83, 87, 88, 89, 90, 91, 227, 250)
    dimer_patch = tuple(range(182, 208))
    for label, resset in (("native footprint", footprint), ("dimer patch", dimer_patch)):
        dists = []
        for res in resset:
            t = [a for a in tgt if a[2] == res]
            if not t:
                continue
            dists.append(min(math.dist(a[4:7], b[4:7]) for a in t for b in rbd))
        if dists:
            print(f"{label}: min {min(dists):.2f} A, median {sorted(dists)[len(dists)//2]:.2f} A over {len(dists)} residues")
    near_fp, near_dp = set(), set()
    for b in rbd:
        for a in tgt:
            d = math.dist(a[4:7], b[4:7])
            if d <= 5.0:
                if a[2] in footprint:
                    near_fp.add(b[2])
                if a[2] in dimer_patch:
                    near_dp.add(b[2])
    print(f"RBD residues within 5 A: footprint {len(near_fp)} ({sorted(near_fp)}), dimer patch {len(near_dp)}")
    print("VERDICT:", "AT FOOTPRINT" if len(near_fp) >= 3 and len(near_fp) > len(near_dp)
          else ("DIMER-PATCH POSE (like Boltz-2)" if len(near_dp) > len(near_fp) else "NO CLEAR POSE"))


if __name__ == "__main__":
    main(sys.argv[1])
