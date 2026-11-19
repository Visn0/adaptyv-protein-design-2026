# Viewpoint render review: mce-14 family and v6

Scope: headless Mol* renders under `challenges/02-tnfa/viewers/views/`. Four new
dirs (`mce-14-mouse`, `mce-14-human`, `v6-mouse`, `dsmce14v3-mouse`), each with
9 PNGs (cartoon, surface, interface x 3 viewpoints) and `manifest.json`. The v6
human-target render in `views/e1b-d7x-t3-3-v6/` already existed and is reviewed
below for comparison.

Conventions in every render: binder is chain A (pink); the TNF trimer is chains
B/C/D (cyan family). Interface mode marks residues in 4.5 A heavy-atom contact
as amber ball-and-stick, on BOTH molecules. Contact counts and chain letters
come from each dir's `manifest.json`. Every claim below names the PNG it came
from. Each fold has its own coordinate frame, so the same view number is not
the same physical direction across dirs.

## mce-14 on mouse TNF (best mouse ipSAE 0.847; 5/5 samples at the designed interface)

- Where it sits: the binder is at the edge of the trimer. Amber contacts bridge
  a darker blue chain and a teal chain, so the contact spans the junction of two
  protomers (`mce-14-mouse_interface_view1.png`, zoom of that file).
- Manifest: 38 interface residues. 17 on the binder (positions 7-46), 14 on one
  protomer, 7 on another. The third protomer is not contacted.
- Contact character: the amber band runs along one long face of the binder and
  looks continuous along that stretch, not patchy
  (`mce-14-mouse_interface_view2.png`).
- Binder shape: an elongated multi-helix element (helix hairpin), lying along
  the trimer edge (`mce-14-mouse_cartoon_view1.png`, `_view2.png`).
- Closeness: in `mce-14-mouse_cartoon_view0.png` a cyan loop crosses in front of
  the pink binder, so the binder is tucked close against the trimer there.
- Surface: from the far side the binder is almost fully occluded, only a tip
  shows below the trimer edge (`mce-14-mouse_surface_view0.png`). From the
  binder side most of its surface is exposed, attached along one side
  (`mce-14-mouse_surface_view1.png`, `_view2.png`). At the seam the two
  surfaces interlock with bumps and notches (`mce-14-mouse_surface_view2.png`).
- From `mce-14-mouse_interface_view0.png` the binder is mostly behind the
  trimer, with the amber contact cluster visible between cyan sheets.

## mce-14 on human TNF (best human ipSAE 0.852; 5/5 samples at the designed interface)

- Where it sits: same arrangement as on mouse. Amber bridges two cyan shades at
  the protomer junction (`mce-14-human_interface_view1.png`, zoom of that file).
- Manifest: 40 interface residues. 19 on the binder (positions 7-46, i.e. two
  more positions than mouse), 13 on one protomer, 8 on another.
- Contact character: amber spread along the binder's contact face over a long
  stretch, contiguous (`mce-14-human_interface_view2.png`).
- Binder shape: helical hairpin, hugging the trimer's lower edge
  (`mce-14-human_cartoon_view1.png`); from another angle the hairpin sits at the
  edge with a visible gap in that projection (`mce-14-human_cartoon_view2.png`).
- From `mce-14-human_cartoon_view0.png` the binder is mostly hidden behind the
  trimer (only pink segments show between cyan sheets); in
  `mce-14-human_surface_view0.png` only a small pink sliver shows at the right
  edge.
- Surface: binder largely exposed from its own side, attached along one face
  where a blue chain and a teal chain meet
  (`mce-14-human_surface_view1.png`); interlocking notches at the seam
  (`mce-14-human_surface_view2.png`).

## v6 on mouse TNF (mouse ipSAE 0.632; human record 0.871)

- Where it sits: at the trimer's rim, but the binder is more perched than in
  the mce-14 renders. In `v6-mouse_cartoon_view0.png` the long helix is angled
  up and away from the trimer with a clear black gap under most of its length;
  only its lower-left end is near the trimer.
- Manifest: 35 interface residues. 16 on the binder (positions 7-46), 13 on one
  protomer, 6 on another. Again a two-protomer contact.
- Interface: amber runs along the binder's lower face
  (`v6-mouse_interface_view1.png`, `v6-mouse_interface_view2.png`). In
  `v6-mouse_interface_view0.png` amber sits on both the binder underside and
  the trimer top edge; the zoom of that file shows the two amber sets
  approaching each other, with open space beside them where the binder tilts
  away.
- Binder shape: a long helix plus a shorter helix at an angle (a bent element,
  not a tight hairpin) (`v6-mouse_cartoon_view0.png`, `_view1.png`).
- Surface: the binder sits on top of the trimer rim, roughly half its surface
  exposed, not sunk in a groove (`v6-mouse_surface_view0.png`,
  `v6-mouse_surface_view1.png`). It attaches where a blue and a teal chain meet
  (`v6-mouse_surface_view2.png`).
- `v6-mouse_cartoon_view2.png`: binder perched at the top of the trimer,
  extending free to the left.

## ds-mce-14-v3 on mouse TNF (tightest mouse spread 0.835-0.860)

- Where it sits: same junction geometry as mce-14. The binder zigzag crosses
  the trimer's face diagonally, with amber along its length and cyan shades of
  two protomers behind the amber (`dsmce14v3-mouse_interface_view1.png`).
