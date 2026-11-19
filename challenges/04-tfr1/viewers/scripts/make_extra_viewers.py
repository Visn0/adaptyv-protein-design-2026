#!/usr/bin/env python3
"""Two extra explorers, both on the shared page renderer:

  c5-multi-chain.html  - the c5 block-target rescue: the 22 assembled
                         two-chain units folded against the 221-res apical
                         block (Boltz-2, best model each; chain A + B = the
                         designed unit, chain C = the block).
  c6-unrestrained.html - the unrestrained re-folds of the final twenty
                         (chai, out_unrestrained, best model each): does the
                         binder find its designed site without restraints?

Run with the repo venv python. The per-chain c5 page is preserved as
c5-per-chain.html.
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from tools.serve import molstar_viewer  # noqa: E402
from Bio.PDB import MMCIFParser, PDBIO, Select, Superimposer  # noqa: E402

WORK = pathlib.Path.home() / "c4-work"
OUT = REPO / "challenges" / "04-tfr1" / "viewers" / "multiview"
GLYCAN = {"NAG", "MAN", "BMA", "FUC", "GAL", "SIA"}


class _Chains(Select):
    def __init__(self, chains):
        self.chains = set(chains)

    def accept_chain(self, ch):
        return ch.id in self.chains

    def accept_residue(self, r):
        return r.resname not in GLYCAN


def load(cif: pathlib.Path):
    return MMCIFParser(QUIET=True).get_structure("x", str(cif))[0]


def chain_ca(structure, chain: str) -> dict:
    return {r.id[1]: r["CA"] for c in structure if c.id == chain for r in c if "CA" in r}


def superpose_on(structure, ref_ca: dict, chain: str):
    """Move the whole structure so its `chain` CAs land on ref_ca (shared
    residue numbers). Every fold has its own recentered frame; without this,
    toggling two units shows two offset copies of the target."""
    this = chain_ca(structure, chain)
    keys = [k for k in ref_ca if k in this]
    if not keys:
        return
    sup = Superimposer()
    sup.set_atoms([ref_ca[k] for k in keys], [this[k] for k in keys])
    sup.apply(list(structure.get_atoms()))


def pdb_text(structure, chains: list[str]) -> str:
    io_ = PDBIO()
    io_.set_structure(structure)
    h = io.StringIO()
    io_.save(h, _Chains(chains))
    return h.getvalue()


def focus_of(pdb_text, chains):
    """The binder atoms' bounding sphere, for the viewer's default camera.

    The generator precomputes it so the page can frame the interaction region
    (the visible designs) instead of the whole 639-residue ectodomain. Radius
    carries a margin so a couple of target residues stay in view."""
    pts = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            if chains and line[21] not in chains:
                continue
            try:
                pts.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    if not pts:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    r = max(((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2) ** 0.5 for p in pts)
    return {"center": [round(cx, 1), round(cy, 1), round(cz, 1)], "radius": round(r + 6.0, 1)}


def best_boltz_model(tag: str) -> int:
    d = WORK / "c5-rescue" / tag / f"boltz_results_{tag}" / "predictions" / tag
    best = (None, 0)
    for i in range(5):
        f = d / f"confidence_{tag}_model_{i}.json"
        if not f.exists():
            continue
        v = json.loads(f.read_text()).get("iptm")
        if v is not None and (best[0] is None or v > best[0]):
            best = (v, i)
    return best[1]


def build_rescue():
    rows = {}
    with open(WORK / "logs" / "c5-rescue.csv") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["design"], []).append(r)
    items, ranking = [], []
    for tag in sorted(rows):
        rs = rows[tag]
        eng = sum(1 for r in rs if r["engaged"] == "True")
        iptms = [float(r["iptm"]) for r in rs if r["iptm"]]
        mean = sum(iptms) / len(iptms) if iptms else 0.0
        ab = min((float(r["ab_min_dist"]) for r in rs if r["ab_min_dist"]), default=None)
        ranking.append((eng, mean, tag, ab))
    ranking.sort(reverse=True)
    top3 = {t for _e, _m, t, _a in ranking[:3]}
    ref_tag = ranking[0][2]
    ref_cif = (WORK / "c5-rescue" / ref_tag / f"boltz_results_{ref_tag}" / "predictions"
               / ref_tag / f"{ref_tag}_model_{best_boltz_model(ref_tag)}.cif")
    ref_structure = load(ref_cif)
    ref_block = chain_ca(ref_structure, "C")
    # Every other explorer shows the full 639-residue ectodomain. The assembled
    # fold exists only against the 221-res block, so the units are placed on
    # the same full-ectodomain frame by mapping the block onto it: block
    # residue b is auth b+179; the construct chain A is auth-120 in fold-local
    # numbering; so b maps to chain-A key b+59 (both verified off the files).
    full_structure = load(WORK / "chai" / "designs" / "c3_e12rfd4_r4d5_d2" / "out" / "pred.model_idx_0.cif")
    full_target_ca = chain_ca(full_structure, "A")
    block_to_target = {b: full_target_ca[b + 59] for b in ref_block if (b + 59) in full_target_ca}
    for eng, mean, tag, ab in ranking:
        m = best_boltz_model(tag)
        cif = WORK / "c5-rescue" / tag / f"boltz_results_{tag}" / "predictions" / tag / f"{tag}_model_{m}.cif"
        structure = load(cif)
        superpose_on(structure, block_to_target, "C")
        label = f"{tag} · {eng}/5 engaged · ipTM {mean:.3f}"
        if ab is not None:
            label += f" · B-C brace {ab:.1f} A"
        items.append({
            "id": tag, "label": label, "design": tag, "species": "human",
            "pdb": pdb_text(structure, ["A", "B"]),
            "chains": ["A", "B"],
            "focus": focus_of(pdb_text(structure, ["A", "B"]), ["A", "B"]),
            "chainColors": {"A": 0x7c5cff, "B": 0x22b8a6, "C": 0x8b93a7}, "color": 0x7c5cff,
            "interface": [], "on": tag in top3,
            "scores": {"iptm": round(mean, 3)},
        })
    # the full ectodomain as the target item - the same frame as every other
    # challenge-4 explorer (the units are placed on it via the block mapping)
    items.insert(0, {
        "id": "target", "label": "TfR1 ectodomain (639 aa, binder target)",
        "design": "target", "species": "human",
        "pdb": pdb_text(full_structure, ["A"]), "chains": ["A"],
        "chainColors": {"A": 0x0099ff}, "color": 0x0099ff, "interface": [], "on": True, "scores": {},
    })
    html = molstar_viewer.render_viewer_page(
        items, "c5 assembled units vs the apical block",
        "04-TFR1 · C5 · BLOCK RESCUE", "c5-multi-chain",
        binder_chain="A",
        caption="The 22 assembled two-chain units, Boltz-2 against the 221-res apical block "
                "(pocket restraints on both binders at the E12 anchors, 5 samples each; best "
                "model shown). Violet + teal = the two designed chains; the target shown is the "
                "same full ectodomain as every other explorer - the units are placed on it by "
                "superposing the block they were folded against (the assembled fold against the "
                "full ectodomain is unrunnable on this host). Best three units visible by default.")
    (OUT / "c5-multi-chain.html").write_text(html)
    print(f"c5-multi-chain.html: {len(items)} items ({len(top3)} on)")


def build_unrestrained():
    eng = {}
    with open(REPO / "challenges/04-tfr1/records/unrestrained-engagement-2026-10-29.csv") as fh:
        for r in csv.DictReader(fh):
            eng[r["design"]] = r
    names = sorted(eng)
    ranking = sorted(names, key=lambda n: (-float(eng[n]["mean_iptm"])))
    top3 = set(ranking[:3])
    palette = [0xe879f9, 0x34d399, 0xfbbf24, 0x60a5fa, 0xf472b6, 0x22d3ee,
               0xa78bfa, 0xfb7185, 0x4ade80, 0xfacc15]
    items = []
    # the target: chain A of the best unrestrained fold, everything fits onto it
    ref_structure = load(WORK / "chai" / "designs" / ranking[0] / "out_unrestrained" / "pred.model_idx_0.cif")
    ref_target = chain_ca(ref_structure, "A")
    items.append({
        "id": "target", "label": "TfR1 ectodomain (639 aa, target chain)",
        "design": "target", "species": "human",
        "pdb": pdb_text(ref_structure, ["A"]), "chains": ["A"],
        "chainColors": {"A": 0x0099ff}, "color": 0x0099ff, "interface": [], "on": True, "scores": {},
    })
    for i, n in enumerate(ranking):
        e = eng[n]
        structure = load(WORK / "chai" / "designs" / n / "out_unrestrained" / "pred.model_idx_0.cif")
        superpose_on(structure, ref_target, "A")
        label = (f"{n} · unrestrained {float(e['mean_iptm']):.3f} · "
                 f"{e['n_engaged']}/{e['n_samples']} engaged")
        items.append({
            "id": n, "label": label, "design": n, "species": "human",
            "pdb": pdb_text(structure, ["B"]), "chains": ["B"],
            "focus": focus_of(pdb_text(structure, ["B"]), ["B"]),
            "chainColors": {"B": palette[i % len(palette)]}, "color": palette[i % len(palette)],
            "interface": [], "on": n in top3,
            "scores": {"iptm": float(e["mean_iptm"])},
        })
    html = molstar_viewer.render_viewer_page(
        items, "the unrestrained re-folds of the final twenty",
        "04-TFR1 · C6 · UNRESTRAINED", "c6-unrestrained",
        binder_chain="B",
        caption="Each binder re-folded with no pocket restraints (5 samples; best model shown): "
                "11 of 20 find the designed site on their own, 5 of them in every sample. "
                "The best three by this read are visible by default.")
    (OUT / "c6-unrestrained.html").write_text(html)
    print(f"c6-unrestrained.html: {len(items)} items ({len(top3)} on)")


def main():
    old = OUT / "c5-multi-chain.html"
    if old.exists() and not (OUT / "c5-per-chain.html").exists():
        shutil.copy(old, OUT / "c5-per-chain.html")
        print("kept the per-chain c5 page as c5-per-chain.html")
    build_rescue()
    build_unrestrained()


if __name__ == "__main__":
    main()
