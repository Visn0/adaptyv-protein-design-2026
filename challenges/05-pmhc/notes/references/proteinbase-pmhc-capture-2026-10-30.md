# Proteinbase challenge page — full text capture (2026-10-30)

Source: https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc
Method: `curl -sS -A "Mozilla/5.0 …"` of the page, then the double-escaped
RSC/flight payload decoded and all visible text strings extracted in page
order. This file keeps the page text verbatim (minus navigation strings).

Target payload with sequences and structure files:
`pmhc-targets-2026-10-30.json`.

---

KRAS G12D pMHC

KRAS G12D peptide VVVGADGVGK on HLA-A*11:01

Design a mutation-specific pMHC binder

Cells that carry the KRAS G12D mutation can show T cells a ten-residue piece of the mutant protein, VVVGADGVGK, in the groove of the MHC molecule HLA-A*11:01. The wild-type stretch, VVVGAGGVGK, has a glycine where the mutant has an aspartate, so the two peptides differ at one position of ten and sit in the same groove. This challenge asks for three things: bind the G12D complex, do not bind the wild-type one, and do not bind the same HLA with no peptide in it.

Submissions are open until Sunday, November 8, 23:59 AoE.

KRAS G12D peptide on HLA-A*11:01 · PDB 7OW6

Target information

Design against the whole peptide-MHC complex: the HLA-A*11:01 heavy chain, β2-microglobulin and a ten-residue peptide held in the groove. We recommend targeting the peptide and the groove around it, the surface a T-cell receptor reads. The rest of the complex is the same for both peptides, and the same again with no peptide, so a binder that sits there cannot tell them apart.

This challenge consists of 3 main objectives, and each will be accounted for when selecting the best designs.

Binding affinity

Design a binder against the KRAS G12D peptide presented by HLA-A*11:01. We recommend targeting the peptide and the groove around it, which is the surface a T-cell receptor reads and the only part that differs from the same HLA carrying another peptide.

We'll measure its binding affinity using the complex of HLA-A*11:01, β2-microglobulin and VVVGADGVGK.

human KRAS G12D pMHC

Mutation specificity

On top of that, your binder must not bind the same HLA-A*11:01 carrying the wild-type KRAS peptide VVVGAGGVGK. The two peptides are identical except at position 6, residue 12 of KRAS, where the mutant has an aspartate and the wild type a glycine.

A binder that cannot tell them apart cannot single out cells that carry the mutation. For this, we will measure binding against the wild-type complex in the same conditions as the G12D one.

How designs are ranked

Every tested design is measured against all three targets in the same conditions: the KRAS G12D complex, the wild-type KRAS complex and the HLA-A*11:01 with β2-microglobulin that carries no peptide, with the design immobilised and the target in solution. A design counts as binding a target when its sensorgram gives a fittable curve and a KD, or, where the curve cannot be fitted, when the association shift clears 300% over the negative control. Otherwise we call it no detectable binding.

A measurable KD against the KRAS G12D complex and no detectable binding to the wild-type KRAS complex. Designs that bind both rank after these, by the ratio of their KD for the wild-type complex to their KD for the G12D complex, largest first.

Peptide-dependent binding

A measurable KD against the KRAS G12D complex and no detectable binding to the peptide-free HLA-A*11:01 with β2-microglobulin. Designs that bind it rank after these, by the ratio of their KD for the peptide-free target to their KD for the G12D complex, largest first. A binder that reads the HLA or the β2-microglobulin instead of the peptide binds all three targets and ranks there.

Affinity

Lowest KD against the KRAS G12D complex. A design that binds the peptide and the groove around it has an advantage. Tell us which surface you target and link your evidence. If you don't, we take it from a predicted complex. A design that binds somewhere else is still measured and ranked.

The winner has to clear all three steps, with ties settled in this order, and each step also awards an honourable mention to the best design that did not win.

Timeline

Oct 26 – Nov 8, 2026

now

Submissions open

Design, review, and submit. Submissions close Sunday, November 8 at 23:59 Anywhere on Earth (AoE).

Submissions closed

The window is closed. No further designs are accepted for this challenge.

Selection in progress

Anthropic and Adaptyv select designs for synthesis using a Claude-based workflow, published after the competition.

Wet-lab validation in progress

Selected designs go to Adaptyv's automated lab for experimental validation.

Submission requirements

