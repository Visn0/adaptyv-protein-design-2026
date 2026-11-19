#!/usr/bin/env python3
"""Campaign 3, step 1: pick histidine-engaging positions on campaign-2 designs.

Reads the C2 restrained scores (c2-restrained.csv), keeps designs clearing the
at-site line (mean restrained ipTM >= 0.45 with at least one at-site sample),
takes each design's best at-site model, and for the two switch anchors
(fold K223 / K253 = auth K344 / K374) finds binder positions whose side chain
points at the anchor lysine NZ inside the vendored engage window (3.5-8.5 A),
then annotates each candidate with its relative solvent exposure.

Run with the repo venv python (Bio 1.88 + numpy + pandas):
    .venv/bin/python ~/c4-work/bin/c3-pick-positions.py [--threshold 0.45]
Writes ~/c4-work/chai/c3/positions.jsonl plus a report on stdout.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import pathlib
import statistics
import sys

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
SCORES = WORK / 'logs/c2-restrained.csv'
OUTDIR = WORK / 'chai/c3'
ANCHORS = (223, 253)          # fold numbering = auth 344 / 374
MIN_EXPOSURE = 0.20           # relative SASA floor for a picked position

# from the vendored tool (target_switch_anchors.py)
MAX_ASA = {
    "ALA": 129.0, "ARG": 274.0, "ASN": 195.0, "ASP": 193.0, "CYS": 167.0,
    "GLN": 225.0, "GLU": 223.0, "GLY": 104.0, "HIS": 224.0, "ILE": 197.0,
    "LEU": 201.0, "LYS": 236.0, "MET": 224.0, "PHE": 240.0, "PRO": 159.0,
    "SER": 155.0, "THR": 172.0, "TRP": 285.0, "TYR": 263.0, "VAL": 174.0,
}


def load_switch_positions():
    p = REPO / 'tools/switch/switch_positions.py'
    spec = importlib.util.spec_from_file_location('switch_positions', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_h(structure):
    import copy
    st = copy.deepcopy(structure)
    for chain in st[0]:
        for res in chain:
            for atom in [a for a in res if a.element == 'H']:
                res.detach(atom)
    return st


def rel_sasa(model):
    from Bio.PDB.SASA import ShrakeRupley
    sr = ShrakeRupley()
    sr.compute(model, level='R')
    out = {}
    for chain in model:
        for res in chain:
            if res.id[0] != ' ':
                continue
            maxa = MAX_ASA.get(res.get_resname())
            if maxa:
                out[(chain.id, res.id[1])] = res.sasa / maxa
    return out


def design_rows(scores_path, threshold):
    rows = {}
    with open(scores_path) as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r['design'], []).append(r)
    picks = {}
    for design, rs in rows.items():
        iptms = [float(r['iptm']) for r in rs]
        mean = statistics.mean(iptms)
        at_site = [r for r in rs if int(r['binder_res_at_site'] or 0) > 0]
        if mean < threshold or not at_site:
            continue
        best = max(at_site, key=lambda r: float(r['iptm']))
        arm = next(iter(rs))['arm']
        picks[design] = {'design': design, 'arm': arm, 'mean_iptm': round(mean, 3),
                         'model': int(best['model']), 'model_iptm': float(best['iptm']),
                         'binder_res_at_site': int(best['binder_res_at_site'])}
    return picks


def analyse(sw, design):
    d = DESIGNS / design
    rows = [r for r in d.joinpath('out').glob('pred.model_idx_*.cif')]
    return d, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--threshold', type=float, default=0.45)
    ap.add_argument('--min-exposure', type=float, default=MIN_EXPOSURE)
    args = ap.parse_args()

    sw = load_switch_positions()
    picks = design_rows(SCORES, args.threshold)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f'designs clearing the line (mean >= {args.threshold}, at-site): {len(picks)}')

    out_path = OUTDIR / 'positions.jsonl'
    with open(out_path, 'w') as out:
        for design, info in sorted(picks.items(),
                                   key=lambda kv: -kv[1]['mean_iptm']):
            d = DESIGNS / design
            cif = d / 'out' / f'pred.model_idx_{info["model"]}.cif'
            if not cif.exists():
                print(f'  {design}: MISSING {cif.name}, skipped')
                continue
            structure = sw.load_structure(str(cif))
            model = structure[0]
            chains = sorted((c for c in model if any(r.id[0] == ' ' for r in c)),
                            key=lambda c: -len([r for r in c if r.id[0] == ' ']))
            if len(chains) != 2:
                print(f'  {design}: {len(chains)} chains, skipped')
                continue
            target, binder = chains[0].id, chains[1].id
            sites, missing = [], []
            for num in ANCHORS:
                try:
                    res = model[target][num]
                except KeyError:
                    missing.append(num)
                    continue
                if res.get_resname() != 'LYS':
                    print(f'  {design}: anchor {target}{num} is {res.get_resname()} not LYS — skipped design')
                    sites = []
                    break
                sites.append({'target_chain': target, 'target_resnum': num,
                              'target_resname': 'LYS',
                              'target_tip': [float(v) for v in res['NZ'].coord]})
            if missing:
                print(f'  {design}: anchors missing {missing}, skipped')
                continue
            if not sites:
                continue
            _, best, all_assign, rmsd = sw.analyse(
                str(cif), sites, binder, reference=None, target_chains=(target,))

            # fasta indexing of the binder chain
            reslist = [r for r in model[binder] if r.id[0] == ' ']
            offset = reslist[0].id[1] - 1
            fasta = [l.strip() for l in (d / 'in.fasta').read_text().splitlines()
                     if not l.startswith('>')][1]

            rel = rel_sasa(strip_h(structure)[0])
            cands, seen = [], set()
            for a in sorted(all_assign, key=lambda x: x['distance']):
                key = (a['site_index'], a['binder_resnum'])
                if key in seen:
                    continue
                seen.add(key)
                from Bio.PDB.Polypeptide import protein_letters_3to1
                fpos = a['binder_resnum'] - offset
                if not (1 <= fpos <= len(fasta)):
                    continue
                one = protein_letters_3to1.get(a['binder_resname'].upper(), 'X')
                if fasta[fpos - 1].upper() != one:
                    # numbering mismatch safety: skip rather than mutate the wrong residue
                    print(f'  {design}: number mismatch at {a["binder_resnum"]} '
                          f'({a["binder_resname"]} vs {fasta[fpos - 1]}), dropped')
                    continue
                r = rel.get((binder, a['binder_resnum']))
                cands.append({'site': f'{target}{ANCHORS[a["site_index"]]}',
                              'resnum': a['binder_resnum'], 'fasta_pos': fpos,
                              'resname': a['binder_resname'],
                              'dist': a['distance'],
                              'rel_sasa': round(r, 3) if r is not None else None,
                              'exposed': bool(r is not None and r >= args.min_exposure)})
            rec = {**info, 'target_chain': target, 'binder_chain': binder,
                   'binder_len': len(fasta), 'align_rmsd': rmsd,
                   'candidates': cands}
            out.write(json.dumps(rec) + '\n')
            ex = [c for c in cands if c['exposed']]
            print(f'  {design}  mean {info["mean_iptm"]:.3f} model {info["model"]} '
                  f'| candidates {len(cands)} exposed {len(ex)} '
                  f'| ' + ', '.join(f'{c["site"]}->{c["fasta_pos"]}({c["resname"]} '
                                    f'{c["dist"]}A sasa {c["rel_sasa"]})' for c in ex))
    print(f'\nwrote {out_path}')


if __name__ == '__main__':
    main()
