"""C5 target physics — measure the physical/chemical context of the KRAS G12D pMHC target.

Inputs (committed):
  inputs/7OW6-G12D-noTCR.pdb        organizer file: G12D state, chains A (HLA-A*11:01), B (b2m), C (peptide)
  inputs/7OW5-WT-noTCR.pdb          organizer file: wild-type state
  inputs/7OW6-peptide-free.pdb      organizer file: peptide-free state (chains A, B)
  inputs/reference-structures/7OW6.cif   RCSB: G12D + JDI TCR (chains D, E)
  inputs/reference-structures/7OW5.cif   RCSB: WT + same TCR
  inputs/reference-structures/7OW4.cif   RCSB: G12D, receptor-free (peptide missing P5/P6)
  inputs/reference-structures/7OW3.cif   RCSB: WT, receptor-free

Outputs:
  notes/target-physics.csv     per-peptide-residue table (G12D state)
  notes/references/target-physics.json   all metrics

Run: .venv/bin/python challenges/05-pmhc/scripts/target_physics.py
"""

from __future__ import annotations

import csv
import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, PDBParser
from Bio.PDB.SASA import ShrakeRupley
from Bio.PDB.Superimposer import Superimposer

ROOT = Path(__file__).resolve().parents[3]
assert (ROOT / "challenges" / "05-pmhc").is_dir(), f"unexpected repo root: {ROOT}"
C5 = ROOT / "challenges" / "05-pmhc"
INPUTS = C5 / "inputs"
REFS = INPUTS / "reference-structures"

PDB = PDBParser(QUIET=True)
CIF = MMCIFParser(QUIET=True)

AA3 = {"VAL": "V", "GLY": "G", "ALA": "A", "ASP": "D", "LYS": "K"}
PEPTIDE = "VVVGADGVGK"


def heavy_atoms(res):
    return [a for a in res if a.element != "H"]


def load_pdb(path, name="s"):
    return PDB.get_structure(name, str(path))[0]


def load_cif(path, name="s"):
    return CIF.get_structure(name, str(path))[0]


def chain_residues(model, chain_id):
    return [r for r in model[chain_id] if r.id[0] == " "]


def sasa_residues(structure, chains):
    """Return {(chain, resid): sasa} for the given chains, via Shrake-Rupley."""
    sr = ShrakeRupley()
    sr.compute(structure, level="R")
    out = {}
    for ch in chains:
        for res in structure[ch]:
            if res.id[0] == " ":
                out[(ch, res.id[1])] = res.sasa
    return out


def contacts(structure, chains_a, chains_b, cutoff=4.0):
    """Heavy-atom contact pairs between two chain groups. Returns list of dicts."""
    atoms_a = [(ch, r, a) for ch in chains_a for r in structure[ch]
               if r.id[0] == " " for a in heavy_atoms(r)]
    atoms_b = [(ch, r, a) for ch in chains_b for r in structure[ch]
               if r.id[0] == " " for a in heavy_atoms(r)]
    out = []
    for ch_a, r_a, a_a in atoms_a:
        ca = a_a.get_coord()
        for ch_b, r_b, a_b in atoms_b:
            d = float(np.linalg.norm(ca - a_b.get_coord()))
            if d < cutoff:
                out.append({"a": (ch_a, r_a.id[1], a_a.name),
                            "b": (ch_b, r_b.id[1], a_b.name), "d": round(d, 2)})
    return out


def ca_rmsd_superpose(mobile, target, chain_ids, target_chain_ids=None):
    """Superpose mobile onto target using matched CA atoms of given chains. Returns (rms, sup)."""
    tcs = target_chain_ids or chain_ids
    fixed, moving = [], []
    for mc, tc in zip(chain_ids, tcs):
        mres = {r.id[1]: r for r in mobile[mc] if r.id[0] == " " and "CA" in r}
        tres = {r.id[1]: r for r in target[tc] if r.id[0] == " " and "CA" in r}
        for num in sorted(set(mres) & set(tres)):
            fixed.append(tres[num]["CA"])
            moving.append(mres[num]["CA"])
    sup = Superimposer()
    sup.set_atoms(fixed, moving)
    return sup.rms, sup


