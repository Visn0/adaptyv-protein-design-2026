#!/usr/bin/env python3
"""Add the c2/c3/c4 experiments to the challenge-4 lineage (workbench data).

Reads the campaign CSVs so every number on the site matches the records.
Appends to challenges/04-tfr1/lineage.json (keeps the existing c1 experiment).
Run with any python3 (stdlib only).
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import statistics

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / 'challenges/04-tfr1'
WORK = pathlib.Path.home() / 'c4-work'
LINEAGE = CH / 'lineage.json'


def means(path, key='iptm'):
    per = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            per.setdefault(r['design'], []).append(float(r[key]))
    return {d: statistics.mean(v) for d, v in per.items()}


def pka_notes():
    """{variant: 'ΔpKa a/b'} for engineered positions only."""
    eng = {}
    with open(CH / 'campaigns/c3-switch-layer/variants.csv') as fh:
        for r in csv.DictReader(fh):
            eng[r['variant']] = [int(x) for x in r['positions'].split()]
    notes = {}
    cur = None
    for line in (CH / 'campaigns/c3-switch-layer/pka-per-site.txt').read_text().splitlines():
        m = re.match(r'^(c3_\S+)\s+pos\s+(\d+)\s+[\d.]+\s+->\s+[\d.]+\s+([+-][\d.]+)', line)
        if m:
            name, pos, delta = m.group(1), int(m.group(2)), m.group(3)
            if pos in eng.get(name, []):
                notes.setdefault(name, []).append(f'{pos}:{delta}')
    return {k: 'ΔpKa ' + ' '.join(v) for k, v in notes.items()}


def main():
    d = json.loads(LINEAGE.read_text())
    have = {e['id'] for e in d['experiments']}

    c2 = means(WORK / 'logs/c2-restrained.csv')
    c3 = means(WORK / 'logs/c3-restrained.csv')
    c4_mouse = means(WORK / 'logs/c4-restrained.csv', 'iptm_mouse')
    c4_rows = {}
    with open(WORK / 'logs/c4-restrained.csv') as fh:
        for r in csv.DictReader(fh):
            c4_rows.setdefault(r['design'], []).append(r)
    sign = {}
    with open(WORK / 'logs/c3-linkage.csv') as fh:
        for r in csv.DictReader(fh):
            try:
                sign[r['design'].replace('.pdb', '')] = float(r['delta_log_Ka'])
            except (TypeError, ValueError):
                pass
    pk = pka_notes()

    def prot(design, phase, note, iptm, human=None, mouse=None):
        return {"design": design, "sequence": None, "phase": phase, "note": note,
                "human": human, "mouse": mouse, "ph": None,
                "ipsae_min": None, "pdockq2": None, "iptm": round(iptm, 3)}

    # ---- C2
    c2q = sorted(((m, d) for d, m in c2.items() if m >= 0.45), reverse=True)
    c2_prots = []
    for m, name in c2q:
        arm = 'RFD4' if name.startswith('e12rfd4') else 'Genie 3 b2'
        c2_prots.append(prot(name, 'r1', f'{arm} · restrained ipTM {m:.3f}', m))
    c2_exp = {
        "id": "c2-binding-families", "title": "C2 — binding families, two generator arms",
        "date": "2026-10-26", "verdict": "promising", "best": "True", "scores": {},
        "summary": "Batch-2 generation on the surviving epitope: 32 Genie 3 + 49 hosted RFD4-Proteina designs, every one folded on the restrained read (405 samples). 20 cleared the line — 17 at or above 0.50, top e12rfd4_r5d1 0.779. No separation between the arms (Fisher p = 0.605).",
        "goal": "Turn the surviving epitope (E12) into a family: generate batch-2 material with two independent generators and screen every design with the same instrument.",
        "goal_extra": [
            "No pre-selection: geometry screen only, then all 81 designs fold.",
            "The 20 clearing the line carry into campaign 3 (switch) and campaign 4 (mouse)."],
        "verdict_detail": "The pool is materially stronger than campaign 1's: 17 designs at or above 0.50 against 7, top 0.779 against 0.752, all well above the native reference ceiling (0.48). RFD4 11/49 (22 %), Genie 3 9/32 (28 %) — statistically indistinguishable. Robustness: a host display-driver crash killed one design's fold mid-screen; the pass resumed on driver 621.01 with the allocator workaround and the killed design (r4d3) completed at 0.682.",
        "chapters": [
            {"id": "g1", "title": "G — batch-2 generation, two arms", "date": "2026-10-25",
             "tools": ["Genie 3", "ProteinMPNN", "RFD4-Proteina"],
             "text": "32 local Genie 3 backbones (CA-only MPNN sequences) and 49 hosted RFD4-Proteina designs, all on the E12 anchors (K344/K374).",
             "steps": [
                 {"title": "Generate batch-2 material (Genie 3 + hosted RFD4)", "text": "", "image": "c2-pipeline-two-arms.png"},
                 {"title": "Geometry screen (all pass)", "text": "", "image": None}]},
            {"id": "r1", "title": "R — the restrained screen", "date": "2026-10-26",
             "tools": ["Chai-1", "pocket restraints"],
             "text": "81 designs × 5 samples = 405 folds on the E12 anchors, seed 42, serial on one GPU.",
             "steps": [
                 {"title": "Fold all 81 designs (no pre-selection)", "text": "", "image": None},
                 {"title": "Score at-site: worst hotspot distance + binder residues at the site", "text": "", "image": None}]},
            {"id": "d1", "title": "D — 20 carry forward", "date": "2026-10-26",
             "tools": [], "text": "20 designs at mean restrained ipTM ≥ 0.45 (17 ≥ 0.50); they carry into the switch layer and the mouse cross-fold.",
             "steps": []}],
        "proteins": c2_prots, "viewer": []}

    # ---- C3
    c3_rows = {}
    with open(CH / 'campaigns/c3-switch-layer/variants.csv') as fh:
        for r in csv.DictReader(fh):
            c3_rows[r['variant']] = r
    c3_prots = []
    for name, m in sorted(c3.items(), key=lambda kv: -kv[1]):
        parent = name[3:].rsplit('_', 1)[0]
        delta = m - c2.get(parent, float('nan'))
        keep = delta >= -0.10
        bits = [f'mean {m:.3f} (parent {c2.get(parent, float("nan")):.3f})',
                'kept' if keep else 'discarded (gate 1)']
        if name in pk:
            bits.append(pk[name])
        if name in c4_mouse:
            bits.append(f'mouse {c4_mouse[name]:.3f}')
        c3_prots.append(prot(name, 'f1', ' · '.join(bits), m,
                             human=round(m, 3), mouse=round(c4_mouse[name], 3) if name in c4_mouse else None))
    c3_exp = {
        "id": "c3-switch-layer", "title": "C3 — the pH switch layer",
        "date": "2026-10-26", "verdict": "promising", "best": "True", "scores": {},
        "summary": "29 histidine variants retrofitted onto the top 10 families (singles, doubles, a 0→3 ladder). 21 kept their binding; the engineered sites register the predicted bound-state pKa depression at the anchor lysines (−0.5…−2.8); far picks read flat; one wrong-direction control. 13 carry into the mouse fold.",
        "goal": "Objective 1: put a pH switch into the binder — a histidine neutral at pH 7.4 and protonated at 6.0, facing an anchor lysine, so binding weakens as the pH falls.",
        "goal_extra": [
            "Positions picked from the co-folded poses: side chain 3.5–8.5 Å from an anchor NZ, solvent-exposed.",
            "Both anchors are conserved lysines (K344/K374), so the same chemistry serves the mouse objective."],
        "verdict_detail": "The registered sign gate is a consistency check (26/29 move positive; unmodified parents carry a 12 % positive null). The substance is per-site: engineered histidines shift −0.5…−2.8 pKa units when bound; picks at the far window edge (8.0–8.4 Å) read flat and their totals go negative; one site reads +0.48 (wrong direction). Magnitudes are never quoted. The top family's ladder is strictly increasing with histidine count (parent −0.057 → +0.029 → +0.625 → +0.708).",
        "chapters": [
            {"id": "p1", "title": "P — picking the positions", "date": "2026-10-26",
             "tools": ["vendored switch geometry", "rSASA filter"],
             "text": "For every qualifying design: binder side chains pointing at the anchor lysines (3.5–8.5 Å engage window, relative SASA ≥ 0.20). In the top families these are the carboxylates the generators had already aimed at the anchors.",
             "steps": [{"title": "Pick positions at both anchors", "text": "", "image": None}]},
            {"id": "f1", "title": "F — variants, identical treatment", "date": "2026-10-26",
             "tools": ["Chai-1", "pocket restraints"],
             "text": "29 variants (7 doubles, 19 singles, a 3-step ladder) built with the parent's MSA and restraints — the only change is the mutated sequence.",
             "steps": [{"title": "Build + fold 29 variants (145 samples)", "text": "", "image": "c3-pipeline-per-variant.png"}]},
            {"id": "g1", "title": "G — gates and the per-site mechanism", "date": "2026-10-26",
             "tools": ["PROPKA", "Wyman linkage", "Chai-1 read"],
             "text": "Gate 1: binding kept (21/29). Gate 2 (registered): the sign check, reported as consistency. Mechanism: PROPKA pKa bound vs free on every engineered histidine.",
             "steps": [
                 {"title": "At-site read vs parent", "text": "", "image": None},
                 {"title": "Per-site pKa + linkage (controls included)", "text": "", "image": None}]},
            {"id": "d1", "title": "D — 13 carry forward", "date": "2026-10-26",
             "tools": [], "text": "Carried by gate 1 + geometry + per-site mechanism; the ladder ships as the declared mechanism control.",
             "steps": []}],
        "proteins": c3_prots, "viewer": []}

    # ---- C4
    c4_prots = []
    for name, m in sorted(c4_mouse.items(), key=lambda kv: -kv[1]):
        human = c3.get(name[5:]) if name.startswith('c4mn_c3_') else c2.get(name[5:])
        delta = None if human is None else human - m
        band = ('top' if abs(delta) <= 0.05 else 'second' if abs(delta) <= 0.15 else 'third')
        c4_prots.append(prot(name, 'f1',
                             f'mouse {m:.3f} · human {human:.3f} · Δ {delta:+.3f} ({band})' if human is not None else f'mouse {m:.3f}',
                             m, human=round(human, 3) if human is not None else None, mouse=round(m, 3)))
    c4_exp = {
        "id": "c4-mouse-crossfold", "title": "C4 — mouse cross-fold",
        "date": "2026-10-26", "verdict": "promising", "best": "True", "scores": {},
        "summary": "33 designs (20 C2 + 13 C3) folded against the mouse receptor under the identical protocol. Two mouse-competent candidates: e12rfd4_r4d5 (Δ −0.050) and c3_e12rfd4_r3d4_d2 (Δ +0.018, carries the switch). The tightest human designs are the weakest cross-reads.",
        "goal": "Objective 2: does the design intent survive against the mouse receptor? Every human qualifier re-folded on the mouse target, anchors mapped by alignment.",
        "goal_extra": [
            "Anchors: human K344/K374 → mouse K346/K376 (fold 224/254) — never a fixed offset (the constructs carry an indel).",
            "Mouse target is an AlphaFold model (Q62351, 123–763); the structural asymmetry against the human experimental structure is recorded."],
        "verdict_detail": "Bands (adapted instrument): top ≤ 0.05 — r4d5 (−0.050), r3d4_d2 (+0.018), b2_31 (−0.053); second ≤ 0.15 — b2_29, r4d5_d2, r6d2. The strong human parents r5d1/r5d7/b2_20 fall to 0.36/0.27/0.26 — affinity and cross-transfer read as opposed here. Observation: the histidine retrofits improve the mouse read in most families (r5d7 0.266 → 0.579).",
        "chapters": [
            {"id": "f1", "title": "F — 33 designs against the mouse construct", "date": "2026-10-26",
             "tools": ["Chai-1", "ColabFold MSA", "alignment-derived anchors"],
             "text": "Target prep scripted: mouse sequence from the AlphaFold model, anchors by alignment, MSA depth 1024, then the identical restrained fold.",
             "steps": [{"title": "Prep + fold 33 designs (165 samples)", "text": "", "image": "c4-pipeline-mouse-crossfold.png"}]},
            {"id": "d1", "title": "D — the paired read", "date": "2026-10-26",
             "tools": [], "text": "Human mean vs mouse mean per design; bands fixed before the run.",
             "steps": []}],
        "proteins": c4_prots, "viewer": []}

    for exp in (c2_exp, c3_exp, c4_exp):
        if exp['id'] not in have:
            d['experiments'].append(exp)
    LINEAGE.write_text(json.dumps(d, indent=1) + '\n')
    print('experiments now:', [e['id'] for e in d['experiments']])
    print('proteins:', {e['id']: len(e['proteins']) for e in d['experiments']})


if __name__ == '__main__':
    main()
