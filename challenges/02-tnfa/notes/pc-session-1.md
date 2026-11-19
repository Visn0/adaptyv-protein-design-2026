# PC session 1 — the GPU box comes online

*15 October 2026, evening. Machine: the Windows PC, WSL2 Ubuntu. Purpose: build the
local GPU stack and verify it with real runs, so the C2 work no longer depends on
Tamarind. Nothing was deployed, nothing was bought, nothing left this machine.*

## 1. Machine facts (measured, not assumed)

| Item | Value |
|---|---|
| GPU | **NVIDIA GeForce RTX 5070, 12 227 MiB** |
| Driver | 616.92 (KMD 616.92), CUDA UMD 13.4 |
| Compute capability | sm_120 — torch reports `(12, 0)` |
| CPU / RAM / disk | 20 cores, 24 GB (`~/.wslconfig`), 748 GB free |
| `nvidia-smi` | not on PATH inside WSL; it is `/usr/lib/wsl/lib/nvidia-smi` |

**Correction:** the plans (`master-plan.md`, `gpu-box-setup.md`) said "RTX 5070 Ti,
16 GB". The card is a **5070 with 12 GB**. Boltz-2, RFD3 and ProteinMPNN still fit;
BoltzGen (24 GB floor) stays out. `gpu-box-setup.md` now carries this correction.

## 2. What was built

| Component | State | Verified by |
|---|---|---|
| `.venv` (project) | python 3.12.3, torch 2.11.0+cu128, OpenMM 8.6.1 + mdtraj + pdbfixer | `pdt device` |
| `pdt device` | `cuda: True`, `recommended: cuda`, `resources: gpu -> 'cuda'` | command output |
| pytest (offline) | 63 collected: 57 passed, 6 skipped, ~15 s (`make test`) | `make test` |
| `pdt exp run --all -j 4` | 9 specs: 4 `done`, 5 `waiting_inputs` | run ledger |
| C2 parity | every committed number reproduced (see §4) | `summary.json` |
| `~/.venvs/tools` | PROPKA 3.5.1 + handoff analysis deps; IPSAE runs here | IPSAE output |
| `~/.venvs/boltz` | boltz 2.2.1, torch 2.14.1+cu130, cuda True; weights in `~/.boltz` (4.3 GB) | fold below |
| `~/.venvs/rfd3` | rc-foundry 0.2.0, atomworks 2.2.1, torch 2.14.1+cu130 | smoke test below |
| `~/tools/IPSAE`, `~/tools/ProteinMPNN` | cloned | directory present |
| RFD3 checkpoint | `~/.foundry/checkpoints/rfd3_latest.ckpt`, 2 690 316 669 B | sha256 `9b3f8592…d67c1` |

Everything above rebuilds from the repo: `make setup-gpu`, then `make rfd3`.

## 3. The RFD3 checkpoint — the Mac blocker, solved

`files.ipd.uw.edu` is unreachable from **this** network too: DNS resolves, TCP 443
times out on IPv4 and IPv6. So the Mac's retry loop was hopeless, not a Mac fault.

