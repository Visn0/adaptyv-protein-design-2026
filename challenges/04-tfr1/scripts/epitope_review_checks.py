#!/usr/bin/env python3
"""Independent checks for the challenge-4 campaign plan (written 2026-10-23).

This script recomputes the review numbers WITHOUT importing
`epitope_analysis.py`. It answers four questions:

  1. Do the distances in the plan reproduce (dimer span, glycan clearances,
     hotspot-set spans)?
  2. What is the mouse equivalent of every epitope-set residue (by alignment,
     never by offset), and how big is the species difference around each set?
  3. What does a real binder at this apex touch?  11RN = B19V VP1u RBD
     (2 x 62 aa) bound to the TfR1 ectodomain.
  4. Does the apex leave the transferrin site free?  1SUV = TfR1 with
     transferrin.

Inputs: inputs/11QC.cif, inputs/AF-Q62351-F1.pdb (tracked),
        inputs/11RN.cif, inputs/1SUV.cif (fetched from RCSB 2026-10-23).

Usage:
    .venv/bin/python challenges/04-tfr1/scripts/epitope_review_checks.py
"""
from __future__ import annotations

import itertools
import pathlib

import gemmi
from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.PDB import MMCIFParser, ShrakeRupley

HERE = pathlib.Path(__file__).resolve().parent
CH = HERE.parent
HUMAN = CH / "inputs/11QC.cif"
MOUSE = CH / "inputs/AF-Q62351-F1.pdb"
VP1U = CH / "inputs/11RN.cif"
TRANSFERRIN = CH / "inputs/1SUV.cif"

E0 = (204, 208, 210, 211, 348, 371)   # the organizers' named patch
E1 = (206, 207, 209, 374)             # north loop + 374 K
E2 = (343, 344, 347, 350, 351)        # south ledge
E12 = (344, 374)                      # review proposal: both switch anchors,
                                      # 13.8 A CA-CA (347..374 is 15.8 A, so
                                      # 347 stays out of the dual-anchor set)

# Theoretical maximum side-chain SASA (Tien et al. 2013).
MAX_SASA = {"ALA": 129, "ARG": 274, "ASN": 195, "ASP": 193, "CYS": 167,
            "GLN": 225, "GLU": 223, "GLY": 104, "HIS": 224, "ILE": 197,
            "LEU": 201, "LYS": 236, "MET": 224, "PHE": 240, "PRO": 159,
            "SER": 155, "THR": 172, "TRP": 285, "TYR": 263, "VAL": 174}
CLASS = {"K": "cation", "R": "cation", "E": "anion", "D": "anion"}


def residue_map(path, chain=None):
    """{auth_seq_id: (one_letter, gemmi_residue)} for amino acids."""
    st = gemmi.read_structure(str(path))
    st.setup_entities()
    st.remove_hydrogens()
    ch = st[0][chain] if chain else st[0][0]
    out = {}
    for res in ch:
        info = gemmi.find_tabulated_residue(res.name)
        if info and info.is_amino_acid():
            out[res.seqid.num] = (info.one_letter_code.upper(), res)
    return out


def align_map(rows_a, rows_b):
    """Map a-numbering to b-numbering through a global alignment."""
    sa = "".join(rows_a[k][0] for k in sorted(rows_a))
    sb = "".join(rows_b[k][0] for k in sorted(rows_b))
    al = PairwiseAligner(mode="global", open_gap_score=-11, extend_gap_score=-1)
    al.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a = al.align(sa, sb)[0]
    mapping, ia, ib, ident, cols = {}, 0, 0, 0, 0
    ka, kb = sorted(rows_a), sorted(rows_b)
    for x, y in zip(a[0], a[1]):
        if x != "-" and y != "-":
            mapping[ka[ia]] = kb[ib]
            cols += 1
            ident += x == y
        if x != "-":
            ia += 1
        if y != "-":
            ib += 1
    return mapping, ident, cols


def min_dist(res_a, res_b):
    return min(x.pos.dist(y.pos) for x in res_a for y in res_b)


def ca(res):
    return res.find_atom("CA", "*")


def span_ca(rows, members):
    return max(ca(rows[a][1]).pos.dist(ca(rows[b][1]).pos)
               for a, b in itertools.combinations(members, 2))


def rsa_map(path, chain):
    model = MMCIFParser(QUIET=True).get_structure("m", str(path))[0]
    ShrakeRupley().compute(model, level="R")
    out = {}
    for res in model[chain]:
        name = res.get_resname()
        if name in MAX_SASA:
            out[res.id[1]] = 100.0 * res.sasa / MAX_SASA[name]
    return out


def shell(rows, rsa, members, radius):
    """Exposed residues with a heavy atom within `radius` of a set member."""
    mem_atoms = [a.pos for m in members for a in rows[m][1]]
    out = []
    for k in sorted(rows):
        if k in members or rsa.get(k, 0.0) < 25.0:
            continue
        if any(a.pos.dist(p) <= radius for a in rows[k][1] for p in mem_atoms):
            out.append(k)
    return out


