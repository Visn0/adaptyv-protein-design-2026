# GPU box setup — GeForce RTX 5070 (12 GB, Blackwell)

> **Measured 15 Oct 2026 (evening):** the PC reports **RTX 5070 with 12 227 MiB**, not
> the 5070 Ti 16 GB assumed below. Driver 616.92, CUDA UMD 13.4, sm_120. The venvs,
> the checkpoint and the smoke tests all work; see `pc-session-1.md`. Read "16 GB"
> everywhere below as "12 GB". BoltzGen stays out either way.

Checklist for the Windows/Linux PC that will run the C2 generation stack. Written 15 Oct 2026. Gate: all smoke tests green by the evening of Oct 16, else Experiment 01 starts on the Tamarind fallback.

## 0. What this card can and cannot run

| Tool | Fits 12–16 GB? | Notes |
|---|---|---|
| RFdiffusion3 (RFD3) | Yes | Documented minimum ~3 GB GPU memory; own docs give explicit Blackwell guidance (nightly cu128 upgrade path). The primary generator. Measured on the PC: 2 x 100 aa designs in 46 s. |
| Boltz-2 | Yes | Co-folding of our ~600-residue complexes. Use one complex per job. Measured on the PC: a 4-chain trimer fold used 4.5 GB. |
| ColabFold / AlphaFold2 | Yes | Sequence-to-structure + PAE; chunking keeps memory low. |
| ProteinMPNN | Yes | Tiny model. |
| ipSAE, PROPKA, all our `pdt` scoring | n/a (CPU) | Run on either machine. |
| BoltzGen | **No** | Community-documented floor 24 GB VRAM. Use Tamarind for this tool, or skip it. |

**Never use original RFdiffusion on this card.** Its torch pin is from the cu118 era — no sm_120 kernels; the failure is `CUDA error: no kernel image is available for execution on the device`. RFdiffusion3 replaces it.

## 1. Operating system

- **Linux (Ubuntu 22.04 / 24.04): best.** All tools run natively.
- **Windows: use WSL2 (Ubuntu).** The Windows NVIDIA driver passes CUDA into WSL2; every tool then sees a normal Linux system. Avoid native Windows for ColabFold and the foundry pipelines — their scripts assume a Unix shell.

## 2. Hardware requirements

- NVIDIA driver **≥570** (latest recommended for Blackwell; the 5070 Ti is sm_120).
- CUDA toolkit **12.8+** (13.x is also acceptable on current drivers).
- PyTorch **≥2.7** with **cu128 or newer** wheels. Do not debug around an older pin; it cannot work.
- Free disk **≥60 GB** (RFD3 weights ~3 GB, Boltz-2 weights + MSA caches several GB, ColabFold ~4 GB, Hugging Face caches). Add ~40 GB more only if BoltzGen is ever attempted here.
- System RAM **≥32 GB** recommended.

## 3. Install steps (Ubuntu or WSL2)

```bash
# 1. Driver + toolkit
nvidia-smi                       # expect driver >= 570, CUDA >= 12.8 capability
# If old: install the current NVIDIA driver (open kernel module), reboot.

# 2. Python env (uv is fast; conda also fine)
uv venv --python 3.12 ~/rfd3-env
source ~/rfd3-env/bin/activate

# 3. PyTorch with Blackwell support
pip install torch --index-url https://download.pytorch.org/whl/cu128
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0), torch.version.cuda)"
```

```bash
# 4. RFdiffusion3 (foundry)
pip install "rc-foundry[rfd3]"
foundry install rfd3              # downloads ~3 GB checkpoint

# 5. Boltz-2
pip install boltz                 # weights download on first run

# 6. ColabFold
pip install "colabfold[alphafold]"

# 7. ProteinMPNN (torch only)
git clone https://github.com/dauparas/ProteinMPNN.git
```

**Smoke tests (each must pass before the gate):**

1. RFD3: one 80-residue binder design against a small test target → one PDB out.
2. Boltz-2: co-fold the 3WD5 Fab–TNF complex (two chains) → PAE JSON out.
3. ColabFold: fold one 100-residue sequence → PDB + PAE out.
4. ProteinMPNN: design sequences for one RFD3 backbone → FASTA out.

## 4. Two machines, one repo

- Code: the `protein-design-poc` git repo works on both. Data and runs are plain directories.
- `PDT_DEVICE` selects the device; the PC resolves to CUDA, the Mac to CPU/MPS. Same commands on both.
- Recommended split: **generation + co-folding on the PC; scoring + reports on the Mac** (scoring is CPU-only and lives in the poc venv).
- Transfer: `rsync -av` the `challenges/02-tnfa/` directory (inputs + runs); copy new runs back for the web app.
- Keep one writer per file while both machines are active (AGENT.md rule 15).

## 5. Experiment 01 run template (once the gate passes)

1. Prepare the target: 1TNF chains A+B+C into one PDB (input for RFD3).
2. For each hotspot set S1, S2, S3: 40–60 RFD3 designs, binder 70–95 residues.
3. Co-fold each design with Boltz-2 (one complex per job), 5 models.
4. Copy results to the Mac; run the local scoring pass (ipSAE 10 Å cutoff, ipSAE_min, pDockQ2, contacts, loophole check) + controls (3WD5 positive, shuffled negative).
5. Write the measured rates into `research-phase-0.md` and decide per the tree.

## 6. Licence note

Check each tool's model-weight licence before relying on it for a submission. RFD3 weights, Boltz-2 weights and ColabFold all ship under their own terms.
