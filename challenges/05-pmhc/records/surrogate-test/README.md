# Surrogate screening test: NEGATIVE - 0 of 50 (2026-11-03)

The active-learning idea: train a model on the 634 folded designs' E-scores
and i_pDAE (sequence-composition features), then use it to pick the best of
the 1,612 never-folded designs and fold only those.

## Training (honest cross-validation)

- E_D6: 5-fold CV R2 -0.072, Spearman 0.466.
- i_pDAE: CV R2 0.014, Spearman 0.254.

The value prediction is noise; the rank correlation looked usable-but-weak.
The top-50 test settles it.

## Test result

All 50 predicted candidates were folded and scored:

- strong bar (i_pDAE >= 0.70 and E <= -1.0): **0 of 50**
- soft bar (i_pDAE >= 0.60 and E <= -0.5): **0 of 50**

The historical base rate for a folded design is roughly 5-10% on the soft
bar, and the repair rounds hit ~1 in 9. The surrogate's top tail scored
**below random**. The model's own top pick (tight-wave1 run-019 design_0001,
predicted E -4.88, far outside the training range) folded to a mediocre
interface with a positive E - its single most confident call was its single
worst miss.

## Why (consistent with the project's own lessons)

Composition features cannot see the structural quantity the E-score
measures: where the charges END UP after folding. Worse, the model learned
to prefer long, charge-rich sequences - exactly the designs whose interfaces
destabilise when folded (the C4 lesson: a too-tight/charged interface starves
itself). The old hand-made pose screen rejected these 50, and it was right.

## Close

The surrogate route is closed for this target. The sequence-level screening
priors add nothing over the calibrated structural screens; specificity and
interface quality are fold properties, and the fold remains the only filter
that tracks them (consistent with every campaign in this project). The 50
folds stay in the pool's data. What remains sufficient: generate, screen on
geometry, fold, and rank with the control-validated instruments.
