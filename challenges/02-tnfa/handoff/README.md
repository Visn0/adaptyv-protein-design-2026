# C2 PC handoff — the RTX 5070 Ti route

*Written 15 October 2026. This package carries everything the second machine
(Windows PC, RTX 5070 Ti 16 GB, WSL2 Ubuntu) needs to continue Challenge 2
without the Mac and without the Tamarind quota.*

---

## 1. The state of the evidence (read this first)

| Experiment | Setup | Result |
|---|---|---|
| X1 | BoltzGen, 150 designs, 3 hotspot sets | **0 dock.** Best ipSAE 0.005, best ipTM 0.36 |
| X2 | RFdiffusion3, 72 complexes, S1 hotspots | **58 of 72 sit in the antibody groove, spanning two protomers** |
| Co-fold | Boltz-2, independent, 5 samples | **Pass in 1 of 5 samples** (ipSAE 0.804, pDockQ2 0.236); one near pass, one partial, two failures |

The generator problem is solved. The conditional problem is not started: no
switch exists, no mouse check exists, no control exists. That is the PC work.

The full record lives in `notes/` (start with `c2-runbook.md` and
`x2-results.md`). Every number in this document was measured, not estimated.

## 2. Deadline arithmetic

Challenge 2 closes **18 October 23:59 AoE = 19 October 13:59 CEST**.

| Window | Work | Time |
|---|---|---|
| W0, tonight | Machine setup | 2–4 h |
| W1, tonight | Reproduce the known fold | 1 h |
| W2, 16 Oct | Fold the 8 shortlist designs (human + mouse) | 3–6 h |
| W3, 17 Oct | Switch design, folds, PROPKA audit | 1 day |
| W4, 18 Oct | Controls, selection, submission file | half a day |
| 19 Oct 12:00 | Stop and upload | — |

If W2 fails (no new design passes), stop the campaign track and record the
negative. Do not spend W3 and W4 on a dead route.

## 3. What this package holds

| Path | Content |
|---|---|
| `designs/all-designs.csv` | All 72 X2 designs: rank, metrics, sequence, source PDB |
| `designs/designs.csv` | The 8 clean shortlist designs for the next folds |
| `designs/pdb/*.pdb` | The shortlist complexes (binder = chain A, target = B/C/D) |
| `sequences/targets.fasta` | The human construct (P01375 82–233) and the mouse construct (P06804 85–235) |
| `sequences/shortlist-binders.fasta` | The 8 binder sequences |
| `sequences/all-site-binders.fasta` | All 58 site designs |
| `boltz/fold-human-*.yaml` | Ready Boltz-2 input, one per shortlist design |
| `boltz/fold-mouse-*.yaml` | Boltz-2 input for the top design against mouse TNF |
| `records/` | Job JSONs, both triage CSVs, the fold metrics, the X1 metrics |
| `notes/` | The full challenge notes and the pipeline diagram |
| `data-raw/` | The two original result zips from Tamarind |
| `scripts/triage_rfd3.py` | The triage tool: site adherence, clashes, interface size |

Two facts that the X2 input fixes: the 1TNF construct covers **P01375 82–233**
and it differs from the UniProt sequence at one position (**1TNF 219 is L, the
UniProt residue is D**). All folds must use the same construct, or the numbers
are not comparable.

## 4. W0 — machine setup (WSL2)

Prerequisite checks, in this order:

1. Windows NVIDIA driver **570 or newer**. Inside WSL, `nvidia-smi` must show
   the RTX 5070 Ti. If it does not, the WSL driver stack is broken. Fix it
   before anything else.
2. `~/.wslconfig` — give WSL at least 12 GB of RAM (MSA generation is
   memory-hungry) and half the CPU cores:
   ```
   [wsl2]
   memory=12GB
   processors=8
   ```
