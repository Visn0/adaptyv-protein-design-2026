#!/usr/bin/env python3
"""Align our chain A against the HLA spec; list gaps (unresolved regions)."""
import difflib
import gemmi

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


spec = ("GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQ"
        "TDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQIT"
        "KRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEIT"
        "LTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT")

st = gemmi.read_structure(
    str(_repo_root() / "challenges/05-pmhc/inputs/7OW6-G12D-noTCR.pdb"))
ours = gemmi.one_letter_code([r.name for r in st[0]["A"]])

print(f"spec {len(spec)} aa | crystal chain A {len(ours)} aa")
sm = difflib.SequenceMatcher(None, spec, ours, autojunk=False)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "equal":
        continue
    print(f"{op}: spec[{i1}:{i2}]='{spec[i1:i2]}' vs ours[{j1}:{j2}]='{ours[j1:j2]}'")
ratio = sm.ratio()
print(f"identity ratio: {ratio:.4f}")

# map to challenge construct numbering (25-305)
sm2 = difflib.SequenceMatcher(None, spec, ours, autojunk=False)
blocks = sm2.get_matching_blocks()
first = blocks[0]
last = blocks[-2] if len(blocks) >= 2 else blocks[0]
print(f"first aligned spec idx {first[0]} -> construct res {25+first[0]}; "
      f"last aligned {last[0]+last[2]-1} -> construct res {25+last[0]+last[2]-1}")
