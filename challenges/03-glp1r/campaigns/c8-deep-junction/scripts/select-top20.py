#!/usr/bin/env python3
"""Our own selection run for Challenge 3, modeled on the organizers' prompt.

The organizers select by: (1) a real chance to express and bind, (2) evidence
for the hardest goal (for GLP1R: activation), (3) method novelty and diversity,
(4) no single in silico metric deciding. Three screens are recorded per design:
pLDDT, ipSAE, mean Kyte-Doolittle hydropathy.

Rubric (each criterion scored 0-5 in whole and half points; activation-first
weights, because activation is the hardest goal):

  A - activation evidence (the gate): 6/6 with strong pose agreement = 5,
      6/6 with weaker agreement = 4, 5/6 = 3.5, 4/6 = 2, shelf = 1.5,
      groove = 1, wrong_face = 0. Depth > 30 A (a wrapping pose) costs 1.
  B - binding: ipSAE >= 0.90 = 5, >= 0.85 = 4, >= 0.80 = 3, >= 0.75 = 2,
      else 1; +0.5 for pDockQ2 >= 0.30 (cap 5).
  E - expression/solubility: mean of the pLDDT band (>=70=5, >=60=4, >=50=3,
      else 2) and the hydropathy band (-0.5..0.5=5, -1..1=4, else 3).
  R - reach (the activation path): (groove/6 + tm/4 + ecl3/8) / 3 * 5.

  total = 2.0*A + 1.5*B + 1.0*E + 0.5*R

Selection: rank by total; keep at most 5 per method family (soft diversity,
as the organizers cap families); take the best 20.
"""
from __future__ import annotations

import csv
import collections
import datetime
import itertools
import math
import pathlib

WORK = pathlib.Path.home() / "c3-work"
# The repo-side score record the workbench reads. One writer: the score shown on a
# campaign page cannot drift from the selector that produced it.
REPO = pathlib.Path(__file__).resolve().parents[5]
RECORD_DIR = REPO / "challenges" / "03-glp1r" / "records"
KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
      "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
      "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}


FAMILIES = {
    "e1": "rfd3-miniprotein", "e1b": "rfd3-miniprotein", "e1b2": "rfd3-miniprotein",
    "e3": "rfd3-miniprotein", "c1": "rfd3-miniprotein",
    "c2": "evobind-peptide",
    "c3": "boltzgen-peptide", "c4": "boltzgen-peptide",
    "c5": "bindcraft2-peptide",
    "c6": "solublemnn-resequenced",
    "c7": "boltzgen-long-peptide",
    "c8": "boltzgen-junction",
    "c9": "solublemnn-c3",
    # The three RFD4-Proteina rounds. Named so the cap and the verdicts can speak
    # about them; note c12-mpnn-* designs share the "c12" prefix and so count in
    # the same family as bare c12-* under the split-on-first-dash rule.
    "c12": "rfd4-proteina",
    "c13": "rfd4-junction",
    "c14": "rfd4-short-band",
}

# One normalized score, comparable across campaigns, instead of a verdict label.
# total = 2.0*A + 1.5*B + 1.0*E + 0.5*R with each component capped at 5.0.
SCORE_WEIGHTS = {"A": 2.0, "B": 1.5, "E": 1.0, "R": 0.5}
COMPONENT_MAX = 5.0
MAX_TOTAL = sum(SCORE_WEIGHTS.values()) * COMPONENT_MAX  # 25.0


def normalized(total: float) -> float:
    """`total` rescaled to 0-100."""
    return round(100.0 * total / MAX_TOTAL, 1)


# The quality floors the methodology promises. They used to be applied by hand to
# the chosen twenty, so the selector could and did return designs below them -
# including a 24-residue poly-alanine tract that scored 88.4.
PLDDT_FLOOR = 63.0
PDOCKQ2_FLOOR = 0.18
MIN_ENTROPY = 2.5          # bits over the residue distribution
MAX_TOP_SHARE = 0.45       # share of the single most common residue
MAX_HOMOPOLYMER = 6        # longest run of one residue


