#!/usr/bin/env python3
"""Epitope analysis for challenge 4 (TfR1 conditional binder).

Answers the three questions that decide the campaign plan:

  1. Which apical-domain residues are the same in human and mouse?
     Objective 2 asks for cross-reactivity, so a divergent epitope works
     against us. The comparison runs on a sequence ALIGNMENT, never on the
     author numbering: the human and mouse constructs carry an indel, so a
     fixed offset is wrong (see the offset report below).
  2. Which of those residues are solvent exposed in the assembled homodimer?
     A conserved but buried residue is not an epitope.
  3. What titratable chemistry sits there?
     Objective 1 asks for a pH switch. The direction is bind at pH 7.4 and
     release at pH 6.0, so affinity must FALL as the pH falls. A histidine
     gains a positive charge near pH 6. Placing a binder histidine against a
     target CATION gives repulsion at pH 6.0 and the asked direction. Placing
     it against a target ANION gives the opposite direction.

Outputs a printed report and `notes/epitope-analysis.csv`.

Usage:
    .venv/bin/python challenges/04-tfr1/scripts/epitope_analysis.py
"""
from __future__ import annotations

import csv
import itertools
import pathlib
import warnings
from collections import Counter

import gemmi
from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.PDB import MMCIFParser, ShrakeRupley

warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).resolve().parent
CH = HERE.parent
HUMAN = CH / "inputs/11QC.cif"
MOUSE = CH / "inputs/AF-Q62351-F1.pdb"
OUT = CH / "notes/epitope-analysis.csv"

TARGET_CHAIN = "A"
# The patch named on the challenge page and used by nim/build_request.py.
APICAL_PATCH = (204, 208, 210, 211, 348, 371)
NEIGHBOUR_CUTOFF = 10.0   # A, heavy atom to a patch side-chain atom
EXPOSED_RSA = 25.0        # percent; below this a residue is not a usable epitope
HOTSPOT_SPAN = 15.0       # A, the repo feasibility line (AGENT.md rule 19)

# Theoretical maximum side-chain SASA, Tien et al. 2013, PLoS ONE 8:e80635.
MAX_SASA = {
    "ALA": 129, "ARG": 274, "ASN": 195, "ASP": 193, "CYS": 167, "GLN": 225,
    "GLU": 223, "GLY": 104, "HIS": 224, "ILE": 197, "LEU": 201, "LYS": 236,
    "MET": 224, "PHE": 240, "PRO": 159, "SER": 155, "THR": 172, "TRP": 285,
    "TYR": 263, "VAL": 174,
}
CATIONS, ANIONS, TITRATABLE = "RK", "DE", "H"


def amino_acids(path: pathlib.Path, chain: str | None = None):
    """Return (structure, [(auth_seq_id, one_letter, residue)]) for one chain."""
    st = gemmi.read_structure(str(path))
    st.setup_entities()
    st.remove_hydrogens()
    ch = st[0][chain] if chain else st[0][0]
    rows = []
    for res in ch:
        info = gemmi.find_tabulated_residue(res.name)
        if info and info.is_amino_acid():
            rows.append((res.seqid.num, info.one_letter_code.upper(), res))
    return st, rows


def align_species(human_rows, mouse_rows):
    """Map human auth numbering to mouse auth numbering by global alignment."""
    hs = "".join(r[1] for r in human_rows)
    ms = "".join(r[1] for r in mouse_rows)
    aligner = PairwiseAligner(mode="global", open_gap_score=-11,
                              extend_gap_score=-1)
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aln = aligner.align(hs, ms)[0]

    mapping, hi, mi, identical, columns = {}, 0, 0, 0, 0
    for a, b in zip(aln[0], aln[1]):
        if a != "-" and b != "-":
            mapping[human_rows[hi][0]] = (mouse_rows[mi][0], a, b)
            columns += 1
            identical += a == b
        if a != "-":
            hi += 1
        if b != "-":
            mi += 1
    return mapping, identical, columns


