"""Reading a run at a glance: metric directions, legends, and the verdict.

Three questions this module answers for every page of the app:

1. **Which way is better?** `METRICS` gives every number the pipelines print a
   label, a direction (`higher` / `lower` / `range` / `context`) and one plain
   sentence. `legend_html()` renders the ones a run actually reports.
2. **Is this evidence, or only a method check?** `assess_run()` turns a run's
   spec + status + summary into one verdict chip and one sentence. It never
   says "good protein": the strongest verdict is "promising (in-silico)", and
   every verdict names the rule it applied.
3. **What is the pre-registered bar?** `BARS` holds the acceptance lines fixed
   before the campaign, as numbers and as text. `fold.py` applies the same
   numbers, so the pass count and the sentence can never disagree.

Verdict levels
--------------
    promising    at least one candidate or sample clears a pre-registered bar
    partial      a signal exists but stays under the bar (a qualified pass)
    insufficient not enough evidence: no candidate clears the bar, or too few samples
    negative     the measured result is against the design idea (e.g. no docks)
    check        a reference/parity or a control run — it validates the method,
                 it says nothing about a binder
    waiting      the run waits for input files; no evidence yet
    failed       the run ended in an error

The module lives outside `tools/serve/` because the static report
(`tools/report/html.py`) renders the same verdicts and legends.
"""
from __future__ import annotations

import html as _html
from datetime import datetime, timezone
from pathlib import Path

# How many runs a page reads from the ledger. One constant: the run numbers
# ('#n') must not depend on which caller asked.
RECENT_RUNS = 200

# ---------------------------------------------------------------- metrics

