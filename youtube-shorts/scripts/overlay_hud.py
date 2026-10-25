"""2D pointing overlay for film 1 v2.
Reads a rendered clip plus its *_anchors.json (per-frame screen position of
each anchor, exported by film1_v2.py) and draws, in screen space:
 - a pulsing ring + dot on the anchor
 - a leader line that draws itself from the anchor to the label over 8 frames
 - a one-word label (white, dark halo) placed in a fixed free corner
 - optional headlines (gold, lower third) and a title for the first 3 s
Usage: python -I overlay_hud.py IN.mp4 ANCHORS.json OUT.mp4 [--title "TEXT"]
"""
import subprocess, sys, json, math
from PIL import Image, ImageDraw, ImageFont

FONT_B = 'C:/Windows/Fonts/segoeuib.ttf'
src, anc_path, out = sys.argv[1:4]
title = sys.argv[sys.argv.index('--title') + 1] if '--title' in sys.argv else None
with open(anc_path, encoding='utf-8') as fh:
    A = json.load(fh)
FPS = A['fps']
W, H = [int(v) for v in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                         'stream=width,height', '-of', 'csv=p=0', src],
                                        capture_output=True, text=True).stdout.strip().split(',')]
sx, sy = W / A['size'][0], H / A['size'][1]
f_label = ImageFont.truetype(FONT_B, int(H * 0.036))
f_head = ImageFont.truetype(FONT_B, int(H * 0.040))
f_title = ImageFont.truetype(FONT_B, int(H * 0.024))
M = int(W * 0.06)                     # screen margin
CORNERS = {'tl': (M, int(H * 0.16)), 'tr': (W - M, int(H * 0.16)), 'bl': (M, int(H * 0.78)), 'br': (W - M, int(H * 0.78))}


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def text_halo(d, xy, text, font, fill, anchor='la'):
    x, y = xy
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, text, font=font, fill=fill, anchor=anchor)


def draw_label(img, fr, lab):
    f0, f1 = lab['frames']
    if fr < f0 or fr > f1:
        return
    pos = lab['pos'].get(str(fr))
    if pos is None:
        return
    ax, ay = pos[0] * sx, pos[1] * sy
    t_in = ease((fr - f0) / 8.0)
    t_out = ease((f1 - fr) / 8.0)
    vis = min(t_in, t_out)
    if vis <= 0:
        return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(255 * vis)
    # pulsing ring + dot on the subject
    pulse = 0.5 + 0.5 * math.sin(fr * 0.35)
    r = H * 0.011 + H * 0.004 * pulse
    d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=(255, 255, 255, a), width=max(2, int(H * 0.0025)))
    d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], fill=(255, 255, 255, a))
    # label position and leader (elbow: horizontal run into the text)
    cx, cy = CORNERS[lab['corner']]
    right = lab['corner'].endswith('r')
    tw = d.textlength(lab['text'], font=f_label)
    tx = cx - tw if right else cx
    ty = cy
    end_x = (tx + tw + 14) if right else (tx - 14)
    end = (end_x, ty + f_label.size * 0.55)
    elbow = (end_x + (40 if right else -40), end[1])
    # draw the leader progressively: anchor -> elbow -> end
    seg1 = math.hypot(elbow[0] - ax, elbow[1] - ay)
    seg2 = abs(end[0] - elbow[0])
    total = seg1 + seg2
    drawn = total * ease((fr - f0) / 8.0)
    lw = max(2, int(H * 0.0022))
    if drawn <= seg1:
        k = drawn / max(seg1, 1e-6)
        d.line([(ax, ay), (ax + (elbow[0] - ax) * k, ay + (elbow[1] - ay) * k)], fill=(235, 245, 255, a), width=lw)
    else:
        d.line([(ax, ay), elbow], fill=(235, 245, 255, a), width=lw)
        k = (drawn - seg1) / max(seg2, 1e-6)
        d.line([elbow, (elbow[0] + (end[0] - elbow[0]) * k, elbow[1])], fill=(235, 245, 255, a), width=lw)
    if drawn >= total * 0.95:
        text_halo(d, (tx, ty), lab['text'], f_label, (255, 255, 255, a))
    img.alpha_composite(ov)


def draw_headlines(img, fr):
    t = fr / FPS
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for a0, a1, text in A.get('headlines', []):
        if a0 <= t <= a1:
            vis = min(ease((t - a0) / 0.35), ease((a1 - t) / 0.35))
            fh = f_head
            if d.textlength(text, font=fh) > 0.92 * W:
                fh = ImageFont.truetype(FONT_B, int(f_head.size * 0.92 * W / d.textlength(text, font=fh)))
            text_halo(d, (W / 2, H * 0.70), text, fh, (255, 216, 110, int(255 * vis)), anchor='mm')
    for a0, a1, l1, l2 in A.get('cards', []):
        if a0 <= t <= a1:
            vis = min(ease((t - a0) / 0.5), ease((a1 - t) / 0.5))
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(120 * vis)))
            for yy, txt, fnt, col in ((0.47, l1, f_head, (255, 255, 255)), (0.53, l2, f_label, (255, 216, 110))):
                if d.textlength(txt, font=fnt) > 0.88 * W:
                    fnt = ImageFont.truetype(FONT_B, int(fnt.size * 0.88 * W / d.textlength(txt, font=fnt)))
                text_halo(d, (W / 2, H * yy), txt, fnt, col + (int(255 * vis),), anchor='mm')
    if title and t < 3.2:
        vis = min(1.0, ease((t - 0.2) / 0.5), ease((3.2 - t) / 0.5))
        if vis > 0:
            text_halo(d, (W / 2, H * 0.06), title, f_title, (245, 245, 245, int(255 * vis)), anchor='mm')
    img.alpha_composite(ov)


labels = list(A['labels'].values())
rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                      stdout=subprocess.PIPE, bufsize=10 ** 8)
wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '%dx%d' % (W, H),
                       '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                       '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
n = W * H * 4
fr = 0
while True:
    buf = rd.stdout.read(n)
    if len(buf) < n:
        break
    fr += 1
    img = Image.frombuffer('RGBA', (W, H), buf, 'raw', 'RGBA', 0, 1).copy()
    for lab in labels:
        draw_label(img, fr, lab)
    draw_headlines(img, fr)
    wr.stdin.write(img.tobytes())
wr.stdin.close()
wr.wait()
print('OVERLAY_DONE', out, fr, 'frames')
