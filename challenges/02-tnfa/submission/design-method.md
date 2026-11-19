# Design method — as entered on the submission page

Method name: **Genie 3 + ProteinMPNN + Boltz-2**

## Description (general pipeline / reasoning)

De-novo single-chain mini-binders for the released TNF-α problem (the B102/D62
junction between two protomers). Genie 3 generates the backbones; full-backbone
ProteinMPNN designs the sequences (sequence design on CA atoms alone caps every
design low — the full backbone is the working configuration); Boltz-2 co-folds
each design with the target and IPSAE scores the interface at the designed
site. Cross-reactivity is selected for, not checked: candidates are folded
against the mouse protein first and the human protein second. The submitted set
is the product of a directed-evolution loop (mutate the previous winners, fold,
keep what improves) plus a histidine retrofit that gives the pH switch.

## Configuration (workflow, parameters, settings)

Genie 3: released checkpoint, problem 10_tnfa (hotspots B102 + D62).
ProteinMPNN: full-backbone model, sampling T = 0.1/0.3, multiple seeds;
fixed-position mode for the evolution rounds (3 free positions per variant).
Boltz-2 2.2.1: 5 diffusion samples per design, seed 42, MSA server; local
RTX 5070. IPSAE: 10 Å PAE cutoff, at-site screen at the designed two-protomer
junction. Mouse cross-reactivity: mouse construct P06804 85–235, selected
mouse-first. pH switch: histidine placed against an interface lysine from the
fold geometry; the lead design converts the Glu33 salt bridge to a histidine
(E33H).