# key -> (label, direction, one-line meaning)
METRICS: dict[str, tuple[str, str, str]] = {
    "score": (
        "selection score (0-100)", "higher",
        "The primary selection score, from select-top20.py: "
        "100 x (2.0*A + 1.5*B + 1.0*E + 0.5*R) / 25. "
        "A = activation geometry (how many of the 6 agonist features the pose meets, "
        "and whether samples agree), B = binding (ipSAE, with a bonus for pDockQ2 >= 0.30), "
        "E = expression (pLDDT band + Kyte-Doolittle hydropathy), R = epitope reach. "
        "Each component is capped at 5, so the weighted total caps at 25. "
        "The six epitope-gate additions of 2026-11-04 carry the v4 composite "
        "instead (25 i_pDAE + 15 ipTM + 15 dfree + 15 E + 10 dWT + 20 "
        "peptide_read): same 0-100 scale, different formula. "
        "Row order is this score, descending."),
    "selectivity": (
        "selectivity (kcal/mol)", "lower",
        "Binding energy difference between pH 6.5 and 7.4. More negative means "
        "binding is favoured at the LOW pH — the wanted direction for C1.",
    ),
    "best_selectivity": (
        "best selectivity (kcal/mol)", "lower",
        "The most negative selectivity in the set. Lower is better for C1.",
    ),
    "delta_log_Ka": (
        "delta log Ka", "higher",
        "pH linkage of the complex. Positive means binding is favoured at the "
        "HIGH pH (7.4) — the wanted direction for C2.",
    ),
    "best_delta_log_Ka": (
        "best delta log Ka", "higher",
        "The largest positive linkage in the set. Higher is better for C2.",
    ),
    "ipsae": (
        "ipSAE", "higher",
        "Interface confidence from the PAE matrix (10 A cutoff). >= 0.6 is the "
        "usual acceptance line; below 0.6 the model has little idea where the "
        "chains meet.",
    ),
    "ipsae_min": (
        "ipSAE min", "higher",
        "The weaker of the two interface directions. The best single lab-binding "
        "predictor in the 2025 meta-analysis.",
    ),
    "pdockq2": (
        "pDockQ2", "higher",
        "Interface quality that counts only the interface residues. The second "
        "half of the acceptance bar (>= 0.23).",
    ),
    "ipdae": (
        "i_pDAE", "higher",
        "Interface pDAE over the interface residues (CA-CA <= 8 A mask). Best "
        "top-decile precision of the fold metrics in the ProteinBase benchmark.",
    ),
    "tier": (
        "specificity tier", "—",
        "Dual-signal = wild-type discrimination (dWT >= 0.15) and peptide-free "
        "dependence (dfree >= 0.2); otherwise the axis that carries the design.",
    ),
    "groove_site": (
        "groove", "higher",
        "Contacts at the GLP-1 binding groove (of 6 residues). The address half "
        "of the site: filling it makes a binder, not necessarily an agonist.",
    ),
    "tm_site": (
        "TM pocket", "higher",
        "Contacts in the transmembrane pocket (of 4). The deeper, message-side "
        "region — the reach that matters for activation.",
    ),
    "activation": (
        "activation geometry", "higher",
        "The GLP-1 message-region pharmacophore: contacts of 6 plus insertion depth "
        "below the vestibule rim, from the calibrated activation gate. 6/6 at depth "
        ">= 16 A is the full agonist pattern.",
    ),
    "ecl3_site": (
        "ECL3", "higher",
        "Contacts on outer loop 3 (of 8). ECL3 moves when the receptor switches "
        "on; contact there is part of the activation pattern.",
    ),
    "iptm": (
        "ipTM", "higher",
        "Predicted interface TM. Stays high even when the interface score "
        "collapses — never decide on ipTM alone.",
    ),
    "best_iptm": (
        "best ipTM", "higher",
        "The highest interface TM in the set. Weak evidence on its own.",
    ),
    "ptm": (
        "pTM", "higher",
        "Overall fold confidence of the whole predicted complex.",
    ),
    "plddt": (
        "mean pLDDT", "higher",
        "Per-residue confidence of the model. It says the fold is well-formed, "
        "not that the chains bind.",
    ),
    "n_contacts": (
        "interface contacts", "context",
        "Atom pairs under 4.5 A. Context only: contact counts look good on "
        "poses that do not dock.",
    ),
    "presence_3p6": (
        "contact presence (3.6 A)", "higher",
        "Fraction of MD frames with the designed contact. Compare the two pH "
        "states; one state alone says little.",
    ),
    "presence_delta": (
        "contact presence delta", "higher",
        "Low-pH presence minus high-pH presence for the switch contact. Positive "
        "means the designed contact is stronger at the low pH.",
    ),
    "min_dist": (
        "minimum heavy-atom distance (A)", "higher",
        "Closest approach between the chains. Below 2.0 A is a clash: raw "
        "diffusion geometry, not a design.",
    ),
    "atoms4": (
        "interface atoms (4 A)", "higher",
        "Binder atoms within 4 A of the target. A rough size of the interface.",
    ),
    "n_sites": (
        "covered switch sites", "higher",
        "How many of the three motif sites a backbone can reach. Two or more is "
        "the pre-registered minimum for sequence design.",
    ),
    "n_passed_coverage": (
        "backbones passing coverage", "higher",
        "Backbones that reach at least two switch sites.",
    ),
    "n_binding_at_high_pH": (
        "designs binding at pH 7.4", "higher",
        "Designs whose linkage favours the high pH — the wanted sign for C2. "
        "The score ranks; it does not prove binding.",
    ),
    "n_docked": (
        "docked designs", "higher",
        "Designs that pass the interface bar after an independent co-fold. The "
        "number that decides a campaign.",
    ),
    "n_candidates": (
        "candidates", "context",
        "How many structures entered this stage.",
    ),
    "rmsd": (
        "RMSD (A)", "lower",
        "Deviation from the starting pose. Lower means the predicted pose held.",
    ),
    "clearance": (
        "clearance (A)", "higher",
        "Distance from the placed histidine to the nearest target atom. Below "
        "3.6 A is a clash.",
    ),
    "span": (
        "span (A)", "range",
        "Distance the motif has to cover. A binder face can bridge about 15-20 A; "
        "wider spreads failed in two campaigns.",
    ),
    "n_switch_conserved": (
        "conserved switch anchors", "higher",
        "Titratable groups whose chemistry class survives the human/mouse "
        "difference (Asp/Glu keep the class, His/Tyr lose it).",
    ),
}

