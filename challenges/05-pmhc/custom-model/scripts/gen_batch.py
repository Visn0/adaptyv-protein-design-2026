#!/usr/bin/env python3
"""Baseline batch: N RFD4-Proteina designs against the G12D pMHC.

Generates designs with different seeds, writes one CIF each. The features are
prepared once (same target) and reused; each design gets its own generator.
"""

import pathlib
import sys

import torch
from diffusers import RFD4ProteinaPipeline
from rfd4_proteina_prep import prepare_cif, write_cif

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


OUR_CIF = str(_repo_root() / "challenges/05-pmhc/nim/target_pmhc_PEPRIM_annotated.cif")
OUT = pathlib.Path.home() / "c5-work/rfd4-batch1/designs"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 32
SEED0 = 1000

REQUIRED = ["padding_mask", "is_in_context_conditioning", "supports_local_latent",
            "token_type", "atom37_mask", "coords_nm"]

OUT.mkdir(parents=True, exist_ok=True)
print(f"generating {N} designs (seeds {SEED0}..{SEED0 + N - 1})", flush=True)
pipe = RFD4ProteinaPipeline.from_pretrained(
    "nvidia/RFD4-Proteina-Diffusers", dtype=torch.bfloat16).to("cuda:0")
print("pipeline loaded", flush=True)

features, atoms = prepare_cif(OUR_CIF, seed=SEED0, device=pipe.device)
conditioning = {k: v for k, v in features.items() if k not in REQUIRED}
print("features prepared", flush=True)

for i in range(N):
    seed = SEED0 + i
    out = pipe(
        padding_mask=features["padding_mask"],
        is_in_context_conditioning=features["is_in_context_conditioning"],
        supports_local_latent=features["supports_local_latent"],
        token_type=features["token_type"],
        atom37_mask=features["atom37_mask"],
        conditioning_features=conditioning,
        generator=torch.Generator("cuda:0").manual_seed(seed),
    )
    dest = OUT / f"batch1-{i:03d}.cif"
    write_cif(out, features, atoms, str(dest))
    n = int(out.emit_mask.sum().item())
    print(f"[{i + 1}/{N}] seed {seed} -> {dest.name} ({n} designed)", flush=True)

print("GEN_DONE", flush=True)