Length

10–250 amino acids

Format

Single chain protein, nanobody, scFv, or Fab

Designs per participant

Up to 40 for Track 1, up to 20 for Tracks 2 and 3

Design

De novo designs only

Position 6, where the two peptides differ, sits in the mobile middle of the peptide. 7OW4, the G12D crystal without a T-cell receptor, has no coordinates for positions 5 and 6. With a receptor bound (7OW6), the aspartate is tucked against Arg114 and Gln70 of the HLA (PDB numbering). The viewer shows the receptor-bound crystals 7OW6 (G12D) and 7OW5 (wild type; Poole et al., Nat Commun 2022) with the receptor deleted, and the peptide too for the third target. The complexes' His and Avi tags (not shown) and your design's C-terminal Twin-Strep capture tag are off limits: binding to a tag does not count.

wild-type KRAS pMHC

Finally, your binder must not bind the same HLA-A*11:01 and β2-microglobulin when the groove holds no peptide. A binder that sticks to the heavy chain or to β2-microglobulin binds every peptide on this HLA, those of healthy cells included, and tells us nothing about the peptide it was made for.

For this, we will measure binding against the peptide-free HLA-A*11:01 with β2-microglobulin in the same conditions as the other two.

peptide-free MHC

Results published

Every measurement, including the failures, is on Proteinbase with sequences and methods.

Frequently asked questions

We recommend providing this FAQs list to your Claudes. We expect to update this document throughout the competition as more FAQs emerge.

What classes of molecules can be designed and submitted?

De novo proteins (including minibinders, larger proteins, and microbinders), nanobodies, and antibodies can be submitted. Importantly:

For single chain proteins, the minimum length is 10 amino acids and the maximum length is 250 amino acids.

ANARCI

How will different classes of molecules be evaluated?

We will stratify performance into five molecule categories:

Protein minibinders: Proteins consisting of between 40 and 100 amino acids (inclusive)

Large protein binders: Proteins consisting of >100 amino acids

Protein microbinders: Proteins consisting of <40 amino acids

Nanobodies

Antibodies (formatted as either scFv or Fab, see Question 5)

What criteria will be used to determine the winners of the competition?

one winner, which has to meet every objective

one honourable mention per objective

A design counts as binding in a condition when its sensorgram gives a fittable curve and a KD, or, where the curve cannot be fitted, when the association shift clears 300% over the negative control. Challenges with other objectives (receptor activation for GLP1R, peptide specificity for the peptide-MHC challenge) state their own rules on their page. The primary goal of the competition is to show frontier protein design capabilities, which is why the winner has to meet the hard objectives and not only bind tightly.

How many designs should I submit?

If you are part of track 1, you should submit at least 20 designs and at most 40 designs. If you are part of tracks 2 or 3, you should submit at most 20 designs.

How and where should I submit my designs? Should I submit any additional information with my designs? Can I submit anonymously?

Submit your designs as a CSV ordered by how you would rank your molecules (top row higher) with, at minimum, the following columns:

name: a unique identifier

For Fabs submit as a single sequence with VH followed by VL separated by a “:” (e.g. “{VH}:{VL}”). Use molecule_class to indicate whether you intend for the light chain to be kappa or lambda.

molecule_class: one of “protein”, “nanobody”, “scfv”, “fab_kappa”, “fab_lambda”

We encourage participants to submit as much information as they are comfortable sharing, including metrics (e.g. ipTM, ipSAE, self-consistency, physics-based metrics, sequences liability scores), structure models from design and folding models, and methodologies (e.g. AI models, design models, folding models, strategies, provenance on how designs were generated). Participants are welcome to upload data to a shared repository (e.g. Google Drive, GitHub) and provide a link with their submission. One option is to ask your Claudes to write a methods paper and create a metadata package for submission. Please note that all data and methodology submitted may be made publicly available.

As described below in FAQ 8, for Tracks 2 and 3, we will provide the additional information you submit to Claude to help select designs. We expect that with more information, Claude can make more informed decisions. Please note that any use of embedded instructions or prompt injection may be deemed grounds for disqualification.

You can submit anonymously by making an anonymous Proteinbase account. If you later choose to deanonymize, you can. See FAQ 11 for more information.

challenges

When will problems be released? When should I submit my designs?