# Pre-registered acceptance lines, fixed before the work (do not move them).
# Numbers and text live together: the code compares the numbers, the pages
# quote `rule`, and neither can drift from the other.
BARS = {
    "dock": {
        "label": "docked complex",
        "ipsae": 0.6,
        "pdockq2": 0.23,
        "rule": "ipSAE >= 0.6 AND pDockQ2 >= 0.23",
    },
    "coverage": {
        "label": "backbone for sequence design",
        "rule": "at least 2 of 3 switch sites in reach (3.5-8.5 A)",
    },
    "mouse": {
        "label": "mouse check",
        "rule": "the contacting residues stay on the conserved set",
    },
}

_DIRECTION_WORD = {
    "higher": "higher is better",
    "lower": "lower is better",
    "range": "there is a wanted range",
    "context": "context only — no direction",
}


def esc(value) -> str:
    """HTML-escape any value for the pages and the report."""
    return _html.escape(str(value))


def _legend(rows: list[str]) -> str:
    """One legend box; an empty row list renders nothing at all."""
    return "<div class='legend'>" + "".join(rows) + "</div>" if rows else ""


def legend_html(keys: list[str]) -> str:
    """Rows for the metrics a page shows: label, direction, one sentence."""
    rows = []
    seen = set()
    for key in keys:
        entry = METRICS.get(key)
        if not entry or key in seen:
            continue
        seen.add(key)
        label, direction, meaning = entry
        rows.append(
            "<div class='mleg'>"
            f"<span class='mono'>{esc(label)}</span>"
            f"<span class='dir {direction}'>{_DIRECTION_WORD[direction]}</span>"
            f"<span class='sub'>{esc(meaning)}</span>"
            "</div>"
        )
    return _legend(rows)


def bars_html(keys: list[str]) -> str:
    """The pre-registered acceptance lines that apply to a challenge."""
    rows = []
    for key in keys:
        bar = BARS.get(key)
        if not bar:
            continue
        rows.append(
            "<div class='mleg'>"
            f"<span class='mono'>{esc(bar['label'])}</span>"
            f"<span class='sub'>{esc(bar['rule'])}</span>"
            "</div>"
        )
    return _legend(rows)


def colour_legend_html() -> str:
    """The standing viewer standard (rule 4 in AGENT.md)."""
    return _legend([
        "<div class='mleg'><span class='swatch' style='background:#60a5fa'></span>"
        "<span class='mono'>target</span><span class='sub'>the protein to bind</span></div>",
        "<div class='mleg'><span class='swatch' style='background:#e879f9'></span>"
        "<span class='mono'>designed binder</span><span class='sub'>the design</span></div>",
        "<div class='mleg'><span class='swatch' style='background:#fbbf24'></span>"
        "<span class='mono'>interface</span><span class='sub'>the residues that touch</span></div>",
    ])


# The verdict levels, in the order the legend lists them.
def format_when(iso) -> str:
    """'2026-10-15T19:47:33+00:00' -> '15 Oct 2026, 19:47 UTC'. The ledger is UTC."""
    try:
        moment = datetime.fromisoformat(str(iso)).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return "unknown time"
    return f"{moment.day} {moment:%b %Y, %H:%M} UTC"


def run_sort_key(row: dict) -> str:
    return str(row.get("started_utc") or "")


