#!/usr/bin/env python3
"""Build the C0 instrument-calibration inputs (campaign c0-instrument-calibration).

Arms (binder chains A,B; target chains C,D,E = HLA heavy, b2m, peptide):

    pos-g12d        JDI TCR + G12D pMHC      7OW6 chains A,B,C,D,E
    pos-wt          JDI TCR + WT pMHC        7OW5 chains A,B,C,D,E
    neg-peptidefree JDI TCR + empty MHC      7OW6 chains A,B,D,E
    neg-shuffled    shuffled JDI sequences   G12D pMHC (sequence-level)

Outputs under ~/c5-work/c0:
    pdb/     extracted complexes (also copied to the gitignored inputs/controls/)
    seqs/    msa-targets.fa (the protein chains to fetch MSAs for)
    folds/   boltz-2 yamls
    chai/designs/<arm>/in.fasta + restraints.csv

MSAs are looked up as <sha1(seq)[:12]-d*.a3m in challenges/05-pmhc/inputs/msa;
fetch them with scripts/work/fetch_msas.py, then re-run this builder.
Missing MSA -> `msa: empty` in the yaml, with a warning.

Run: .venv/bin/python challenges/05-pmhc/scripts/work/c0-build-controls.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import shutil

from Bio.PDB import MMCIFParser, PDBIO, Select

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
assert (ROOT / "challenges" / "05-pmhc").is_dir(), f"unexpected repo root: {ROOT}"
C5 = ROOT / "challenges" / "05-pmhc"
MSA_DIR = C5 / "inputs" / "msa"
CONTROLS = C5 / "inputs" / "controls"

# The 811-res full-size folds crash this host at model load (three 0x20001
# crashes on 2026-10-30). --trim cuts each TCR chain at the V/C domain
# boundary (the conserved FR4 "FGxGTRLTVT" motif) for the ~625-res
# Fv-only constructs, which sit in the documented-safe fold zone.
FR4 = re.compile(r"FG.GTRL")


def trim_vdomain(seq: str) -> str:
    m = FR4.search(seq)
    return seq[:m.end() + 3] if m else seq[:120]

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V", "MSE": "M"}


class _StdResidues(Select):
    def accept_chain(self, chain):
        return chain.id in self.keep  # type: ignore[attr-defined]

    def accept_residue(self, residue):
        return residue.id[0] == " " and residue.resname in AA3


def chain_sequence(structure, chain_id: str) -> str:
    return "".join(AA3[r.resname] for r in structure[chain_id]
                   if r.id[0] == " " and r.resname in AA3)


def extract(structure, chains: tuple[str, ...], dest: pathlib.Path) -> None:
    io = PDBIO()
    io.set_structure(structure)
    sel = _StdResidues()
    sel.keep = chains  # type: ignore[attr-defined]
    io.save(str(dest), sel)


def msa_path(seq: str) -> str:
    tag = hashlib.sha1(seq.encode()).hexdigest()[:12]
    hits = sorted(MSA_DIR.glob(f"{tag}-d*.a3m"))
    return str(hits[0]) if hits else ""


def boltz_yaml(path: pathlib.Path, chains: list[tuple[str, str, bool]]) -> list[str]:
    """chains: (id, sequence, use_msa). Returns warnings."""
    warn = []
    lines = ["version: 1", "sequences:"]
    for cid, seq, use_msa in chains:
        msa = msa_path(seq) if use_msa else ""
        if use_msa and not msa:
            warn.append(f"{path.name}: no MSA for chain {cid} ({len(seq)} aa)")
        lines += ["  - protein:",
                  f"      id: {cid}",
                  f"      sequence: {seq}",
                  f"      msa: {msa or 'empty'}"]
    path.write_text("\n".join(lines) + "\n")
    return warn


def chai_inputs(work: pathlib.Path, arm: str, chains: list[tuple[str, str]],
                peptide_positions: list[int], rim_positions: list[int],
                binder_chains: tuple[str, ...]) -> None:
    d = work / "chai" / "designs" / arm
    d.mkdir(parents=True, exist_ok=True)
    seqs = dict(chains)
    with open(d / "in.fasta", "w") as fh:
        for cid, seq in chains:
            fh.write(f">protein|{cid}\n{seq}\n")
    rows = ["restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,"
            "min_distance_angstrom,connection_type,confidence,comment"]
    n = 0
    for binder in binder_chains:
        for pos in peptide_positions:
            if "E" not in seqs:
                break
            letter = seqs["E"][pos - 1]
            n += 1
            rows.append(f"restraint_{n},{binder},,E,{letter}{pos},8.0,0.0,pocket,1.0,"
                        f"peptide-P{pos}")
        for pos in rim_positions:
            letter = seqs["C"][pos - 1]
            n += 1
            rows.append(f"restraint_{n},{binder},,C,{letter}{pos},8.0,0.0,pocket,1.0,"
                        f"groove-rim-{pos}")
    (d / "restraints.csv").write_text("\n".join(rows) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path.home() / "c5-work" / "c0")
    ap.add_argument("--trim", action="store_true",
                    help="cut TCR chains to the V domain (FR4 boundary)")
    args = ap.parse_args()
    work = args.work
    parser = MMCIFParser(QUIET=True)
    ow6 = parser.get_structure("ow6", str(C5 / "inputs" / "reference-structures" / "7OW6.cif"))[0]
    ow5 = parser.get_structure("ow5", str(C5 / "inputs" / "reference-structures" / "7OW5.cif"))[0]

    tcr_a = chain_sequence(ow6, "D")
    tcr_b = chain_sequence(ow6, "E")
    full_lengths = (len(tcr_a), len(tcr_b))
    if args.trim:
        tcr_a, tcr_b = trim_vdomain(tcr_a), trim_vdomain(tcr_b)
    hla = chain_sequence(ow6, "A")
    b2m = chain_sequence(ow6, "B")
    pep = chain_sequence(ow6, "C")
    hla_wt = chain_sequence(ow5, "A")
    b2m_wt = chain_sequence(ow5, "B")
    pep_wt = chain_sequence(ow5, "C")
    assert pep == "VVVGADGVGK", pep
    assert pep_wt == "VVVGAGGVGK", pep_wt

    rng = random.Random(42)
    shuf_a = "".join(rng.sample(tcr_a, len(tcr_a)))
    shuf_b = "".join(rng.sample(tcr_b, len(tcr_b)))

    for sub in ("pdb", "seqs", "folds"):
        (work / sub).mkdir(parents=True, exist_ok=True)
    CONTROLS.mkdir(parents=True, exist_ok=True)
    suffix = "-fv" if args.trim else ""

    extract(ow6, ("A", "B", "C", "D", "E"), work / "pdb" / "jdi-g12d.pdb")
    extract(ow5, ("A", "B", "C", "D", "E"), work / "pdb" / "jdi-wt.pdb")
    extract(ow6, ("A", "B", "D", "E"), work / "pdb" / "jdi-peptidefree.pdb")
    for f in ("jdi-g12d.pdb", "jdi-wt.pdb", "jdi-peptidefree.pdb"):
        if not args.trim:
            shutil.copyfile(work / "pdb" / f, CONTROLS / f)

    (work / "seqs" / "msa-targets.fa").write_text(
        "".join(f">{name}\n{seq}\n" for name, seq in
                (("hla_a1101", hla), ("b2m", b2m), ("tcr_alpha", tcr_a),
                 ("tcr_beta", tcr_b))))

    warn: list[str] = []
    warn += boltz_yaml(work / "folds" / "pos-g12d.yaml",
                       [("A", tcr_a, True), ("B", tcr_b, True), ("C", hla, True),
                        ("D", b2m, True), ("E", pep, False)])
    warn += boltz_yaml(work / "folds" / "pos-wt.yaml",
                       [("A", tcr_a, True), ("B", tcr_b, True), ("C", hla_wt, True),
                        ("D", b2m_wt, True), ("E", pep_wt, False)])
    warn += boltz_yaml(work / "folds" / "neg-peptidefree.yaml",
                       [("A", tcr_a, True), ("B", tcr_b, True), ("C", hla, True),
                        ("D", b2m, True)])
    warn += boltz_yaml(work / "folds" / "neg-shuffled.yaml",
                       [("A", shuf_a, False), ("B", shuf_b, False), ("C", hla, True),
                        ("D", b2m, True), ("E", pep, False)])

    chai_inputs(work, "pos-g12d", [("A", tcr_a), ("B", tcr_b), ("C", hla), ("D", b2m),
                                   ("E", pep)], [4, 5, 6, 7, 8], [65, 155], ("A", "B"))
    chai_inputs(work, "pos-wt", [("A", tcr_a), ("B", tcr_b), ("C", hla_wt), ("D", b2m_wt),
                                 ("E", pep_wt)], [4, 5, 6, 7, 8], [65, 155], ("A", "B"))
    chai_inputs(work, "neg-peptidefree", [("A", tcr_a), ("B", tcr_b), ("C", hla),
                                          ("D", b2m)], [4, 5, 6, 7, 8], [65, 155],
                ("A", "B"))
    chai_inputs(work, "neg-shuffled", [("A", shuf_a), ("B", shuf_b), ("C", hla),
                                       ("D", b2m), ("E", pep)], [4, 5, 6, 7, 8],
                [65, 155], ("A", "B"))

    manifest = {
        "built": "c0-build-controls.py",
        "arms": ["pos-g12d", "pos-wt", "neg-peptidefree", "neg-shuffled"],
        "chains": "A=TCRalpha B=TCRbeta C=HLA-heavy D=b2m E=peptide",
        "sequences": {"tcr_alpha": len(tcr_a), "tcr_beta": len(tcr_b),
                      "hla": len(hla), "b2m": len(b2m), "peptide": pep},
        "trimmed": bool(args.trim),
        "full_tcr_lengths": list(full_lengths),
        "shuffled_seed": 42,
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    if args.trim:
        print(f"trim: TCRalpha {full_lengths[0]} -> {len(tcr_a)}, "
              f"TCRbeta {full_lengths[1]} -> {len(tcr_b)}; "
              f"total {len(tcr_a) + len(tcr_b) + len(hla) + len(b2m) + len(pep)} res")
    print("built under", work)
    for arm in manifest["arms"]:
        print(" ", arm)
    if warn:
        print("\nMISSING MSAs (fetch then re-run):")
        for w in sorted(set(warn)):
            print("  ", w)
    else:
        print("\nall target MSAs found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
