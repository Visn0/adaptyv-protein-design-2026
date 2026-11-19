#!/usr/bin/env python3
"""Membrane-space check for a predicted complex (co-folds have no membrane).

Flags binder atoms that sit where lipid would be: outside the receptor's TM
bundle envelope, inside the bilayer core band, and >4 A from every receptor
atom ("free in lipid").  Calibrate first on the natural ligand -- it must
flag zero atoms (e.g. 6X18: --rec R --bind P --tm 145:365 --ecd 29:128).

  python membrane_space_check.py complex.cif --rec B --bind A \
      --tm 122:342 --ecd 6:105

The frame is derived from the model's OWN TM helices (PCA axis, ECD side = +z,
core = middle 30 A of the helix extent, envelope = 98th-percentile CA radius
+2 A).  Do not borrow a membrane plane by superposing onto an experimental
structure -- the ECD drags the fit (measured 3.7 A TM RMSD, 7 A global).
Screen-grade result; per-design receptor-prediction variance is a few A.
"""
from __future__ import annotations
import argparse
import numpy as np
from Bio.PDB import MMCIFParser, PDBParser


def load(path):
    p = PDBParser(QUIET=True) if path.endswith(".pdb") else MMCIFParser(QUIET=True)
    return p.get_structure("s", path)[0]


def frame(chain, tm_lo, tm_hi, ecd_lo, ecd_hi):
    tm_cas, ecd_cas = [], []
    for res in chain:
        if "CA" not in res:
            continue
        n = res.id[1]
        if tm_lo <= n <= tm_hi:
            tm_cas.append(res["CA"].coord)
        if ecd_lo <= n <= ecd_hi:
            ecd_cas.append(res["CA"].coord)
    tm = np.array(tm_cas)
    cen = tm.mean(0)
    axis = np.linalg.svd(tm - cen)[2][0]
    if (np.array(ecd_cas).mean(0) - cen) @ axis < 0:
        axis = -axis
    z = (tm - cen) @ axis
    r = np.linalg.norm((tm - cen) - np.outer(z, axis), axis=1)
    zmid = 0.5 * (float(np.percentile(z, 98)) + float(np.percentile(z, 2)))
    return cen, axis, zmid, float(np.percentile(r, 98))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("structure")
    ap.add_argument("--rec", default="B")
    ap.add_argument("--bind", default="A")
    ap.add_argument("--tm", required=True, help="TM residue window lo:hi (receptor numbering)")
    ap.add_argument("--ecd", required=True, help="ECD window lo:hi, sets the up direction")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.tm.split(":"))
    elo, ehi = (int(x) for x in a.ecd.split(":"))

    model = load(a.structure)
    rec, lig = model[a.rec], model[a.bind]
    cen, axis, zmid, bundle_r = frame(rec, lo, hi, elo, ehi)
    rec_atoms = np.array([x.coord for x in rec.get_atoms()])
    coords = np.array([x.coord for x in lig.get_atoms()])
    z = (coords - cen) @ axis
    r = np.linalg.norm((coords - cen) - np.outer(z, axis), axis=1)
    core = (r > bundle_r + 2.0) & (z > zmid - 15) & (z < zmid + 15)
    d = np.full(len(coords), 1e9)
    for i in range(0, len(rec_atoms), 400):
        blk = rec_atoms[i:i + 400]
        d = np.minimum(d, np.linalg.norm(coords[:, None, :] - blk[None, :, :], axis=2).min(1))
    free = core & (d > 4.0)
    touch = core & (d <= 4.0)
    past = core & (z <= zmid)
    print(f"frame: core {zmid-15:.1f}..{zmid+15:.1f} A (0 = midplane), bundle radius {bundle_r:.1f}")
    print(f"chain {a.bind}: {len(coords)} atoms | in band {int(core.sum())} "
          f"| free {int(free.sum())} | touching {int(touch.sum())} | past midplane {int(past.sum())}"
          + (f" | deepest {zmid - z[past].min():.1f} A past" if past.any() else ""))
    verdict = "FLAG" if (free.any() or past.any()) else "clean"
    print(f"verdict: {verdict} (free atoms or past the midplane = flag; a touch-only graze = weak signal)")


if __name__ == "__main__":
    main()
