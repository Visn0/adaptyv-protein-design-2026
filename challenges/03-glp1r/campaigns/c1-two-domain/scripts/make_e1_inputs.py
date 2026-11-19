#!/usr/bin/env python3
"""Build the campaign-1 target: 6X18 chain R (protein only) as a PDB, with the
contiguous residue blocks (RFD3 contigs must not skip a residue) and the E1
generation JSON (binder 60-100 aa against the groove + TM-pocket hotspots).

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/make_e1_inputs.py
"""
import json
import pathlib

from Bio.PDB import MMCIFParser, PDBIO, Select
from Bio.PDB.Polypeptide import is_aa

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "03-glp1r"
CIF = CH / "inputs" / "6X18.cif"
OUT_PDB = CH / "inputs" / "target-R.pdb"
OUT_JSON = CH / "inputs" / "rfd3-e1.json"

# groove (ECD) + TM-pocket hotspots, 6X18/UniProt numbering
HOTSPOTS = "R67,R69,R88,R91,R121,R128,R298,R300,R309,R313"

structure = MMCIFParser(QUIET=True).get_structure("6x18", str(CIF))[0]
chain = structure["R"]
residues = [r for r in chain if is_aa(r, standard=False)]
numbers = sorted(r.id[1] for r in residues)

# contiguous blocks
blocks = []
start = prev = numbers[0]
for num in numbers[1:]:
    if num == prev + 1:
        prev = num
        continue
    blocks.append((start, prev))
    start = prev = num
blocks.append((start, prev))
print("blocks:", blocks)


class OnlyR(Select):
    def accept_chain(self, c):
        return c.id == "R"

    def accept_residue(self, r):
        return r.id[0] == " "  # protein residues only (drop waters/ligands)


io = PDBIO()
io.set_structure(structure)
io.save(str(OUT_PDB), OnlyR())
print(f"wrote {OUT_PDB}")

contig_target = ",".join(f"R{a}-{b}" if b > a else f"R{a}" for a, b in blocks)
config = {
    "c3-e1": {
        "input": str(OUT_PDB),
        "contig": f"60-100,/0,{contig_target}",
        "select_hotspots": HOTSPOTS,
        "infer_ori_strategy": "hotspots",
        "is_non_loopy": True,
    }
}
OUT_JSON.write_text(json.dumps(config, indent=2))
print(f"wrote {OUT_JSON}")
print(f"contig: 60-100,/0,{contig_target}")
print(f"hotspots: {HOTSPOTS}")
