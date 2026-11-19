#!/usr/bin/env python3
"""Single-design close-up viewer pages for visual (vision) analysis.

Reuses the campaign viewer generator's machinery (superpose onto the 7OW6
crystal frame, extract the binder) but renders ONE design per page with the
camera focused tightly on the interface region.

Usage: PYTHONPATH= .venv/bin/python view-singles.py <design> [...]
Writes challenges/05-pmhc/viewers/multiview/single-<design>.html
"""

from __future__ import annotations

import io
import pathlib
import sys

import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "challenges" / "05-pmhc" / "viewers" / "scripts"))

from Bio.PDB import PDBIO, Select  # noqa: E402

from tools.serve import molstar_viewer  # noqa: E402
import make_molstar_multiview as mm  # noqa: E402

OUT = REPO / "challenges" / "05-pmhc" / "viewers" / "multiview"
COLORS = [0xe879f9, 0x34d399, 0xa3e635, 0xf472b6, 0x22d3ee, 0xa78bfa,
          0xfb923c, 0xfacc15, 0x2dd4bf, 0x818cf8]
INTERFACE_CUTOFF = 12.0


class _Binder(Select):
    def accept_chain(self, chain):
        return chain.id == mm.BINDER_CHAIN


def focus_from_interface(structure):
    """Centroid + radius over binder atoms within 12 A of the peptide."""
    pep = [a.get_coord() for c in structure if c.id == "C" for a in c.get_atoms()]
    binder = [a.get_coord() for a in structure[mm.BINDER_CHAIN].get_atoms()]
    near = [b for b in binder
            if pep and min(float(np.linalg.norm(b - p)) for p in pep) <= INTERFACE_CUTOFF]
    pts = pep + (near or binder)
    center = np.mean(pts, axis=0)
    rad = float(np.max(np.linalg.norm(pts - center, axis=1))) + 10.0
    return {"center": [round(float(v), 2) for v in center],
            "radius": round(rad, 1)}


def main() -> int:
    ref_pdb = (REPO / "challenges/05-pmhc/inputs/7OW6-G12D-noTCR.pdb").read_text()
    for i, design in enumerate(sys.argv[1:]):
        cif = mm.fold_cif(design)
        if not cif:
            print(f"no fold: {design}")
            continue
        st = mm.MMCIFParser(QUIET=True).get_structure("m", str(cif))[0]
        rms, nfit, mode = mm.superpose_onto_crystal(st)
        buf = io.StringIO()
        io_ = PDBIO()
        io_.set_structure(st)
        io_.save(buf, select=_Binder())
        color = COLORS[i % len(COLORS)]
        items = [
            {"id": "target", "label": "KRAS G12D pMHC (7OW6) - reference",
             "color": 39423, "pdb": ref_pdb, "chains": ["A", "B", "C"],
             "chainColors": {}, "interface": [], "focus": None, "on": True,
             "scores": {}},
            {"id": design, "label": design, "color": color,
             "pdb": buf.getvalue(), "chains": [mm.BINDER_CHAIN],
             "chainColors": {mm.BINDER_CHAIN: color},
             "interface": [], "focus": focus_from_interface(st), "on": True,
             "scores": {}},
        ]
        html = molstar_viewer.render_viewer_page(
            items, title=f"{design} - interface close-up", label=design,
            slug=f"single-{design}", binder_chain=mm.BINDER_CHAIN)
        out = OUT / f"single-{design}.html"
        out.write_text(html)
        print(f"wrote {out.name} (fit {mode} on {nfit} CA, RMSD {rms:.2f} A)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
