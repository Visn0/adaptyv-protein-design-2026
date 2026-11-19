#!/usr/bin/env python3
"""Evolutionary loop over the composite (one generation per run).

Operators, in priority order:
  1. combo mutants: stack the best round-1/2 repair hit with a second shell
     mutation of the same parent (single-point hits that lost a metric may
     win together);
  2. unsampled shell: basic swaps at shell positions the repair rounds have
     not yet tried (capped per design);
  3. (the surrogate's pool picks run separately as their own test).

Guardrails (the project's own lessons):
  - a variant only counts if i_pDAE >= 0.70 and ipTM >= 0.93 (the fold gates);
  - the loop only PROPOSES swaps; the incumbent set changes only after the
    full validation (seeds/chai/apo) and a composite win;
  - every generation writes a record and never deletes anything.

Usage: PYTHONPATH= .venv/bin/python evo.py <generation-number>
"""

from __future__ import annotations

import csv
import glob
import pathlib
import itertools
import re
import subprocess
import sys

import gemmi

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
W = HOME / "c5-work"
GEN = int(sys.argv[1]) if len(sys.argv) > 1 else 1
G = W / "evo" / f"gen{GEN}"
SETS = ("s1", "s1w3", "camp", "c2p", "c6", "s1w4", "repair", "repair2",
        "s1w5", "s1w6", "evo/gen1")
BASIC = "KR"
ACIDIC = "DE"
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}
CHARGED = {"NZ", "NH1", "NH2", "NE", "OD1", "OD2", "OE1", "OE2"}


def fold_cif(name: str):
    for s in SETS:
        hits = glob.glob(str(W / s / "folds" / name / "boltz_results_*"
                             / "predictions" / name / f"{name}_model_0.cif"))
        if hits:
            return hits[0]
    # fallback: the design may live in any era's fold tree (evo gen N, val dirs)
    hits = glob.glob(str(W / "**" / "folds" / name / "boltz_results_*"
                         / "predictions" / name / f"{name}_model_0.cif"),
                     recursive=True)
    return hits[0] if hits else None


def parent_yaml(name: str):
    for s in SETS:
        for suff in ("", "__g12d"):
            p = W / s / "folds" / f"{name}{suff}.yaml"
            if p.exists():
                return p
    # fallback: the design may live in any era's fold tree (evo gen N, val dirs)
    for suff in ("", "__g12d"):
        hits = sorted(W.glob(f"**/folds/{name}{suff}.yaml"))
        if hits:
            return hits[-1]
    return None


def parent_seq(name: str) -> str | None:
    p = parent_yaml(name)
    if not p:
        return None
    import yaml
    d = yaml.safe_load(p.read_text())
    return [x for x in d["sequences"]
            if x["protein"]["id"] == "D"][0]["protein"]["sequence"]


def shell(name: str, lo=5.0, hi=13.0):
    cif = fold_cif(name)
    if not cif:
        return []
    st = gemmi.read_structure(cif)[0]
    b = st.find_chain("D")
    pep = st.find_chain("C")
    d6 = [a for rr in pep if rr.seqid.num == 6 for a in rr
          if a.name in ("OD1", "OD2")]
    out = []
    for rr in b:
        ca = next((a for a in rr if a.name == "CA"), None)
        if ca is None:
            continue
        d = min(ca.pos.dist(p.pos) for p in d6)
        if lo <= d <= hi:
            out.append((rr.seqid.num, AA3.get(rr.name, "X"), round(d, 1)))
    return out


def current_top(n=16):
    # v4 selection: the gen4 rerank table carries the organizer-gate (epitope)
    # term that the v2 ranking never had; breeding must start from the
    # gate-passers, not from a score blind to the organizers' primary criterion.
    v4 = W / "evo/gen4/rerank-v4.csv"
    if v4.exists():
        rows = sorted(csv.DictReader(v4.open()),
                      key=lambda r: -float(r.get("v4_score", 0) or 0))
        return [(r["design"], float(r.get("v4_score", 0) or 0)) for r in rows[:n]]
    rows = list(csv.DictReader((REPO / "challenges/05-pmhc/records/final2/"
                                "ranking-v2.csv").open()))
    return [(r["design"], float(r["score_v2"])) for r in rows[:n]]


