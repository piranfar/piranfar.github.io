"""Generate the episode-3 narration clips with edge-tts -> narration/01..10.wav (v2 story lines) (48 kHz mono).
Usage: python episodes/ep03-where-it-comes-from/scripts/make_narration.py [voice] [--force]
"""
import asyncio, os, subprocess, sys
import edge_tts

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EP, 'narration')
VOICE = next((a for a in sys.argv[1:] if not a.startswith('--')), 'en-US-AndrewMultilingualNeural')
RATE, PITCH = '-6%', '-2Hz'
LINES = [
    "This enzyme has a name. TEM. After Temoneira, a patient in Athens, 1963, whose E. coli ate penicillin.",
    "Where did it come from? Not from the chromosome.",
    "From this. A plasmid: a spare ring of DNA with one gene on it. A passenger.",
    "The gene is read, the protein is made, and it is shipped across the inner membrane to wait by the door.",
    "Now the part that should worry you. Bacteria have sex.",
    "A pilus hooks a neighbour that has no enzyme. One strand of the ring crosses. The neighbour completes it.",
    "It did not evolve resistance. It was handed it. In minutes.",
    "Same drug. Same door. Ring broken.",
    "Resistance does not need a stronger cell. It needs a gene that travels.",
]
TIMES = [0.5, 10.5, 13.0, 19.8, 27.0, 31.0, 38.5, 46.5, 52.5]


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
            except Exception as e:
                print('retry %d on line %02d: %s' % (attempt + 1, i, e))
                await asyncio.sleep(2)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-af',
                        'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.15',
                        '-ar', '48000', '-ac', '1', wav], check=True)
        os.unlink(mp3)
        d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', wav],
                           capture_output=True, text=True).stdout.strip()
        print('%02d %5.2fs  %s' % (i, float(d), text[:60]))

if __name__ == '__main__':
    asyncio.run(main())