def low_complexity(seq: str) -> bool:
    """True for a repeat-rich sequence that scoring alone does not catch."""
    if not seq:
        return True
    counts = collections.Counter(seq)
    n = len(seq)
    entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())
    run = longest = 1
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if a == b else 1
        longest = max(longest, run)
    return (entropy < MIN_ENTROPY
            or max(counts.values()) / n > MAX_TOP_SHARE
            or longest >= MAX_HOMOPOLYMER)


def quality_fail(row, seqs) -> list[str]:
    """Why a design is ineligible, or an empty list if it clears every floor."""
    why = []
    if float(row["plddt"]) < PLDDT_FLOOR:
        why.append(f"pLDDT {float(row['plddt']):.1f} < {PLDDT_FLOOR:.0f}")
    if float(row["pdockq2"]) < PDOCKQ2_FLOOR:
        why.append(f"pDockQ2 {float(row['pdockq2']):.3f} < {PDOCKQ2_FLOOR}")
    if low_complexity(seqs.get(row["design"], "")):
        why.append("low-complexity sequence")
    return why


TARGET_PICKS = 20
FAMILY_CAP = max(1, round(0.25 * TARGET_PICKS))  # the note's 25% per track

_unmapped: set = set()


def family(name):
    """Campaign family for the diversity cap.

    The prefix is the text before the first "-", matched exactly. The old
    ``startswith("c1-")`` ladder matched no campaign numbered 10 or above, so
    every c12/c13/c14 design fell through to one shared "other" bucket and the
    per-family cap discarded most of them. This is AGENT.md mistake 1 again:
    anchor the match, never prefix-match an id.

    An unmapped prefix becomes its own family rather than sharing one bucket,
    so a new campaign is capped on its own merits and stays visible.
    """
    prefix = name.split("-", 1)[0]
    fam = FAMILIES.get(prefix)
    if fam is None:
        if prefix not in _unmapped:
            _unmapped.add(prefix)
            print(f"warning: campaign prefix {prefix!r} is not in FAMILIES; "
                  "treating it as its own family")
        return prefix
    return fam


def load_screen():
    """design -> best sample row by ipSAE (from the shared screen table)."""
    best = {}
    for r in csv.DictReader(open(WORK / "folds-screen.csv")):
        d = r["design"]
        if d not in best or float(r["ipsae"]) > float(best[d]["ipsae"]):
            best[d] = r
    return best


def load_gate():
    """design -> {met, tier, depth, deep_samples, samples} (best sample)."""
    gate = {}
    if (WORK / "c8-agonism/rescore-summary.csv").exists():
        for r in csv.DictReader(open(WORK / "c8-agonism/rescore-summary.csv")):
            gate[r["design"]] = {"met": int(r["features"]), "tier": r["best_tier"],
                                 "depth": float(r["depth"]),
                                 "deep": int(r["deep_samples"]), "samples": int(r["samples"])}
    # campaigns 8 and 9: per-sample rows, aggregate here
    order = {"deep": 0, "shelf": 1, "groove": 2, "wrong_face": 3}
    for fname in ("c8-gate-rows.csv", "c9-gate-rows.csv"):
        path = WORK / "c8-agonism" / fname
        if not path.exists():
            continue
        per = collections.defaultdict(list)
        for r in csv.DictReader(open(path)):
            per[r["design"]].append(r)
        for d, rs in per.items():
            b = min(rs, key=lambda r: (order[r["tier"]], -int(r["met"])))
            gate[d] = {"met": int(b["met"]), "tier": b["tier"], "depth": float(b["depth"]),
                       "deep": sum(1 for r in rs if r["tier"] == "deep"),
                       "samples": len(rs)}
    return gate