The mirror used: Hugging Face dataset `sgetttt/rfdiffusion3-assets`, file
`models/weight/rfd3_latest.ckpt`. The file is byte-identical to the official URL
(same 2 690 316 669 bytes, sha256 `9b3f85923e0d51e9453e15cdd2f8c666e7ce096a60577f57d11bbc54ae6d67c1`,
the hash the mirror's own manifest pins to the IPD URL). 34 MB/s here, about 80 s.
`make rfd3` downloads and verifies it.

Licence: the RFD3 weights are **CC-BY-NC-SA-4.0** (non-commercial). Check before any
use outside this competition.

## 4. C2 parity on this machine (all matches the committed numbers)

| Experiment | Result here | Documented |
|---|---|---|
| `c2-anchors` | 14 candidates, 12 chemistry-class-conserved, 7 within 6 A of the groove; A73 and B73 `SWITCH LOST` | same |
| `c2-switch-motif` | clearances 4.57 / 5.00 / 3.79 A, max span 20.23 A, hotspots `A103,B112,B103` | same |
| `c2-scorer-controls` | 3 controls, 3 delta checks OK, 3 site-count checks OK | same |
| `c2-baseline-results` | 36 built, 32 scanned, 12 pass coverage, 48 sequences, 0 docked, best ipTM 0.161, 20 submitted | same |

`waiting_inputs` on this box, with the reason:

- `c2-coverage-scan` — needs generated backbones in `inputs/backbones/`.
- `c2-score-designs` — needs folded complexes in `inputs/complexes/`.
- `c1-replay-parents`, `c1-replay-full`, `c1-md-switch` — need
  `challenges/01-egfr/data/`, which comes from the study repo
  `~/Projects/Protein-design-competition-Anthropic-X-adaptyv`. That clone exists on
  the Mac only. Copy the directory over (`rsync -av`), then `make fetch-data` works.

## 5. W1 first attempt — the known design, folded locally

Design: `config_c2-x2-rfd3-s1-groove-1_0_model_1` (73 aa), the design that passed on
Tamarind. Command:

```bash
cd challenges/02-tnfa/handoff
~/.venvs/boltz/bin/boltz predict boltz/fold-human-config_c2-x2-rfd3-s1-groove-1_0_model_1.pdb.yaml \
    --out_dir ~/c2-work/w1-5 --use_msa_server --seed 42 --diffusion_samples 5
```

GPU time: 92 s for 5 samples (plus about 3 min for the MSA fetch and the weight load).
IPSAE: `python ~/tools/IPSAE/ipsae.py <pae.npz> <model.cif> 10 10` in
`~/.venvs/tools`.

| model | ipTM | ipSAE A-B | ipSAE B-A | ipSAE min | pDockQ2 A-B |
|---|---|---|---|---|---|
| 0 | 0.937 | **0.733** | 0.488 | 0.488 | 0.133 |
| 1 | 0.949 | 0.454 | 0.337 | 0.337 | **0.224** |
| 2 | 0.946 | **0.646** | 0.493 | 0.493 | 0.178 |
| 3 | 0.933 | 0.433 | 0.267 | 0.267 | 0.062 |
| 4 | 0.903 | 0.025 | 0.070 | 0.025 | 0.029 |

Tamarind reference for the same design (seed differs): ipSAE A-B 0.527 / 0.804 / 0.378
/ 0.000 / 0.000, pDockQ2 A-B 0.132 / 0.236 / 0.000 / 0.014 / 0.010, ipTM 0.944 / 0.962
/ 0.939 / 0.847 / 0.839.

**Acceptance (the W1 bar).** At least one sample with ipSAE(A-B) >= 0.6 or close to it,
and the same spread shape. Here two of five samples reach 0.733 and 0.646; the spread
(one locked interface, one near, one partial, two losses) has the same shape as the
Tamarind run. **The W1 acceptance test passes locally.**

**Caveats, stated plainly.** The strict pre-registered bar (ipSAE >= 0.6 AND pDockQ2
>= 0.23) is met by 0 of 5 local samples; Tamarind met it once (0.804 / 0.236). ipTM
stays high (0.90-0.95) in every sample, even where the interface score collapses — the
ipSAE/pDockQ2 caveat holds. Five samples on one design is not a rate.

## 6. RFD3 smoke test — the generator runs on the GPU

```bash
~/.venvs/rfd3/bin/rfd3 design out_dir=~/c2-work/rfd3-smoke inputs=null \
    +specification.length=100 diffusion_batch_size=2
```

Result: two de-novo 100-residue designs in **45.75 s**, written as `_0_model_0.cif.gz`
and `_0_model_1.cif.gz` with per-design metrics (radius of gyration 12.5 A, helix 0.25
/ sheet 0.42, 0 clashes, 0 chain breaks). The GPU path for the primary generator is
alive.

## 7. What broke, and the fix (do not relearn these)

1. **A CPU torch arrived with a GPU tool.** `uv pip install --torch-backend=auto
   "rc-foundry[rfd3]"` installed `torch 2.14.1+cpu` — the flag does not cover a
   transitive torch dependency. Fix:
   `uv pip install --python ~/.venvs/rfd3/bin/python --torch-backend=cu130 --reinstall-package torch torch`.
   `--reinstall-package` is required: uv otherwise reports "Checked 1 package" and
   keeps the CPU build. Always assert `torch.cuda.is_available()` after a GPU install.
2. **rc-foundry 0.2.0 + the newest atomworks is a broken pair.** It declares
   `atomworks[ml]>=2.1.1`, so the resolver takes 3.0.1, which removed
   `get_inferred_polymer_bonds`; RFD3 then dies with an ImportError. Fix: pin
   `atomworks[ml]==2.2.1`.
3. **RFD3 hydra arguments.** `specification.length=100` fails ("Could not override");
   use `+specification.length=100`. `contig` cannot be given without an `input`
   structure — a pure de-novo run sets the length only.
4. **Background shells lose the interactive PATH** (`uv: command not found`). Use the
   absolute path in scripts (`~/.hermes/bin/uv`).
5. **OpenMM has no GPU platform on this box.** The venv has Reference and CPU only;
   the `openmm-cuda` package exists but pins openmm 8.1.1 and would downgrade 8.6.1.
   The `md` pipeline stays CPU here (the Mac used OpenCL). Not on the C2 path.
6. **`nvidia-smi` was not on PATH, and cuequivariance assumed the wrong card.** The
   fold logs carry `Error getting GPU memory: No such file or directory: 'nvidia-smi'`
   and `Failed to get GPU information from pynvml: Not Supported`, then
   `GPU information: NVIDIA RTX A6000, 8, 6, 45, 84, 300, 2100` — a 48 GB placeholder.
   Source read: the message comes from `cuequivariance_ops/triton/cache_manager.py`;
   the numbers are a **Triton kernel cache key and tuning default**, not a batching
   decision (Boltz has no memory-aware auto-batching). Fix (no sudo):
   `ln -sf /usr/lib/wsl/lib/nvidia-smi ~/.local/bin/nvidia-smi`. The error disappears
   and the name is right, but the 5070 has no entry in that default map, so the A6000
   defaults still apply. Measured impact: none on the runs (5 samples peak at 7.8 GB
   of 12 GB). Details: `x2-fold-local-vs-tamarind.md` §5.
7. **The Makefile resolved `uv` to the Mac binary in a background shell.** Background
   jobs have no interactive PATH, so `command -v uv` failed and the fallback went to
   `~/.hermes/tools/uv-0.12.3-darwin-arm64/uv` — `make rfd3` died with
   `No such file or directory` (exit 127) before installing anything. Fix: the fallback
   now checks `~/.hermes/bin/uv` first, and a new `uv-check` target fails with a clear
   message (exit 2) instead of a path error. Verify with
   `env -i HOME=$HOME PATH=/usr/bin:/bin bash -c 'make -n rfd3 | head -1'`.
8. **`uv venv` is not idempotent.** A second `make rfd3` failed with
   `A virtual environment already exists at: ~/.venvs/rfd3`. Every venv
   creation in the Makefile now passes `--allow-existing`. Both targets then re-run
   clean: `make setup-gpu` exit 0, `make rfd3` exit 0 (checkpoint `OK`), with the venvs
   unchanged (torch 2.11.0+cu128 / 2.14.1+cu130, cuda True in both).

The lesson for the record: an earlier revision of this note claimed both targets were
verified end to end. They were not — the first `make rfd3` had failed at its first line,
and the claim came from checking the environment state instead of the command's exit
code. Read the exit code of the command under test.

## 8. Next step

W2: fold the 8 shortlist designs (human, 5 samples each, about 8 min of GPU in total),
then ranks 1-2 against the mouse construct, and triage every sample with IPSAE. Then W3
(the switch layer) and W5 (RFD3 generation at scale) run on this box.
