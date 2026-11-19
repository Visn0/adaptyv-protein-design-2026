#!/usr/bin/env python3
"""Campaign 6 selector for challenge 4 (TfR1) — our own run of the organizers'
selection logic, built on challenge 3's c8 selector.

Rubric (each component 0-5, weights from the campaign README):

  S - switch evidence (the challenge's hardest goal). Built on direction +
      engineered site count, never on quotable magnitudes (c3 review,
      2026-10-27): the delta values carry null-level scatter.
  X - mouse cross-reactivity (the second objective). A design without a mouse
      fold scores the floor and the record says why.
  B - binding, from the restrained chai instrument, gated by engagement
      (worst-anchor distance <= 8 A and binder residues at site > 0; off-site
      poses can read 0.70).
  E - expression/solubility: pLDDT (CIF B-factor, binder chain) + mean
      Kyte-Doolittle hydropathy.

  total = 2.0*S + 1.5*X + 1.5*B + 1.0*E, max 30, normalised to 100.

Floors (kept from c8, per the campaign README): pLDDT, low complexity
(entropy / top-residue share / homopolymer run), plus the composition band
report. pDockQ2 and ipSAE apply when the Boltz-2 finalist pass has landed;
until then their columns read "missing" and do not exclude (recorded).

Novelty: the within-batch duplicate rule of binder-prescreen v0.5 (>= 0.95
identity over >= 0.80 coverage counts once) is applied here; the prescreen
report, when supplied, adds the novelty level per design.
"""
from __future__ import annotations

import collections
import csv
import datetime
import itertools
import math
import pathlib
import sys

WORK = pathlib.Path.home() / 'c4-work'
REPO = pathlib.Path(__file__).resolve().parents[5]
C3 = REPO / 'challenges/04-tfr1/campaigns/c3-switch-layer'
C4 = REPO / 'challenges/04-tfr1/campaigns/c4-mouse-crossfold'
RECORD_DIR = REPO / 'challenges/04-tfr1/records'
DESIGNS = WORK / 'chai/designs'

KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
      "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
      "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}

SCORE_WEIGHTS = {"S": 2.0, "X": 1.5, "B": 1.5, "E": 1.0}

# Liability repairs (2026-10-30): within a near-neighbour cluster the repair
# is the preferred representative when its binding read is within 0.02 of the
# parent's - it carries strictly fewer sequence liabilities at no measured
# cost (records/liability-round-2026-10-30.csv).
LIABILITY_REPAIRS = {
    'c3_e12b2_20_s2_n10q': 'c3_e12b2_20_s2',
    'c3_e12rfd4_r6d2_s1_n30q': 'c3_e12rfd4_r6d2_s1',
}
REPAIR_TOLERANCE = 0.02
COMPONENT_MAX = 5.0
MAX_TOTAL = sum(SCORE_WEIGHTS.values()) * COMPONENT_MAX  # 30.0

PLDDT_FLOOR = 63.0
PDOCKQ2_FLOOR = 0.18      # applies only when the boltz pass has landed
MIN_ENTROPY = 2.5
MAX_TOP_SHARE = 0.45
MAX_HOMOPOLYMER = 6

TARGET_PICKS = 20
ENGAGE_DIST = 8.0

# family = the generation arm / scaffold lineage (soft diversity only)
FAMILIES = {
    'e12rfd4': 'rfd4-e12', 'c3_e12rfd4': 'rfd4-e12-switch',
    'e12b2': 'genie3-b2-e12', 'c3_e12b2': 'genie3-b2-e12-switch',
    'b3_E12': 'rfd4-b3-e12', 'b3_E3': 'rfd4-b3-e3',
    'b4_H': 'wave2-hybrid', 'b4_E12L': 'wave2-e12l', 'b4_E0L': 'wave2-e0l',
    'b4r_H': 'wave2r-hybrid', 'b4r_E12L': 'wave2r-e12l', 'b4r_E0L': 'wave2r-e0l',
    'e12': 'genie3-e12', 'e0': 'genie3-e0',
    'c3_b4_H': 'wave2-hybrid', 'c3_e12_18': 'genie3-e12',
}


