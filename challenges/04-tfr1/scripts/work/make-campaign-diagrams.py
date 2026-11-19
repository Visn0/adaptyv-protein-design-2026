#!/usr/bin/env python3
"""Emit per-campaign Gantt SVGs (same visual language as the campaign-1
figures) for campaigns 2, 3 and 4, using measured numbers from the logs.

Rows = strategies/arms; bars = pipeline steps in minutes; one GPU, serial.
Writes challenges/04-tfr1/campaigns/<c>/diagram/<name>.svg.
"""
from __future__ import annotations

import pathlib

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / 'challenges/04-tfr1'

# palette
BG = '#0f172a'
GRID = '#1e293b'
WHITE = '#f8fafc'
DIM = '#94a3b8'
FAINT = '#64748b'
C = {'gen': '#22d3ee', 'seq': '#a78bfa', 'prep': '#94a3b8',
     'fold': '#f472b6', 'gate': '#4ade80', 'score': '#fbbf24'}


def svg(title, subtitle, rows, tmax, footer, width=1200):
    x0, y0 = 320, 118
    scale = (width - 40 - x0 - 60) / tmax
    rowh = 64
    height = y0 + rowh * len(rows) + 74
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'font-family="\'JetBrains Mono\',\'SF Mono\',\'Cascadia Code\',monospace">',
        '<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M 40 0 L 0 0 0 40" fill="none" stroke="{GRID}" stroke-width="0.5"/></pattern></defs>',
        f'<rect width="100%" height="100%" fill="{BG}"/>',
        '<rect width="100%" height="100%" fill="url(#grid)"/>',
        f'<text x="40" y="44" fill="{WHITE}" font-size="16" font-weight="700">{title}</text>',
        f'<text x="40" y="64" fill="{DIM}" font-size="9">{subtitle}</text>',
    ]
    # time axis
    step = 2 if tmax <= 16 else 4
    parts.append('<g font-size="8" fill="' + FAINT + '">')
    for t in range(0, int(tmax) + 1, step):
        x = x0 + t * scale
        label = str(t) if t < tmax else 'min'
        parts.append(f'<text x="{x:.0f}" y="94" text-anchor="middle">{label}</text>')
    parts.append('</g>')
    parts.append(f'<g stroke="{GRID}" stroke-width="0.7" stroke-dasharray="3,5">')
    for t in range(0, int(tmax) + 1, step):
        x = x0 + t * scale
        parts.append(f'<line x1="{x:.0f}" y1="100" x2="{x:.0f}" y2="{y0 + rowh*len(rows) - 10}"/>')
    parts.append('</g>')
    y = y0
    for label, sub, bars in rows:
        parts.append(f'<text x="40" y="{y+18}" fill="{WHITE}" font-size="10.5" font-weight="600">{label}</text>')
        parts.append(f'<text x="40" y="{y+33}" fill="{FAINT}" font-size="8">{sub}</text>')
        small = []
        for name, start, dur, color in bars:
            bx = x0 + start * scale
            bw = max(dur * scale, 2)
            parts.append(f'<rect x="{bx:.1f}" y="{y+2}" width="{bw:.1f}" height="22" rx="3" fill="{color}" opacity="0.92"/>')
            if bw > 46:
                parts.append(f'<text x="{bx + bw/2:.1f}" y="{y+16.5}" fill="#0b1220" font-size="8" font-weight="600" text-anchor="middle">{name}</text>')
            else:
                small.append(f'<text x="{bx + bw + 4:.1f}" y="{y-3}" fill="#e2e8f0" font-size="8">{name}</text>')
        parts.extend(small)
        y += rowh
    fy = y + 8
    for i, line in enumerate(footer):
        parts.append(f'<text x="40" y="{fy + i*13}" fill="{FAINT}" font-size="8.5">{line}</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def write(name, campaign, content):
    d = CH / 'campaigns' / campaign / 'diagram'
    d.mkdir(parents=True, exist_ok=True)
    p = d / f'{name}.svg'
    p.write_text(content)
    print('wrote', p)


write('pipeline-two-arms', 'c2-binding-families', svg(
    'Campaign 2 — per-design wall time by arm (Gantt)',
    'measured campaign-2 numbers · RTX 5070 (12 GB) · one GPU, serial folds · 81 designs',
    [('RFD4 arm (49)', 'hosted NIM · own sequences · ~20 s per design generation',
      [('hosted gen', 0.0, 0.33, C['gen']), ('fold', 0.4, 8.5, C['fold']),
       ('screen + score', 8.95, 0.25, C['score'])]),
     ('genie3 arm (32)', 'local GPU · CA-only MPNN sequences (2 min)',
      [('generate', 0.0, 0.8, C['gen']), ('MPNN', 0.85, 2.0, C['seq']),
       ('fold', 2.9, 8.5, C['fold']), ('screen + score', 11.45, 0.25, C['score'])])],
    tmax=14,
    footer=['81 designs, 405 samples · ~11.5 h GPU in 16 h wall (the host crash cost 4.5 h; the pass resumed mid-design)',
            '20 designs cleared the line · top e12rfd4_r5d1 0.779 · arm rates 22 % (RFD4) vs 28 % (genie3), Fisher p = 0.605']))

write('pipeline-per-variant', 'c3-switch-layer', svg(
    'Campaign 3 — per-variant wall time (Gantt)',
    'measured campaign-3 numbers · 29 histidine variants on the top 10 families · one GPU, serial',
    [('variant pipeline', 'pick (CPU) → build → restrained fold → gates → per-site pKa (CPU)',
      [('pick', 0.0, 0.03, C['prep']), ('build', 0.05, 0.02, C['prep']),
       ('restrained fold', 0.1, 7.6, C['fold']), ('linkage + pKa', 7.75, 0.15, C['gate'])])],
    tmax=10,
    footer=['29 variants, 145 samples · 3.7 h GPU · pick + build < 2 s each (CPU)',
            '13 carry: binding kept + engineered-site pKa depression (−0.5..−2.8); far picks flat; one wrong-direction control']))

write('pipeline-mouse-crossfold', 'c4-mouse-crossfold', svg(
    'Campaign 4 — per-design wall time against the mouse target (Gantt)',
    'measured campaign-4 numbers · 33 designs · mouse target prep once (alignment + MSA), then identical folds',
    [('mouse pipeline', 'target prep once (~3 min: alignment, ColabFold MSA, pqt) → restrained fold → paired read',
      [('prep (once)', 0.0, 3.0, C['prep']), ('restrained fold', 3.1, 7.6, C['fold']),
       ('paired read', 10.75, 0.15, C['score'])])],
    tmax=12,
    footer=['33 designs, 165 samples · 4.2 h GPU · anchors by alignment: human K344/K374 → mouse K346/K376 (fold 224/254)',
            'top band: e12rfd4_r4d5 (−0.050) and c3_e12rfd4_r3d4_d2 (+0.018, carries the switch); tightest human parents are mouse-weakest']))
