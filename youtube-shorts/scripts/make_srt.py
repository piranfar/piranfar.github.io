"""Build an English SRT from narration clips and their start times.

  python scripts/make_srt.py OUT.srt --dir narration_dir --lines lines.py --times 1.0,12.0,...

`--lines` is a python file defining LINES (the make_narration script); each clip is split into sentences and
the clip's measured duration is shared between the sentences by character count. One cue per sentence.
"""
import os, re, sys, glob, subprocess, runpy


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def dur(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]).decode())


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return '%02d:%02d:%06.3f' % (h, m, s)


def split_sentences(line):
    # split after . ! ? but not after a one-letter abbreviation such as "E." in E. coli
    parts = re.split(r'(?<![A-Z]\.)(?<=[.!?])\s+', line.strip())
    out = []
    for p in parts:
        # merge very short fragments ("TEM.") into the previous cue
        if out and len(p) < 8:
            out[-1] += ' ' + p
        else:
            out.append(p)
    return out


out = sys.argv[1]
ndir = arg('--dir')
lines = runpy.run_path(arg('--lines'))['LINES']
times = [float(x) for x in arg('--times').split(',')]
clips = sorted(glob.glob(os.path.join(ndir, '*.wav')))
assert len(clips) == len(lines) == len(times), (len(clips), len(lines), len(times))
cues = []
for clip, line, t0 in zip(clips, lines, times):
    d = dur(clip)
    sents = split_sentences(line)
    total = sum(len(s) for s in sents)
    t = t0
    for s in sents:
        dt = d * len(s) / total
        cues.append((t, t + dt - 0.05, s))
        t += dt
with open(out, 'w', encoding='utf-8') as f:
    for i, (a, b, s) in enumerate(cues, 1):
        f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(a).replace('.', ','), ts(b).replace('.', ','), s))
print('SRT', out, len(cues), 'cues, ends', ts(cues[-1][1]))