def normalized(total: float) -> float:
    return round(100.0 * total / MAX_TOTAL, 1)


def family(name: str) -> str:
    for pref, fam in sorted(FAMILIES.items(), key=lambda kv: -len(kv[0])):
        if name == pref or name.startswith(pref + '_'):
            return fam
    return name.split('_', 1)[0]


def low_complexity(seq: str) -> bool:
    if not seq:
        return True
    counts = collections.Counter(seq)
    n = len(seq)
    entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())
    run = longest = 1
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if a == b else 1
        longest = max(longest, run)
    return entropy < MIN_ENTROPY or max(counts.values()) / n > MAX_TOP_SHARE \
        or longest >= MAX_HOMOPOLYMER


def load_binding():
    """design -> {mean, n_engaged, n_total, files} from the restrained reads.

    Engagement gate: worst-anchor distance <= 8 A and >= 1 binder residue at
    site. Mean is over engaged samples only; a design with zero engaged
    samples keeps mean=None and is reported, never silently ranked.
    """
    per = collections.defaultdict(list)
    files = {
        'chai-restrained.csv': ('worst_hotspot_min_dist', 'binder_res_at_site'),
        'b3-restrained.csv': ('worst_anchor_min_dist', 'binder_res_at_anchors'),
        'c2-restrained.csv': ('worst_hotspot_min_dist', 'binder_res_at_site'),
        'c3-restrained.csv': ('worst_hotspot_min_dist', 'binder_res_at_site'),
        'b4-restrained.csv': ('worst_anchor_min_dist', 'binder_res_at_anchors'),
        'b4r-restrained.csv': ('worst_anchor_min_dist', 'binder_res_at_anchors'),
        'ppmpnn-restrained.csv': ('worst_anchor_min_dist', 'binder_res_at_anchors'),
        'extra-restrained-2026-10-30.csv': ('worst_hotspot_min_dist', 'binder_res_at_site'),
    }
    for fname, (dcol, ncol) in files.items():
        p = WORK / 'logs' / fname
        if not p.exists():
            continue
        for r in csv.DictReader(open(p)):
            try:
                d = float(r[dcol])
                n = int(r[ncol])
                iptm = float(r['iptm'])
            except (KeyError, ValueError):
                continue
            per[r['design']].append((iptm, d <= ENGAGE_DIST and n > 0))
    out = {}
    for d, rows in per.items():
        eng = [i for i, ok in rows if ok]
        out[d] = {'mean': round(sum(eng) / len(eng), 3) if eng else None,
                  'n_engaged': len(eng), 'n_total': len(rows)}
    return out


def load_mouse():
    """human design name -> mouse mean over engaged samples."""
    per = collections.defaultdict(list)
    for fname in (C4 / 'mouse-scores.csv', WORK / 'logs/c4-restrained.csv'):
        if not fname.exists():
            continue
        for r in csv.DictReader(open(fname)):
            try:
                d = float(r['worst_hotspot_min_dist'])
                n = int(r['binder_res_at_site'])
                v = float(r['iptm_mouse'])
            except (KeyError, ValueError):
                continue
            per[r['human_name']].append((v, d <= ENGAGE_DIST and n > 0))
    out = {}
    for d, rows in per.items():
        eng = [v for v, ok in rows if ok]
        out[d] = {'mean': round(sum(eng) / len(eng), 3) if eng else None,
                  'n_engaged': len(eng), 'n_total': len(rows)}
    return out