3. Disk: 25 GB free.
4. Python environment:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv --python 3.12 ~/.venvs/boltz
   uv venv --python 3.12 ~/.venvs/tools
   ```
5. Boltz-2:
   ```
   uv pip install -p ~/.venvs/boltz/bin/python -U "boltz[cuda]"
   ~/.venvs/boltz/bin/boltz predict --help
   ```
   Read the help output and write the sampling flags down. Flag names changed
   between releases (`--diffusion_samples` and `--num_samples` both appear in
   the wild). The flags used below are the ones to verify first:
   `--out_dir`, `--use_msa_server`, `--devices`, `--seed`.
6. IPSAE (interface confidence):
   ```
   git clone https://github.com/DunbrackLab/IPSAE ~/tools/IPSAE
   ```
   Their README gives the exact invocation for Boltz outputs (PAE npz plus
   the model PDB). The expected form is
   `python ipsae.py <pae.npz> <model.pdb> 10 10`.
7. PROPKA (pKa audit):
   ```
   uv pip install -p ~/.venvs/tools/bin/python propka==3.5.1
   ```
8. Verification: one small fold end to end, then IPSAE on its output. If the
   numbers print, W0 is done.

## 5. W1 — reproduce the known fold

The design that already passed on Tamarind: rank 2 in the shortlist,
`config_c2-x2-rfd3-s1-groove-1_0_model_1.pdb`, 73 aa.

```
cd ~/c2-handoff
~/.venvs/boltz/bin/boltz predict boltz/fold-human-config_c2-x2-rfd3-s1-groove-1_0_model_1.pdb.yaml \
    --out_dir runs/w1 --use_msa_server --seed 42
