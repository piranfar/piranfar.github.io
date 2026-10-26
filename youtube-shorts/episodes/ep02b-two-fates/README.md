# Episode 2b: Two Fates (landscape, 102 s)

Episodes 1 and 2 cut against each other: same drug, same door, then the beta-lactamase destroys the
drug on the left while the drug locks PBP1b and the wall fails on the right.

## Build order

1. `scripts/make_narration.py [voice]` -> `narration/01..15.wav` (edge-tts, Azure neural voice Andrew;
   lines and timecodes in `NARRATION.md`).
2. `blender -b blend/gram_negative_base.blend --python episodes/ep02b-two-fates/scripts/film2b_shots.py -- MODE [PCT] [STILLS]`
   for MODE in `intro` (1920x1080, 30 s tour), `macro1`/`macro2` (960x1080, 5 s ring openings),
   `carry`/`lysis` (960x1080, 18 s, same camera: the wall keeps growing / the wall fails).
   Each writes `renders/tf_MODE.mp4` plus `tf_MODE_anchors.json`. Validate with stills first.
3. `python episodes/ep02b-two-fates/scripts/two_fates_v4.py [--stage picture|text|audio]` ->
   `renders/two_fates_v4.mp4`. Stage picture = ffmpeg (sources, split screen from the vertical
   HUD-free entries, transitions, grade); text = PIL layer (labels from the anchor files, title,
   captions, tints, end card); audio = music ducked under the narration, SFX from `tools/sfx/`
   (`scripts/make_sfx.py` regenerates them).

`two_fates_v3.py` is the same pipeline on the pillarboxed vertical renders (no Blender needed);
`assemble_two_fates.py` is the first pure-ffmpeg cut (v1/v2). Both kept for reference.

## Timeline (seconds)

| 0-30 | 30-33 | 33-64.5 | 64.5-74.5 | 74.5-92.5 | 92.5-102 |
|---|---|---|---|---|---|
| native tour | title | split screen (frame-aligned entries, ep1 then ping-pongs its last 3 s) | macro ring openings, half speed | two-cell shot | end card |