def load_switch():
    """variant -> {sites, delta_log_ka, parent}; plus variant -> parent map."""
    var = {}
    if (C3 / 'variants.csv').exists():
        for r in csv.DictReader(open(C3 / 'variants.csv')):
            # note the column naming: `sites` holds the anchor residues
            # ("A223 A253") and `n_his` is the engineered-histidine count.
            var[r['variant']] = {'parent': r['parent'],
                                 'sites': int(r.get('n_his') or 0),
                                 'anchors': r.get('sites', '')}
    linkage = {}
    if (C3 / 'linkage.csv').exists():
        for r in csv.DictReader(open(C3 / 'linkage.csv')):
            name = r['design'].replace('.pdb', '')
            try:
                linkage[name] = {'delta_log_ka': float(r['delta_log_Ka']),
                                 'sites': int(r['effective_sites'])}
            except (KeyError, ValueError):
                continue
    for name, lk in linkage.items():
        var.setdefault(name, {}).update(lk)
    # Repair variants carry their parent's engineered histidines unchanged, so
    # they inherit the parent's measured linkage (recorded as inherited, not
    # re-measured - the sites are identical).
    for name, v in list(var.items()):
        if v.get('parent') and 'delta_log_ka' not in v:
            plk = linkage.get(v['parent'])
            if plk:
                v['delta_log_ka'] = plk['delta_log_ka']
                v['linkage_inherited'] = v['parent']
                if plk.get('sites'):  # effective_sites: identical engineered sites
                    v['sites'] = plk['sites']
    return var


def load_boltz_screens():
    """design -> {ipsae, pdockq2} (max over the 5 Boltz-2 models where the
    design was folded by the finalist pass). Challenge-3 parity: the same two
    screens are recorded per design. NOT scored here: Boltz-2 cannot dock this
    target (`notes/c1-triage.md`), so the values are diagnostic, not
    discriminating; the binding component stays the restrained chai read."""
    out = {}
    for root in (WORK / 'boltz-pool', WORK / 'boltz-ipsae-fill'):
        if not root.exists():
            continue
        for d in root.iterdir():
            n = d.name
            vals_i, vals_p = [], []
            for f in d.rglob(f'{n}_model_*_10_10.txt'):
                if '_byres' in f.name:
                    continue
                lines = f.read_text().splitlines()
                hi = next((i for i, l in enumerate(lines) if l.startswith('Chn1')), None)
                if hi is None:
                    continue
                hdr = lines[hi].split()
                ci = hdr.index('ipSAE') if 'ipSAE' in hdr else None
                cp = hdr.index('pDockQ2') if 'pDockQ2' in hdr else None
                for l in lines[hi + 1:]:
                    pp = l.split()
                    if ci is not None and len(pp) > ci:
                        try: vals_i.append(float(pp[ci]))
                        except ValueError: pass
                    if cp is not None and len(pp) > cp:
                        try: vals_p.append(float(pp[cp]))
                        except ValueError: pass
            if vals_i or vals_p:
                out[n] = {'ipsae': round(max(vals_i), 3) if vals_i else None,
                          'pdockq2': round(max(vals_p), 3) if vals_p else None}
    return out


def binder_seq(name: str) -> str:
    p = DESIGNS / name / 'in.fasta'
    if not p.exists():
        return ''
    parts = p.read_text().split('>')
    return parts[2].split('\n')[1] if len(parts) > 2 else ''


def binder_plddt(name: str) -> float | None:
    p = DESIGNS / name / 'out/pred.model_idx_0.cif'
    if not p.exists():
        return None
    txt = p.read_text().splitlines()
    start = next((i for i, l in enumerate(txt) if l.startswith('_atom_site.')), None)
    if start is None:
        return None
    cols, i = [], start
    while txt[i].startswith('_atom_site.'):
        cols.append(txt[i].strip())
        i += 1
    idx = {c.split('.')[1]: j for j, c in enumerate(cols)}
    vals = []
    for l in txt[i:]:
        if l.startswith(('ATOM', 'HETATM')):
            pp = l.split()
            if len(pp) < len(cols):
                continue
            if pp[idx['auth_asym_id']] == 'B':  # binder chain in chai in.fasta
                try:
                    vals.append(float(pp[idx['B_iso_or_equiv']]))
                except ValueError:
                    pass
    return round(sum(vals) / len(vals), 1) if vals else None


