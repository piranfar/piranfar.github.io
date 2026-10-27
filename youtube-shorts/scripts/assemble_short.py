"""Assemble a Short: HUD clip + music (loudness-normalised, ducked under narration) + SFX cues
+ optional narration clips placed by timecode. Writes OUT and OUT_mobile (720p).

Usage: python scripts/assemble_short.py IN_HUD.mp4 OUT.mp4 [--narration DIR --times t1,t2,...]
                                        [--ring t1,t2,...] [--boom t1,...] [--whoosh t1,...] [--music-db -18]
SFX come from tools/sfx (scripts/make_sfx.py); music is tools/music_rain_over_kyoto_station.mp3.
"""
import subprocess, sys, os, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(BASE, 'tools', 'music_rain_over_kyoto_station.mp3')
SFXD = os.path.join(BASE, 'tools', 'sfx')


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def times(name):
    v = arg(name)
    return [float(x) for x in v.split(',')] if v else []


src, out = sys.argv[1], sys.argv[2]
narr_dir = arg('--narration')
narr_times = times('--times')
music_db = int(arg('--music-db', '-18'))
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', src],
                         capture_output=True, text=True).stdout.strip())
narr = sorted(glob.glob(os.path.join(narr_dir, '*.wav'))) if narr_dir else []
if narr:
    assert len(narr) == len(narr_times), 'need one timecode per narration clip'
    music_db = min(music_db, -20)
inputs = ['-i', src, '-i', MUSIC]
cues = [('ring', t, 0.8) for t in times('--ring')] + [('boom', t, 0.6) for t in times('--boom')] + [('whoosh', t, 0.6) for t in times('--whoosh')]
names = sorted(set(c[0] for c in cues))
idx = {}
for nm in names:
    idx[nm] = len(inputs) // 2
    inputs += ['-i', os.path.join(SFXD, {'ring': 'ring_break.wav', 'boom': 'boom.wav', 'whoosh': 'whoosh.wav'}[nm])]
fil = ["[1:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,afade=t=out:st=%.2f:d=2.5,loudnorm=I=%d:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=%.2f[m0]"
       % (D, D - 2.5, music_db, D)]
sx = []
for i, (nm, t, vol) in enumerate(cues):
    fil.append("[%d:a]adelay=%d|%d,volume=%.2f[s%d]" % (idx[nm], int(t * 1000), int(t * 1000), vol, i))
    sx.append("[s%d]" % i)
if narr:
    base = len(inputs) // 2
    for i, f in enumerate(narr):
        inputs += ['-i', f]
        t = narr_times[i]
        fil.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=%d|%d,volume=6dB[n%d]" % (base + i, int(t * 1000), int(t * 1000), i))
    fil.append("".join("[n%d]" % i for i in range(len(narr))) + "amix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%.2f,asplit[nark][nar]" % (len(narr), D))
    fil.append("[m0][nark]sidechaincompress=threshold=0.01:ratio=10:attack=60:release=700[md]")
    mix_in, n = "[md]" + "".join(sx) + "[nar]", 2 + len(sx)
else:
    mix_in, n = "[m0]" + "".join(sx), 1 + len(sx)
fil.append(mix_in + "amix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%.2f,atrim=0:%.2f,alimiter=limit=0.95[a]" % (n, D, D))
cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ";".join(fil), '-map', '0:v', '-map', '[a]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode:
    print(r.stderr[-800:]); sys.exit(1)
mobile = out.replace('.mp4', '_mobile.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '24', '-preset', 'fast', '-c:a', 'copy', mobile], check=True)
print('ASSEMBLED', out, '%.1f s' % D, 'narration clips:', len(narr))
