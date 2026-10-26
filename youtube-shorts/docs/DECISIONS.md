# Decisions and lessons

A running log. Newest at the bottom.

## 2026-10-23

- **GPU for GROMACS under WSL.** The conda-forge OpenCL build cannot see an NVIDIA card in WSL. Use the `nompi_cuda` build (env `mdgpu`): 384 vs 41 ns/day on the same TEM-1 system.
- **Real LPS, not a generic bilayer.** MemProtMD gives OmpF in DPPC for free; CHARMM-GUI Membrane Builder was used instead for an asymmetric E. coli outer membrane with lipid A, R1 core and O1 antigen (45 LPS). Keep the O-antigen: pathogenic E. coli is smooth. Solve visibility with a cross-section, not by deleting sugars.
- **Molecular Nodes materials** are set through the Material socket of the Style node, not the mesh material slot.
- **Trajectory import loses secondary structure** for the GROMACS TEM-1 topology (DSSP fails on terminal OC1/OC2). Copy `sec_struct` from a static import of the same file (`scripts/fix_tem1_traj.py`), otherwise cartoons render as nothing. This bug made the enzymes invisible in the first two previews.
- **Blender 5.2 API changes** that each cost a render: `scene.compositing_node_group` replaces `scene.node_tree`; Glare options are sockets; actions are slotted (no `action.fcurves`); video output needs `image_settings.media_type='VIDEO'`.
- **Render cost is small.** Full 1080x1920 EEVEE on the RTX 3080 laptop: about 20 minutes for 60 s. Iterate freely; the expensive thing is a wrong decision, not a render.

## 2026-10-24

- **Camera-parented 3D text is unusable with depth of field.** Headlines and titles are burned in with ffmpeg instead.
- **Labels left the 3D scene entirely** (v2 pass 1). The render exports each anchor's screen position per frame; `scripts/overlay_hud.py` draws ring, leader and word in 2D. Text can never hide behind geometry.
- **Camera looks along -Y**, so screen-right is world -X. Several labels landed on the wrong edge until this was written down.
- **Anchors must be on visible geometry.** With an elevated camera, a point on the cut plane and a point on the strand behind it differ by nanometers on screen; the ring floated in space twice.
- **Dim the context.** While a component is introduced, every other material is darkened and desaturated; the subject gets a mild glow. This replaced most of the text.
- **One continuous camera journey** beats seven jump cuts; variable dwell (3.5 to 5.5 s) beats a metronome.
- **The climax needs its own machinery**: macro camera, slower transformation, a flash at the bond, 2D burst rings, a synthesized impact sound and a music duck.
- **Thumbnails for Shorts** cannot be set from Studio on desktop; built anyway (`episodes/ep01-envelope/thumbs/`) for the mobile app or horizontal uploads.
- **Publishing**: Claude cannot press Publish or select large files; those two clicks are the author's.

## 2026-10-25

- **Layout**: shared assets at the root, per-episode `scripts/renders/thumbs`. Episode scripts never save the base scene.
- **Docx export of a post** must run from a copy outside the Quarto project; the site's HTML includes break other formats.

- **Geometry-nodes modifier inputs cannot be set from Python in Blender 5.2** (`modifier[socket] = value` raises "id properties not supported"). Drive animated node groups with an empty wired to an Object Info node inside the group, and keyframe the empty's location/scale. Use `transform_space = 'RELATIVE'` so Array-tiled copies read the control in their own space.
- **Episode-2 wall mechanics** (`episodes/ep02-hit-the-wall/scripts/wall_mechanics.py`) are all run-time: new strands grow from PBP1b (bevel_factor_end), a sphere deletes wall geometry (gap), a gaussian Set Position lifts the inner-membrane lipids (bulge). Gap and bulge sit screen-right of PBP1b where the wall is visible, not hidden behind the protein.

## 2026-10-26

- **Shorts safe area.** Phones crop a few percent from each side and YouTube's UI covers the bottom ~25 % and a right column; in episode 1 the 'OUTER MEMBRANE' label sat under the channel name and the leader ran to the edge. From episode 2 the overlay keeps 11 % side margins, label rows at 15 % and 66 % of height, headlines at 60 %, nothing below 70 %. Episode 1 stays as published (600+ views); the rule applies going forward.

- **Material.copy() shares the action.** When a material is already keyed (the film scripts key `key_normal(1)` before building), `old.copy()` gives the copy the same action, so keys inserted on the copy animate the original too. That is why the whole old wall glowed while new strands grew in episode 2. `fresh_material()` now clears the copy's animation data first; only the new strands glow.
- **16:9 wide shots need wider tiling.** The vertical films saw 36 nm; a landscape wide shot at 35 mm sees ~60 nm, so `film2b_shots.py --intro` adds array copies at run time (OM +4 tiles, PG strands x3, inner membrane holed-sheet + fill x3 with the extra AcrB holes outside the frame). Array modifiers must go BEFORE the Molecular Nodes style modifier (index 0) or they do nothing.
- **Every camera stop needs two keys** (arrive, leave with a small drift). A single key per component means the camera is already travelling while the label is up; the anchor positions in the exported JSON drift off-screen by mid-label. Check the anchor JSON before rendering: start/middle/end positions should all be inside the frame.
- **Two Fates pipeline is three re-runnable stages** (`two_fates_v3.py`/`v4.py --stage picture|text|audio`): ffmpeg picture (sources, transitions, grade), PIL text layer (one consistent layer; labels from the anchor files, animated title, tints, end card), ffmpeg audio (music ducked under narration, SFX cues, ambience). Keep the text out of the Blender render and out of ffmpeg drawtext.
- **HUD-free sources for compilations.** Never stack a film's baked captions under a new text layer; assemble from the `*_entry.mp4` / `*_tour.mp4` renders, not the `_hud` clips.
