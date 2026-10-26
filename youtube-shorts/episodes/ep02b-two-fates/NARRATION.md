# Episode 2b: Two Fates. Narration script

Landscape, 1920x1080, about 2 min 20 s. Calm, unhurried delivery, one idea per sentence.
Timecodes refer to the assembled film (`scripts/assemble_two_fates.py`). Leave the pauses; the
pictures carry the beats between lines. Total about 230 words, roughly 1 min 40 s of speech.

| Time | Picture | Line |
|---|---|---|
| 0:00 | Black, then the whole envelope fades in | *(pause 1 s)* An antibiotic is about to enter a bacterium. |
| 0:04 | Slow push toward the outer membrane | Everything you will see is a real structure. The proteins come from crystallography. The motion comes from molecular dynamics. |
| 0:12 | Tour: outer membrane, porin, periplasm | This is a Gram-negative cell. Two membranes, a thin wall in between, and only a few ways in. |
| 0:20 | Tour continues: enzyme, inner membrane, target | Inside the periplasm, two things can be waiting for the drug: an enzyme that destroys it, or the target it came for. |
| 0:28 | Title card: TWO FATES | Same drug. Same door. Two fates. |
| 0:32 | Split screen appears; both columns identical | On the left, a cell that carries a beta-lactamase. On the right, a cell that does not. Watch them together. |
| 0:40 | Drug crosses LPS in both | Ceftazidime. A third-generation cephalosporin. The same molecule on both sides. |
| 0:47 | Both pass the porin | Through the porin. Identical, frame for frame. |
| 0:55 | Columns diverge: left meets TEM-1, right drifts toward PBP | And here they part. |
| 1:00 | Left: docking in TEM-1. Right: wall being built by PBP | On the left the enzyme catches it first. On the right there is no enzyme, and the drug finds the protein that is building the wall. |
| 1:10 | Both climaxes, slowed: ring opens in TEM-1 / ring opens on PBP serine | Now the same chemistry happens twice. The beta-lactam ring opens. |
| 1:18 | Left: product released. Right: acyl-enzyme stays | In the enzyme, the broken drug is released. Harmless. On the target, it stays bound. The protein is locked. |
| 1:28 | Right: wall stops, gap, bulge. Left: cell carries on | Wall synthesis stops. The wall opens. The membrane pushes through. One cell dies. The other never noticed. |
| 1:40 | Single wide frame, both outcomes faded in behind | One enzyme made the difference. That is what resistance is. Not a stronger cell. One extra protein. |
| 1:52 | End card | Next: how bacteria get that enzyme, and how they share it. |

## Recording notes

- Record at 48 kHz, mono is fine; leave 2 s of room tone at the start for noise profiling.
- Read each line as its own take; the assembler places lines by timecode, so timing does not need to be perfect.
- Export one file per line as `narration/NN.wav` (01 to 15), or one continuous file plus this table; either works.
- The music is ducked under speech automatically; no need to leave extra gaps for it.

## Where to turn this into audio

Own voice (preferred for a personal channel): any phone voice memo app, or Audacity on the PC.

Text to speech, if you want a draft or decide not to record:

| Tool | Notes |
|---|---|
| ElevenLabs | Most natural English; free tier covers this length; "Daniel" or "Brian" suit documentary tone |
| OpenAI TTS (tts-1-hd, voice "onyx" or "echo") | Very clean, API or playground; cheap |
| Microsoft Edge "Read aloud" / Azure Neural (en-US-AndrewNeural) | Free in Edge; export via a recorder, or use the `edge-tts` Python package offline-free |
| Piper (local, open source) | Runs on this PC without an account; quality a step below the cloud voices |

If you go with TTS, give me the voice and I will generate the 15 clips with `edge-tts` or Piper directly from this table and drop them into the mix.
