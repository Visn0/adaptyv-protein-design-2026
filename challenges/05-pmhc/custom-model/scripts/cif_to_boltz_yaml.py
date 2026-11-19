#!/usr/bin/env python3
"""Debug + convert: RFD4 output CIF -> boltz yaml."""
import sys
import gemmi
import yaml

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


cif = sys.argv[1]
out = sys.argv[2]

st = gemmi.read_structure(cif)
st.setup_entities()
print("models:", len(st), "| chains:", [ch.name for ch in st[0]])
seqs = {}
for ch in st[0]:
    if len(ch) == 0:
        continue
    try:
        seq = gemmi.one_letter_code([r.name for r in ch])
    except Exception as exc:
        print("chain", ch.name, "error:", exc)
        continue
    seqs[ch.name] = seq
    print("chain", ch.name, len(ch), "res,", len(seq), "in sequence")

if not seqs:
    print("NO CHAINS PARSED")
    sys.exit(1)

# order chains by their atom order in the file: 0,1,2,3 -> A,B,C,D
mapping = {}
letters = "ABCD"
for i, name in enumerate(seqs):
    mapping[name] = letters[i]

# canonical chain ids for the whole pipeline (A=HLA, B=b2m, C=peptide, D=binder),
# regardless of the order the generator emitted
HLA_MSA = str(_repo_root() / "challenges/05-pmhc/inputs/msa/c56917c149b0-d1024.a3m")
B2M_MSA = str(_repo_root() / "challenges/05-pmhc/inputs/msa/3c7486ad1c1e-d1024.a3m")


def canon(seq: str):
    """Return (chain_id, msa) for a sequence."""
    if seq.startswith("GSHSMRY"):
        return "A", HLA_MSA
    if seq.startswith("IQRTPKIQ"):
        return "B", B2M_MSA
    if seq == "VVVGADGVGK":
        return "C", "empty"
    return "D", "empty"


doc = {"version": 1, "sequences": []}
used = set()
for name, seq in seqs.items():
    cid, msa = canon(seq)
    n = 1
    while cid in used:  # duplicate designed chains keep the letter
        n += 1
        cid = cid.rstrip("0123456789") + str(n)
    used.add(cid)
    doc["sequences"].append({"protein": {"id": cid, "sequence": seq, "msa": msa}})
with open(out, "w") as f:
    yaml.safe_dump(doc, f, sort_keys=False)
print("wrote", out, {mapping[k]: len(v) for k, v in seqs.items()})
