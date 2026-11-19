#!/usr/bin/env python3
"""Rosetta desolvation / ddG instrument (the Wu 2022 protocol).

For a folded complex: interface analysis (dG_separated + the fa_sol
decomposition), then the same analysis with the P6 residue mutated D->G.
The ddG = dG_sep(G6) - dG_sep(D6): positive means the mutant peptide binds
better - the specificity direction this project needs, measured with an
explicit desolvation term that the charge-Coulomb E-score lacks.

Control discipline: the JDI TCR fold must read positive (it prefers G12D);
if the control's sign is wrong, the instrument is disqualified and recorded
as such - no exceptions.

Usage:
  ~/.venvs/rosetta/bin/python ros-desolv.py --pdb X.pdb --pep-chain C --pep-res 6 \
      --fixed "A,B,C" [--label NAME]
"""

from __future__ import annotations

import argparse
import sys

import pyrosetta
from pyrosetta import pose_from_pdb
from pyrosetta.rosetta.protocols.rosetta_scripts import XmlObjects

XML = """<ROSETTASCRIPTS>
<SCOREFXNS><ScoreFunction name="sf" weights="ref2015"/></SCOREFXNS>
<MOVERS>
 <InterfaceAnalyzerMover name="ia" scorefxn="sf" fixedchains="{fixed}"
   pack_input="true" pack_separated="false"/>
</MOVERS>
<PROTOCOLS><Add mover="ia"/></PROTOCOLS>
</ROSETTASCRIPTS>"""


def analyze(pose, fixed: str) -> dict:
    xo = XmlObjects.create_from_string(XML.format(fixed=fixed))
    mover = xo.get_mover("ia")
    mover.apply(pose)
    dg = mover.get_interface_dG()
    dsasa = mover.get_interface_delta_sasa()
    return {"dG_sep": dg, "dSASA": dsasa,
            "dG_per_dSASA": dg / max(dsasa, 1e-6)}


def fa_sol(pose) -> float:
    sf = pyrosetta.create_score_function("ref2015")
    sf(pose)
    energies = pose.energies()
    return float(energies.total_energies()[pyrosetta.rosetta.core.scoring.fa_sol])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdb", required=True)
    ap.add_argument("--pep-chain", default="C")
    ap.add_argument("--pep-res", type=int, default=6)
    ap.add_argument("--fixed", default="A,B,C")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    pyrosetta.init("-ignore_unrecognized_res -mute all", silent=True)
    pose = pose_from_pdb(args.pdb)
    info = pose.pdb_info()
    seqpos = info.pdb2pose(args.pep_chain, args.pep_res)
    if seqpos == 0:
        print(f"ERROR: P6 ({args.pep_chain}{args.pep_res}) not found", file=sys.stderr)
        return 1
    wt_name = pose.residue(seqpos).name3()

    wt = analyze(pose, args.fixed)
    wt_sol = fa_sol(pose)

    from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
    mut = MutateResidue(target=seqpos, new_res="GLY")
    mut.apply(pose)
    mut_an = analyze(pose, args.fixed)
    mut_sol = fa_sol(pose)

    ddg = mut_an["dG_sep"] - wt["dG_sep"]
    print(f"{args.label or args.pdb}\t{wt_name}->GLY\t"
          f"dG_wt {wt['dG_sep']:.1f}\tdG_mut {mut_an['dG_sep']:.1f}\t"
          f"ddG {ddg:+.1f}\tEsol_wt {wt_sol:.1f}\tEsol_mut {mut_sol:.1f}\t"
          f"dEsol {mut_sol - wt_sol:+.1f}\tdSASA {wt['dSASA']:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
