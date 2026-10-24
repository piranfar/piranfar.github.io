"""Assemble the cinematic film: tour + entry clips, a persistent small title at the
top and big gold headlines (timings exported by film1_cinematic.py as JSON next
to each clip). Labels are already in the 3D render.
Usage: python -I assemble_cinematic.py TOUR.mp4 ENTRY.mp4 OUT.mp4 [--test SECONDS]
"""
import subprocess, sys, os, json, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FONT = 'C:/Windows/Fonts/segoeuib.ttf'
TITLE = 'INSIDE A GRAM-NEGATIVE BACTERIUM'


def fontpath(p):
    return p.replace(':', '\\:')


def esc(s):
    s = s.replace("'", '\u2019')
    return s.replace('\\', '\\\\').replace(':', '\\:').replace(',', '\\,').replace('%', '\\%')


def probe(path, key):
    return subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=' + key,
                           '-of', 'default=nw=1:nk=1', path], capture_output=True, text=True).stdout.strip()


def headline_filters(items, offset, h, w):
    parts = []
    for a, b, text in items:
        a, b = a + offset, b + offset
        alpha = "if(lt(t\\,%.2f)\\,(t-%.2f)/0.35\\,if(gt(t\\,%.2f)\\,(%.2f-t)/0.35\\,1))" % (a + 0.35, a, b - 0.35, b)
        fs = min(int(h * 0.046), int(w * 0.92 / (0.60 * max(len(text), 1))))
        parts.append("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.70"
                     ":borderw=4:bordercolor=black@0.7:enable='between(t\\,%.2f\\,%.2f)':alpha='%s'"
                     % (fontpath(FONT), esc(text), fs, a, b, alpha))
    return parts


def main():
    tour, entry, out = sys.argv[1:4]
    test = float(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else None
    h = int(probe(tour, 'height'))
    w = int(probe(tour, 'width'))
    d_tour = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                                   'default=nw=1:nk=1', tour], capture_output=True, text=True).stdout.strip())
    XF = 0.6                                   # crossfade between the two clips (s)
    heads = []
    for clip, off in ((tour, 0.0), (entry, d_tour - XF)):
        js = clip.replace('.mp4', '_headlines.json')
        if os.path.exists(js):
            with open(js, encoding='utf-8') as fh:
                heads += headline_filters(json.load(fh), off, h, w)
    title = ("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=white@0.85:x=(w-text_w)/2:y=h*0.045"
             ":borderw=3:bordercolor=black@0.6" % (fontpath(FONT), esc(TITLE), int(h * 0.022)))
    graph = ("[0:v][1:v]xfade=transition=fade:duration=%.2f:offset=%.3f[v0];[v0]" % (XF, d_tour - XF)
             + ",".join([title] + heads) + "[v]")
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write(graph)
        script = fh.name
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', tour, '-i', entry, '-/filter_complex', script,
           '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30']
    if test:
        cmd += ['-t', str(test)]
    cmd.append(out)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.unlink(script)
    print(r.stderr[-400:] if r.returncode else 'OK %s (%.1f s tour)' % (out, d_tour))
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()