def main():
    report = {}

    g12d = load_pdb(INPUTS / "7OW6-G12D-noTCR.pdb", "g12d")
    wt = load_pdb(INPUTS / "7OW5-WT-noTCR.pdb", "wt")
    empty = load_pdb(INPUTS / "7OW6-peptide-free.pdb", "empty")
    tcr_complex = load_cif(REFS / "7OW6.cif", "tcr")
    wt_tcr = load_cif(REFS / "7OW5.cif", "wttcr")
    ow4 = load_cif(REFS / "7OW4.cif", "ow4")
    ow3 = load_cif(REFS / "7OW3.cif", "ow3")

    # ---------- 1. peptide burial (G12D and WT states) ----------
    burial = {}
    for label, model in (("g12d", g12d), ("wt", wt)):
        # complex SASA
        sasa_cplx = sasa_residues(model, ["A", "B", "C"])
        # peptide alone
        pep_alone = model["C"].copy()
        pep_alone.id = "C"
        sr = ShrakeRupley()
        sr.compute(pep_alone, level="R")
        rows = []
        for res in chain_residues(model, "C"):
            n = res.id[1]
            s_complex = sasa_cplx[("C", n)]
            s_alone = pep_alone[n].sasa if n in pep_alone else float("nan")
            rel = s_complex / s_alone if s_alone else float("nan")
            rows.append({"pos": n, "aa": AA3.get(res.resname, res.resname),
                         "sasa_complex": round(s_complex, 1),
                         "sasa_alone": round(s_alone, 1),
                         "relative_exposure": round(rel, 3)})
        burial[label] = rows
    report["peptide_burial"] = burial

    # ---------- 2. peptide-HLA contacts + D6 specific interactions ----------
    pep_contacts = {}
    for label, model in (("g12d", g12d), ("wt", wt)):
        cons = contacts(model, ["C"], ["A", "B"], cutoff=4.0)
        per_res = {}
        for c in cons:
            per_res.setdefault(c["a"][1], []).append(c)
        pep_contacts[label] = {
            "n_contacts": len(cons),
            "per_residue": {str(k): len(v) for k, v in sorted(per_res.items())},
            "contact_pairs": [{"pep": c["a"], "hla": c["b"], "d": c["d"]} for c in cons],
        }
    # D6 to R114/Q70/D116 distances (G12D)
    d6 = next(r for r in chain_residues(g12d, "C") if r.id[1] == 6)
    special = {}
    for resno, label in ((114, "R114"), (70, "Q70"), (116, "D116")):
        res = next((r for r in chain_residues(g12d, "A") if r.id[1] == resno), None)
        if res is None:
            continue
        best = None
        for a1 in heavy_atoms(d6):
            if a1.name not in ("OD1", "OD2"):
                continue
            for a2 in heavy_atoms(res):
                d = float(np.linalg.norm(a1.get_coord() - a2.get_coord()))
                if best is None or d < best["d"]:
                    best = {"d": round(d, 2), "pep_atom": a1.name, "hla_atom": f"{label}:{a2.name}"}
        special[label] = best
    report["d6_interactions"] = special

    # sidechain SASA of position 6 (the buried-Asp question), atom-level
    pos6 = {}
    for label, model in (("g12d", g12d), ("wt", wt)):
        sra = ShrakeRupley()
        sra.compute(model, level="A")
        res = next(r for r in chain_residues(model, "C") if r.id[1] == 6)
        bb = ("N", "CA", "C", "O", "OXT")
        whole = sum(a.sasa for a in res)
        sc = sum(a.sasa for a in res if a.name not in bb)
        pep = model["C"].copy()
        pep.id = "C"
        sra2 = ShrakeRupley()
        sra2.compute(pep, level="A")
        res_alone = next(r for r in pep if r.id[1] == 6)
        sc_alone = sum(a.sasa for a in res_alone if a.name not in bb)
        pos6[label] = {"resname": res.resname, "sasa_whole_A2": round(whole, 1),
                       "sasa_sidechain_A2": round(sc, 1),
                       "sasa_sidechain_alone_A2": round(sc_alone, 1),
                       "sidechain_relative_exposure": round(sc / sc_alone, 3) if sc_alone else None}
    report["position6_burial"] = pos6

    # ---------- 3. B-factors (peptide vs heavy chain) ----------
    bfac = {}
    for label, model in (("g12d", g12d), ("wt", wt)):
        def mean_b(res):
            vals = [a.get_bfactor() for a in res if a.get_bfactor() is not None]
            return float(np.mean(vals)) if vals else float("nan")
        pep_b = {r.id[1]: round(mean_b(r), 1) for r in chain_residues(model, "C")}
        hla_b = [mean_b(r) for r in chain_residues(model, "A")]
        bfac[label] = {"peptide": pep_b, "hla_mean": round(float(np.mean(hla_b)), 1)}
    # real B-factors from the RCSB file
    pep_b_rcsb = {r.id[1]: round(float(np.mean([a.get_bfactor() for a in r])), 1)
                  for r in chain_residues(tcr_complex, "C")}
    hla_b_rcsb = float(np.mean([float(np.mean([a.get_bfactor() for a in r]))
                                for r in chain_residues(tcr_complex, "A")]))
    bfac["rcsb_7OW6"] = {"peptide": pep_b_rcsb, "hla_mean": round(hla_b_rcsb, 1)}
    report["bfactors"] = bfac

    # ---------- 4. TCR footprint (7OW6: chains D, E vs A, B, C) ----------
    tcr_cons = contacts(tcr_complex, ["D", "E"], ["A", "B", "C"], cutoff=4.5)
    pep_fp, hla_fp = {}, {}
    for c in tcr_cons:
        ch, num = c["b"][0], c["b"][1]
        tgt = pep_fp if ch == "C" else hla_fp
        tgt[num] = tgt.get(num, 0) + 1
    # interface area: dSASA = SASA(A,B,C) + SASA(D,E) - SASA(all), each computed alone
    def sasa_of(model, chains):
        m2 = deepcopy(model)
        for ch in [c.id for c in m2 if c.id not in chains]:
            m2.detach_child(ch)
        sr_local = ShrakeRupley()
        sr_local.compute(m2, level="R")
        return sum(r.sasa for ch in m2 for r in ch if r.id[0] == " ")

    dsasa = (sasa_of(tcr_complex, ["A", "B", "C"]) + sasa_of(tcr_complex, ["D", "E"])
             - sasa_of(tcr_complex, ["A", "B", "C", "D", "E"]))

    # waters: near the peptide, at the D6 carboxylate, bridging the TCR interface
    waters = [r for r in tcr_complex.get_residues() if r.id[0] == "W"]
    pep_atoms = [a for r in chain_residues(tcr_complex, "C") for a in heavy_atoms(r)]
    d6_oxy = [a for a in d6 if a.name in ("OD1", "OD2")]
    pmhc_atoms = [a for ch in ("A", "B", "C") for r in chain_residues(tcr_complex, ch)
                  for a in heavy_atoms(r)]
    tcr_atoms_all = [a for ch in ("D", "E") for r in chain_residues(tcr_complex, ch)
                     for a in heavy_atoms(r)]

    def wcount(ref, cutoff):
        n = 0
        for w in waters:
            o = next((a for a in w if a.element != "H"), None)
            if o is None:
                continue
            if min(float(np.linalg.norm(o.get_coord() - a.get_coord())) for a in ref) < cutoff:
                n += 1
        return n

    def near(a, ref, cutoff):
        return min(float(np.linalg.norm(a.get_coord() - b.get_coord())) for b in ref) < cutoff

    bridging = 0
    for w in waters:
        o = next((a for a in w if a.element != "H"), None)
        if o is not None and near(o, pmhc_atoms, 4.5) and near(o, tcr_atoms_all, 4.5):
            bridging += 1
    w_min = None
    for w in waters:
        o = next((a for a in w if a.element != "H"), None)
        if o is None:
            continue
        d = min(float(np.linalg.norm(o.get_coord() - a.get_coord())) for a in pep_atoms)
        if w_min is None or d < w_min:
            w_min = d
    report["waters_7OW6"] = {
        "total_HOH": len(waters),
        "within_6A_of_peptide": wcount(pep_atoms, 6.0),
        "within_4_5A_of_D6_carboxylate": wcount(d6_oxy, 4.5),
        "bridging_pMHC_TCR": bridging,
        "min_dist_water_to_peptide_A": round(w_min, 2) if w_min is not None else None,
    }
    report["tcr_footprint"] = {
        "n_contacts_4_5A": len(tcr_cons),
        "peptide_contacts_per_pos": {str(k): v for k, v in sorted(pep_fp.items())},
        "hla_contacts_per_res": {str(k): v for k, v in sorted(hla_fp.items())},
        "peptide_contact_share": round(sum(pep_fp.values()) / len(tcr_cons), 3),
        "interface_area_A2": round(dsasa, 0),
    }
    # same for WT + TCR (7OW5), for comparison
    tcr_cons_wt = contacts(wt_tcr, ["D", "E"], ["A", "B", "C"], cutoff=4.5)
    pep_fp_wt = {}
    for c in tcr_cons_wt:
        if c["b"][0] == "C":
            pep_fp_wt[c["b"][1]] = pep_fp_wt.get(c["b"][1], 0) + 1
    report["tcr_footprint_wt"] = {
        "n_contacts_4_5A": len(tcr_cons_wt),
        "peptide_contacts_per_pos": {str(k): v for k, v in sorted(pep_fp_wt.items())},
    }

    # ---------- 5. peptide conformation: bound vs receptor-free ----------
    # superpose 7OW4 copy-1 heavy chain onto 7OW6 heavy chain, then read the peptide
    rms, sup = ca_rmsd_superpose(ow4, tcr_complex, ["A"], ["A"])
    sup.apply([r["CA"] for r in ow4["C"] if r.id[0] == " " and "CA" in r])
    shift = {}
    for res in chain_residues(ow4, "C"):
        n = res.id[1]
        ref = next((r for r in chain_residues(tcr_complex, "C") if r.id[1] == n), None)
        if ref is not None and "CA" in res and "CA" in ref:
            shift[n] = round(float(np.linalg.norm(res["CA"].get_coord() - ref["CA"].get_coord())), 2)
    ow4_positions = sorted(r.id[1] for r in chain_residues(ow4, "C"))
    report["unbound_peptide"] = {
        "note": "7OW4 copy-1: heavy-chain CA superpose onto 7OW6, then peptide CA displacements",
        "hla_ca_rmsd": round(rms, 2),
        "peptide_positions_present": ow4_positions,
        "missing_positions": [n for n in range(1, 11) if n not in ow4_positions],
        "per_position_ca_shift_A": {str(k): v for k, v in sorted(shift.items())},
    }

    # ---------- 6. peptide-free state: what the peptide deletion exposes ----------
    # The organizer peptide-free file carries the SAME heavy-chain/b2m coordinates as the
    # G12D file (verified below: CA RMSD 0.0) -- it is a deletion model, not an
    # experimental empty-MHC structure. Measure the newly exposed surface instead.
    rms2, _ = ca_rmsd_superpose(empty, g12d, ["A", "B"], ["A", "B"])
    sre = ShrakeRupley()
    sre.compute(empty, level="R")
    srg = ShrakeRupley()
    srg.compute(g12d, level="R")
    dsasa = []
    for res in chain_residues(g12d, "A"):
        n = res.id[1]
        e = next((r for r in chain_residues(empty, "A") if r.id[1] == n), None)
        if e is None:
            continue
        dsasa.append((n, float(e.sasa - res.sasa)))
    dsasa.sort(key=lambda x: -x[1])
    report["peptide_free_state"] = {
        "construction": ("organizer file = 7OW6 coordinates with the peptide deleted; "
                         f"heavy-chain CA RMSD vs the G12D file = {round(rms2, 2)} A"),
        "total_new_sasa_A2": round(sum(d for _, d in dsasa if d > 0), 0),
        "top_newly_exposed": [{"res": n, "d_sasa_A2": round(d, 1)} for n, d in dsasa[:15]],
    }

    # ---------- 7. electrostatics: the D6 carboxylate field above the groove ----------
    # direction "above the groove" = from the peptide CA centroid toward the TCR centroid
    pep_ca = np.array([r["CA"].get_coord() for r in chain_residues(tcr_complex, "C")])
    tcr_ca = np.array([r["CA"].get_coord() for ch in ("D", "E")
                       for r in chain_residues(tcr_complex, ch)])
    u = tcr_ca.mean(axis=0) - pep_ca.mean(axis=0)
    u = u / np.linalg.norm(u)
    d6_cg_rcsb = next(r for r in chain_residues(tcr_complex, "C") if r.id[1] == 6)["CG"].get_coord()
    # Debye-Huckel: phi[kT/e] = 332 * q * exp(-kappa*(r-1.4)) / (eps * r * 0.5932)
    kappa = 0.125  # 1/A, ~150 mM ionic strength
    charges = [(-0.5, "OD1"), (-0.5, "OD2")]
    oxy = {a.name: a.get_coord() for a in d6 if a.name in ("OD1", "OD2")}
    field = []
    for eps in (10, 20, 40, 80):
        for dist in (6, 7, 8):
            pt = d6_cg_rcsb + u * dist
            phi = 0.0
            for q, an in charges:
                r = float(np.linalg.norm(pt - oxy[an]))
                phi += 332.0 * q * math.exp(-kappa * (r - 1.4)) / (eps * r * 0.5932)
            field.append({"epsilon": eps, "distance_A": dist, "phi_kT_per_e": round(phi, 2)})
    # lateral sweep over the groove plane above P6-P7 at 7 A, eps 20
    p7 = next(r for r in chain_residues(tcr_complex, "C") if r.id[1] == 7)["CA"].get_coord()
    p1 = next(r for r in chain_residues(tcr_complex, "C") if r.id[1] == 1)["CA"].get_coord()
    p10 = next(r for r in chain_residues(tcr_complex, "C") if r.id[1] == 10)["CA"].get_coord()
    axis = p10 - p1
    axis = axis / np.linalg.norm(axis)
    v = np.cross(u, axis)
    v = v / np.linalg.norm(v)
    w = np.cross(u, v)
    mid = 0.5 * (d6_cg_rcsb + p7)

    def phi_at(pt, eps):
        phi = 0.0
        for q, an in charges:
            r = float(np.linalg.norm(pt - oxy[an]))
            phi += 332.0 * q * math.exp(-kappa * (r - 1.4)) / (eps * r * 0.5932)
        return phi

    patch_min, patch_at = 0.0, None
    for du in (-3.0, -1.5, 0.0, 1.5, 3.0):
        for dv in (-3.0, -1.5, 0.0, 1.5, 3.0):
            pt = mid + u * 7.0 + v * du + w * dv
            phi = phi_at(pt, 20.0)
            if phi < patch_min:
                patch_min, patch_at = phi, (du, dv)
    # closest TCR atom to the D6 carboxylate (the reported ~7.5 A)
    tcr_heavy = [a for ch in ("D", "E") for r in chain_residues(tcr_complex, ch)
                 for a in heavy_atoms(r)]
    dmin_tcr = min(float(np.linalg.norm(oxy[an] - a.get_coord()))
                   for an in oxy for a in tcr_heavy)
    report["electrostatics"] = {
        "note": ("Debye-Huckel point-charge estimate of the D6 carboxylate field; the WT state "
                 "carries no such charge, so this is the G12D-minus-WT difference field. "
                 "Uniform dielectric, no boundary - order-of-magnitude only."),
        "direction_above_groove": [round(float(x), 3) for x in u],
        "phi_table": field,
        "patch_sweep_eps20_7A": {"min_phi_kT_per_e": round(patch_min, 2),
                                 "lateral_offset_A": patch_at},
        "min_dist_D6_carboxylate_to_TCR_A": round(dmin_tcr, 2),
    }

    # ---------- write outputs ----------
    csv_path = C5 / "notes" / "target-physics.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pos", "aa", "sasa_complex_A2", "sasa_alone_A2", "relative_exposure",
                    "hla_contacts_4A", "bfactor_g12d", "bfactor_rcsb_7ow6"])
        g = burial["g12d"]
        for row in g:
            n = row["pos"]
            w.writerow([n, row["aa"], row["sasa_complex"], row["sasa_alone"],
                        row["relative_exposure"],
                        pep_contacts["g12d"]["per_residue"].get(str(n), 0),
                        bfac["g12d"]["peptide"].get(n, ""),
                        bfac["rcsb_7OW6"]["peptide"].get(n, "")])
    json_path = C5 / "notes" / "references" / "target-physics.json"
    json_path.write_text(json.dumps(report, indent=1))

    print("== peptide burial (G12D) ==")
    for row in burial["g12d"]:
        print(f"  P{row['pos']:<2} {row['aa']}  sasa {row['sasa_complex']:>6} A2 "
              f"({row['relative_exposure']:.2f} exposed)  hla contacts "
              f"{pep_contacts['g12d']['per_residue'].get(str(row['pos']), 0):>2}  "
              f"B={bfac['rcsb_7OW6']['peptide'].get(row['pos'])}")
    print("== D6 interactions ==", json.dumps(special, indent=1))
    print("== bfactors ==", json.dumps(bfac, indent=1))
    print("== TCR footprint ==", json.dumps(report["tcr_footprint"], indent=1))
    print("== unbound peptide (7OW4) ==", json.dumps(report["unbound_peptide"], indent=1))
    print("== peptide-free state ==", json.dumps(report["peptide_free_state"], indent=1))
    print("== electrostatics ==")
    for row in field:
        print(f"  eps={row['epsilon']:>2} d={row['distance_A']}A  phi={row['phi_kT_per_e']:>7} kT/e")
    print(f"  patch min (eps 20, 7 A, offsets {patch_at}): {patch_min:.2f} kT/e")
    print(f"  closest D6 carboxylate-to-TCR atom: {dmin_tcr:.2f} A")
    print("wrote", csv_path)
    print("wrote", json_path)


if __name__ == "__main__":
    main()