def main() -> int:
    G.mkdir(parents=True, exist_ok=True)
    folds = G / "folds"
    folds.mkdir(exist_ok=True)
    log = [f"# Evo generation {GEN}", ""]
    top = current_top()
    log.append(f"parents (current top {len(top)}): " + ", ".join(
        f"{d.split('__')[0]} {s:.0f}" for d, s in top))
    made = 0
    for name, score in top:
        seq = parent_seq(name)
        if not seq:
            log.append(f"- {name}: no sequence found, skipped")
            continue
        sh = shell(name)
        # positions already tried in earlier rounds (skip duplicates)
        core = re.sub(r"^(repair-|evo)", "", name)
        core = re.sub(r"-[A-Z]\d+[A-Z]$", "", core)
        tried = set()
        pats = [W / "repair" / "folds", W / "repair2" / "folds"] + \
            sorted((W / "evo").glob("gen*/folds"))
        for pat in pats:
            for p in pat.glob(f"*{core}*.yaml"):
                m = re.search(r"-([A-Z])(\d+)[A-Z]\.yaml$", p.name)
                if m:
                    tried.add(int(m.group(2)))
        # operator 2: unsampled shell positions -> basic swaps (cap 8)
        cand = [(num, aa, d) for num, aa, d in sh
                if aa not in BASIC and aa != "P" and num not in tried]
        cand = sorted(cand, key=lambda x: x[2])[:5]
        for num, aa, d in cand:
            s2 = list(seq)
            if num - 1 >= len(s2):
                continue
            s2[num - 1] = "K"
            vname = f"evo{name}-{aa}{num}K"
            py = parent_yaml(name)
            if py:
                (folds / f"{vname}.yaml").write_text(
                    py.read_text().replace(seq, "".join(s2), 1))
                made += 1
        # operator 1: untried PAIRS of this family's known mutations (deduped)
        hits = {}
        for pat in pats:
            for p in pat.glob(f"*{core}*.yaml"):
                m = re.search(r"-([A-Z])(\d+)([A-Z])\.yaml$", p.name)
                if m:
                    hits[int(m.group(2))] = m.group(3)
        for a, b in list(itertools.combinations(sorted(hits), 2))[:4]:
            if a - 1 >= len(seq) or b - 1 >= len(seq):
                continue
            s2 = list(seq)
            s2[a - 1] = hits[a]
            s2[b - 1] = hits[b]
            vname = f"evo{name}-combo{a}x{b}"
            if (folds / f"{vname}.yaml").exists():
                continue
            py = parent_yaml(name)
            if py:
                (folds / f"{vname}.yaml").write_text(
                    py.read_text().replace(seq, "".join(s2), 1))
                made += 1
    log.append(f"variants built: {made}")
    (G / "build-log.md").write_text("\n".join(log) + "\n")
    print(f"gen{GEN}: built {made} variant yamls under {folds}")
    # fold + score + E (serialized behind any GPU job)
    qlog = G / "queue.log"
    wait = (
        f"V={W}/v4-val/logs/chain.log; "
        f"V5={W}/v5-val/logs/chain.log; "
        f"S={W}/ml/surrogate-folds/queue.log; "
        "while ! grep -q V4_VAL_END \"$V\" 2>/dev/null "
        "|| ! grep -q V5_VAL_END \"$V5\" 2>/dev/null "
        "|| ! grep -q SURROGATE_TEST_END \"$S\" 2>/dev/null "
        "|| [ \"$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)\" -gt 2500 ]; "
        "do sleep 60; done"
    )
    subprocess.run(["bash", "-c",
                    f"{wait}; cd {REPO} && MEMLIMIT_MB=12000 C0_WORK={G} "
                    f"bash challenges/05-pmhc/scripts/work/c0-probe-fold.sh all "
                    f">> {qlog} 2>&1 && "
                    f"PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py "
                    f"--work {G} --jobs 3 >> {qlog} 2>&1 && "
                    f"PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/escore.py "
                    f"{G}/folds/*/boltz_results_*/predictions/*/*_model_0.cif "
                    f"> {G}/escores.txt 2>&1"],
                   check=False)
    print(f"gen{GEN}: folds + scores done; run evo-select.py {GEN} next")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