- Manifest: 38 interface residues. The 17 binder contact positions are
  IDENTICAL to the mce-14 mouse fold (7, 10, 14, 21, 26, 29, 30, 33, 34, 36,
  37, 38, 40, 41, 44, 45, 46); 14 on one protomer, 7 on another.
- Contact character: a dense amber cluster along the binder's right side over
  about half its length (`dsmce14v3-mouse_interface_view2.png`); amber along
  its left face in `dsmce14v3-mouse_interface_view0.png`.
- Binder shape: multi-helix zigzag standing along the trimer's right edge, top
  helix extending free (`dsmce14v3-mouse_cartoon_view0.png`, `_view1.png`).

## v6 on human TNF (existing render in views/e1b-d7x-t3-3-v6/; human ipSAE 0.871)

- Where it sits: the binder lies flat across the trimer's lower face, hugging
  it (`e1b-d7x-t3-3-v6_cartoon_view0.png`). Cyan loops drape in front of it in
  places, so it is tucked close to the surface.
- Manifest: 34 interface residues. 16 on the binder (positions 10-46), 11 on
  one protomer, 7 on another. Two-protomer contact again.
- Contact character: a dense amber band runs the full height between the
  binder's right edge and the trimer edge, with no visible gap
  (`e1b-d7x-t3-3-v6_interface_view1.png`).
- Contact distribution: dense at the binder's left/central region; the right
  half of the helix extends free with sparse amber
  (`e1b-d7x-t3-3-v6_interface_view2.png`).
- `e1b-d7x-t3-3-v6_interface_view0.png`: binder horizontal across the trimer
  face; densest amber at its left end and along its upper side.
- `e1b-d7x-t3-3-v6_cartoon_view1.png`: binder stands alongside the trimer
  edge, full height against it, outer side exposed.

## Comparison

### mce-14 human vs mouse: recognizably the same pose

- Same arrangement in both: multi-helix binder at the trimer edge, amber band
  along one long face, contact on two protomers. Compare
  `mce-14-human_interface_view1.png` with `mce-14-mouse_interface_view1.png`;
  both show the same kind of contact pattern.
- Binder region engaged is nearly the same: positions 7-46 on both (manifest
  files). Human adds positions 24, 25, 27, 43; mouse adds 38 and 45. I could
  not see that difference by eye.
- The absolute angles in the images differ, but that is because each fold has
  its own coordinate frame. I saw no obvious difference in tilt or depth of the
  binder against the trimer.

### mce-14 vs v6 on mouse: similar site, different posture

- Both binders are elongated helical elements contacting one face over a long
  stretch at the junction of two protomers (manifests; interface PNGs of both).
- Visible difference: v6-mouse's binder stands off the surface more. In
  `v6-mouse_cartoon_view0.png` there is a black gap under most of the helix,
  while in `mce-14-mouse_cartoon_view0.png` a trimer loop crosses in front of
  the binder, meaning it is tucked close.
- In interface mode the difference is modest. Both show a long amber band
  (`v6-mouse_interface_view1.png` vs `mce-14-mouse_interface_view2.png`). Be
  honest: the contact footprints look similar; the posture (tilt/standoff) is
  the main visible difference.

### v6 human vs v6 mouse: the clearest pose difference in this set

- On human the binder lies flat along the trimer face
  (`e1b-d7x-t3-3-v6_cartoon_view0.png`, `e1b-d7x-t3-3-v6_interface_view0.png`).
  On mouse it is angled away with a visible standoff
  (`v6-mouse_cartoon_view0.png`, `v6-mouse_interface_view0.png`).
- The mce-14 renders look closer to the v6-human style (tucked against the
  trimer) than to the v6-mouse style (perched). Cite:
  `mce-14-mouse_cartoon_view0.png` and `mce-14-human_cartoon_view1.png`.

## Caveats

- These images show geometry and contacts, not affinities. A fold is a model.
  The ipSAE numbers come from scoring, not from these pictures.
- Vision cannot judge small score differences. mce-14 mouse (0.847) vs human
  (0.852), or the ds-mce-14-v3 mouse spread (0.835-0.860), are not visible in
  these renders. `mce-14-mouse_interface_view1.png` and
  `dsmce14v3-mouse_interface_view1.png` show near-identical contact geometry,
  yet their scores differ slightly.
- Do not read pose quality from a single projection. Each fold has its own
  coordinate frame, so identical view numbers point in different directions in
  different dirs. The comparisons above rely on binder-versus-trimer
  arrangement and depth ordering (which element occludes which).
- Chain letters differ between folds. In every render the binder contacts two
  of the three protomers; which letters carry those contacts differs per file
  (each `manifest.json`). The design brief requires the two halves of the
  epitope to touch the binder on different protomers
  (`notes/genie3-feasibility.md`); all five poses meet that cross-protomer
  geometry at the fold level.
- Amber marks 4.5 A heavy-atom contacts computed from the structure
  (`manifest.json`), not measured binding.
- Surface mode colors chains, not chemistry. No hydrophobic-versus-charged
  texture can be read from these PNGs; that would need the hydrophobicity mode.
- The dark patches on surface renders are openings in the medium-quality
  surface mesh showing the dark interior, not binder features
  (`mce-14-mouse_surface_view0.png`, `mce-14-human_surface_view0.png`).
- Every observation above names its PNG. Anything not named was not claimed.