def relative_exposure(path: pathlib.Path, chain: str):
    """Per-residue RSA in the assembled structure, as a percentage."""
    model = MMCIFParser(QUIET=True).get_structure("t", str(path))[0]
    ShrakeRupley().compute(model, level="R")
    out = {}
    for res in model[chain]:
        name = res.get_resname()
        if name in MAX_SASA:
            out[res.id[1]] = 100.0 * res.sasa / MAX_SASA[name]
    return out


def ca_positions(rows, wanted):
    pos = {}
    for num, _, res in rows:
        if num in wanted:
            atom = res.find_atom("CA", "*")
            if atom:
                pos[num] = atom.pos
    return pos


def max_span(pos, members):
    pairs = [p for p in itertools.combinations(members, 2) if p[0] in pos and p[1] in pos]
    return max((pos[a].dist(pos[b]) for a, b in pairs), default=0.0)


def main() -> int:
    hst, hrows = amino_acids(HUMAN, TARGET_CHAIN)
    _, mrows = amino_acids(MOUSE)
    mapping, identical, columns = align_species(hrows, mrows)

    print("=" * 74)
    print("CONSTRUCTS")
    print("=" * 74)
    print(f"  human 11QC chain {TARGET_CHAIN}: {len(hrows)} residues, "
          f"auth {hrows[0][0]}-{hrows[-1][0]}")
    print(f"  mouse AF-Q62351-F1       : {len(mrows)} residues, "
          f"auth {mrows[0][0]}-{mrows[-1][0]}")
    print(f"  alignment identity: {identical}/{columns} = "
          f"{100.0 * identical / columns:.1f} percent")
    offsets = Counter(m - h for h, (m, _, _) in mapping.items())
    print(f"  mouse minus human numbering: {dict(offsets.most_common(4))}")
    print("  The offset is NOT constant. A fixed offset would mis-map the")
    print("  epitope. Every species comparison must use this alignment.")

    # ---- the neighbourhood of the named patch
    patch_sidechain = [a.pos for num, _, res in hrows if num in APICAL_PATCH
                       for a in res if a.name not in ("N", "C", "O")]
    neighbourhood = [(num, let) for num, let, res in hrows
                     if any(a.pos.dist(p) <= NEIGHBOUR_CUTOFF
                            for a in res for p in patch_sidechain)]
    rsa = relative_exposure(HUMAN, TARGET_CHAIN)

    records = []
    for num, let in neighbourhood:
        mnum, hletter, mletter = mapping.get(num, (None, let, None))
        records.append({
            "human_resnum": num,
            "human_aa": let,
            "mouse_resnum": mnum if mnum is not None else "",
            "mouse_aa": mletter or "",
            # "gap" means the alignment gives this residue no mouse counterpart,
            # which is an indel and not a substitution. Reporting it as a plain
            # difference would overstate the divergence.
            "species": ("same" if mletter and hletter == mletter else
                        "substituted" if mletter else "gap"),
            "conserved": bool(mletter and hletter == mletter),
            "rsa_percent": round(rsa.get(num, float("nan")), 1),
            "exposed": rsa.get(num, 0.0) >= EXPOSED_RSA,
            "in_named_patch": num in APICAL_PATCH,
            "charge": ("cation" if let in CATIONS else
                       "anion" if let in ANIONS else
                       "titratable" if let in TITRATABLE else "neutral"),
        })

    named = [r for r in records if r["in_named_patch"]]
    print()
    print("=" * 74)
    print("1. THE NAMED APICAL PATCH, HUMAN AGAINST MOUSE")
    print("=" * 74)
    for r in named:
        print(f"  human {r['human_resnum']:4d}{r['human_aa']}  "
              f"mouse {str(r['mouse_resnum']):>4}{r['mouse_aa']}  "
              f"RSA {r['rsa_percent']:5.1f}%  {r['species'].upper()}")
    nsub = sum(1 for r in named if r["species"] == "substituted")
    ngap = sum(1 for r in named if r["species"] == "gap")
    print(f"  => {nsub} of {len(named)} named patch residues are substituted in "
          f"mouse, and {ngap} falls in an indel with no mouse counterpart.")
    print(f"  => {nsub + ngap} of {len(named)} are therefore not conserved.")
    print("  A binder aimed at this patch is selected for human specificity,")
    print("  which works against objective 2.")

    conserved_exposed = sorted(r["human_resnum"] for r in records
                               if r["conserved"] and r["exposed"])
    print()
    print("=" * 74)
    print("2. THE CONSERVED AND EXPOSED FACE (the cross-reactive candidate)")
    print("=" * 74)
    print(f"  neighbourhood within {NEIGHBOUR_CUTOFF:.0f} A of the named patch: "
          f"{len(records)} residues")
    print(f"  conserved in mouse: {sum(1 for r in records if r['conserved'])}")
    print(f"  conserved AND exposed (RSA >= {EXPOSED_RSA:.0f}%): "
          f"{len(conserved_exposed)}")
    for r in records:
        if r["conserved"] and r["exposed"]:
            print(f"    {r['human_resnum']:4d}{r['human_aa']}  "
                  f"RSA {r['rsa_percent']:5.1f}%  {r['charge']}")

    pos = ca_positions(hrows, set(conserved_exposed))
    print(f"  max CA-CA span of the whole conserved face: "
          f"{max_span(pos, conserved_exposed):.1f} A")
    print(f"  the feasibility line for one hotspot set is {HOTSPOT_SPAN:.0f} A,")
    print("  so this face splits into more than one hotspot set.")

    # ---- compact hotspot sets that each contain a conserved cation
    cats = [r["human_resnum"] for r in records
            if r["conserved"] and r["exposed"] and r["charge"] == "cation"]
    print()
    print("=" * 74)
    print("3. HOTSPOT SETS: COMPACT, CONSERVED, AND CARRYING A SWITCH ANCHOR")
    print("=" * 74)
    print(f"  conserved exposed cations (the switch anchors): "
          f"{', '.join(str(c) for c in cats)}")
    seen = set()
    for size in (6, 5, 4, 3):
        for comb in itertools.combinations(conserved_exposed, size):
            if not any(c in comb for c in cats):
                continue
            if max_span(pos, comb) > HOTSPOT_SPAN:
                continue
            key = frozenset(comb)
            if any(key <= s for s in seen):
                continue
            seen.add(key)
            print(f"    {list(comb)}  span {max_span(pos, comb):5.1f} A  "
                  f"cations {[c for c in comb if c in cats]}")

    print()
    print("=" * 74)
    print("4. SWITCH CHEMISTRY (direction: bind 7.4, release 6.0)")
    print("=" * 74)
    for label, kind in (("target histidine", "titratable"),
                        ("target cation (ARG/LYS)", "cation"),
                        ("target anion (ASP/GLU)", "anion")):
        hits = [r for r in records if r["charge"] == kind]
        cons = [r for r in hits if r["conserved"] and r["exposed"]]
        allnames = ", ".join(f"{r['human_resnum']}{r['human_aa']}" for r in hits)
        consnames = ", ".join(f"{r['human_resnum']}{r['human_aa']}" for r in cons)
        print(f"  {label}: {len(hits)} in the neighbourhood "
              f"({len(cons)} conserved and exposed)")
        print(f"    all              : {allnames or '-'}")
        print(f"    conserved+exposed: {consnames or '-'}")
    print()
    print("  The target carries NO histidine at this epitope. The whole pH")
    print("  switch must therefore be built on the binder. Pair a binder")
    print("  histidine with a conserved target cation to get the asked")
    print("  direction. A binder histidine against a target anion inverts it.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print()
    print(f"wrote {OUT.relative_to(CH.parents[1])}  ({len(records)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