def unique_labels(rows: list[dict]) -> dict[str, str]:
    """run_dir name -> unique display label ('c2-fold-w1-gpu #2', oldest is #1)."""
    counters: dict[str, int] = {}
    labels: dict[str, str] = {}
    for row in sorted(rows, key=run_sort_key):
        name = str(row.get("name", "?"))
        counters[name] = counters.get(name, 0) + 1
        run_id = Path(str(row.get("run_dir", ""))).name
        labels[run_id] = f"{name} #{counters[name]}"
    return labels


# ---------------------------------------------------------------- verdicts


def _stages(summary) -> list[dict]:
    return [stage for stage in ((summary or {}).get("stages") or []) if isinstance(stage, dict)]


def _stage(summary, name: str) -> dict | None:
    for stage in _stages(summary):
        if stage.get("stage") == name:
            return stage
    return None


def _num(stage: dict | None, key: str):
    if not isinstance(stage, dict):
        return None
    value = stage.get(key)
    return value if isinstance(value, (int, float)) else None


def _verdict(level: str, label: str, reason: str, basis: str) -> dict:
    """Every rule returns through here, so a chip always carries all four keys."""
    return {"level": level, "label": label, "reason": reason, "basis": basis}


def _reference_pairs(summary) -> list[tuple[str, object, object]]:
    """(metric, expected, actual) triples a stage's `reference` block exposes.

    Stage keys sometimes carry a unit suffix (`max_span_A` vs the reference's
    `max_span`), so look for the exact key first, then for `_A`.
    """
    pairs = []
    for stage in _stages(summary):
        reference = stage.get("reference")
        if not isinstance(reference, dict):
            continue
        for key, expected in reference.items():
            actual = stage.get(key)
            if actual is None:
                actual = stage.get(f"{key}_A")
            if actual is None:
                continue
            pairs.append((key, expected, actual))
    return pairs


def _values_match(expected, actual) -> bool:
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        if len(expected) != len(actual):
            return False
        return all(_values_match(a, b) for a, b in zip(expected, actual))
    if expected == actual:
        return True
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 1e-6
    return False


def _reference_matches(pairs: list[tuple[str, object, object]]) -> int:
    """How many reference numbers match (lists compare element by element)."""
    return sum(1 for _key, expected, actual in pairs if _values_match(expected, actual))