def load_sequences():
    seqs = {}
    for y in (WORK / "folds").glob("*.yaml"):
        txt = y.read_text().splitlines()
        for i, l in enumerate(txt):
            if l.strip() == "id: A":
                seqs[y.stem] = txt[i + 1].split("sequence:")[1].strip()
                break
    return seqs


def score_design(name, srow, gate, seqs):
    ipsae = float(srow["ipsae"])
    pdq = float(srow["pdockq2"])
    plddt = float(srow["binder_plddt"])
    seq = seqs.get(name, "")
    hydro = sum(KD.get(a, 0) for a in seq) / len(seq) if seq else 0

    # A - activation evidence
    g = gate.get(name)
    A = 0.0
    agon = "none"
    met = None
    if g:
        agree = g["deep"] / max(g["samples"], 1)
        if g["met"] >= 6:
            A = 5.0 if agree >= 0.8 else (4.5 if agree >= 0.6 else 4.0)
            if g["depth"] > 30:
                A -= 1.0
        elif g["met"] == 5:
            A = 3.5 + (0.5 if agree >= 0.8 else 0.0)
        elif g["met"] == 4:
            A = 2.0
        elif g["tier"] == "shelf":
            A = 1.5
        elif g["tier"] == "groove":
            A = 1.0
        agon = f"{g['met']}/6 d{g['depth']:.1f} {g['deep']}/{g['samples']}"
        met = g["met"]

    # B - binding
    B = 5.0 if ipsae >= 0.90 else 4.0 if ipsae >= 0.85 else 3.0 if ipsae >= 0.80 \
        else 2.0 if ipsae >= 0.75 else 1.0
    if pdq >= 0.30:
        B = min(5.0, B + 0.5)

    # E - expression / solubility
    e_plddt = 5.0 if plddt >= 70 else 4.0 if plddt >= 60 else 3.0 if plddt >= 50 else 2.0
    e_hydro = 5.0 if -0.5 <= hydro <= 0.5 else 4.0 if -1.0 <= hydro <= 1.0 else 3.0
    E = (e_plddt + e_hydro) / 2

    # R - reach
    reach = (float(srow["groove_hits"]) / 6 + float(srow["tm_hits"]) / 4
             + float(srow["ecl3_hits"]) / 8) / 3 * 5
    total = 2.0 * A + 1.5 * B + 1.0 * E + 0.5 * reach
    return {"total": round(total, 2), "score": normalized(total), "A": A, "met": met, "B": B, "E": round(E, 2), "R": round(reach, 2),
            "ipsae": ipsae, "pdockq2": pdq, "plddt": plddt, "hydro": round(hydro, 2),
            "agon": agon, "family": family(name), "verdict": srow["verdict"]}


def reason(name, s):
    bits = []
    met = s.get("met")
    if met is not None and met >= 6:
        bits.append(f"full 6/6 activation pharmacophore ({s['agon']})")
    elif met == 5:
        bits.append(f"5/6 activation pharmacophore ({s['agon']})")
    elif met is not None and met >= 3:
        bits.append(f"partial activation geometry ({s['agon']})")
    else:
        bits.append("no activation geometry")
    bits.append(f"ipSAE {s['ipsae']:.3f}, pDockQ2 {s['pdockq2']:.3f}")
    bits.append(f"pLDDT {s['plddt']:.0f}, hydropathy {s['hydro']:+.2f}")
    if "two-domain" in s["verdict"]:
        bits.append("two-domain HIT")
    return "; ".join(bits)


def near_dup(seq, kept, cutoff=0.90):
    """True if ``seq`` is >= cutoff identical to any kept equal-length sequence.

    Moved here from build-final-submission.py: that script was re-selecting with
    a filter this one did not have, so the two produced different sets of 20.
    Selection lives in one place now.
    """
    for other in kept:
        if len(other) != len(seq):
            continue
        if sum(1 for a, b in zip(seq, other) if a == b) / len(seq) >= cutoff:
            return True
    return False


