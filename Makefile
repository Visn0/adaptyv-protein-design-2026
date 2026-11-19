SHELL := /bin/bash
# uv: PATH first, then the common install locations. A background shell has no
# interactive PATH, so the fallbacks matter; uv-check fails loudly (exit 2)
# with the resolved path when none of them is executable.
UV ?= $(shell { command -v uv || ls $(HOME)/.local/bin/uv || ls $(HOME)/.hermes/bin/uv || echo uv; } 2>/dev/null | head -1)
PY := .venv/bin/python
SUBDATE := $(shell date +%F)

.PHONY: install sync fetch-data exp-list exp-run exp-status dashboard viewers select device torch setup-gpu rfd3 md-deps clean-runs uv-check

uv-check:
	@test -x "$(UV)" || { echo "uv not found: install it, or run make UV=/path/to/uv (resolved: $(UV))"; exit 2; }

install: uv-check .venv
.venv:
	$(UV) venv --allow-existing --python 3.12 .venv
	$(UV) pip install --python $(PY) -e .
$(PY): .venv

sync: uv-check       ## fast path: sync the venv from uv.lock (keeps extras + torch installs)
	$(UV) sync --all-extras --inexact

fetch-data:          ## copy the public target files (1TNF.cif, target_AB.pdb, fastas)
	$(PY) -m tools.cli fetch-data

exp-list:            ## list available experiments
	$(PY) -m tools.cli exp list

exp-run:             ## run every experiment, 4 in parallel
	$(PY) -m tools.cli exp run --all -j 4

exp-status:          ## recent run ledger
	$(PY) -m tools.cli exp status

dashboard:           ## rebuild challenges/**/runs + global dashboard
	$(PY) -m tools.cli dashboard

viewers:             ## regenerate challenge 3's Mol* multiview pages from the shared template
	@for f in challenges/03-glp1r/viewers/multiview/*.html; do \
		s=$$(basename "$$f" .html); \
		$(PY) challenges/03-glp1r/viewers/scripts/make_molstar_multiview.py "$$s" | tail -1; \
	done

select:              ## the authoritative selection: gate -> score -> top 20 -> candidates
	$(PY) challenges/03-glp1r/campaigns/c8-deep-junction/scripts/rescore-all.py
	$(PY) challenges/03-glp1r/campaigns/c8-deep-junction/scripts/select-top20.py
	$(PY) challenges/03-glp1r/campaigns/c8-deep-junction/scripts/build-final-submission.py
	$(PY) challenges/03-glp1r/campaigns/c1-two-domain/submission/make_competition_csv.py \
		--candidates $$HOME/c3-work/final-candidates.csv \
		--out challenges/03-glp1r/submission/competition-submission-rubric-$(SUBDATE).csv
	$(PY) -m tools.analysis.validate_submission \
		challenges/03-glp1r/submission/competition-submission-rubric-$(SUBDATE).csv --max-rows 20

device:              ## show what compute this machine offers (cpu/mps/cuda)
	$(PY) -m tools.cli device

torch: uv-check                          ## install torch: MPS (Mac) / CUDA (Nvidia PC) picked by uv
	$(UV) pip install --python $(PY) --torch-backend=auto torch

setup-gpu: uv-check                  ## PC/WSL2: the GPU stack (project venv, tools venv, Boltz-2, IPSAE, MPNN)
	$(UV) venv --allow-existing --python 3.12 .venv
	$(UV) pip install --python $(PY) -e ".[md]"
	$(UV) pip install --python $(PY) --torch-backend=auto torch
	$(UV) venv --allow-existing --python 3.12 $(HOME)/.venvs/tools
	$(UV) pip install -p $(HOME)/.venvs/tools/bin/python propka==3.5.1 -r challenges/02-tnfa/handoff/requirements-tools.txt
	$(UV) venv --allow-existing --python 3.12 $(HOME)/.venvs/boltz
	$(UV) pip install -p $(HOME)/.venvs/boltz/bin/python -U "boltz[cuda]"
	mkdir -p $(HOME)/tools
	test -d $(HOME)/tools/IPSAE || git clone --depth 1 https://github.com/DunbrackLab/IPSAE.git $(HOME)/tools/IPSAE
	test -d $(HOME)/tools/ProteinMPNN || git clone --depth 1 https://github.com/dauparas/ProteinMPNN.git $(HOME)/tools/ProteinMPNN
	$(PY) -m tools.cli device

rfd3: uv-check                            ## PC: RFdiffusion3 (rc-foundry) + its checkpoint. files.ipd.uw.edu is
                     ## unreachable from every network we tested; the mirror below is byte-identical.
                     ## Two pins matter: atomworks 2.2.1 (3.0.1 removed an API rc-foundry uses)
                     ## and a CUDA torch (the resolver picks a CPU build on its own).
	$(UV) venv --allow-existing --python 3.12 $(HOME)/.venvs/rfd3
	$(UV) pip install -p $(HOME)/.venvs/rfd3/bin/python "rc-foundry[rfd3]" "atomworks[ml]==2.2.1"
	$(UV) pip install -p $(HOME)/.venvs/rfd3/bin/python --torch-backend=cu130 --reinstall-package torch torch
	$(HOME)/.venvs/rfd3/bin/python -c "import torch; assert torch.cuda.is_available(), 'no CUDA torch'; print('rfd3 venv on', torch.cuda.get_device_name(0))"
	mkdir -p $(HOME)/.foundry/checkpoints
	test -f $(HOME)/.foundry/checkpoints/rfd3_latest.ckpt || curl -L --retry 3 --retry-delay 5 \
		-o $(HOME)/.foundry/checkpoints/rfd3_latest.ckpt \
		https://huggingface.co/datasets/sgetttt/rfdiffusion3-assets/resolve/main/models/weight/rfd3_latest.ckpt
	echo "9b3f85923e0d51e9453e15cdd2f8c666e7ce096a60577f57d11bbc54ae6d67c1  $(HOME)/.foundry/checkpoints/rfd3_latest.ckpt" | sha256sum -c -
	$(HOME)/.venvs/rfd3/bin/foundry list-installed

md-deps: uv-check                      ## install the OpenMM stack for the real-physics (md) pipeline
	$(UV) pip install --python $(PY) -e ".[md]"

clean-runs:          ## delete all experiment run outputs
	find challenges -type d -name runs -exec rm -rf {} +
