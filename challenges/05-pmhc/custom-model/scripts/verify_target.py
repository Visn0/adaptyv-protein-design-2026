#!/usr/bin/env python3
"""Verify our local target structure against the challenge specification."""
import gemmi

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


SPEC = {
    "HLA": ("GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQ"
            "TDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQIT"
            "KRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEIT"
            "LTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT"),
    "B2M": ("IQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFT"
            "PTEKDEYACRVNHVTLSQPKIVKWDRDM"),
    "PEP": "VVVGADGVGK",
}

st = gemmi.read_structure(
    str(_repo_root() / "challenges/05-pmhc/inputs/7OW6-G12D-noTCR.pdb"))
st.setup_entities()
seqs = {}
for ch in st[0]:
    if len(ch):
        seqs[ch.name] = gemmi.one_letter_code([r.name for r in ch])

for name, spec in SPEC.items():
    hit = None
    for cid, seq in seqs.items():
        if seq == spec:
            hit = (cid, "exact")
        elif spec in seq or seq in spec:
            hit = (cid, f"overlap: ours {len(seq)} aa, spec {len(spec)} aa, "
                        f"ours {'inside spec' if seq in spec else 'extends spec'}")
        if hit:
            break
    print(f"{name}: {hit or 'NOT FOUND'}")

# where do our chains fall within the HLA spec?
hla = seqs.get("A", "")
missing = []
for i, aa in enumerate(SPEC["HLA"]):
    if aa not in (hla[i] if i < len(hla) else ""):
        missing.append(i + 1)
# simple subsequence check
if hla and hla in SPEC["HLA"]:
    off = SPEC["HLA"].index(hla)
    print(f"HLA chain A: our {len(hla)} aa = spec residues {off+1}-{off+len(hla)} "
          f"(construct numbering 25-305 => PDB numbering ~{25+off}-{25+off+len(hla)-1})")
pep = seqs.get("C", "")
print("peptide exact:", pep == SPEC["PEP"], "| ours:", pep)
b2m = seqs.get("B", "")
print("b2m exact:", b2m == SPEC["B2M"], "| ours len:", len(b2m), "spec len:", len(SPEC["B2M"]))