def main() -> int:
    H = residue_map(HUMAN, "A")
    st_ab = gemmi.read_structure(str(HUMAN))
    B211 = next(r for r in st_ab[0]["B"] if r.seqid.num == 211)
    Hm = residue_map(MOUSE)
    rsa = rsa_map(HUMAN, "A")
    mapping, ident, cols = align_map(H, Hm)

    def cons(k):
        return k in mapping and H[k][0] == Hm[mapping[k]][0]

    print("=" * 74)
    print("1. THE DISTANCES IN THE PLAN")
    print("=" * 74)
    print(f"  Y211(A)-Y211(B): {ca(H[211][1]).pos.dist(ca(B211).pos):.1f} A")
    nags = [r for r in st_ab[0]["A"] if r.name == "NAG"]
    nag = min(nags, key=lambda r: r.seqid.num)
    for n in (231, 371, 374, 344, 348):
        print(f"  NAG{nag.seqid.num} (N251) - {n}{H[n][0]}: "
              f"{min_dist(nag, H[n][1]):.1f} A")
    for name, s in (("E0", E0), ("E1", E1), ("E2", E2), ("E12", E12)):
        print(f"  {name} CA-CA span: {span_ca(H, s):.1f} A")
    print(f"  alignment identity: {ident}/{cols} = {100*ident/cols:.1f}%")

    print()
    print("=" * 74)
    print("2. THE SPECIES MAP OF EVERY SET (by alignment)")
    print("=" * 74)
    for name, s in (("E0", E0), ("E1", E1), ("E2", E2), ("E12", E12)):
        cells = []
        for k in s:
            if k in mapping:
                m = mapping[k]
                tag = "same" if cons(k) else "DIFF"
                cells.append(f"{k}{H[k][0]}->{m}{Hm[m][0]}({tag})")
            else:
                cells.append(f"{k}{H[k][0]}->gap(DIFF)")
        print(f"  {name}: " + "  ".join(cells))

    print()
    print("=" * 74)
    print("3. THE EXPOSED CONTACT RING AROUND EACH SET (species-aware)")
    print("=" * 74)
    for name, s in (("E0", E0), ("E1", E1), ("E2", E2), ("E12", E12)):
        for radius in (5.0, 8.0):
            ring = shell(H, rsa, s, radius)
            cons_n = [k for k in ring if cons(k)]
            diff = [k for k in ring if not cons(k)]
            cls = [f"{k}{H[k][0]}->{Hm[mapping[k]][0]} class"
                   for k in diff if k in mapping
                   and CLASS.get(H[k][0]) and CLASS.get(Hm[mapping[k]][0])
                   and CLASS[H[k][0]] == CLASS[Hm[mapping[k]][0]]]
            print(f"  {name} @ {radius:.0f} A: {len(ring)} exposed neighbours, "
                  f"{len(cons_n)} conserved, {len(diff)} divergent"
                  f"{(' (' + ', '.join(cls) + ' survive by class)') if cls else ''}")
            print(f"      divergent: "
                  f"{[f'{k}{H[k][0]}->{Hm[mapping[k]][0]}' if k in mapping else f'{k}{H[k][0]}->gap' for k in diff]}")

    print()
    print("=" * 74)
    print("4. 11RN - WHAT A REAL BINDER AT THIS APEX TOUCHES")
    print("=" * 74)
    st_v = gemmi.read_structure(str(VP1U))
    va = {r.seqid.num: r for r in st_v[0]["A"]
          if gemmi.find_tabulated_residue(r.name) and gemmi.find_tabulated_residue(r.name).is_amino_acid()}
    x_atoms = [a for r in st_v[0]["X"] for a in r]

    def dist_to_vp1u(res):
        return min(a.pos.dist(b.pos) for a in res for b in x_atoms)

    for cutoff in (5.0, 8.0):
        hits = [n for n, r in va.items() if dist_to_vp1u(r) <= cutoff]
        print(f"  VP1u contacts <= {cutoff:.0f} A: {sorted(hits)}")
    hits5 = {n for n, r in va.items() if dist_to_vp1u(r) <= 5.0}
    for name, s in (("E0", E0), ("E1", E1), ("E2", E2), ("E12", E12)):
        print(f"  overlap {name} at 5 A: {sorted(set(s) & hits5)}")
    m = MMCIFParser(QUIET=True).get_structure("v", str(VP1U))[0]
    sr = ShrakeRupley()
    def chain_sasa(keep):
        import copy
        mm = copy.deepcopy(m)
        for ch in list(mm):
            if ch.id not in keep:
                mm.detach_child(ch.id)
        sr.compute(mm, level="C")
        return sum(ch.sasa for ch in mm)
    a_only, x_only, both = chain_sasa({"A"}), chain_sasa({"X"}), chain_sasa({"A", "X"})
    print(f"  interface buried SASA: {a_only + x_only - both:.0f} A^2 "
          f"(A {a_only:.0f}, X {x_only:.0f}, complex {both:.0f})")

    print()
    print("=" * 74)
    print("5. 1SUV - IS THE TRANSFERRIN SITE FREE?")
    print("=" * 74)
    st_t = gemmi.read_structure(str(TRANSFERRIN))
    ta = {r.seqid.num: r for r in st_t[0]["A"]
          if gemmi.find_tabulated_residue(r.name) and gemmi.find_tabulated_residue(r.name).is_amino_acid()}
    tf_atoms = {c: [a for r in st_t[0][c] for a in r] for c in ("C", "E")}
    tf = []
    for chain in ("C", "E"):
        tf += [n for n, r in ta.items()
               if min(a.pos.dist(b.pos) for a in r
                      for b in tf_atoms[chain]) <= 5.0]
    tf = sorted(set(tf))
    print(f"  transferrin contacts on TfR1 (chain A, <= 5 A): {tf}")
    print(f"  contacts inside the apical window 189-382: "
          f"{[n for n in tf if 189 <= n <= 382]}")
    for name, s in (("E0", E0), ("E1", E1), ("E2", E2), ("E12", E12)):
        best = min((min_dist(ta[k], ta[t]), k, t) for k in s for t in tf)
        print(f"  {name}: nearest transferrin contact {best[0]:.1f} A "
              f"({best[1]}..{best[2]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