```

Then run IPSAE on every sample and compare with
`records/x2-fold-metrics.csv`.

**Acceptance:** at least one sample with ipSAE(A–B) ≥ 0.6 or close to it, and
the same spread shape (some samples lock the interface, some lose it). Exact
reproduction is not expected: the seeds differ. A comparable regime is the
criterion.

## 6. W2 — fold the shortlist

The eight clean designs (site-spanning, minimum distance ≥ 2.0 Å, interface
≥ 80 atoms):

| Rank | Design | Length | min_d | atoms4 | Helix | Note |
|---|---|---|---|---|---|---|
| 1 | groove-3_1_model_1 | 94 | 2.03 | 109 | 0.90 | largest interface |
| 2 | groove-1_0_model_1 | 73 | 2.27 | 108 | 0.77 | **already folded — the passing design** |
| 3 | groove-2_1_model_0 | 76 | 2.13 | 98 | 0.87 | |
| 4 | groove-5_0_model_4 | 85 | 2.07 | 98 | 0.75 | |
| 5 | groove-0_1_model_1 | 91 | 2.22 | 93 | 0.00 | all-loop geometry, keep as a probe |
| 6 | groove-4_1_model_2 | 84 | 2.10 | 88 | 0.93 | |
| 7 | groove-2_1_model_5 | 76 | 2.12 | 87 | 0.75 | |
| 8 | groove-5_0_model_5 | 85 | 2.35 | 86 | 0.88 | |

Liability note: the sequences contain free cysteines (for example rank 2
starts `DCG...`). Record them. Do not remove them before the folds, or the
comparison breaks.

Loop over `boltz/fold-human-*.yaml`, 5 samples each, IPSAE on every sample.
Then fold rank 1 and rank 2 against the mouse construct
(`boltz/fold-mouse-*.yaml`) and check that the contacting target residues are
the conserved set.

**Acceptance:** two or more designs beyond the known one pass (ipSAE ≥ 0.6 in
at least one sample). That makes the generator finding robust. Zero extra
passes means the first result was seed luck. Record it and stop.

## 7. W3 — the switch layer

The C2 objective is inverted pH behaviour: bind at 7.4, release at 6.0, and
bind mouse TNF. The known mechanism, and the only one with a literature
basis here:

1. **Histidine is the switch.** Below pH 6.5 it is protonated and carries +1.
2. **K65 is the counter-charge.** It is a lysine in the S1 groove, it is
   conserved in mouse, and it is inside the designed interface.
3. Protonated His next to Lys repels. Binding weakens at 6.0 and holds at
   7.4 — the wanted direction.

Steps:

1. **Geometry screen.** For each folded complex, list the binder positions
   within 4–8 Å of K65 NZ. `scripts/triage_rfd3.py` is the template.
2. **Substitute.** Replace 1–3 of those positions with histidine. Change
   nothing else.
3. **Fold every variant** (Boltz-2, 5 samples). Keep the variant only if the
   interface survives (ipSAE ≥ 0.6 in at least one sample) and the His ring
   keeps a 3.5–8.5 Å standoff to K65 NZ.
4. **PROPKA audit.** Run the complex, the free binder and the free target.
   The expected signature is a positive linkage (binding favoured at 7.4).
   PROPKA is empirical and is not validated on designed interfaces. Report it
   as evidence, never as proof.
5. **Controls.** Every switch variant pairs with an unmodified control, same
   binder, no histidine. The challenge format expects the pair.
6. **Mouse check.** Fold each kept variant against the mouse construct. The
   contact set must stay on the conserved residues.

Do not touch residues that face the antibody epitope's other protomer. Do not
introduce a histidine that loses a buried hydrogen bond for the sake of the
switch.

## 8. W4 — selection and the submission

Pre-register the ranking rule before looking at the results:

- fold-level pass in at least 3 of 5 samples, and
- positive PROPKA linkage, and
- clean mouse fold, and
- no new buried polar atom.

Build the submission with the repository tools (`tools/switch/build_submission.py`,
`tools/analysis/validate_submission.py`). Their chain expectation is binder
`C`, targets `A` and `B`. Our complexes use binder `A`, targets `B`/`C`/`D`.
Rename the chains before scoring, and check `tools/pipelines/c2.py` for the
exact assumptions.

Confirm the upload format on the C2 page before the upload. The C1 entry used
a sequences CSV with paired controls.

## 9. W5 — optional: scale generation

Only if W1–W4 finish early. RFdiffusion3 on CUDA (the official foundry
package, `pip install 'rc-foundry[all]'`) with the same settings as X2:
`targetChains A B C`, `hotspots {"A": "65 67", "C": "75"}`, `binderLength
70,95`, `nonLoopy`, 200–500 designs. Triage with `scripts/triage_rfd3.py`,
fold only the clean site designs. This supplies the volume that the
instructions ask for.

## 10. Copy the package and verify it

1. Download `c2-handoff.tar.gz` from the chat card, or copy the folder:
   ```
   rsync -av ~/Projects/protein-design-poc/challenges/02-tnfa/handoff/ user@pc:~/c2-handoff/
   ```
2. Verify:
   ```
   tar -xzf c2-handoff.tar.gz -C ~/c2-handoff
   cd ~/c2-handoff && shasum -a 256 -c SHA256SUMS
   ```

## 11. Report back with this template

```md
## PC session N — <date>
- Machine: RTX 5070 Ti, WSL2, driver <version>, boltz <version>
- Commands: <exact commands>
- Results: design | samples | best ipSAE(A-B) | ipSAE_min | pDockQ2
- Decisions: <kept/dropped designs, reasons>
- Next step: <one line>
```

Save it as `notes/pc-session-N.md` in this package. The numbers go back into
the same tables as the Tamarind results.

## 12. Rules that carried this work (do not relearn them)

- Full trimer only. A partial target lets binders fill the missing protomer.
- Hotspot span ≤ 15 Å. Wider spans failed in two independent campaigns.
- The pass bar is pre-registered: ipSAE ≥ 0.6 and pDockQ2 ≥ 0.23.
- Score interfaces with ipSAE and pDockQ2. Contact counts lie.
- One writer per file. Another session may work on the same repository.
- Every claim gets a date and a source.

## 13. Facts and limits of the Tamarind route (for the record)

- The monthly quota is spent: 10 of 10 jobs (3 for X1, 6 for the X2 batch, 1
  for the fold). It resets on 1 November, after the C2 deadline.
- RFdiffusion3 bills about one job per 8 designs. BoltzGen bills one job per
  run. This is not in the tool documentation; it was measured.
- The API key stays on the Mac (`~/.config/tamarind/api_key`). The PC does
  not need it.
