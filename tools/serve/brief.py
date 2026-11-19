"""Per-challenge briefs, shaped like the proteinbase challenge pages.

One entry per challenge folder. Keep all text short and factual.
Keys:
    subtitle     protein full name, shown under the title
    description  two to four sentences: what the challenge asks
    viewer       hero target structure: file path (relative to the challenge
                 folder) and the mono caption under the viewer
    rows         extra "Target information" rows: (label, value)
    objectives   the numbered objectives from the official brief
    ranking      the ranking order from the official brief
    requirements true: show the shared submission requirements
"""

BRIEF = {
    # Challenge 1 closed before this workspace existed and we did not take part,
    # so this entry carries the brief only — no target files, no hero viewer.
    "01-egfr": {
        "subtitle": "Epidermal growth factor receptor",
        "description": "EGFR is one of the most clinically validated targets in oncology. "
        "This challenge asks for three properties that current EGFR therapeutics reach "
        "only in part. We could not work on it: the challenge closed before this workspace existed.",
        "viewer": {"file": "inputs/target_extracellular.pdb",
                   "caption": "EGFR extracellular region with a cetuximab Fab mutant · PDB 6ARU"},
        "targets": [
            {
                "id": "human", "label": "Human EGFR", "form": "Extracellular region",
                "accession": "P00533-1", "uniprot": "https://www.uniprot.org/uniprotkb/P00533/entry",
                "residues": "25–645",
                "sequence": "LEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEVVLGNLEITYVQRNYDLSFLKTIQEVAGYVLIALNTVERIPLENLQIIRGNMYYENSYALAVLSNYDANKTGLKELPMRNLQEILHGAVRFSNNPALCNVESIQWRDIVSSDFLSNMSMDFQNHLGSCQKCDPSCPNGSCWGAGEENCQKLTKIICAQQCSGRCRGKSPSDCCHNQCAAGCTGPRESDCLVCRKFRDEATCKDTCPPLMLYNPTTYQMDVNPEGKYSFGATCVKKCPRNYVVTDHGSCVRACGADSYEMEEDGVRKCKKCEGPCRKVCNGIGIGEFKDSLSINATNIKHFKNCTSISGDLHILPVAFRGDSFTHTPPLDPQELDILKTVKEITGFLLIQAWPENRTDLHAFENLEIIRGRTKQHGQFSLAVVSLNITSLGLRSLKEISDGDVIISGNKNLCYANTINWKKLFGTSGQKTKIISNRGENSCKATGQVCHALCSPEGCWGPEPRDCVSCRNVSRGRECVDKCNLLEGEPREFVENSECIQCHPECLPQAMNITCTGRGPDNCIQCAHYIDGPHCVKTCPAGVMGENNTLVWKYADAGHVCHLCHPNCTYGCTGPGLEGCPTNGPKIPS",
                "details": [
                    ("Recommended epitope", "Domain III", None),
                    ("Structure reference", "6ARU · Chain A", "https://www.rcsb.org/structure/6ARU"),
                ],
                "viewer": {"file": "inputs/target_extracellular.pdb", "ref_label": "PDB 6ARU", "ref_url": "https://www.rcsb.org/structure/6ARU"},
            },
            {
                "id": "mouse", "label": "Mouse EGFR", "form": "Extracellular region",
                "accession": "Q01279", "uniprot": "https://www.uniprot.org/uniprotkb/Q01279/entry",
                "residues": "25–647",
                "sequence": "LEEKKVCQGTSNRLTQLGTFEDHFLSLQRMYNNCEVVLGNLEITYVQRNYDLSFLKTIQEVAGYVLIALNTVERIPLENLQIIRGNALYENTYALAILSNYGTNRTGLRELPMRNLQEILIGAVRFSNNPILCNMDTIQWRDIVQNVFMSNMSMDLQSHPSSCPKCDPSCPNGSCWGGGEENCQKLTKIICAQQCSHRCRGRSPSDCCHNQCAAGCTGPRESDCLVCQKFQDEATCKDTCPPLMLYNPTTYQMDVNPEGKYSFGATCVKKCPRNYVVTDHGSCVRACGPDYYEVEEDGIRKCKKCDGPCRKVCNGIGIGEFKDTLSINATNIKHFKYCTAISGDLHILPVAFKGDSFTRTPPLDPRELEILKTVKEITGFLLIQAWPDNWTDLHAFENLEIIRGRTKQHGQFSLAVVGLNITSLGLRSLKEISDGDVIISGNRNLCYANTINWKKLFGTPNQKTKIMNNRAEKDCKAVNHVCNPLCSSEGCWGPEPRDCVSCQNVSRGRECVEKCNILEGEPREFVENSECIQCHPECLPQAMNITCTGRGPDNCIQCAHYIDGPHCVKTCPAGIMGENNTLVWKYADANNVCHLCHANCTYGCAGPGLQGCEVWPSGPKIPS",
                "details": [
                    ("Recommended epitope", "Domain III", None),
                ],
                "viewer": {"file": "inputs/AF-Q01279-F1.pdb", "ref_label": "AlphaFold · 25–647", "ref_url": "https://alphafold.ebi.ac.uk/entry/AF-Q01279-F1"},
            },
        ],
        "rows": [("UniProt reference", "P00533-1"),
                 ("Target residues", "25–645 / 621 aa"),
                 ("Recommended epitope", "Domain III"),
                 ("Structure reference", "6ARU · Chain A")],
        "objectives": [
            ("Binding affinity",
             "Design a binder against human EGFR. Target a functional epitope such as "
             "domain III, which the antibody drugs cetuximab and panitumumab also use. "
             "We measure affinity against the full extracellular region.",
             "human EGFR"),
            ("Mouse cross-reactivity",
             "Design a binder that recognises human and mouse EGFR. We test binding "
             "against mouse EGFR at pH 7.4.",
             "human + mouse"),
            ("pH-selective binding",
             "Design a binder that binds EGFR at pH 6.5 and shows no detectable binding "
             "at pH 7.4. pH 6.5 matches the tumour microenvironment.",
             "pH 6.5 → 7.4"),
        ],
        "ranking": [
            ("pH-selective binding", "Binds at pH 6.5, no detectable binding at pH 7.4."),
            ("Mouse cross-reactivity", "One sequence binds mouse and human EGFR."),
            ("Affinity", "Affinity against human EGFR."),
        ],
        "requirements": True,
    },
    "02-tnfa": {
        "subtitle": "Tumor necrosis factor",
        "description": "TNF-α signals as a trimer, with three receptor-binding sites where "
        "its subunits meet. Antibody drugs such as adalimumab and infliximab neutralise it "
        "by blocking those sites. This challenge adds two requirements to plain binding.",
        "viewer": {"file": "inputs/1TNF.cif",
                   "caption": "Human TNF-α trimer, apo form · PDB 1TNF"},
        "targets": [
            {
                "id": "human", "label": "Human TNF-α", "form": "Soluble trimer",
                "accession": "P01375-1", "uniprot": "https://www.uniprot.org/uniprotkb/P01375/entry",
                "residues": "77–233",
                "sequence": "VRSSSRTPSDKPVAHVVANPQAEGQLQWLNRRANALLANGVELRDNQLVVPSEGLYLIYSQVLFKGQGCPSTHVLLTHTISRIAVSYQTKVNLLSAIKSPCQRETPEGAEAKPWYEPIYLGGVFQLEKGDRLSAEINRPDYLDFAESGQVYFGIIAL",
                "details": [
                    ("Assay construct", "TNA-H4211 · tag-free", "https://www.acrobiosystems.com/products/protein/tnf-alpha-human-tna-h4211"),
                    ("Recommended epitope", "Receptor-binding site between two protomers", None),
                    ("Structure reference", "1TNF · Chains A–C", "https://www.rcsb.org/structure/1TNF"),
                ],
                "viewer": {"file": "inputs/1TNF.cif", "ref_label": "PDB 1TNF", "ref_url": "https://www.rcsb.org/structure/1TNF"},
            },
            {
                "id": "mouse", "label": "Mouse TNF-α", "form": "Soluble trimer",
                "accession": "P06804", "uniprot": "https://www.uniprot.org/uniprotkb/P06804/entry",
                "residues": "80–235",
                "sequence": "LRSSSQNSSDKPVAHVVANHQVEEQLEWLSQRANALLANGMDLKDNQLVVPADGLYLVYSQVLFKGQGCPDYVLLTHTVSRFAISYQEKVNLLSAVKSPCPKDTPEGAELKPWYEPIYLGGVFQLEKGDQLSAEVNLPKYLDFAESGQVYFGVIAL",
                "details": [
                    ("Assay construct", "TNA-M52H3 · C-terminal polyhistidine tag", "https://www.acrobiosystems.com/products/protein/tnf-alpha-mouse-tna-m52h3"),
                    ("Recommended epitope", "Equivalent site on the mouse trimer", None),
                    ("Structure reference", "2TNF · Chains A–C", "https://www.rcsb.org/structure/2TNF"),
                ],
                "viewer": {"file": "inputs/2TNF.cif", "ref_label": "PDB 2TNF", "ref_url": "https://www.rcsb.org/structure/2TNF"},
            },
        ],
        "rows": [("UniProt reference", "P01375-1"),
                 ("Target residues", "77–233 / 157 aa"),
                 ("Recommended epitope", "Receptor-binding site between two protomers"),
                 ("Structure reference", "1TNF · Chains A–C")],
        "objectives": [
            ("Binding affinity",
             "Design a binder against human TNF-α. Target the receptor-binding site at "
             "the interface between adjacent protomers, which adalimumab and infliximab "
             "also use. We measure affinity against soluble trimeric human TNF-α.",
             "human TNF-α"),
            ("Mouse cross-reactivity",
             "Design a binder that recognises human and mouse TNF-α. We test binding "
             "against mouse TNF-α at pH 7.4.",
             "human + mouse"),
            ("pH-selective binding",
             "Design a binder that binds human TNF-α at pH 7.4 and shows no detectable "
             "binding at pH 6.0. pH 7.4 matches blood plasma; pH 6.0 matches the early "
             "endosome.",
             "pH 7.4 → 6.0"),
        ],
        "ranking": [
            ("pH-selective binding", "Binds at pH 7.4, no detectable binding at pH 6.0."),
            ("Mouse cross-reactivity", "One sequence binds mouse and human TNF-α."),
            ("Affinity", "Affinity against human TNF-α."),
        ],
        "requirements": True,
    },
    "03-glp1r": {
        "subtitle": "Glucagon-like peptide-1 receptor",
        "description": "GLP-1R is the incretin receptor that the GLP-1 therapeutics target. "
        "This challenge asks for an agonist: the design must bind the receptor AND activate "
        "it, and a binder that does not activate does not count.",
        "viewer": {"file": "inputs/6X18.cif",
                   "caption": "GLP-1R with the GLP-1 peptide · PDB 6X18, chain R"},
        "targets": [
            {
                "id": "human", "label": "Human GLP1R", "form": "Receptor in detergent",
                "accession": "P43220-1", "uniprot": "https://www.uniprot.org/uniprotkb/P43220/entry",
                "residues": "24–432",
                "sequence": "RPQGATVSLWETVQKWREYRRQCQRSLTEDPPPATDLFCNRTFDEYACWPDGEPGSFVNVSCPWYLPWASSVPQGHVYRFCTAEGLWLQKDNSSLPWRDLSECEESKRGERSSPEEQLLFLYIIYTVGYALSFSALVIASAILLGFRHLHCTRNYIHLNLFASFILRALSVFIKDAALKWMYSTAAQQHQWDGLLSYQDSLSCRLVFLLMQYCVAANYYWLLVEGVYLYTLLAFSVLSEQWIFRLYVSIGWGVPLLFVVPWGIVKYLYEDEGCWTRNSNMNYWLIIRLPILFAIGVNFLIFVRVICIVVSKLKANLMCKTDIKCRLAKSTLTLIPLLGTHEVIFAFVMDEHARGTLRFIKLFTELSFTSFQGLMVAILYCFVNNEVQLEFRKSWERWRLEHLHIQRDSS",
                "details": [
                    ("Assay construct", "13944-H18H-DD · N-terminal FLAG, C-terminal polyhistidine tag", "https://www.sinobiological.com/recombinant-proteins/human-glp1r-13944-h18h-dd"),
                    ("Recommended epitope", "Peptide-binding groove of the extracellular domain", None),
                    ("Structure reference", "6X18 · Chain R", "https://www.rcsb.org/structure/6X18"),
                ],
                "viewer": {"file": "inputs/6X18.cif", "ref_label": "PDB 6X18", "ref_url": "https://www.rcsb.org/structure/6X18"},
            },
        ],
        "rows": [("UniProt reference", "P43220-1"),
                 ("Target residues", "24–432 / 409 aa"),
                 ("Recommended epitope", "the peptide-binding groove (ECD)"),
                 ("Structure reference", "6X18 · chain R")],
        "objectives": [
            ("Affinity",
             "Bind human GLP-1R. Binding is measured on the detergent-solubilised receptor.",
             "human GLP1R"),
            ("Activation",
             "A confirmed agonist in a cell-based reporter assay (cAMP → luminescence), "
             "compared with untreated cells and a reference agonist.",
             "agonist, not a binder"),
        ],
        "ranking": [
            ("Affinity", "Binding against human GLP-1R."),
            ("Activation", "Confirmed agonist in the reporter assay."),
        ],
        "hints": [
            ("Activation is the hard half",
             "A binder that does not switch the receptor on does not count. Activating "
             "geometry is what separates a candidate from a strong submission."),
            ("Target the groove, not the whole receptor",
             "The recommended epitope is the peptide-binding groove of the ECD, where "
             "GLP-1 and semaglutide dock — the site the assay rewards."),
            ("The row order is the ranking",
             "The submission file is read in order: the first row is the design whose "
             "evidence we ask the organizers to weigh most."),
            ("Safety screening is automatic",
             "Every sequence passes SecureDNA screening on the hosting platform before "
             "anything reaches the wet lab."),
        ],
        "requirements": True,
    },
    "04-tfr1": {
        "subtitle": "Transferrin receptor 1 (CD71)",
        "description": "TfR1 carries iron-loaded transferrin into cells and recycles to the "
        "surface once the iron is released. Every dividing cell uses it, the blood-brain "
        "barrier expresses it highly, and antibodies against it are the most advanced way to "
        "ferry drugs into the brain.",
        "viewer": {"file": "inputs/11QC.cif",
                   "caption": "Human transferrin receptor ectodomain · PDB 11QC, chains A–B"},
        "targets": [
            {
                "id": "human", "label": "Human TfR1", "form": "Ectodomain homodimer",
                "accession": "P02786-1", "uniprot": "https://www.uniprot.org/uniprotkb/P02786/entry",
                "residues": "121–760",
                "sequence": "RLYWDDLKRKLSEKLDSTDFTGTIKLLNENSYVPREAGSQKDENLALYVENQFREFKLSKVWRDQHFVKIQVKDSAQNSVIIVDKNGRLVYLVENPGGYVAYSKAATVTGKLVHANFGTKKDFEDLYTPVNGSIVIVRAGKITFAEKVANAESLNAIGVLIYMDQTKFPIVNAELSFFGHAHLGTGDPYTPGFPSFNHTQFPPSRSSGLPNIPVQTISRAAAEKLFGNMEGDCPSDWKTDSTCRMVTSESKNVKLTVSNVLKEIKILNIFGVIKGFVEPDHYVVVGAQRDAWGPGAAKSGVGTALLLKLAQMFSDMVLKDGFQPSRSIIFASWSAGDFGSVGATEWLEGYLSSLHLKAFTYINLDKAVLGTSNFKVSASPLLYTLIEKTMQNVKHPVTGQFLYQDSNWASKVEKLTLDNAAFPFLAYSGIPAVSFCFCEDTDYPYLGTTMDTYKELIERIPELNKVARAAAEVAGQFVIKLTHDVELNLDYERYNSQLLSFVRDLNQYRADIKEMGLSLQWLYSARGDFFRATSRLTTDFGNAEKTDRFVMKKLNDRVMRVEYHFLSPYVSPKESPFRHVFWGSGSHTLPALLENLKLRKQNNGAFNETLFRNQLALATWTIQGAANALSGDVWDIDNEF",
                "details": [
                    ("Assay construct", "Ectodomain 121–760 · tag-free", None),
                    ("Recommended epitope", "Apical domain", None),
                    ("Structure reference", "11QC · Chains A–B", "https://www.rcsb.org/structure/11QC"),
                    ("Apical-domain complex", "11RN · Chain A with VP1u", "https://www.rcsb.org/structure/11RN"),
                ],
                "viewer": {"file": "inputs/11QC.cif", "ref_label": "PDB 11QC", "ref_url": "https://www.rcsb.org/structure/11QC"},
            },
            {
                "id": "mouse", "label": "Mouse TfR1", "form": "Ectodomain homodimer",
                "accession": "Q62351", "uniprot": "https://www.uniprot.org/uniprotkb/Q62351/entry",
                "residues": "123–763",
                "sequence": "RLYWADLKTLLSEKLNSIEFADTIKQLSQNTYTPREAGSQKDESLAYYIENQFHEFKFSKVWRDEHYVKIQVKSSIGQNMVTIVQSNGNLDPVESPEGYVAFSKPTEVSGKLVHANFGTKKDFEELSYSVNGSLVIVRAGEITFAEKVANAQSFNAIGVLIYMDKNKFPVVEADLALFGHAHLGTGDPYTPGFPSFNHTQFPPSQSSGLPNIPVQTISRAAAEKLFGKMEGSCPARWNIDSSCKLELSQNQNVKLIVKNVLKERRILNIFGVIKGYEEPDRYVVVGAQRDALGAGVAAKSSVGTGLLLKLAQVFSDMISKDGFRPSRSIIFASWTAGDFGAVGATEWLEGYLSSLHLKAFTYINLDKVVLGTSNFKVSASPLLYTLMGKIMQDVKHPVDGKSLYRDSNWISKVEKLSFDNAAYPFLAYSGIPAVSFCFCEDADYPYLGTRLDTYEALTQKVPQLNQMVRTAAEVAGQLIIKLTHDVELNLDYEMYNSKLLSFMKDLNQFKTDIRDMGLSLQWLYSARGDYFRATSRLTTDFHNAEKTNRFVMREINDRIMKVEYHFLSPYVSPRESPFRHIFWGSGSHTLSALVENLKLRQKNITAFNETLFRNQLALATWTIQGVANALSGDIWNIDNEF",
                "details": [
                    ("Assay construct", "Ectodomain 123–763 · tag-free", None),
                    ("Recommended epitope", "Equivalent site on the mouse apical domain", None),
                    ("Identity to human", "499 of 639 aligned residues (78%)", None),
                ],
                "viewer": {"file": "inputs/AF-Q62351-F1.pdb", "ref_label": "AlphaFold · 123–763", "ref_url": "https://alphafold.ebi.ac.uk/entry/AF-Q62351-F1"},
            },
        ],
        "rows": [("UniProt reference", "P02786-1"),
                 ("Target residues", "121–760 / 640 aa"),
                 ("Recommended epitope", "the apical domain"),
                 ("Structure reference", "11QC · chains A–B")],
        "objectives": [
            ("Binding affinity",
             "Design a binder against human TfR1, preferably at a functional epitope such as "
             "the apical domain, so transferrin can still dock and the receptor keeps "
             "recycling. Binding is measured on the soluble ectodomain homodimer.",
             "human TfR1"),
            ("Mouse cross-reactivity",
             "Bind mouse TfR1 as well as human at pH 7.4. The two ectodomains are 78% "
             "identical and the apical patch differs at six of nine positions.",
             "human + mouse"),
            ("pH-selective binding",
             "A measurable KD against human TfR1 at pH 7.4 and no detectable binding at "
             "pH 6.0 — the same direction as the TNF-α challenge.",
             "pH 7.4 → 6.0"),
        ],
        "ranking": [
            ("pH-selective binding", "Binds at pH 7.4, no detectable binding at pH 6.0."),
            ("Mouse cross-reactivity",
             "Mouse-to-human KD ratio close to 1, among designs with human KD below 1 µM."),
            ("Affinity", "Lowest KD against human TfR1 at pH 7.4."),
        ],
        "requirements": True,
    },
    "05-pmhc": {
        "subtitle": "KRAS G12D peptide on HLA-A*11:01",
        "description": "Cells that carry the KRAS G12D mutation display a ten-residue "
        "piece of the mutant protein in the groove of HLA-A*11:01. The wild-type peptide "
        "differs at one position of ten. This challenge asks for three things: bind the "
        "G12D complex, do not bind the wild-type one, and do not bind the same HLA with "
        "no peptide in it.",
        "viewer": {"file": "inputs/7OW6-G12D-noTCR.pdb",
                   "caption": "KRAS G12D pMHC · PDB 7OW6, TCR removed"},
        "targets": [
            {
                "id": "kras-g12d", "label": "KRAS G12D pMHC", "form": "Peptide–MHC complex",
                "accession": "Q5S3G3", "uniprot": "https://www.uniprot.org/uniprotkb/Q5S3G3/entry",
                "residues": "25–305",
                "sequence": "GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQTDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQITKRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEITLTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT",
                "details": [
                    ("Assay construct", "Three chains: HLA-A*11:01 heavy chain, β2-microglobulin, peptide · tags not shown", None),
                    ("Allele", "A*11:01:01:01 · IPD-IMGT/HLA HLA00043", None),
                    ("Peptide", "VVVGADGVGK · KRAS 7–16 · position 6 = Asp (KRAS residue 12)", None),
                    ("Recommended epitope", "The peptide and the groove around it", None),
                    ("Structure reference", "7OW6 · Chains A–C · TCR removed", "https://www.rcsb.org/structure/7OW6"),
                ],
                "viewer": {"file": "inputs/7OW6-G12D-noTCR.pdb", "ref_label": "PDB 7OW6", "ref_url": "https://www.rcsb.org/structure/7OW6"},
            },
            {
                "id": "wild-type", "label": "Wild-type KRAS pMHC", "form": "Peptide–MHC complex",
                "accession": "Q5S3G3", "uniprot": "https://www.uniprot.org/uniprotkb/Q5S3G3/entry",
                "residues": "25–305",
                "sequence": "GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQTDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQITKRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEITLTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT",
                "details": [
                    ("Peptide", "VVVGAGGVGK · position 6 = Gly", None),
                    ("Differs from G12D", "Peptide position 6 (KRAS residue 12): glycine for aspartate", None),
                    ("Structure reference", "7OW5 · Chains A–C · TCR removed", "https://www.rcsb.org/structure/7OW5"),
                ],
                "viewer": {"file": "inputs/7OW5-WT-noTCR.pdb", "ref_label": "PDB 7OW5", "ref_url": "https://www.rcsb.org/structure/7OW5"},
            },
            {
                "id": "peptide-free", "label": "Peptide-free MHC", "form": "HLA + β2-microglobulin, empty groove",
                "accession": "Q5S3G3", "uniprot": "https://www.uniprot.org/uniprotkb/Q5S3G3/entry",
                "residues": "25–305",
                "sequence": "GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQTDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQITKRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEITLTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT",
                "details": [
                    ("Differs from G12D", "No peptide in the groove", None),
                    ("Structure reference", "7OW6 · Chains A–B · peptide and TCR removed", "https://www.rcsb.org/structure/7OW6"),
                ],
                "viewer": {"file": "inputs/7OW6-peptide-free.pdb", "ref_label": "PDB 7OW6", "ref_url": "https://www.rcsb.org/structure/7OW6"},
            },
        ],
        "rows": [("UniProt reference", "Q5S3G3"),
                 ("Target residues", "25–305 / 281 aa"),
                 ("Recommended epitope", "the peptide and the groove around it"),
                 ("Structure reference", "7OW6 · chains A–C")],
        "objectives": [
            ("Binding affinity",
             "Design a binder against the KRAS G12D peptide presented by HLA-A*11:01. "
             "We recommend targeting the peptide and the groove around it, which is the "
             "surface a T-cell receptor reads and the only part that differs from the "
             "same HLA carrying another peptide. We measure affinity using the complex "
             "of HLA-A*11:01, β2-microglobulin and VVVGADGVGK.",
             "human KRAS G12D pMHC"),
            ("Mutation specificity",
             "Your binder must not bind the same HLA-A*11:01 carrying the wild-type KRAS "
             "peptide VVVGAGGVGK. The two peptides are identical except at position 6, "
             "residue 12 of KRAS, where the mutant has an aspartate and the wild type a "
             "glycine.",
             "G12D, not wild type"),
            ("Peptide-dependent binding",
             "Your binder must not bind the HLA-A*11:01 with β2-microglobulin when the "
             "groove holds no peptide — a binder that reads the HLA or the β2-microglobulin "
             "binds every peptide on this HLA, those of healthy cells included.",
             "G12D, not peptide-free"),
        ],
        "ranking": [
            ("Mutation specificity",
             "Measurable KD against G12D, no detectable binding to wild type; otherwise by the KD ratio (wild type / G12D), largest first."),
            ("Peptide-dependent binding",
             "Measurable KD against G12D, no detectable binding to peptide-free MHC; otherwise by the KD ratio (peptide-free / G12D), largest first."),
            ("Affinity", "Lowest KD against the G12D complex; naming the targeted surface counts in the design's favour."),
        ],
        "requirements": True,
    },
}

REQUIREMENTS = [
    ("Length", "10–250 amino acids"),
    ("Format", "Single chain protein, nanobody, scFv, or Fab"),
    ("Designs per participant", "Up to 40 for Track 1, up to 20 for Tracks 2 and 3"),
    ("Design", "De novo designs only"),
]

