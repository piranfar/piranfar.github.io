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

- [x] Acyl-enzyme pose (transfer_pbp_pose.py, RMSD 0.58 A on the three motifs): superpose 2C5W (S. pneumoniae PBP1a with cefotaxime) onto 3VMA active site (Ser510 in E. coli PBP1b numbering), transfer ligand, then swap to ceftazidime by core alignment. State the approximation in the description.
- [x] Wall-building animation (wall_mechanics.build_wall / stop_wall): strand growth from PBP1b (curve bevel factor keyed), cross-link pops.
- [x] Wall failure (wall_mechanics.open_gap / bulge_membrane): delete/scale glycan segments near PBP over time; inner-membrane bulge via a lattice or proportional edit on the IM lipid object (or a simple sphere displacement in geometry nodes).
- [ ] Autolysin note: one headline or narration line, not a new object.
- [ ] Reuse: `overlay_hud.py`, `render_preview.py`, music and SFX from ep1.

## Next

- [ ] Shot script `film2.py`: hook (empty periplasm), PBP introduction with build_wall, drug path from the porin to the PBP entrance (ENTRANCE 33.2, 53.8, -100.9 A), docking + acyl cross-fade, stop_wall, open_gap, bulge, split payoff, end card.
- [ ] Headlines and anchors JSON; overlay; music; assemble.

## Alignment with episode 1 (for the long comparison film)

`film2.py entry` keeps frames 1-450 identical to `film1_v2.py entry` (same drug path,
camera keys and timing), so a third, longer film can show the two entries side by side
in one landscape frame and let them diverge at the enzyme / the target. Keep this
alignment when editing either script. Episode 3 (long form) = hook + split screen
(ep1 entry | ep2 entry) + a closing comparison; see docs/SERIES.md.
