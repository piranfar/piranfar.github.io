# The series: where we came from, where we are going

## Origin

The site's Learning section explains antibiotic PK/PD, beta-lactams, beta-lactamases and resistance in plain language. The series turns those lessons into 60-second vertical videos. The founding decision (October 2026) was that nothing in the frame would be invented: proteins from the PDB, membranes built physically, protein motion from molecular dynamics, the drug as the real molecule. Only the peptidoglycan mesh is stylized, because it has no single atomic structure to import.

A second decision followed the first review: the videos must look like films, not diagrams. Moving camera, shallow depth of field, labels that point at the object instead of captions at the bottom, one real climax per episode. Reference style: the better science Shorts (BIO_FACTS, Biotermsanimate).

## One scene, many episodes

`blend/gram_negative_base.blend` is the shared kit: outer membrane with LPS and three OmpF porins, periplasm with peptidoglycan and three TEM-1 copies (MD-driven), inner membrane with one AcrB pump and PBP1b, a ceftazidime molecule with a path through a porin. Each episode's scripts add cameras, labels, drug paths and animation keys at run time and save nothing back, so the kit stays clean and every episode re-renders from the same source.

## Episodes

| # | Title | Claim | Status |
|---|---|---|---|
| 1 | Inside a Gram-negative bacterium | How a beta-lactam gets in, and how TEM-1 destroys it | Published 2026-10-24, https://youtube.com/shorts/kJKye8xqjRg |
| 2 | Beta-lactams hit the wall | With no enzyme waiting, the drug locks PBP1b and the wall stops growing | Published 2026-10-26, https://youtube.com/shorts/ufXzk6dhlX8 |
| 2b | Two fates (long form, landscape) | Episodes 1 and 2 side by side: same entry, then the enzyme eats the drug vs the drug locks the target. Not a Short; a 2-3 min video for the main feed | First cut 2026-10-26 (87 s, no narration yet); `episodes/ep02b-two-fates/` has NARRATION.md and the ffmpeg assembler |
| 3 | How beta-lactamases save the wall | Classes A/C/D, plasmid spread, and why one enzyme covers a whole cell | Planned |
| 4 | Porins shut the door | OmpF/OmpC loss and what it costs the cell | Planned |
| 5 | Efflux pumps throw the drug out | AcrAB-TolC; needs TolC added above the existing AcrB (13.9 nm gap already fits) | Planned |
| 6 | MIC is a threshold, not the whole story | Bridge to PK/PD and the Learning lessons | Planned |
| 7 | Plasmid vs chromosome resistance | Bridge to Learning lesson 14 | Planned |

Later assets needed: TolC (PDB 1EK9, already in `pdb/memprotmd/`), avibactam for a CAZ-AVI episode, an OmpC structure, a PE/PG inner membrane if the inner membrane is ever simulated.

## Audience and channel

English only for now. Channel: MicroBiology, Diving and Cycling. Playlist: https://www.youtube.com/playlist?list=PLbsoyL1U-sWc. Narration is not recorded yet; the headlines double as the script. Music comes from the YouTube Audio Library (episode 1: "Rain Over Kyoto Station", The Mini Vandals).

## Standing rules

1. Validate every shot with check stills before a sequence render.
2. Anchors sit on geometry that is visible from the camera.
3. One climax per episode gets a third of the effort.
4. State approximations in the description (episode 1: the hydrolyzed product pose is borrowed from KPC-2 with cefotaxime).
5. Review a 1.5-second contact sheet before publishing.
