# Linkage check outcome (2026-10-17)

All five lineage complexes scored with the vendored linkage scorer (PROPKA).
Wanted sign: delta_log_Ka > 0 (tighter at pH 7.4). Result: ALL NEGATIVE.

| design | delta_log_Ka | fold_selectivity | sites |
|---|---|---|---|
| ds-mce-14-v6-human | -0.113 | 0.8 | 2 |
| v6-human | -0.167 | 0.7 | 1 |
| ds-mce-14-v6-mouse | -0.712 | 0.2 | 2 |
| ds-mce-14-v7-mouse | -0.946 | 0.1 | 3 |
| mce-14-mouse | -0.991 | 0.1 | 4 |

Reading: the lineage does not just lack a pH switch — its natural linkage runs
the wrong way (tighter at pH 6.0). Small on human targets (~1.3-1.4x), strong
on mouse targets (5-10x). The scorer is rank-grade and conservative by about
two orders against the FcRn reference, so the magnitudes are indicative only;
the SIGN is the informative result.

Consequence for C2 (objectives ranked: 1 pH switch, 2 mouse cross-reactivity,
3 affinity): the current lineage cannot claim objective 1 and would likely
fail "no detectable binding at pH 6.0" outright. It competes on objectives 2
and 3 only. A pH-switch retrofit (place histidines facing the target cation
triad A103/B103/B112 on these backbones, re-fold, re-score) is a new design
experiment - not started.
