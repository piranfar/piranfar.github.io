# Episode 1: Inside a Gram-negative bacterium

Published 2026-10-24: https://youtube.com/shorts/kJKye8xqjRg (v2; the v1 upload IVKyoSsN-Pc is private).
Write-up: `posts/shorts-pipeline/` on the site.

## Final pipeline (v2)

```
blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/film1_v2.py -- tour 100
blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/film1_v2.py -- entry 100
python scripts/overlay_hud.py renders/film1_v2_tour.mp4  renders/film1_v2_tour_anchors.json  renders/film1_v2_tour_hud.mp4
python scripts/overlay_hud.py renders/film1_v2_entry.mp4 renders/film1_v2_entry_anchors.json renders/film1_v2_entry_hud.mp4
ffmpeg xfade (0.6 s) -> music (loudnorm -16 LUFS, fades, gaussian duck at the break) + tools/sfx/ring_break.wav -> film1_v2_final.mp4
```

Structure: 2 s hook, continuous descent through seven components (3.5 to 5.5 s each), pull-out, crossfade, drug entry through the porin, docking in TEM-1, ring opening (macro, flash, bursts, SFX), release, pull-out, end card. 64 s.

## Script history (kept for reference)

| Script | Role |
|---|---|
| `render_membrane_compare.py` | before/after MD still of the outer membrane |
| `add_drug_path.py`, `add_shot_cameras.py`, `add_s3_hydrolysis.py` | first drug path, follow camera, hydrolysis sequence (these modified the base scene and are now baked into it) |
| `tune_cameras.py`, `add_glow_cameras.py` | camera and glow passes of the first cinematic version |
| `film1_cinematic.py` + `assemble_cinematic.py` | v1 with 3D labels (published first, then replaced) |
| `render_intro_tour.py`, `render_wide_entry.py`, `assemble_film1.py` | the flat "captions at the bottom" version, rejected |
| `cinematic_look.py` | look test for 3D labels and DOF |
| `film1_v2.py` | the final: dimming, anchor export, journey camera, hook, climax, end card |

## Known approximations

- Hydrolyzed product pose is hydrolyzed cefotaxime from KPC-2 (5UJ3) superposed on TEM-1; the travelling drug is ceftazidime.
- 5 ns of membrane MD does not relax the O-antigen; it is there for motion, not for a claim.
- Inner membrane lipids are DPPC from MemProtMD, not PE/PG.