def assess_run(spec, status, summary) -> dict:
    """One verdict per run: {level, label, reason, basis}.

    `spec` may be None (a run whose spec is gone). `status` and `summary` are
    the run's JSON files. The function never guesses: when no rule applies it
    returns level `insufficient` with the basis "no rule".
    """
    state = str((status or {}).get("state", "?"))
    name = str((status or {}).get("name") or getattr(spec, "name", "") or "?")
    pipeline_name = str((status or {}).get("pipeline")
                        or getattr(spec, "pipeline", "") or "")

    if state == "failed":
        return _verdict("failed", "run failed",
                        str((status or {}).get("error") or "the run ended in an error"),
                        "exit state")
    if state == "waiting_inputs":
        waiting = (summary or {}).get("waiting_for") or (status or {}).get("error") or ""
        return _verdict("waiting", "no evidence yet",
                        f"the run waits for inputs: {waiting}" if waiting
                        else "the run waits for inputs",
                        "run state")

    # A co-fold: the design evidence. Judge it against the pre-registered dock bar.
    fold_stage = _stage(summary, "import") if pipeline_name == "fold" else None
    if fold_stage is not None:
        bar = BARS["dock"]
        n_pass = _num(fold_stage, "n_pass")
        n_samples = _num(fold_stage, "n_samples")
        best = _num(fold_stage, "ipsae")
        best_pd2 = _num(fold_stage, "pdockq2")
        if n_pass:
            return _verdict("promising",
                            f"{int(n_pass)} of {int(n_samples or 0)} samples pass the bar",
                            f"A sample meets {bar['rule']}: the model puts an interface "
                            "together somewhere on the target. The score does NOT say the "
                            "interface is at the designed site — check the contacts against "
                            "the designed residues before calling this a binder. In-silico "
                            "only; a lab assay decides.",
                            bar["rule"])
        if best is not None and best >= bar["ipsae"]:
            return _verdict("partial", f"best sample ipSAE {best:.2f} — under the full bar",
                            f"ipSAE clears the ipSAE half of {bar['rule']}, but pDockQ2 "
                            f"{(best_pd2 if best_pd2 is not None else 0.0):.3f} misses its "
                            "half. A qualified pass: more samples before trusting it.",
                            bar["rule"])
        if best is not None:
            return _verdict("insufficient", f"best sample ipSAE {best:.2f}",
                            f"No sample reaches {bar['rule']}. Fold spread is large, so "
                            "this is not yet a verdict on the design.",
                            bar["rule"])

    # Designs scored for pH linkage (the C2 decision stage).
    score = _stage(summary, "score")
    if score is not None:
        scored = _num(score, "n_scored")
        if scored is None:
            scored = _num(score, "n_designs")
        wanted = _num(score, "n_binding_at_high_pH")
        if wanted:
            return _verdict("partial", f"{int(wanted)} design(s) with the wanted sign",
                            "A positive delta log Ka is the wanted direction, but the score "
                            "ranks; it does not prove binding.",
                            "linkage score")
        if scored is not None:
            return _verdict("insufficient", "no design clears the sign check",
                            f"{int(scored)} complex(es) scored, none favoured pH 7.4.",
                            "linkage score")

    pairs = _reference_pairs(summary)
    if pairs:
        matched = _reference_matches(pairs)
        if matched == len(pairs):
            return _verdict("check", "reproduces the reference",
                            f"{matched} of {matched} reference numbers match. This is a "
                            "regression check of the pipeline, not evidence about a binder.",
                            "reference numbers")
        return _verdict("negative", "reference mismatch",
                        f"{matched} of {len(pairs)} reference numbers match — investigate "
                        "before trusting new results.", "reference numbers")

    compare = _stage(summary, "compare")
    if compare is not None:
        delta = compare.get("presence_delta")
        if isinstance(delta, float):
            return _verdict("check", f"switch contact delta {delta:+.2f}",
                            "A short MD run tests the predicted pose. It is not a binding "
                            "assay and not a free-energy calculation.", "MD trajectory")

    return _verdict("insufficient", "not enough evidence",
                    f"No assessment rule covers '{name}'. Read the report; do not treat "
                    "the numbers as a design verdict.", "no rule")


def result_block(verdict: dict) -> str:
    """The factual reading of a run: what the numbers say and which rule said it.

    The subjective level chip ("promising" / "partial" / ...) is deliberately
    gone: a label invites reading a judgement into an in-silico number. The
    reason and the basis are facts, so they stay. Designs carry a single
    normalized 0-100 score from the selection rubric instead.
    """
    return (
        "<div class='verdict'>"
        f"<span class='sub'>{esc(verdict.get('reason', ''))}</span>"
        f"<span class='mono basis'>basis: {esc(verdict.get('basis', ''))}</span>"
        "</div>"
    )


def score_chip(score) -> str:
    """The normalized 0-100 selection score, or an em dash when unscored."""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "<span class='vchip'>—</span>"
    return f"<span class='vchip'>{value:.1f}<span class='sub'> / 100</span></span>"


def stage_metric_keys(stages: list[dict]) -> list[str]:
    """Which legend entries a run's summary justifies (by key name)."""
    keys: list[str] = []
    seen: set[str] = set()

    def add(key: str) -> None:
        if key in METRICS and key not in seen:
            seen.add(key)
            keys.append(key)

    def walk(value, prefix: str = "") -> None:
        if isinstance(value, dict):
            for nested_key, nested in value.items():
                walk(nested, nested_key)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            add(prefix)

    for stage in stages or []:
        if not isinstance(stage, dict):
            continue
        for key, value in stage.items():
            if key in ("tables", "charts", "viewer", "notes", "steps", "reference"):
                continue
            walk(value, key)
    return keys
