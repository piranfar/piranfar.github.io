"""Episode 3 landscape assembly: renders/film3_wide.mp4 -> renders/ep3_wide_final.mp4 (+ _720p).

Stages (--stage picture|text|audio|all):
  picture : fades + film grade (ffmpeg)                     -> ep3_wide_base.mp4
  text    : PIL layer: inline labels from film3_wide_anchors.json, headlines, cold-open title,
            bursts, end card                                 -> ep3_wide_silent.mp4
  audio   : scripts/assemble_short.py with narration_wide + music + SFX -> ep3_wide_final.mp4
"""
import os, sys, subprocess, json, math
BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep03-where-it-comes-from')
REN = os.path.join(EP, 'renders')
sys.path.insert(0, os.path.join(BASE, 'episodes', 'ep02b-two-fates', 'scripts'))
STAGE = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'all'
import two_fates_v3 as v3
import two_fates_v4 as v4
from two_fates_v3 import W, H, FPS, ease, vis_window, font, text_halo, load_anchors, Geom, draw_burst, headline, F_HEAD, F_SMALL, F_SUB
from two_fates_v4 import draw_inline_label, G_FULL
from PIL import Image, ImageDraw

SRC = os.path.join(REN, 'film3_wide.mp4')
BASE_MP4 = os.path.join(REN, 'ep3_wide_base.mp4')
SILENT = os.path.join(REN, 'ep3_wide_silent.mp4')
OUT = os.path.join(REN, 'ep3_wide_final.mp4')
A = load_anchors(os.path.join(REN, 'film3_wide_anchors.json'))
NARR_TIMES = [1.0, 12.0, 21.5, 25.0, 34.8, 38.2, 50.0, 54.5, 61.0, 68.0, 73.0, 79.0, 83.0, 88.0, 100.0, 113.0]


def stage_picture():
    D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', SRC],
                             capture_output=True, text=True).stdout.strip())
    # tail: hold the last frame 4 s for the end card; last segment: slow push-in so the four cells read
    D += 4.0
    z = "(1+0.35*min(max((t-106)/6,0),1))"
    vf = ("tpad=stop_mode=clone:stop_duration=4,crop=w=iw/%s:h=ih/%s:x=(iw-iw/%s)/2:y=(ih-ih/%s)/2,scale=%d:%d,"
          "fade=t=in:st=0:d=1.5,fade=t=out:st=%.2f:d=1.5,eq=contrast=1.05:saturation=1.08,vignette=angle=PI/4.6,noise=alls=5:allf=t+u,format=yuv420p"
          % (z, z, z, z, W, H, D - 1.5))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-vf', vf, '-r', str(FPS), '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', BASE_MP4], check=True)
    print('PICTURE_DONE', BASE_MP4, '%.1f s' % D)


F_TITLE = font(H * 0.12)
F_CARD = font(H * 0.055)
F_LABEL = font(H * 0.033)


def draw_frame(img, fr):
    t = (fr - 1) / FPS
    d = ImageDraw.Draw(img)
    for lab in A['labels'].values():
        draw_inline_label(d, fr, lab, G_FULL)
    for f0, f1, key in A.get('bursts', []):
        draw_burst(d, fr, A, key, f0, f1, G_FULL)
    for a, b, text in A.get('headlines', []):
        if text == 'ATHENS, 1963':
            v = vis_window(t, a, b, 0.8, 0.8)
            if v > 0:
                text_halo(d, (W / 2, H * 0.30), 'ATHENS, 1963', F_TITLE, (255, 255, 255, int(255 * v)), anchor='mm')
                sv = vis_window(t, a + 1.5, b, 0.6, 0.8)
                if sv > 0:
                    text_halo(d, (W / 2, H * 0.42), 'a blood culture that should have cleared, and did not', F_SUB, (255, 216, 110, int(255 * sv)), anchor='mm')
        else:
            headline(d, t, a, b, text, y=0.90)
    for a, b, l1, l2 in A.get('cards', []):
        v = vis_window(t, a + 0.3, b, 0.6, 0.8)
        if v > 0:
            text_halo(d, (W / 2, H * 0.40), l1, F_CARD, (255, 255, 255, int(255 * v)), anchor='mm')
            text_halo(d, (W / 2, H * 0.50), l2, F_SUB, (255, 216, 110, int(255 * v)), anchor='mm')
            sv = vis_window(t, a + 1.5, b, 0.5, 0.8)
            if sv > 0:
                text_halo(d, (W / 2, H * 0.66), 'Episodes 1 and 2 and the comparison film Two Fates are on the channel.', F_SMALL, (235, 235, 235, int(255 * sv)), anchor='mm')
                text_halo(d, (W / 2, H * 0.72), 'Subscribe for episode 4: how we fight back.', F_SMALL, (255, 216, 110, int(255 * sv)), anchor='mm')


def stage_text():
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', BASE_MP4, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', SILENT], stdin=subprocess.PIPE)
    n = W * H * 4
    fr = 0
    while True:
        buf = rd.stdout.read(n)
        if len(buf) < n:
            break
        fr += 1
        img = Image.frombuffer('RGBA', (W, H), buf, 'raw', 'RGBA', 0, 1).copy()
        draw_frame(img, fr)
        wr.stdin.write(img.tobytes())
    wr.stdin.close()
    wr.wait()
    print('TEXT_DONE', SILENT, fr, 'frames')


def stage_audio():
    cmd = [sys.executable, os.path.join(BASE, 'scripts', 'assemble_short.py'), SILENT, OUT,
           '--narration', os.path.join(EP, 'narration_wide'), '--times', ','.join('%.1f' % t for t in NARR_TIMES),
           '--ring', '85.3', '--boom', '29.7,50.0,118.5', '--whoosh', '51.3,56.0,89.5']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(r.stdout.strip()[-400:], r.stderr.strip()[-400:])
    if r.returncode:
        sys.exit(1)
    p720 = OUT.replace('.mp4', '_720p.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k', p720], check=True)
    print('AUDIO_DONE', OUT)


if __name__ == '__main__':
    if STAGE in ('picture', 'all'):
        stage_picture()
    if STAGE in ('text', 'all'):
        stage_text()
    if STAGE in ('audio', 'all'):
        stage_audio()
