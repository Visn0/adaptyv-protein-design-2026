#!/usr/bin/env python3
"""Clone the four C4 problems as batch-2 keys (11qc_e0b2 ...) and write their
Genie 3 run yamls (n_sample 32). Used by the C2 continuation chain so batch 2
never collides with batch-1 output names in the same problem directory.
"""
from __future__ import annotations

import json
import pathlib

HOME = pathlib.Path.home()
BENCH = HOME / "tools/genie3/data/design/binder_design/binderbench"
WORK = HOME / "c4-work"
SEEDS = {"11qc_e0b2": 81, "11qc_e1b2": 82, "11qc_e2b2": 83, "11qc_e12b2": 84}

for key, seed in SEEDS.items():
    base = key[:-2]
    src = json.loads((BENCH / f"problems/{base}.json").read_text())
    src["key"] = key
    src["name"] = src["name"] + " batch2"
    src["note"] = (src.get("note", "") + " | batch 2 of the same epitope set "
                   "(campaign 2 pool top-up); hotspots unchanged.")
    (BENCH / f"problems/{key}.json").write_text(json.dumps(src, indent=4) + "\n")
    (WORK / f"genie3/{key}.yaml").write_text(f"""experiment:
  name: {key.replace('_', '-')}
  seed: {seed}

paths:
  rootdir: {WORK}/genie3/runs
  dataset: data/design/binder_design/binderbench

generation:
  dataset:
    source: target
    selections: {key}
    n_sample: 32
  sampler:
    sampler:
      direction_scale: 0.0

evaluation:
  version: binder
  inverse_folding:
    num_seq: 1
  folding:
    model_name: colabfold
    mode: template
""")
    print(f"{key}: problem + yaml written (hotspots "
          f"{src['target_interface_residues']['hotspot']})")
