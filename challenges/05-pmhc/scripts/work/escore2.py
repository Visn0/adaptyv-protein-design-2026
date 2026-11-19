#!/usr/bin/env python3
"""E-score v2: histidine-aware electrostatic reading of the P6 mutant charge.

The v1 charge model (ASP/GLU/LYS/ARG) is blind to histidine - the residue the
native JDI discriminator uses (TCRbeta His100, 7.5 A from the Asp6
carboxylate). v2 adds the binder's histidines with their real protonation
fraction from PROPKA run on the folded complex (f = 1/(1+10^(7.4-pKa))); the
ring nitrogens carry +0.5*f each.

Usage: PYTHONPATH= .venv/bin/python escore2.py <fold.cif> [...]
Writes one line per structure: E_D6_v2, charged_near, n_charges, n_his_shell,
plus the per-His detail to stderr.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

import gemmi

CHARGED = {
    "ASP": {"OD1": -0.5, "OD2": -0.5},
    "GLU": {"OE1": -0.5, "OE2": -0.5},
    "LYS": {"NZ": 1.0},
    "ARG": {"NH1": 0.5, "NH2": 0.5, "NE": 0.5},
}
D6_CHARGE = {"OD1": -0.5, "OD2": -0.5}
PEPTIDE_RES = 6
BINDER_CHAIN = "D"
PROPKA = pathlib.Path.home() / ".venvs" / "propka" / "bin" / "propka3"


def his_fractions(pdb_path: pathlib.Path, chain: str) -> dict[int, float]:
    """resnum -> protonation fraction at pH 7.4, from PROPKA."""
    with tempfile.TemporaryDirectory() as td:
        pdb_copy = pathlib.Path(td) / "in.pdb"
        pdb_copy.write_text(pdb_path.read_text())
        subprocess.run([str(PROPKA), "in.pdb"], cwd=td, check=True,
                       capture_output=True, timeout=600)
        pka_file = pathlib.Path(td) / "in.pka"
        if not pka_file.exists():
            return {}
        out: dict[int, float] = {}
        for line in pka_file.read_text().splitlines():
            m = re.match(r"^\s*HIS\s+(\d+)\s+([A-Za-z0-9]+)\s+(-?\d+\.\d+)", line)
            if m and m.group(2) == chain:
                pka = float(m.group(3))
                out[int(m.group(1))] = 1.0 / (1.0 + 10 ** (7.4 - pka))
        return out


def score(path: pathlib.Path) -> dict | None:
    st = gemmi.read_structure(str(path))
    if len(st) == 0:
        return None
    m = st[0]
    binder = m.find_chain(BINDER_CHAIN)
    peptide = m.find_chain("C")
    if binder is None or peptide is None:
        return None
    d6 = [(D6_CHARGE[a.name], a.pos) for r in peptide
          if r.seqid.num == PEPTIDE_RES for a in r if a.name in D6_CHARGE]
    if not d6:
        return None
    # PROPKA on a temp pdb of the complex
    with tempfile.TemporaryDirectory() as td:
        pdb = pathlib.Path(td) / "c.pdb"
        st.write_pdb(str(pdb))
        fracs = his_fractions(pdb, BINDER_CHAIN)
    charges = []
    for r in binder:
        q = CHARGED.get(r.name)
        if q:
            for a in r:
                if a.name in q:
                    charges.append((q[a.name], a.pos, f"{r.name}{r.seqid.num}"))
        elif r.name == "HIS":
            f = fracs.get(r.seqid.num, 0.0)
            if f <= 0.01:
                continue
            for a in r:
                if a.name in ("ND1", "NE2"):
                    charges.append((0.5 * f, a.pos, f"HIS{r.seqid.num}(f={f:.2f})"))
    e = 0.0
    near = 0
    his_shell = 0
    for q, pos, label in charges:
        for qd, p in d6:
            r = pos.dist(p)
            if r < 1.5:
                continue
            e += 83.0 * q * qd / (r * r)  # matches v1: eps = 4r folded in
        dmin = min(pos.dist(p) for _, p in d6)
        if dmin < 8.0:
            near += 1
            if label.startswith("HIS"):
                his_shell += 1
    return {"E_D6": round(e, 2), "charged_near_D6": near,
            "n_binder_charges": len(charges), "n_his_shell": his_shell,
            "his": {k: round(v, 2) for k, v in fracs.items()}}


def main() -> int:
    print("    E_D6 near   q  his  design")
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        r = score(p)
        if not r:
            print(f"     ---  --- --- ---  {p.name} (parse failed)")
            continue
        print(f"{r['E_D6']:8.2f} {r['charged_near_D6']:4d} {r['n_binder_charges']:3d} "
              f"{r['n_his_shell']:3d}  {p.name}")
        if r["his"]:
            print(f"         his fractions: {r['his']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
