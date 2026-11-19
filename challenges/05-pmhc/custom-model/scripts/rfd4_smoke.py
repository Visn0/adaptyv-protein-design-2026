#!/usr/bin/env python3
"""RFD4-Proteina smoke test: run the shipped example, then our pMHC target.

Downloads the model on first run (1.74 GB), then samples one design for the
known-good protein_binder example and one against our annotated pMHC CIF.
"""

import sys
import traceback

import torch
from huggingface_hub import hf_hub_download
from diffusers import RFD4ProteinaPipeline
from rfd4_proteina_prep import prepare_cif, write_cif

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


OUR_CIF = str(_repo_root() / "challenges/05-pmhc/nim/target_pmhc_PEPRIM_annotated.cif")
OUT = str(_repo_root() / "challenges/05-pmhc/custom-model/data/smoke")

print("loading pipeline (first run downloads ~1.7 GB)...", flush=True)
pipe = RFD4ProteinaPipeline.from_pretrained(
    "nvidia/RFD4-Proteina-Diffusers", dtype=torch.bfloat16).to("cuda:0")
print("pipeline loaded", flush=True)

REQUIRED = ["padding_mask", "is_in_context_conditioning", "supports_local_latent",
            "token_type", "atom37_mask", "coords_nm"]


def run_one(cif_path, tag, seed=42):
    print(f"=== {tag}: preparing {cif_path}", flush=True)
    features, atoms = prepare_cif(cif_path, seed=seed, device=pipe.device)
    conditioning = {k: v for k, v in features.items() if k not in REQUIRED}
    output = pipe(
        padding_mask=features["padding_mask"],
        is_in_context_conditioning=features["is_in_context_conditioning"],
        supports_local_latent=features["supports_local_latent"],
        token_type=features["token_type"],
        atom37_mask=features["atom37_mask"],
        conditioning_features=conditioning,
        generator=torch.Generator("cuda:0").manual_seed(seed),
    )
    dest = f"{OUT}/{tag}.cif"
    write_cif(output, features, atoms, dest)
    n = int(output.emit_mask.sum().item())
    print(f"=== {tag}: wrote {dest}, {n} designed residues", flush=True)


# 1. shipped example (sanity check)
try:
    ex = hf_hub_download("nvidia/RFD4-Proteina-Diffusers",
                         "examples/protein_binder/input.cif")
    run_one(ex, "example_binder")
except Exception:
    traceback.print_exc()

# 2. our target
try:
    run_one(OUR_CIF, "pmhc_target")
except Exception:
    traceback.print_exc()

print("SMOKE_DONE", flush=True)
