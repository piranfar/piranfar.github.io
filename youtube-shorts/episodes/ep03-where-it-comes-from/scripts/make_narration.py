"""Generate the episode-3 narration clips with edge-tts -> narration/01..12.wav (48 kHz mono).
Usage: python episodes/ep03-where-it-comes-from/scripts/make_narration.py [voice] [--force]
"""
import asyncio, os, subprocess, sys
import edge_tts

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EP, 'narration')
VOICE = next((a for a in sys.argv[1:] if not a.startswith('--')), 'en-US-AndrewMultilingualNeural')
RATE, PITCH = '-6%', '-2Hz'
LINES = [
    "Where did this enzyme come from?",
    "Not from the chromosome.",
    "From this. A plasmid: one extra ring of DNA, carrying one gene.",
    "The gene is read. The protein is made.",
    "Its signal sequence sends it across the inner membrane, into the periplasm. That is where it waits.",
    "Next door, a cell with no enzyme.",
    "A pilus pulls it close. One strand of the ring crosses, and the neighbour completes it.",
    "Now it has the gene too.",
    "Minutes later, it makes the enzyme.",
    "Same drug. Same door.",
    "Ring broken. The cell carries on.",
    "One gene, passed from cell to cell. That is how resistance spreads.",
]
TIMES = [0.5, 5.5, 9.5, 15.6, 19.0, 27.0, 30.5, 38.5, 42.5, 47.5, 51.5, 55.0]


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
