"""Generate the Two Fates narration clips with edge-tts (Azure neural voice, free).
Writes narration/01.wav .. 15.wav (48 kHz mono) that assemble_two_fates.py picks up.
Usage: python episodes/ep02b-two-fates/scripts/make_narration.py [voice]
"""
import asyncio, os, subprocess, sys
import edge_tts

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EP, 'narration')
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'en-US-AndrewMultilingualNeural'
RATE, PITCH = '-6%', '-2Hz'

LINES = [
    "An antibiotic is about to enter a bacterium.",
    "Everything you will see is a real structure. The proteins come from crystallography. The motion comes from molecular dynamics.",
    "This is a Gram-negative cell. Two membranes, a thin wall in between, and only a few ways in.",
    "Inside the periplasm, two things can be waiting for the drug: an enzyme that destroys it, or the target it came for.",
    "Same drug. Same door. Two fates.",
    "On the left, a cell that carries a beta-lactamase. On the right, a cell that does not. Watch them together.",
    "Ceftazidime. A third-generation cephalosporin. The same molecule on both sides.",
    "Through the porin. Identical, frame for frame.",
    "And here they part.",
    "On the left, the enzyme catches it first. On the right, there is no enzyme, and the drug finds the protein that is building the wall.",
    "Wall synthesis stops. The wall opens. The membrane pushes through.",
    "Now the same chemistry, twice. The beta-lactam ring opens.",
    "In the enzyme, the broken drug is released. Harmless. On the target, it stays bound. The protein is locked.",
    "One cell dies. The other never noticed. One enzyme made the difference. That is what resistance is. Not a stronger cell. One extra protein.",
    "Next: how bacteria get that enzyme, and how they share it.",
]


async def main():
    os.makedirs(OUT, exist_ok=True)
    for i, text in enumerate(LINES, 1):
        mp3 = os.path.join(OUT, '%02d.mp3' % i)
        wav = os.path.join(OUT, '%02d.wav' % i)
        if os.path.exists(wav) and '--force' not in sys.argv:
            continue
        for attempt in range(5):
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(mp3)
                break
            except Exception as e:  # the service sometimes returns no audio; retry
                print('retry %d on line %02d: %s' % (attempt + 1, i, e))
                await asyncio.sleep(2)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-af', 'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.15',
                        '-ar', '48000', '-ac', '1', wav], check=True)
        os.unlink(mp3)
        d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', wav],
                           capture_output=True, text=True).stdout.strip()
        print('%02d %5.2fs  %s' % (i, float(d), text[:60]))

asyncio.run(main())
