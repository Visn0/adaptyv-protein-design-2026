"""Prepare one complex for the molecular-dynamics stages.

Four jobs. Each job is pure text or geometry work, so the unit tests cover it:

    find_fold                 locate exactly one fold file for a design id
    complete_structure        fill missing heavy atoms and terminal groups (PDBFixer)
    set_his_state             name the switch histidine for one protonation state
    nearest_carboxylate_pairs the tracked N...O distance pairs
    pick_neutral_tautomer     keep the pose-facing nitrogen protonated

Chain convention, same as the challenge pipelines: binder = chain B,
target = chain A. Distances are Angstrom.
"""
from __future__ import annotations

import re
from pathlib import Path

DEFAULT_CUTOFF = 12.0


# --------------------------------------------------------------- fold finder

def find_fold(folds_dir, design_id: str) -> Path | None:
    """The fold file for exactly this design.

    A plain prefix glob is wrong: design '..._H47' also matches the pair file
    '..._H47_H51_unrelaxed_rank_001*.pdb'. Anchor the match after the id.
    This is the same bug class as the c1 score-file matcher.
    """
    pattern = re.compile(rf"^{re.escape(design_id)}(?:_unrelaxed)?_rank_001.*\.pdb$")
    matches = sorted(p for p in Path(folds_dir).rglob("*.pdb") if pattern.match(p.name))
    return matches[0] if matches else None


# ----------------------------------------------------------- structure clean

def complete_structure(path, out_path: Path) -> dict:
    """Complete heavy atoms and terminal groups with PDBFixer.

    AlphaFold outputs are almost complete. PDBFixer adds the C-terminal
    oxygens and reports any missing residues or atoms. This step must run
    before any histidine is renamed: PDBFixer knows HIS, not HIP or HIE.
    """
    from openmm.app import PDBFile
    from pdbfixer import PDBFixer

    fixer = PDBFixer(filename=str(path))
    fixer.findMissingResidues()
    missing_residues = {str(key): value for key, value in fixer.missingResidues.items()}
    fixer.findNonstandardResidues()
    nonstandard = [str(item[0]) for item in fixer.nonstandardResidues]
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(keepWater=False)
    fixer.findMissingAtoms()
    missing_atoms = {str(key): sorted(value) for key, value in fixer.missingAtoms.items()}
    fixer.addMissingAtoms()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as handle:
        PDBFile.writeFile(fixer.topology, fixer.positions, handle)
    return {
        "atoms": fixer.topology.getNumAtoms(),
        "missing_residues": missing_residues,
        "nonstandard": nonstandard,
        "missing_atoms": missing_atoms,
    }


# ----------------------------------------------------------- histidine state

def set_his_state(text: str, chain: str, resnum: int, resname: str) -> tuple[str, int]:
    """Rename one histidine in an ATOM block. Returns (text, atoms renamed).

    The residue name picks the protonation state in the AMBER naming:
        HIP  both nitrogens protonated, charge +1 (the low-pH state)
        HIE  proton on NE2 only, neutral        (the high-pH state)
        HID  proton on ND1 only, neutral
    OpenMM adds the matching hydrogens from the residue name alone.
    """
    out, changed = [], 0
    for line in text.splitlines():
        if (line.startswith(("ATOM", "HETATM")) and line[21] == chain
                and line[17:20].strip() == "HIS"):
            try:
                same_residue = int(line[22:26]) == int(resnum)
            except ValueError:
                same_residue = False
            if same_residue:
                line = line[:17] + f"{resname:<3}" + line[20:]
                changed += 1
        out.append(line)
    return "\n".join(out) + "\n", changed


# -------------------------------------------------------- tracked atom pairs

def _model(path):
    from Bio.PDB import MMCIFParser, PDBParser

    text = str(path).lower()
    if text.endswith((".cif", ".mmcif")):
        return MMCIFParser(QUIET=True).get_structure("s", str(path))[0]
    return PDBParser(QUIET=True).get_structure("s", str(path))[0]


def nearest_carboxylate_pairs(path, his_chain: str = "B", his_resnum: int = 47,
                              target_chain: str = "A",
                              cutoff: float = DEFAULT_CUTOFF,
                              max_pairs: int = 6) -> list[dict]:
    """The nearest His-nitrogen ... carboxylate-oxygen pairs of one complex.

    Each entry: his_atom (ND1 or NE2), target_atom (OD1/OD2/OE1/OE2),
    target_resname, target_resnum, distance (Angstrom). Sorted by distance.
    An empty list means the histidine has no carboxylate within `cutoff`.
    """
    model = _model(path)
    if his_chain not in model or target_chain not in model:
        raise ValueError(f"chains {his_chain} and {target_chain} are both required")
    residue = model[his_chain][int(his_resnum)]
    if residue.get_resname().strip() != "HIS":
        raise ValueError(
            f"residue {his_chain}{his_resnum} is {residue.get_resname()}, not HIS. "
            "Check the switch_his parameter."
        )
    oxygens = []
    for res in model[target_chain]:
        if res.id[0] != " " or res.get_resname() not in ("ASP", "GLU"):
            continue
        for atom_name in ("OD1", "OD2", "OE1", "OE2"):
            if atom_name in res:
                oxygens.append((res.get_resname(), res.id[1], atom_name, res[atom_name].coord))
    pairs = []
    for nitrogen in ("ND1", "NE2"):
        if nitrogen not in residue:
            continue
        for resname, resnum, atom_name, coord in oxygens:
            distance = float(((residue[nitrogen].coord - coord) ** 2).sum() ** 0.5)
            if distance <= cutoff:
                pairs.append({
                    "his_atom": nitrogen,
                    "target_resname": resname,
                    "target_resnum": int(resnum),
                    "target_atom": atom_name,
                    "distance": round(distance, 2),
                })
    pairs.sort(key=lambda entry: entry["distance"])
    return pairs[:max_pairs]


def pick_neutral_tautomer(pairs: list[dict], default: str = "HIE") -> str:
    """The neutral tautomer that keeps the pose-facing proton.

    Rule: protonate the nitrogen that points at the partner oxygen. A
    histidine with NE2 near a carboxylate becomes HIE. One with ND1 near
    the carboxylate becomes HID. No pairs at all returns the default.
    """
    best = {}
    for entry in pairs:
        best.setdefault(entry["his_atom"], entry["distance"])
        best[entry["his_atom"]] = min(best[entry["his_atom"]], entry["distance"])
    if not best:
        return default
    if best.get("NE2") is None:
        return "HID"
    if best.get("ND1") is None:
        return "HIE"
    return "HIE" if best["NE2"] <= best["ND1"] else "HID"
