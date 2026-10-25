# Episode 2: Beta-lactams hit the wall

The same drug, the same door, a different ending: no beta-lactamase is waiting, so ceftazidime reaches PBP1b, acylates its active-site serine, and the wall stops being built.

## Beats (target 60 s)

| s | Beat | Visual | Headline |
|---|---|---|---|
| 0-3 | Hook | Drug exits the porin into an empty periplasm (TEM-1 copies hidden) | NO ENZYME THIS TIME. |
| 3-15 | Meet the target | Camera settles on PBP1b; new glycan strands grow out of it and cross-link into the mesh | PBP: BUILDS THE WALL |
| 15-30 | Binding | Drug docks on the PBP transpeptidase site; ring opens and stays on Ser (pose from 2C5W superposed on 3VMA) | THE RING OPENS... AND STAYS. |
| 30-50 | Consequence | Strand growth stops; gaps open in the mesh; inner membrane bulges through | THE WALL STOPS GROWING / LYSIS |
| 50-60 | Payoff + card | Split: ep1 (enzyme ate the drug) vs ep2 (drug locked the enzyme) | SAME DRUG. SAME DOOR. DIFFERENT ENDING. / NEXT: HOW BACTERIA FIGHT BACK |

## To build

- [ ] Acyl-enzyme pose: superpose 2C5W (S. pneumoniae PBP1a with cefotaxime) onto 3VMA active site (Ser510 in E. coli PBP1b numbering), transfer ligand, then swap to ceftazidime by core alignment. State the approximation in the description.
- [ ] Wall-building animation: strand growth from PBP1b (curve bevel factor keyed), cross-link pops.
- [ ] Wall failure: delete/scale glycan segments near PBP over time; inner-membrane bulge via a lattice or proportional edit on the IM lipid object (or a simple sphere displacement in geometry nodes).
- [ ] Autolysin note: one headline or narration line, not a new object.
- [ ] Reuse: `overlay_hud.py`, `render_preview.py`, music and SFX from ep1.
