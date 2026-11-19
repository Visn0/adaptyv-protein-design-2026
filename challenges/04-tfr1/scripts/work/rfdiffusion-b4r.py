#!/usr/bin/env python3
"""Batch-4R: the RFdiffusion arm of the generation wave (hosted NIM).

The rfd4-proteina endpoint is down (server-side CUDA faults since 2026-10-27
10:17); the classic rfdiffusion NIM on the same platform works. Same wave
conditions, third generator:
  E12L -> hotspots A223, A253   (fold numbering; auth - 121), binder 110-140
  E0L  -> hotspots A83, A87, A89, A90, A227, A250,           binder 110-140
  H    -> hotspots A87, A90, A223, A253,                     binder 60-110
Target: targets/tfr1_639.pdb (chain A, numbered 1-639). One API call per
design (the schema has no num_designs), different random_seed each.

Writes  ~/c4-work/rfdiffusion/B4R/<tag>/design_<i>.pdb + meta.json
"""
from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.request

TARGET = pathlib.Path.home() / 'c4-work/targets/tfr1_639.pdb'
OUT = pathlib.Path.home() / 'c4-work/rfdiffusion/B4R'
URL = 'https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate'
ARMS = {
    'E12L': (['A223', 'A253'], '110-140', 8),
    'E0L': (['A83', 'A87', 'A89', 'A90', 'A227', 'A250'], '110-140', 8),
    'H': (['A87', 'A90', 'A223', 'A253'], '60-110', 8),
}


def one_call(hotspots, length, seed, attempt=1):
    payload = {
        'input_pdb': TARGET.read_text(),
        'contigs': f'A1-639/0 {length}',
        'hotspot_res': hotspots,
        'diffusion_steps': 50,
        'random_seed': seed,
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={'Authorization': f"Bearer {os.environ['NVIDIA_API_KEY']}",
                 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except Exception as exc:  # noqa: BLE001
        if attempt < 3:
            time.sleep(20)
            return one_call(hotspots, length, seed, attempt + 1)
        print(f'    FAILED seed {seed}: {exc}')
        return None


def main():
    for tag, (hotspots, length, count) in ARMS.items():
        d = OUT / tag
        d.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            pdb = d / f'design_{i:04d}.pdb'
            if pdb.exists():
                continue
            seed = 4200 + i * 17 + sum(ord(c) for c in tag)
            t0 = time.time()
            body = one_call(hotspots, length, seed)
            if not body:
                continue
            pdb.write_text(body['output_pdb'])
            print(f'{tag}/design_{i:04d}: {len(body["output_pdb"])} chars, '
                  f'{body.get("elapsed_ms", "?")} ms server, {time.time() - t0:.1f} s total')
    print('B4R_END')


if __name__ == '__main__':
    main()