def main():
    screen = load_screen()
    gate = load_gate()
    seqs = load_sequences()

    with open(WORK / "c8-agonism/gate-summary-all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["design", "met", "tier", "depth",
                                          "deep_samples", "samples"])
        w.writeheader()
        for d, g in sorted(gate.items()):
            w.writerow({"design": d, "met": g["met"], "tier": g["tier"],
                        "depth": g["depth"], "deep_samples": g["deep"],
                        "samples": g["samples"]})
    scored = []
    for name, srow in screen.items():
        s = score_design(name, srow, gate, seqs)
        s["design"] = name
        s["reason"] = reason(name, s)
        scored.append(s)
    scored.sort(key=lambda s: -s["total"])

    # every scored design, so a campaign page can show a score for any row
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    record = RECORD_DIR / f"selection-scores-{stamp}.csv"
    with record.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["design", "score", "total", "A", "B", "E", "R",
                                          "family"])
        w.writeheader()
        for row in scored:
            w.writerow({k: row[k] for k in w.fieldnames})
    print(f"wrote {record.relative_to(REPO)}: {len(scored)} scored designs")

    with open(WORK / "c8-agonism/selection-all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["design", "score", "total", "A", "B", "E", "met", "R", "ipsae",
                                          "pdockq2", "plddt", "hydro", "agon", "family",
                                          "verdict", "reason"])
        w.writeheader()
        w.writerows(scored)

    # Diversity is a PREFERENCE, not a gate. The note's "family cap 25% per
    # track" is explicitly "relaxed as needed", and a better-scoring design must
    # never be dropped in favour of a worse one. So fill by score under the cap,
    # then top up strictly by score until the submission is full. The old code
    # hard-dropped anything over a hardcoded 5 and could return fewer than 20.
    picked, per_fam, kept_seqs = [], collections.Counter(), []

    def admit(row) -> bool:
        """Take `row` unless its sequence duplicates one already kept."""
        seq = seqs.get(row["design"], "")
        if not seq or seq in kept_seqs or near_dup(seq, kept_seqs):
            return False
        kept_seqs.append(seq)
        picked.append(row)
        per_fam[row["family"]] += 1
        return True

    # Score decides. The family count is a TIE-BREAK only: designs that draw on
    # `total` are taken least-represented-family first, so diversity never costs
    # a better-scoring design its slot. FAMILY_CAP is therefore not a gate here;
    # it is kept as the reported 25 % reference line.
    eligible = []
    for row in scored:
        why = quality_fail(row, seqs)
        if why:
            row["excluded"] = "; ".join(why)
        else:
            eligible.append(row)
    blocked = len(scored) - len(eligible)
    print(f"{blocked} design(s) fail the quality floors "
          f"(pLDDT >= {PLDDT_FLOOR:.0f}, pDockQ2 >= {PDOCKQ2_FLOOR}, complexity); "
          f"{len(eligible)} eligible")

    for _total, group in itertools.groupby(eligible, key=lambda r: r["total"]):
        group = list(group)
        while group and len(picked) < TARGET_PICKS:
            group.sort(key=lambda r: per_fam[r["family"]])
            admit(group.pop(0))
        if len(picked) == TARGET_PICKS:
            break
    picked.sort(key=lambda s: -s["total"])

    print(f"{len(scored)} designs scored; top 20 selected:\n")
    print(f"{'#':>2s} {'design':26s} {'score':>6s} {'total':>6s} A    B    E    R   family")
    for i, s in enumerate(picked, 1):
        print(f"{i:2d} {s['design']:26s} {s['score']:6.1f} {s['total']:6.2f} "
              f"{s['A']:<4.1f} {s['B']:<4.1f} "
              f"{s['E']:<4.1f} {s['R']:<4.1f} {s['family']}")
    with open(WORK / "c8-agonism/selection-top20.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(picked[0]))
        w.writeheader()
        w.writerows(picked)
    print(f"\nfamilies: {dict(per_fam)}")


if __name__ == "__main__":
    main()