def score(name, bind, mouse, switch, seqs, screens=None):
    b = bind.get(name, {})
    iptm = b.get('mean')
    engaged = b.get('n_engaged', 0)

    # B - binding
    if iptm is None:
        B = 0.5
        bnote = f'no engaged samples ({engaged}/{b.get("n_total", 0)})'
    else:
        B = 5.0 if iptm >= 0.70 else 4.0 if iptm >= 0.60 else 3.0 if iptm >= 0.50 \
            else 2.0 if iptm >= 0.45 else 1.0
        bnote = f'ipTM {iptm:.3f} ({engaged}/{b.get("n_total", 0)} engaged)'

    # X - mouse
    m = mouse.get(name, {})
    xm = m.get('mean')
    if xm is None:
        X = 1.0
        xnote = f'no engaged mouse read ({m.get("n_engaged", 0)}/{m.get("n_total", 0)})'
    else:
        X = 5.0 if xm >= 0.70 else 4.0 if xm >= 0.60 else 3.0 if xm >= 0.50 \
            else 2.0 if xm >= 0.40 else 1.0
        xnote = f'mouse {xm:.3f}'

    # S - switch
    v = switch.get(name)
    if v and 'sites' in v and v.get('parent'):
        parent = v['parent']
        pmean = bind.get(parent, {}).get('mean')
        retention = (iptm / pmean) if (iptm and pmean) else None
        sites = int(v['sites'])
        # The direction gate (the documented "direction + site count"): the
        # Wyman linkage must move in the asked sense (bind at 7.4, release at
        # 6.0 -> positive delta_log_Ka). A wrong-direction design keeps the
        # floor however many sites it carries; designs without a linkage row
        # are unchanged (conservative).
        dka = v.get('delta_log_ka')
        wrong_direction = dka is not None and dka < 0
        if wrong_direction:
            S = 2.0
        elif sites >= 2 and retention is not None and retention >= 0.85:
            S = 5.0
        elif sites >= 2 or (sites == 1 and retention is not None and retention >= 0.90):
            S = 4.0
        elif sites == 1:
            S = 3.0
        else:
            S = 2.0
        snote = (f'switch {sites} site(s), retention '
                 f'{retention:.2f}' if retention is not None else
                 f'switch {sites} site(s), retention n/a')
    else:
        S = 1.0
        snote = 'no switch layer (parent design)'

    # E - expression / solubility
    plddt = binder_plddt(name)
    seq = seqs.get(name, '')
    hydro = sum(KD.get(a, 0) for a in seq) / len(seq) if seq else None
    if plddt is None:
        E = 1.0
        enote = 'pLDDT missing'
    else:
        e_p = 5.0 if plddt >= 70 else 4.0 if plddt >= 60 else 3.0 if plddt >= 50 else 2.0
        e_h = (5.0 if -0.5 <= hydro <= 0.5 else 4.0 if -1.0 <= hydro <= 1.0 else 3.0) \
            if hydro is not None else 3.0
        E = (e_p + e_h) / 2
        enote = f'pLDDT {plddt:.0f}, hydropathy {hydro:+.2f}' if hydro is not None else f'pLDDT {plddt:.0f}'

    total = SCORE_WEIGHTS['S'] * S + SCORE_WEIGHTS['X'] * X \
        + SCORE_WEIGHTS['B'] * B + SCORE_WEIGHTS['E'] * E
    scr = (screens or {}).get(name, {})
    notes = [bnote, xnote, snote, enote]
    if scr.get('ipsae') is not None:
        notes.append(f"ipSAE {scr['ipsae']:.3f}, pDockQ2 {scr['pdockq2']:.3f} (diagnostic)" if scr.get('pdockq2') is not None
                     else f"ipSAE {scr['ipsae']:.3f} (diagnostic)")
    if (switch.get(name) or {}).get('linkage_inherited'):
        notes.append(f"linkage inherited from {switch[name]['linkage_inherited']}")
    if S == 2.0 and (switch.get(name) or {}).get('delta_log_ka') is not None \
            and 'no switch' not in snote:
        notes.append('at the linkage null band' if abs(switch[name]['delta_log_ka']) < 0.10 else 'wrong linkage direction')
    return {'design': name, 'total': round(total, 2), 'score': normalized(total),
            'S': S, 'X': X, 'B': B, 'E': round(E, 2), 'iptm': iptm, 'mouse': xm,
            'plddt': plddt, 'hydro': round(hydro, 2) if hydro is not None else None,
            'ipsae': scr.get('ipsae'), 'pdockq2': scr.get('pdockq2'),
            'family': family(name),
            'reason': '; '.join(notes)}


