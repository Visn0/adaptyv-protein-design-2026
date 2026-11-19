#!/usr/bin/env python3
"""Map 6X18: which chain is the receptor, which is the agonist peptide, and
which receptor residues line the peptide-binding groove (the challenge's
recommended epitope). Writes notes/groove-contacts.md + a hotspot CSV.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/analyze_6x18.py
"""
import csv
import pathlib

from Bio.PDB import MMCIFParser
from Bio.PDB.Polypeptide import is_aa
from Bio.Data.PDBData import protein_letters_3to1_extended as _t31

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "03-glp1r"
CIF = CH / "inputs" / "6X18.cif"
OUT_NOTE = CH / "notes" / "groove-contacts.md"
OUT_CSV = CH / "inputs" / "groove-hotspots.csv"

TARGET_SEQ = ("RPQGATVSLWETVQKWREYRRQCQRSLTEDPPPATDLFCNRTFDEYACWPDGEPGSFVNVSCPWYLPWASSVPQGHVYRFCTAEGLWL"
              "QKDNSSLPWRDLSECEESKRGERSSPEEQLLFLYIIYTVGYALSFSALVIASAILLGFRHLHCTRNYIHLNLFASFILRALSVFIKD"
              "AALKWMYSTAAQQHQWDGLLSYQDSLSCRLVFLLMQYCVAANYYWLLVEGVYLYTLLAFSVLSEQWIFRLYVSIGWGVPLLFVVPW"
              "GIVKYLYEDEGCWTRNSNMNYWLIIRLPILFAIGVNFLIFVRVICIVVSKLKANLMCKTDIKCRLAKSTLTLIPLLGTHEVIFAFV"
              "MDEHARGTLRFIKLFTELSFTSFQGLMVAILYCFVNNEVQLEFRKSWERWRLEHLHIQRDSS")

def _one_letter(resname: str) -> str:
    return _t31.get(resname, "X")


structure = MMCIFParser(QUIET=True).get_structure("6x18", str(CIF))[0]
print("chains:")
chains = {}
for chain in structure:
    residues = [r for r in chain if is_aa(r, standard=False)]
    seq = "".join(_one_letter(r.resname) for r in residues)
    chains[chain.id] = (chain, residues, seq)
    print(f"  {chain.id}: {len(residues)} residues, first={residues[0].id[1] if residues else '-'} "
          f"last={residues[-1].id[1] if residues else '-'}")

# the receptor = chain R (the brief names it); verify by identity against the
# challenge segment with a real alignment (6X18 has disordered internal loops,
# so a naive position-wise comparison misaligns after the first gap)
from Bio.Align import PairwiseAligner

receptor_id = "R"
rseq = chains[receptor_id][2]
offset = chains[receptor_id][1][0].id[1] - 24
expected = TARGET_SEQ[offset:offset + len(rseq)]
_aligner = PairwiseAligner()
_aligner.mode = "global"
_alignment = _aligner.align(expected, rseq)[0]
_matches = sum(1 for a, b in zip(_alignment[0], _alignment[1]) if a == b and a != "-")
identity = _matches / max(len(expected), len(rseq))
print(f"receptor chain {receptor_id}: aligned identity vs the challenge segment = {identity:.3f} "
      f"(offset {offset}, {len(rseq)} residues)")

# the peptide = the shortest chain that is not the receptor and is >= 20 residues
peptide_candidates = [(cid, len(res)) for cid, (_, res, _) in chains.items()
                      if cid != receptor_id and len(res) >= 20]
print(f"peptide candidates: {peptide_candidates}")
peptide_id = min(peptide_candidates, key=lambda kv: kv[1])[0] if peptide_candidates else None
print(f"peptide chain: {peptide_id}")

# contacts: receptor residues within 4.5 A of any peptide atom
receptor = chains[receptor_id][0]
contacts = {}
if peptide_id:
    peptide_atoms = [a for a in chains[peptide_id][0].get_atoms()]
    for res in receptor:
        if not is_aa(res, standard=False):
            continue
        for atom in res:
            hit = False
            for patom in peptide_atoms:
                d2 = sum((atom.coord[i] - patom.coord[i]) ** 2 for i in range(3))
                if d2 <= 4.5 ** 2:
                    hit = True
                    break
            if hit:
                contacts[res.id[1]] = res.resname
                break

print(f"receptor residues within 4.5 A of the peptide: {len(contacts)}")
print("contacts:", ", ".join(f"{n}{r}" for n, r in sorted(contacts.items())))

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["resnum_6x18", "resname"])
    for num, name in sorted(contacts.items()):
        writer.writerow([num, name])

lines = [
    "# 6X18 — chains and the peptide-binding groove (computed)",
    "",
    f"Chains: {', '.join(f'{cid} ({len(res)} res)' for cid, (_, res, _) in chains.items())}",
    f"Receptor chain: **{receptor_id}** (identity {identity:.3f} vs the challenge segment)",
    f"Peptide chain: **{peptide_id}** ({len(chains[peptide_id][1]) if peptide_id else 0} residues)",
    "",
    f"Receptor residues within 4.5 Å of the peptide ({len(contacts)}):",
    "",
    ", ".join(f"{name}{num}" for num, name in sorted(contacts.items())),
    "",
    f"Hotspot CSV: `inputs/groove-hotspots.csv` (6X18 numbering).",
    "",
]
OUT_NOTE.write_text("\n".join(lines))
print(f"wrote {OUT_NOTE} and {OUT_CSV}")
