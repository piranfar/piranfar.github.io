"""Episode 2b: Two Fates. Landscape 1920x1080 comparison film built from the
existing vertical renders (no Blender needed).

Timeline (seconds):
  0.0  - 30.0  intro: ep1 tour (vertical) letterboxed on a blurred copy of itself, headlines
  30.0 - 33.0  title card TWO FATES
  33.0 - 64.5  split screen: ep1 entry | ep2 entry (frame-aligned for the first 15 s),
               column captions WITH A BETA-LACTAMASE / WITHOUT
  64.5 - 74.5  climax replay at half speed (+2 s hold): both ring-opening moments side by side
  74.5 - 92.5  outro: ep2's lysis shot wide at 0.6x, held, with the closing statements
  92.5 - 99.0  end card
Narration (if present) is mixed from episodes/ep02b-two-fates/narration/NN.wav by the
timecodes in NARRATION.md; music ducks under it.
Usage: python episodes/ep02b-two-fates/scripts/assemble_two_fates.py [--test SECONDS]
"""
import subprocess, sys, os, glob, tempfile

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02b-two-fates')
E1 = os.path.join(BASE, 'episodes', 'ep01-envelope', 'renders')
E2 = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall', 'renders')
MUSIC = os.path.join(BASE, 'tools', 'music_rain_over_kyoto_station.mp3')
SFX = os.path.join(BASE, 'tools', 'sfx', 'ring_break.wav')
FONT = 'C\\:/Windows/Fonts/segoeuib.ttf'
OUT = os.path.join(EP, 'renders', 'two_fates_v2.mp4')
W, H = 1920, 1080
test = float(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else None

tour, e1, e2 = os.path.join(E1, 'film1_v2_tour_hud.mp4'), os.path.join(E1, 'film1_v2_entry_hud.mp4'), os.path.join(E2, 'film2_entry_hud.mp4')
for f in (tour, e1, e2):
    assert os.path.exists(f), f


def esc(s):
    return s.replace("'", '\u2019').replace(':', '\\:').replace(',', '\\,')


def head(text, a, b, y='h*0.86', size=52, col='0xffd86e'):
    alpha = "if(lt(t\\,%.2f)\\,(t-%.2f)/0.4\\,if(gt(t\\,%.2f)\\,(%.2f-t)/0.4\\,1))" % (a + 0.4, a, b - 0.4, b)
    return ("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=%s:x=(w-text_w)/2:y=%s:borderw=4:bordercolor=black@0.7"
            ":enable='between(t\\,%.2f\\,%.2f)':alpha='%s'" % (FONT, esc(text), size, col, y, a, b, alpha))


# ---- segment A: intro from the tour (0-30 s), vertical pillarboxed on a blurred backdrop ----
segA = ("[0:v]trim=0:30,setpts=PTS-STARTPTS,split[a0][a1];"
        "[a0]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,gblur=sigma=40,eq=brightness=-0.25[abg];"
        "[a1]scale=-2:%d[afg];[abg][afg]overlay=(W-w)/2:0[A]" % (W, H, W, H, H))
# ---- title card (30-33) ----
segT = ("color=c=0x0a0d18:s=%dx%d:d=3,format=yuv420p,"
        "drawtext=fontfile='%s':text='TWO FATES':fontsize=140:fontcolor=white:x=(w-text_w)/2:y=h*0.38,"
        "drawtext=fontfile='%s':text='SAME DRUG. SAME DOOR.':fontsize=48:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.58[T]" % (W, H, FONT, FONT))
# ---- segment B: split screen (33-68.6): ep1 entry is 24.7 s, ep2 entry 33.7 s; run 35.6 s, ep1 holds its last frame ----
colw = 540
# both entries are cut before their own end cards (ep1 at 25.3 s, ep2 at 31.5 s); ep1 then holds its last frame
segB = ("[1:v]trim=0:25.3,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=6.2,scale=%d:-2[L];"
        "[2:v]trim=0:31.5,setpts=PTS-STARTPTS,scale=%d:-2[R];"
        "color=c=0x0a0d18:s=%dx%d:d=31.5,format=yuv420p[Bbg];"
        "[Bbg][L]overlay=%d:(H-h)/2[B1];[B1][R]overlay=%d:(H-h)/2," % (colw, colw, W, H, W // 2 - colw - 40, W // 2 + 40)
        + "drawtext=fontfile='%s':text='WITH A BETA-LACTAMASE':fontsize=40:fontcolor=white:x=%d:y=24:borderw=3:bordercolor=black@0.7,"
          "drawtext=fontfile='%s':text='WITHOUT':fontsize=40:fontcolor=white:x=%d:y=24:borderw=3:bordercolor=black@0.7,"
          "drawtext=fontfile='%s':text='SAME ENTRY\\, FRAME FOR FRAME':fontsize=36:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.9:borderw=3:bordercolor=black@0.7:enable='between(t\\,2\\,14)',"
          "drawtext=fontfile='%s':text='HERE THEY PART':fontsize=44:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.9:borderw=3:bordercolor=black@0.7:enable='between(t\\,15\\,19)',"
          "drawtext=fontfile='%s':text='THE CELL CARRIES ON':fontsize=34:fontcolor=white:x=%d+(%d-text_w)/2:y=h*0.69:borderw=3:bordercolor=black@0.7:enable='between(t\\,26\\,31.5)'[B]"
          % (FONT, W // 2 - colw - 40 + 150, FONT, W // 2 + 40 + 200, FONT, FONT, FONT, W // 2 - colw - 40, colw))
# ---- segment C: climax replay at half speed (ep1 ring 18.6-21.3 s of entry; ep2 ring 21.5-24.5 s) ----
segC = ("[1:v]trim=18.0:22.0,setpts=2*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=2,scale=%d:-2[Lc];"
        "[2:v]trim=21.0:25.0,setpts=2*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=2,scale=%d:-2[Rc];"
        "color=c=0x0a0d18:s=%dx%d:d=10,format=yuv420p[Cbg];[Cbg][Lc]overlay=%d:(H-h)/2[C1];[C1][Rc]overlay=%d:(H-h)/2,"
        % (colw, colw, W, H, W // 2 - colw - 40, W // 2 + 40)
        + "drawtext=fontfile='%s':text='THE SAME CHEMISTRY\\, TWICE':fontsize=44:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.9:borderw=3:bordercolor=black@0.7:enable='between(t\\,0.5\\,4)',"
          "drawtext=fontfile='%s':text='RELEASED. HARMLESS.':fontsize=36:fontcolor=white:x=%d:y=h*0.12:borderw=3:bordercolor=black@0.7:enable='between(t\\,5\\,10)',"
          "drawtext=fontfile='%s':text='LOCKED. FOR GOOD.':fontsize=36:fontcolor=white:x=%d:y=h*0.12:borderw=3:bordercolor=black@0.7:enable='between(t\\,5\\,10)'[C]"
          % (FONT, FONT, W // 2 - colw - 40 + 120, FONT, W // 2 + 40 + 170))
# ---- segment D: outro from ep2 lysis (entry 25-33.7) pillarboxed, closing statements ----
segD = ("[2:v]trim=25.0:33.7,setpts=1.6*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=4.1,split[d0][d1];"
        "[d0]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,gblur=sigma=40,eq=brightness=-0.3[dbg];"
        "[d1]scale=-2:%d[dfg];[dbg][dfg]overlay=(W-w)/2:0," % (W, H, W, H, H)
        + head('ONE ENZYME MADE THE DIFFERENCE', 9.5, 12.3) + ',' + head('THAT IS WHAT RESISTANCE IS', 12.5, 18.0) + "[D]")
# ---- end card (6.5 s) ----
segE = ("color=c=0x0a0d18:s=%dx%d:d=6.5,format=yuv420p,"
        "drawtext=fontfile='%s':text='NEXT\\: HOW BACTERIA GET THE ENZYME':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=h*0.42,"
        "drawtext=fontfile='%s':text='Episodes 1 and 2 are on the channel as Shorts':fontsize=34:fontcolor=0xffd86e:x=(w-text_w)/2:y=h*0.56[E]" % (W, H, FONT, FONT))

graph = ";".join([segA, segT, segB, segC, segD, segE,
                  "[A][T][B][C][D][E]concat=n=6:v=1:a=0,format=yuv420p[v]"])
with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
    fh.write(graph)
    script = fh.name
silent = OUT.replace('.mp4', '_silent.mp4')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', tour, '-i', e1, '-i', e2, '-/filter_complex', script, '-map', '[v]',
       '-r', '30', '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p']
if test:
    cmd += ['-t', str(test)]
cmd.append(silent)
if '--audio-only' in sys.argv and os.path.exists(silent):   # remix without re-rendering the picture
    r = subprocess.CompletedProcess(cmd, 0)
else:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
os.unlink(script)
if r.returncode:
    print(r.stderr[-600:]); sys.exit(1)
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', silent],
                         capture_output=True, text=True).stdout.strip())
print('video %.1f s' % D)

narr = sorted(glob.glob(os.path.join(EP, 'narration', '*.wav')))
# ---- audio: music (+ narration clips if present, ducking) + two ring SFX ----
times = [1.0, 4.8, 13.5, 21.0, 30.3, 33.5, 44.5, 41.0, 51.0, 52.3, 61.4, 67.0, 72.3, 80.5, 93.0]   # NARRATION.md; 07/08 swapped on purpose
inputs = ['-i', silent, '-i', MUSIC, '-i', SFX]
fil = ["[1:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,afade=t=out:st=%.2f:d=3,loudnorm=I=%d:TP=-1.5:LRA=9[m0]" % (D, D - 3, -20 if narr else -18)]
# SFX at both ring openings in the replay segment (68.6 + 1.2 and 68.6 + 1.0 approx) and in the split (33 + 18.6, 33 + 21.5)
sfx_at = [33 + 18.7, 33 + 22.1, 64.5 + 1.4, 64.5 + 2.2]
sx = []
for i, t in enumerate(sfx_at):
    fil.append("[2:a]adelay=%d|%d,volume=0.8[s%d]" % (int(t * 1000), int(t * 1000), i))
    sx.append("[s%d]" % i)
mix_in = "[m0]" + "".join(sx)
n_mix = 1 + len(sx)
if narr:
    for i, f in enumerate(narr):
        inputs += ['-i', f]
        t = times[i] if i < len(times) else times[-1] + 8 * (i - len(times) + 1)
        fil.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=%d|%d,volume=6dB[n%d]" % (3 + i, int(t * 1000), int(t * 1000), i))
    fil.append("".join("[n%d]" % i for i in range(len(narr))) + "amix=inputs=%d:normalize=0:duration=longest,asplit[nark][nar]" % len(narr))
    fil.append("[m0][nark]sidechaincompress=threshold=0.01:ratio=10:attack=60:release=700[md]")
    mix_in = "[md]" + "".join(sx) + "[nar]"
    n_mix = 2 + len(sx)
fil.append(mix_in + "amix=inputs=%d:normalize=0:duration=first,alimiter=limit=0.95[a]" % n_mix)
cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ";".join(fil), '-map', '0:v', '-map', '[a]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode:
    print(r.stderr[-600:]); sys.exit(1)
print('OK', OUT, 'narration clips:', len(narr))
