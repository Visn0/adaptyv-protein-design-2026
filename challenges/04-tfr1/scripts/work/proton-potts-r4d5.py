#!/usr/bin/env python3
"""First Proton-PottsMPNN run on our own complex: e12rfd4_r4d5 (the top c6 pick's parent).

Direction note (off-label, recorded): the challenge-4 window releases on
acidification, so the bound complex must FAVOUR the NEUTRAL histidine. The
engine's own campaigns pin protonated centres (engage-on-acid); here the
centre is the neutral state HIS-S and the contrast is HIS-P
(dep_map={"HIS-S": ["HIS-P"]}) - the mirrored objective through the same
selective gap. Positions are pinned with explicit_centers at the two c3-picked
sites of this binder (res 8 and 27, the r4d5_d2 variant's His positions).

Run inside ~/tools/ProtonPottsMPNN (uv run python this_file).
"""
import json
import os
import pathlib

os.environ.pop('DEBUG', None)
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('HBPLUS_PATH', str(pathlib.Path.home() / 'tools/HBPLUS/hbplus/hbplus'))

from atomworks.io.parser import parse  # noqa: E402

import mpnn  # noqa: E402
from mpnn.inference_engines.potts_mpnn_ph import PottsMPNNPHEngine, PHDesignCriteria  # noqa: E402

PKG = pathlib.Path.home() / 'tools/ProtonPottsMPNN'
CKPT = PKG / 'checkpoints' / 'potts_v6_afdb_edge_his0.3_acid0.06' / 'epoch-0125.ckpt'
PDB = pathlib.Path.home() / 'c4-work/ppmpnn-r4d5.pdb'
OUT = pathlib.Path.home() / 'c4-work/ppmpnn-r4d5-out'
OUT.mkdir(exist_ok=True)
BINDER_CHAIN = 'B'

engine = PottsMPNNPHEngine(checkpoint_path=str(CKPT), extended_vocab='v6',
                           out_directory=str(OUT), write_fasta=True, write_structures=False)
# atomworks' own loader: the engine's parser path requires its standard
# annotations (charge et al.) and runs template completion.
atom_array = parse(str(PDB))['asym_unit']
ctx = engine._build_context(atom_array, BINDER_CHAIN)
free = [int(ctx.token_aa.res_id[int(p)]) for p in ctx.chA_free_idx.tolist()]
print(f'engine ready | {len(free)} designable binder positions | '
      f'first/last: {free[0]}..{free[-1]}', flush=True)

# the two c3-picked His positions on this binder (from c3-variants.csv, r4d5_d2)
centers = [{'res_id': 9, 'protonation_type': 'HIS-S'},
           {'res_id': 28, 'protonation_type': 'HIS-S'}]
missing = [c['res_id'] for c in centers if c['res_id'] not in free]
if missing:
    print(f'WARNING: centers {missing} not in the designable set; '
          f'nearest free positions: {sorted(free)[:40]}', flush=True)

crit_list = []
for lam in (0.1, 0.3, 0.6):
    crit_list.append(PHDesignCriteria(
        method='block_descent', backend='potts', temperature=0.05,
        samples_per_site=2, block_size=3, combined_lambda=lam,
        seed_source='native',
        center_count=2,
        explicit_centers=centers,
        #  first sweep had no cap and the mirrored objective
                            # degenerated into His/Arg-rich near-homopolymers
        max_mutations=12,
        # mirrored direction for the 7.4 -> 6.0 window (off-label):
        dep_map={'HIS-S': ['HIS-P'], 'HIS-P': ['HIS-S']},
    ))

design_set = engine.run_ph_redesign(atom_array=atom_array, binder_chain=BINDER_CHAIN,
                                    criteria_list=crit_list, seed=0, n_jobs=4)

# dump what the set carries, defensively
rows = []
for d in design_set:
    rec = {k: v for k, v in vars(d).items() if not k.startswith('_')}
    rec.update(d.to_metadata())
    rows.append(rec)
(OUT / 'designs.json').write_text(json.dumps(rows, indent=2, default=str))
print(f'wrote {OUT}/designs.json with {len(rows)} designs', flush=True)
print(json.dumps(rows[:3], indent=2, default=str)[:1500])
