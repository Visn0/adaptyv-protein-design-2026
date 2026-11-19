#!/usr/bin/env python3
"""Stage-2 tri-state ranker: join G12D / WT / peptide-free reads, apply the
pre-registered vetoes, and rank the survivors.

Free-state note: the free structure has no peptide chain, so peptide reads
cannot exist for it. The free-state preference read is therefore the
binder-HLA interface confidence (iptm_hla / hla_read / ipdae_hla) - the only
interface present. The veto compares it with the same read in the G12D state.

Outputs: records/stage2/stage2-table.csv (full table, sorted by affinity
rank) and prints the ranked list with verdicts.
"""

from __future__ import annotations

import csv
import pathlib

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root() / "challenges" / "05-pmhc"
S1 = HOME / "c5-work" / "s1" / "s1-summary.csv"      # G12D reads
S2 = HOME / "c5-work" / "s2" / "s1-summary.csv"      # WT + free reads
SET = REPO / "records" / "stage1" / "stage1-stage2-set.csv"
OUT = REPO / "records" / "stage2" / "stage2-table.csv"

VETO_MARGIN = 0.05


def load(path):
    return {r["design"]: r for r in csv.DictReader(open(path))}


def f(row, key, default=0.0):
    try:
        v = row.get(key)
        return float(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def main() -> int:
    g12d, s2 = load(S1), load(S2)
    names = [r["design"] for r in csv.DictReader(open(SET))]
    rows = []
    for name in names:
        base = name.replace("__g12d", "")
        g, w, fr = g12d[name], s2.get(base + "__wt", {}), s2.get(base + "__free", {})
        r = {
            "design": name,
            # affinity reads (G12D state)
            "g_iptm_pep": f(g, "iptm_pep"), "g_ipdae_pep": f(g, "ipdae_pep"),
            "g_ipsae_pep": f(g, "peptide_read"), "g_share": f(g, "peptide_share"),
            "g_p6": f(g, "p6_min_dist"),
            # WT state
            "w_iptm_pep": f(w, "iptm_pep"), "w_ipdae_pep": f(w, "ipdae_pep"),
            "w_ipsae_pep": f(w, "peptide_read"),
            # free state (binder-HLA interface - the only interface present)
            "f_iptm_hla": f(fr, "iptm_hla"), "f_ipdae_hla": f(fr, "ipdae_hla"),
            "f_hla_ipsae": f(fr, "hla_read"),
            # G12D-state HLA interface (reference for the free-state veto)
            "g_iptm_hla": f(g, "iptm_hla"), "g_ipdae_hla": f(g, "ipdae_hla"),
        }
        r["d_wt_iptm"] = round(r["g_iptm_pep"] - r["w_iptm_pep"], 3)
        r["d_free_iptm"] = round(r["g_iptm_hla"] - r["f_iptm_hla"], 3)
        vetoes = []
        if r["w_iptm_pep"] > r["g_iptm_pep"] + VETO_MARGIN:
            vetoes.append("VETO-WT")
        if r["f_iptm_hla"] > r["g_iptm_hla"] + VETO_MARGIN:
            vetoes.append("VETO-FREE")
        r["verdict"] = ",".join(vetoes) if vetoes else "keep"
        r["g12d_pref"] = "yes" if r["d_wt_iptm"] > 0.1 else ("flat" if r["d_wt_iptm"] > -0.1 else "wt-pref")
        rows.append(r)

    rows.sort(key=lambda r: -r["g_iptm_pep"])
    for i, r in enumerate(rows, 1):
        r["rank_affinity"] = i

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n_veto = sum(1 for r in rows if r["verdict"] != "keep")
    n_pref = sum(1 for r in rows if r["g12d_pref"] == "yes")
    print(f"{len(rows)} designs | vetoes {n_veto} | G12D-preferring (dWT>0.1) "
          f"{n_pref} | flat {sum(1 for r in rows if r['g12d_pref']=='flat')}")
    print(f"{'#':>2s} {'design':46s} {'G12D':>5s} {'WT':>5s} {'dWT':>6s} "
          f"{'fHLA':>5s} {'dfree':>6s} pref  verdict")
    for r in rows:
        print(f"{r['rank_affinity']:2d} {r['design'][:46]:46s} "
              f"{r['g_iptm_pep']:.3f} {r['w_iptm_pep']:.3f} {r['d_wt_iptm']:+.3f} "
              f"{r['f_iptm_hla']:.3f} {r['d_free_iptm']:+.3f} "
              f"{r['g12d_pref']:7s} {r['verdict']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
