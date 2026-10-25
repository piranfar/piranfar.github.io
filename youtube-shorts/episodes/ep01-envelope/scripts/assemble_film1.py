"""Assemble film 1 with ffmpeg: component tour + drug entry, with bilingual
captions (English top line, Persian below; ffmpeg's drawtext shapes Persian
through harfbuzz/fribidi).
Usage: python -I assemble_film1.py TOUR.mp4 ENTRY.mp4 OUT.mp4 [--test SECONDS]
Caption timings are relative to each clip; edit CAPTIONS below.
"""
import subprocess, sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FONT_EN = 'C:/Windows/Fonts/segoeuib.ttf'
FONT_FA = 'C:/Windows/Fonts/segoeui.ttf'      # Segoe UI has full Arabic-script coverage
if not os.path.exists(FONT_EN):
    FONT_EN = 'C:/Windows/Fonts/arialbd.ttf'
if not os.path.exists(FONT_FA):
    FONT_FA = 'C:/Windows/Fonts/arial.ttf'

# (start, end, english, persian) in seconds within the clip
TOUR_CAPTIONS = [
    (0.3, 2.8, 'Inside a Gram-negative envelope', 'درون پوشش باکتری گرم‌منفی'),
    (3, 8, 'Outer membrane: LPS + phospholipids', 'غشای خارجی: LPS و فسفولیپید'),
    (8, 13, 'Porin (OmpF): the way in', 'پورین OmpF: راه ورود'),
    (13, 18, 'Peptidoglycan: the thin wall', 'پپتیدوگلیکان: دیوارهٔ نازک'),
    (18, 23, 'Beta-lactamase (TEM-1): the drug destroyer', 'بتالاکتاماز TEM-1: نابودگر دارو'),
    (23, 28, 'Inner membrane', 'غشای داخلی'),
    (28, 33, 'PBP1b: the drug\'s real target', 'PBP1b: هدف واقعی دارو'),
    (33, 38, 'Efflux pump (AcrB): throws drugs out', 'پمپ efflux (AcrB): دارو را بیرون می‌ریزد'),
]
ENTRY_CAPTIONS = [
    (0.5, 5, 'A beta-lactam arrives from outside', 'یک بتالاکتام از بیرون می‌رسد'),
    (5.5, 9, 'Through the porin', 'از پورین عبور می‌کند'),
    (9.5, 15.5, 'Into the periplasm, toward the enzyme', 'به پری‌پلاسم، به سوی آنزیم'),
]


def esc(s):
    # single quotes cannot be escaped inside a quoted drawtext value: use a typographic apostrophe
    s = s.replace("'", '’')
    return s.replace('\\', '\\\\').replace(':', '\\:').replace(',', '\\,').replace('%', '\\%')


def fontpath(p):
    # ffmpeg on Windows needs the drive-letter colon escaped even inside quotes
    return p.replace(':', '\\:')


WITH_PERSIAN = '--fa' in sys.argv     # English-only by default (audience is English for now)


def drawtexts(captions, offset, h):
    parts = []
    for a, b, en, fa in captions:
        a, b = a + offset, b + offset
        alpha = "if(lt(t\\,%.2f)\\,(t-%.2f)/0.4\\,if(gt(t\\,%.2f)\\,(%.2f-t)/0.4\\,1))" % (a + 0.4, a, b - 0.4, b)
        common = "enable='between(t\\,%.2f\\,%.2f)':alpha='%s':x=(w-text_w)/2:borderw=3:bordercolor=black@0.6" % (a, b, alpha)
        y_en = int(h * 0.17) if WITH_PERSIAN else int(h * 0.13)
        # shrink long captions so they fit within 90 % of the frame width (9:16 frame)
        w = h * 9 / 16
        fs_en = min(int(h * 0.034), int(w * 0.9 / (0.56 * max(len(en), 1))))
        parts.append("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=white:y=h-%d:%s"
                     % (fontpath(FONT_EN), esc(en), fs_en, y_en, common))
        if WITH_PERSIAN:
            parts.append("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=0xffd27a:y=h-%d:%s"
                         % (fontpath(FONT_FA), esc(fa), int(h * 0.030), int(h * 0.12), common))
    return parts


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                          'default=nw=1:nk=1', path], capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    tour, entry, out = sys.argv[1:4]
    test = float(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else None
    h = 960 if test else int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                              '-show_entries', 'stream=height', '-of', 'default=nw=1:nk=1', tour],
                                             capture_output=True, text=True).stdout.strip())
    d_tour = duration(tour)
    filters = ["[0:v][1:v]concat=n=2:v=1:a=0[v0]"]
    chain = drawtexts(TOUR_CAPTIONS, 0.0, h) + drawtexts(ENTRY_CAPTIONS, d_tour, h)
    filters.append("[v0]" + ",".join(chain) + "[v]")
    # write the filter graph to a file: it is long and full of quotes
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write(";".join(filters))
        script = fh.name
    # ffmpeg 7+: a filter graph read from a file is passed as -/filter_complex FILE
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', tour, '-i', entry, '-/filter_complex', script,
           '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30']
    if test:
        cmd += ['-t', str(test)]
    cmd.append(out)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(r.stderr[-400:] if r.returncode else 'OK %s  (%.1f s tour + %.1f s entry)' % (out, d_tour, duration(entry)))
    os.unlink(script)
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()
