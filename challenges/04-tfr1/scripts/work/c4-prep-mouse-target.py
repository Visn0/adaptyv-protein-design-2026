#!/usr/bin/env python3
"""Campaign 4 (mouse cross-fold), step 0: prepare the mouse target.

1. Mouse sequence: extracted from inputs/AF-Q62351-F1.pdb (641 aa, auth 123-763).
2. Anchor mapping: human K344/K374 -> mouse K346/K376, derived from the
   alignment in scripts/epitope_analysis.py (never a fixed offset; the offset
   is +2/+3 depending on the indel). Fold indices: 224 and 254.
3. MSA: fetched from the ColabFold server (depth 1024) with fetch_msas.py and
   converted to a chai .aligned.pqt named by sha256(query.upper()).

Run with the chai venv for the pqt conversion step:
    python c4-prep-mouse-target.py [--skip-fetch]
Writes ~/c4-work/mouse-target.seq and the .aligned.pqt beside the a3m.
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import subprocess
import sys

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / 'challenges/04-tfr1'
WORK = pathlib.Path.home() / 'c4-work'
MSA_DIR = WORK / 'msa'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-fetch', action='store_true')
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location('epi', CH / 'scripts/epitope_analysis.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _, hrows = m.amino_acids(CH / 'inputs/11QC.cif', 'A')
    _, mrows = m.amino_acids(CH / 'inputs/AF-Q62351-F1.pdb', None)
    mapping, identical, columns = m.align_species(hrows, mrows)
    print(f'alignment {identical}/{columns}')
    for h in (344, 374):
        ma, ha, maa = mapping[h]
        assert ha == maa == 'K', f'anchor {h} not conserved K->K'
        print(f'human {h}{ha} -> mouse {ma}{maa} | fold idx {ma - 122}')

    seq = ''.join(aa for _, aa, _ in mrows)
    (WORK / 'mouse-target.seq').write_text(seq + '\n')
    print(f'mouse target seq written ({len(seq)} aa)')

    a3m_candidates = sorted(MSA_DIR.glob('*-d1024.a3m'),
                            key=lambda p: p.stat().st_mtime, reverse=True)
    a3m = None
    for c in a3m_candidates:
        first = [l.strip() for l in c.read_text().splitlines()
                 if not l.startswith('>')][0]
        if first == seq:
            a3m = c
            print(f'cached a3m found: {c.name}')
            break
    if a3m is None:
        if args.skip_fetch:
            sys.exit('no cached a3m and --skip-fetch set')
        subprocess.run([sys.executable, str(WORK / 'bin/fetch_msas.py'),
                        '--fasta', '/dev/stdin', '--depth', '1024',
                        '--out-dir', str(MSA_DIR)],
                       input=f'>mouse\n{seq}\n', text=True, check=True)
        a3m = sorted(MSA_DIR.glob('*-d1024.a3m'),
                     key=lambda p: p.stat().st_mtime, reverse=True)[0]

    from chai_lab.data.parsing.msas.aligned_pqt import (
        a3m_to_aligned_dataframe, expected_basename)
    from chai_lab.data.parsing.msas.data_source import MSADataSource
    df = a3m_to_aligned_dataframe(a3m, MSADataSource.UNIREF90)
    out = MSA_DIR / expected_basename(seq)
    df.to_parquet(out)
    print(f'wrote {out} ({len(df)} rows)')


if __name__ == '__main__':
    main()
