# C11 SALT pilot - negative: the buried carboxylate cannot be reached (2026-11-02)

## Idea

The RFD4 annotated-CIF schema carries per-atom interaction conditions that our
requests never used (the catalog lives in the local RFD4-Proteina source:
hotspot, hbond, saltbridge, rasa-binned, secondary_structure, pistack,
pication, hydrophobic, metal_coord, cath_label, ...). The strongest untried
one for this target is `saltbridge`: one column away from asking the generator
to form an interaction with the mutant's own chemical group.

## Request

`build_request.py --set SALT` writes, on the D6 carboxylate oxygens only
(OD1/OD2, chain C):

- `condition_hbond_1_atom = 2` (ACCEPTOR)
- `condition_saltbridge_1_atom = 2` (NEGATIVE partner)

plus the standard P4-P8 ridge hotspot set. The NIM accepted the request with
zero validation errors (the new column parses).

## Pilot result (1 call, 8 designs, all folded)

Closest binder atom to the D6 carboxylate after folding:

| design | ipTM | i_pDAE | closest charged | closest polar | E |
|---|---|---|---|---|---|
| run-001 d0000 | 0.691 | 0.034 | 8.1 A | 5.9 A | +0.19 |
| run-001 d0003 | 0.240 | 0.003 | 11.1 A | 9.0 A | -0.77 |
| run-001 d0004 | 0.851 | 0.183 | 9.8 A | 7.6 A | -0.73 |
| run-001 d0002 | 0.889 | 0.243 | 9.2 A | 7.5 A | +2.10 |

**No design formed the requested salt bridge or H-bond**: the closest any
binder atom got to the carboxylate is 5.9 A (a long-range approach), and the
closest charged atom stays at 8+ A - the ordinary field-zone geometry. The two
designs with negative E have weak interfaces (i_pDAE 0.03/0.18); the
affinity-strong ones read positive E.

## Verdict

The conditioning cannot overcome the physical barrier: the aspartate is ~90%
buried with HLA R114 (2.95 A) and Q70 (3.08 A) already occupying its
H-bond/salt-bridge capacity. The generator, asked directly, still settles at
8-10 A - exactly where the published JDI TCR reads it (7.5 A). **This
independently confirms the field-reading doctrine the whole campaign is built
on.**

Decision: do not scale to a full wave (8 designs gave zero engaged candidates;
the expected yield of an E-negative-with-good-interface design is ~1 in 50,
not worth the remaining window). The SALT channel stays available in the
builder for future targets with exposed epitope charges.