We expect to release one problem every week on Monday at approximately 9:00 AM PDT starting September 28th, 2026 and ending October 26th, 2026. Each problem is open for two weeks, so consecutive problems overlap: participants have until 23:59 Anywhere on Earth (AoE, UTC−12) on the Sunday of its second week to submit designs. Deadlines: Challenge 1: Wednesday, October 7; Challenge 2: Sunday, October 18; Challenge 3: Sunday, October 25; Challenge 4: Sunday, November 1; Challenge 5: Sunday, November 8.

How many designs will be screened?

Per problem we expect to screen ~1500 designs (50% for Track 1, 25% for Track 2, and 25% for Track 3)

How will you select which designs are screened?

There are some hard criteria or filters that will be used for all designs:

They must meet the criteria described in FAQs 1 and 2 for protein length and “nanobodyness/antibodyness”. They must also be unique (don’t submit the same design multiple times).

latest blog post on novelty.

Beyond the hard criteria, designs will be selected as follows:

For Track 1 participants, their top 20 designs that pass filtering will be screened. We encourage Track 1 participants to send their sequences already ordered by the ranking method they (preferably) describe in their methods.

For Track 2 and 3 participants, all submitted designs will be pooled together along with submitted information and provided to Claude along with a design selection prompt written in advance by Anthropic and Adaptyv. The prompt will make selections based on predicted design quality and novelty, as well as method novelty. Per problem, a total of ~375 designs will be selected for each of tracks 2 and 3.

selection page

How will I know if my designs were selected for screening?

How do I submit my designs?

What if I want to submit anonymously?

This is allowed and you’ll only need to create an anonymous Proteinbase account. It is highly recommended to reveal your identity/company/university afterwards, but we understand that there are circumstances where this would not be possible.

What experimental data will be generated? When and how will experimental data be released?

This competition measures binding and affinity, but with twists. In addition to binding against the human target, for some targets we plan to measure binding in acidic pH environments as well as against the mouse ortholog to measure cross-reactivity. For the peptide-MHC complex we will screen against relevant off-targets. For the GPCR we measure binding, and confirmed binders are then tested in a functional assay for receptor activation. A design has to be a confirmed agonist to count. Specific conditions per challenge will be communicated in each challenge’s competition page once it is launched.

Proteinbase Slack channel

Do I have to use Claude? Can I use other AI tools?

While we strongly encourage participants, especially those in Tracks 1 and 2, to use Claude, you may use other AI tools. Any AI tools or design models used can be disclosed in the submission form.

What happens to unused Claude or Modal credits after the competition?

Unused credits expire at the end of the competition. Claude Max plans will expire approximately three months after the competition begins. We want to see what you can do with this compute so please use it!

What tools and resources may I use for design?

Neither Anthropic nor Adaptyv seek to impose any additional restrictions on tools that can be used. As long as you can access the tool appropriately (e.g. you are not violating licenses), you may use the tool. You may use both externally available tools such as open-source folding and design models, or internal-only tools. For any commercially-licensed tools (e.g., Rosetta), we require that you own that specific license beforehand.

In addition to the Claude and Modal credits provided for this competition, you may use any other resources (e.g. in-house GPU clusters) you have access to.

Who owns the IP for all designs and validated sequences?

Official Competition Terms

Should I disclose any proprietary methods or tools?

We recommend that all participants describe in detail the methods and tools they are using, linking to any papers, articles, technical reports that they based their work on. These details will be used when selecting designs to be validated, ensuring novel methods without prior experimental validation will be fairly represented in the competition. This information will be made public in the Proteinbase Collection, thus we understand if there are details that you will not prefer disclosing (e.g. a proprietary tool).

How will the data generated in this competition be used by Anthropic and Adaptyv?

RBX1 competition

Inputs to and outputs from Claude will be governed by the Terms of Service applicable to the participant’s Anthropic account.

Are there any resources you recommend we review?

Some resources from our teams that we can point you to are:

Adaptyv’s blog

EGFR competition post-analysis paper

Anthropic’s blog post on protein design

technical report

experimental data for the protein design campaign

Anthropic’s blog post on uplifting biomolecular modeling

code

We strongly recommend you use the inference-optimized models to maximize GPU compute and review the significantly simplified binder design prompt in the technical report.

What if I have more questions?

Join us on the Proteinbase Slack channel

Challenge 05: KRAS G12D pMHC | Proteinbase
