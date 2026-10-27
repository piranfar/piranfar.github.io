# Episode 3: Where the enzyme comes from (and how it is shared)

Promise made at the end of episodes 2 and 2b: "Next: how bacteria get that enzyme, and how they share it."
Target: a Short (1080x1920, 45-60 s) plus a landscape cut; publish in World AMR Awareness Week (18-24 Nov 2026).

## The idea in one line

The enzyme that saved the cell in episode 1 is not part of the cell. It is a gene on a plasmid, and the
plasmid travels.

## Beats (Short)

| # | s | Picture | Line (narration) | Science |
|---|---|---|---|---|
| 1 | 0-5 | Hook: the periplasm of episode 1, TEM-1 waiting. Camera drops THROUGH the inner membrane into the cytoplasm | "Where did this enzyme come from?" | |
| 2 | 5-14 | Cytoplasm: the chromosome, a large tangled thread, dim. Beside it a small bright ring: the plasmid. One segment lights up: *bla*TEM-1 | "Not from the chromosome. From this: a plasmid, a small extra ring of DNA, carrying one gene." | blaTEM-1 on a conjugative plasmid (e.g. R100/pBR322 lineage) |
| 3 | 14-24 | The gene is read: a fresh TEM-1 appears near the inner membrane (ribosome shown, simplified), its signal peptide leads it through the membrane; it folds in the periplasm, next to the enzymes we know | "The gene is read, the protein is made, and its signal sequence sends it across the inner membrane into the periplasm. That is where it waits." | Sec translocation; signal peptide cleaved |
| 4 | 24-38 | Pull back: a second cell beside the first, no enzyme (the cell that died in Two Fates). A pilus (real F-pilus structure) reaches from the first cell to the second. A single strand of the plasmid runs along it; in the second cell it is completed into a ring | "And the plasmid travels. A pilus pulls a neighbour close, one strand of the ring crosses, the neighbour completes it." | Conjugation: F-pilus (PDB 5LER), rolling-circle transfer, both cells end with a plasmid |
| 5 | 38-50 | In the second cell: gene lights, TEM-1 appears in its periplasm. Ceftazidime enters through the porin, the ring breaks (the episode 1 climax, reused), the cell carries on | "Minutes later the neighbour makes the enzyme too. The drug arrives, the ring breaks, the cell carries on." | |
| 6 | 50-58 | Wide: both cells intact, plasmid glowing in each. End card | "One gene, passed from cell to cell. That is how resistance spreads." + "Next: how we fight back: beta-lactamase inhibitors" | |

## Assets

| Thing | Source | Status |
|---|---|---|
| Envelope, TEM-1, PBP1b, porin, drug, hydrolysis | `blend/gram_negative_base.blend` + ep1/ep2 scripts | have |
| F-pilus filament | PDB 5LER (pED208 F-pilus, 75 pilins, 13.2 A rise) `pdb/pilus/5LER.cif`; Array along its axis for length | downloaded |
| Plasmid | procedural double helix on a ring (stylized; said so in the description) | to build |
| Chromosome | long random-walk tube, dimmed, mostly out of focus | to build |
| Ribosome | PDB 4V9D (optional; only as a presence, no mechanism) | decide after a render test |
| TEM-1 nascent / signal peptide | TEM-1 cartoon from the base scene, scaled from 0, moved through the IM | have |
| Second cell | same envelope rendered twice side by side (Array by one cell width is not possible: cells are separate); use a second camera position and a wall-to-wall composite as in Two Fates, or duplicate the collections with an x offset | to decide |

## Rules carried over

- No text in Blender; HUD via overlay_hud.py (safe area), landscape via the Two Fates text layer.
- Every camera stop: arrive + hold keys; check anchor JSON before rendering.
- Fresh material copies: clear animation data (wall_mechanics lesson).
- Commit, do not push.

## Honest simplifications to state in the description

Transcription/translation shown as "the gene is read and the protein appears"; the plasmid and chromosome are
stylized DNA; the pilus is the real filament but the transfer machinery (T4SS, relaxase) is not shown.

## v2 (2026-10-27)

Both cuts rebuilt on `scripts/ep3_beats.py` + `scripts/look.py`: ribosome -> mRNA -> SecYEG -> fold in the periplasm;
pilus retracts and pulls cell B 32 nm into contact (DX 72 -> 40); ssDNA crosses at the contact zone, 5' first; recipient
ring grows single-stranded, second strand synthesised; drug enters cell B through its porin c (path shift 51.7 nm);
four cells in the finale. Render cost about 2.2 s/frame landscape with baked surfaces.
