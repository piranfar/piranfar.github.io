# youtube-shorts

Pipeline for the series *Inside a Gram-Negative Bacterium: How Antibiotics Work (and Fail)*.
Playlist: https://www.youtube.com/playlist?list=PLbsoyL1U-sWc

## Layout

| Path | What | Committed |
|---|---|---|
| `pdb/` | Crystal structures (RCSB, OPM) and the CHARMM-GUI outer-membrane build | yes (except `pdb/memprotmd/`) |
| `pdb/ligands/` | Drug coordinates and transferred binding poses | yes |
| `mdp/` | GROMACS parameter files for the TEM-1 run | yes |
| `traj/` | Post-processed MD trajectories and frames used by Blender | no (large) |
| `blend/gram_negative_base.blend` | The reusable envelope scene (all layers, trajectories wired, drug path) | yes |
| `scripts/` | Shared tools: scene builders, trajectory wiring, `overlay_hud.py`, `render_preview.py` | yes |
| `episodes/epNN-*/scripts/` | Shot scripts for one episode (camera, labels, headlines, assembly) | yes |
| `episodes/epNN-*/renders/` | That episode's renders, anchors JSON, review sheets | no |
| `episodes/epNN-*/thumbs/` | Thumbnails (final JPGs committed, source frames not) | partly |
| `tools/` | Molecular Nodes zip, CHARMM-GUI archives, music, SFX | no |

MD itself runs in WSL (`~/md/sim1_tem1`, `~/md/ompf_lps`) with the `mdgpu` micromamba env.

## Making an episode

1. Copy the previous episode's `scripts/` as a starting point; the base scene is shared and should not be modified by episode scripts (they only add cameras, labels, drug paths and animation keys at run time).
2. Validate framing with stills: `blender -b blend/gram_negative_base.blend --python episodes/epNN/scripts/filmN.py -- tour 50 120,300`
3. Render both parts at 100 %, then `python scripts/overlay_hud.py IN ANCHORS OUT`, join with ffmpeg, add music, make a 720p mobile copy.
4. Review a contact sheet (one frame every 1.5 s) before publishing.

Blender 5.2 API notes that cost time once: compositor is `scene.compositing_node_group`; Glare options are input sockets; actions are slotted (no `action.fcurves`); video output needs `image_settings.media_type = 'VIDEO'`.