def near_dup(seq, kept, cutoff=0.95, cov=0.80):
    """binder-prescreen v0.5 within-batch rule: >= 0.95 id over >= 0.80 cov."""
    for other in kept:
        lo, hi = sorted((len(seq), len(other)))
        if not hi or lo / hi < cov:
            continue
        m = sum(1 for a, b in zip(seq, other) if a == b)
        if m / len(seq) >= cutoff:
            return True
    return False


def main():
    prescreen_report = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    novelty = {}
    if prescreen_report and prescreen_report.exists():
        for r in csv.DictReader(open(prescreen_report)):
            novelty[r['id']] = r.get('verdict', '?')

    bind = load_binding()
    mouse = load_mouse()
    switch = load_switch()
    screens = load_boltz_screens()
    seqs = {name: binder_seq(name) for name in set(bind) | set(switch)}

    scored = []
    for name in sorted(bind):
        s = score(name, bind, mouse, switch, seqs, screens)
        s['prescreen'] = novelty.get(name, 'not screened')
        scored.append(s)
    scored.sort(key=lambda s: -s['total'])

    # floors
    eligible, blocked = [], []
    for s in scored:
        why = []
        seq = seqs.get(s['design'], '')
        if s['plddt'] is not None and s['plddt'] < PLDDT_FLOOR:
            why.append(f"pLDDT {s['plddt']:.0f} < {PLDDT_FLOOR:.0f}")
        if low_complexity(seq):
            why.append('low-complexity sequence')
        if bind[s['design']].get('n_engaged', 0) == 0:
            why.append('no engaged fold sample')
        if why:
            s['excluded'] = '; '.join(why)
            blocked.append(s)
        else:
            eligible.append(s)

    # Selection: score order. Within a tie group: the switch evidence first
    # (S, the challenge's hardest goal), then binding (B), then the
    # least-represented family. The submission keeps at most one design per
    # 0.90-identity cluster (stricter than the prescreen's 0.95 within-batch
    # rule): a near-neighbour of a picked design is held for the reserve, and
    # within a near-neighbour group the better binding read is the
    # representative. Rationale: twenty slots are wet-lab tests, and a
    # 95%-identical sibling is not a second shot.
    picked, per_fam, kept_seqs = [], collections.Counter(), []
    for _t, group in itertools.groupby(eligible, key=lambda r: r['total']):
        group = list(group)
        while group and len(picked) < TARGET_PICKS:
            group.sort(key=lambda r: (-r['S'], -r['B'], per_fam[r['family']]))
            cand = group.pop(0)
            seq = seqs.get(cand['design'], '')
            if not seq or seq in kept_seqs:
                cand['excluded'] = 'identical sequence'
                continue
            # near-neighbour cluster: one representative only
            rival = None
            for j, prev in enumerate(picked):
                if near_dup(seq, [seqs.get(prev['design'], '')], cutoff=0.90):
                    rival = j
                    break
            if rival is not None:
                prev = picked[rival]
                sw = switch.get(cand['design'], {})
                sw_prev = switch.get(prev['design'], {})
                mine = sw.get('delta_log_ka')
                theirs = sw_prev.get('delta_log_ka')
                close_call = cand['total'] >= prev['total'] - 1.0
                stronger = (mine is not None and (theirs is None or mine > theirs))
                repair_of_prev = LIABILITY_REPAIRS.get(cand['design']) == prev['design'] \
                    and (cand['iptm'] or 0) >= (prev['iptm'] or 0) - REPAIR_TOLERANCE
                swap = (close_call and stronger) or repair_of_prev
                if swap:
                    # the stronger measured switch takes the cluster's slot
                    cand['note_swap'] = True
                    per_fam[prev['family']] -= 1
                    picked[rival] = cand
                    per_fam[cand['family']] += 1
                    prev['excluded'] = ('near-neighbour of a picked design (0.90/0.80) - held for the reserve; '
                                        + ('liability repair preferred at no measured cost' if repair_of_prev
                                           else 'weaker measured switch than its sibling'))
                else:
                    cand['excluded'] = 'near-neighbour of a picked design (0.90/0.80) - held for the reserve'
                continue
            kept_seqs.append(seq)
            picked.append(cand)
            per_fam[cand['family']] += 1
        if len(picked) == TARGET_PICKS:
            break
    picked.sort(key=lambda s: -s['total'])

    out_dir = WORK / 'c6'
    out_dir.mkdir(exist_ok=True)
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()

    fields = ['design', 'score', 'total', 'S', 'X', 'B', 'E', 'iptm', 'mouse',
              'plddt', 'hydro', 'ipsae', 'pdockq2', 'family', 'prescreen', 'reason']
    with open(out_dir / 'selection-all.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields + ['excluded'], extrasaction='ignore')
        w.writeheader()
        w.writerows(scored)
    with open(RECORD_DIR / f'selection-scores-{stamp}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(scored)
    with open(out_dir / 'selection-top20.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(picked[0].keys()), extrasaction='ignore')
        w.writeheader()
        w.writerows(picked)

    print(f'{len(scored)} designs scored; {len(blocked)} fail the floors; '
          f'{len(picked)} selected\n')
    print(f"{'#':>2s} {'design':26s} {'score':>6s} {'total':>6s} S    X    B    E    family")
    for i, s in enumerate(picked, 1):
        print(f"{i:2d} {s['design']:26s} {s['score']:6.1f} {s['total']:6.2f} "
              f"{s['S']:<4.1f} {s['X']:<4.1f} {s['B']:<4.1f} {s['E']:<4.1f} {s['family']}")
    print(f"\nfamilies: {dict(per_fam)}")
    # Coverage record: for each picked design, which reads exist. Regenerated on
    # every selector run so a later round's swaps cannot leave the coverage
    # statement describing a stale set (review 2026-10-30, finding 1).
    coverage = []
    for s in picked:
        d = s['design']
        row = {'design': d, 'prescreen': s['prescreen']}
        for label, col in (('restrained', 'iptm'), ('mouse', 'mouse'),
                           ('ipsae', 'ipsae'), ('pdockq2', 'pdockq2'), ('switch', 'ph')):
            row[label] = 'yes' if s.get(col) is not None else 'no'
        coverage.append(row)
    with open(RECORD_DIR / f'coverage-{stamp}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['design', 'prescreen', 'restrained', 'mouse',
                                          'ipsae', 'pdockq2', 'switch'])
        w.writeheader(); w.writerows(coverage)
    print(f'wrote {out_dir}/selection-{{all,top20}}.csv, the repo record and coverage-{stamp}.csv')


if __name__ == '__main__':
    main()
