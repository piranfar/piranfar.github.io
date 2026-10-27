"""Narration v2 for the landscape episode 3 -> narration_wide/01..16.wav (48 kHz mono, edge-tts).
Usage: python episodes/ep03-where-it-comes-from/scripts/make_narration_wide.py [voice] [--force]
"""
import asyncio, os, subprocess, sys
import edge_tts

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EP, 'narration_wide')
VOICE = next((a for a in sys.argv[1:] if not a.startswith('--')), 'en-US-AndrewMultilingualNeural')
RATE, PITCH = '-6%', '-2Hz'
LINES = [
    "Athens, 1963. A blood culture from a patient named Temoneira grows E. coli that should have died on penicillin. It did not.",
    "The enzyme that saved it got her name. TEM. You met it in episode one: it waits in the periplasm and breaks the drug before it reaches the wall.",
    "So where does it come from? Not from the chromosome.",
    "From this. A plasmid: a spare ring of DNA, a few thousand base pairs, with one gene on it that matters. A passenger.",
    "The gene is read. The protein is made.",
    "A signal sequence at its front sends it across the inner membrane, into the periplasm, to wait by the door. One ring of DNA, and the whole cell is covered.",
    "Now the part that should worry you. Bacteria have sex.",
    "A pilus, the sex pilus, hooks a neighbour that has no enzyme, and pulls it close.",
    "One strand of the ring crosses. The neighbour builds the other strand and closes the circle.",
    "It did not evolve resistance. It was handed it. In minutes.",
    "The gene is read there too. The enzyme is shipped to the periplasm.",
    "Same drug. Same door.",
    "Ring broken. The cell carries on.",
    "Within ten years of Athens, the same gene was in gonorrhoea, and in the Haemophilus that gives children meningitis. Different species. Same passenger.",
    "A plasmid can cross in minutes. A ward can turn in a week. A gene found in one species, in one country, is a problem for every species, in every country.",
    "Resistance does not need a stronger cell. It needs a gene that travels.",
]
# film seconds; the film timeline in film3.py 'wide' mode is built around these
TIMES = [1.0, 12.0, 21.5, 25.0, 34.8, 38.2, 50.0, 54.5, 61.0, 68.0, 73.0, 79.0, 83.0, 88.0, 100.0, 113.0]


async def main():
    os.makedirs(OUT, exist_ok=True)
    for i, text in enumerate(LINES, 1):
        mp3 = os.path.join(OUT, '%02d.mp3' % i)
        wav = os.path.join(OUT, '%02d.wav' % i)
        if os.path.exists(wav) and '--force' not in sys.argv:
            continue
        for attempt in range(6):
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
    for i in range(1, len(LINES) + 1):
        wav = os.path.join(OUT, '%02d.wav' % i)
        d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', wav],
                           capture_output=True, text=True).stdout.strip()
        print('%02d start %5.1f  len %5.2f  end %5.1f  %s' % (i, TIMES[i - 1], float(d), TIMES[i - 1] + float(d), LINES[i - 1][:50]))

if __name__ == '__main__':
    asyncio.run(main())
