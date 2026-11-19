# Campaign 12 — RFD4-Proteina on NVIDIA's hosted Spaces

## Why this campaign
RFD4-Proteina is the successor of the RFdiffusion line and the strongest open generator we
have not used yet. NVIDIA runs it on Hugging Face for free until November 4, 2026, and the
launch blog invites use for this competition. The Space is the only remote compute in this
project that is free, so generation runs there and the PC stays light.

## Configuration
- Target: the same 409-residue human GLP1R construct as every campaign. The Space saw the
  annotated CIF built from `inputs/rfd4-c12.yaml` (design segment 60-100 residues,
  receptor 1-409 fixed).
- Generation: thinking medium, 8 designs per request, one request at a time. Only the
  dedicated GPU pool works well: the free ZeroGPU tier caps one request at a few GPU
  minutes (8 x medium = 462 s was refused).
- Screening: the ordinary boltz co-fold pipeline against the campaign receptor block
  (template `folds/c3-j2-run6.yaml`), so every design is scored by the same script as the
  other campaigns (ipSAE, pDockQ2, activation geometry).

## How it was driven
The Space needs a signed-in browser session; an API token does not pass its gate (checked
in its own source: generation requires the Gradio OAuth session cookie). The session was
made once by hand in the Hermes-managed Chromium (profile `~/.hermes/chrome-debug`, CDP
port 9333), authorized for both Spaces. From then on `~/c3-work/hf-space-drive.py` takes
the session cookies over CDP and calls `/generate_cif` with `gradio_client`. The design
range 60-100 residues is the RFD4 contig length range, matching the winning binder size
band of campaign 1.
