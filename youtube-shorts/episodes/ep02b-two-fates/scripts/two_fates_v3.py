"""Episode 2b: Two Fates, v3 (polish pass). Landscape 1920x1080, 99 s.

Three stages, each re-runnable (--stage picture|text|audio|all):
  picture : ffmpeg. HUD-free sources, pillarboxed intro/outro, split screen that slides in,
            ping-pong instead of a frozen left column, dip-to-black transitions, film grade
            (contrast, saturation, vignette, grain). Writes renders/two_fates_v3_base.mp4.
  text    : PIL, one text layer over the base: margin labels with leaders (from the episodes'
            anchor files), animated title, column headers and captions, divergence tint and
            seam, replay/outro headlines, end card with the episode thumbnails.
            Writes renders/two_fates_v3_silent.mp4.
  audio   : music (ducked), narration clips by timecode, ring SFX, ambience, boom, whoosh, riser.
            Writes renders/two_fates_v3.mp4.
Timeline (film seconds) is the same as v2 so the narration timecodes hold:
  0-30 intro tour | 30-33 title | 33-64.5 split | 64.5-74.5 replay | 74.5-92.5 outro | 92.5-102 end card
"""
import subprocess, sys, os, glob, json, math, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02b-two-fates')
E1 = os.path.join(BASE, 'episodes', 'ep01-envelope')
E2 = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall')
MUSIC = os.path.join(BASE, 'tools', 'music_rain_over_kyoto_station.mp3')
SFXD = os.path.join(BASE, 'tools', 'sfx')
FONT_B = 'C:/Windows/Fonts/segoeuib.ttf'
FONT_R = 'C:/Windows/Fonts/segoeui.ttf'
REN = os.path.join(EP, 'renders')
BASE_MP4 = os.path.join(REN, 'two_fates_v3_base.mp4')
SILENT = os.path.join(REN, 'two_fates_v3_silent.mp4')
OUT = os.path.join(REN, 'two_fates_v3.mp4')
W, H, FPS = 1920, 1080, 30
STAGE = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'all'
TEST = float(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else None

tour = os.path.join(E1, 'renders', 'film1_v2_tour.mp4')
e1 = os.path.join(E1, 'renders', 'film1_v2_entry.mp4')
e2 = os.path.join(E2, 'renders', 'film2_entry.mp4')
for f in (tour, e1, e2):
    assert os.path.exists(f), f

# ---- geometry shared by the stages ----
COLW = 540                       # split column width (1080 -> 540, scale 0.5)
COLH = 960
LX, RX = W // 2 - COLW - 40, W // 2 + 40
CY = (H - COLH) // 2
PBW = 608                        # pillarbox column (1920/1080 of 1080 -> 607.5 -> 608)
PBX = (W - PBW) // 2
T_TITLE, T_SPLIT, T_REPLAY, T_OUTRO, T_END, T_LEN = 30.0, 33.0, 64.5, 74.5, 92.5, 102.0   # last line ends ~97 s; music alone after
SPLIT_L_SECS = 25.3              # ep1 entry runs to its end card; then ping-pong of the last 3.1 s
PING = 3.1
RING_REPLAY = (1.4, 2.2)         # ring SFX offsets inside the replay segment (v4 overrides)

# ======================================================================================
# stage 1: picture
# ======================================================================================
def stage_picture():
    pb = ("scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,gblur=sigma=40,eq=brightness=-0.28:saturation=0.8" % (W, H, W, H))
    segA = ("[0:v]trim=0:30,setpts=PTS-STARTPTS,split[a0][a1];[a0]%s[abg];[a1]scale=-2:%d[afg];"
            "[abg][afg]overlay=(W-w)/2:0,fade=t=in:st=0:d=1.2,fade=t=out:st=29.3:d=0.7,setsar=1[A]" % (pb, H))
    # title backdrop: the last 3 s of the tour, blurred and dark, still moving
    segT = ("[0:v]trim=27:30,setpts=PTS-STARTPTS,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
            "gblur=sigma=60,eq=brightness=-0.42:saturation=0.5,fade=t=in:st=0:d=0.6,fade=t=out:st=2.6:d=0.4,setsar=1[T]" % (W, H, W, H))
    # split: left = ep1 entry to 25.3 s then reverse/forward of its last 3.1 s (no frozen frame); right = ep2 entry
    slide_l = "'%d-%d*pow(1-min(1\\,t/0.7)\\,2)'" % (LX, LX + COLW)
    slide_r = "'%d+%d*pow(1-min(1\\,t/0.7)\\,2)'" % (RX, W - RX)
    segB = ("[1:v]trim=0:%.1f,setpts=PTS-STARTPTS[L0];[1:v]trim=%.1f:%.1f,setpts=PTS-STARTPTS,reverse[Lr];"
            "[1:v]trim=%.1f:%.1f,setpts=PTS-STARTPTS[Lf];[L0][Lr][Lf]concat=n=3:v=1:a=0,trim=0:31.5,scale=%d:-2[L];"
            "[2:v]trim=0:31.5,setpts=PTS-STARTPTS,scale=%d:-2[R];color=c=0x0a0d18:s=%dx%d:d=31.5,format=yuv420p[Bbg];"
            "[Bbg][L]overlay=x=%s:y=%d[B1];[B1][R]overlay=x=%s:y=%d,fade=t=out:st=31.1:d=0.4,setsar=1[B]"
            % (SPLIT_L_SECS, SPLIT_L_SECS - PING, SPLIT_L_SECS, SPLIT_L_SECS - PING, SPLIT_L_SECS, COLW, COLW, W, H,
               slide_l, CY, slide_r, CY))
    segC = ("[1:v]trim=18.0:22.0,setpts=2*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=2,scale=%d:-2[Lc];"
            "[2:v]trim=21.0:25.0,setpts=2*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=2,scale=%d:-2[Rc];"
            "color=c=0x0a0d18:s=%dx%d:d=10,format=yuv420p[Cbg];[Cbg][Lc]overlay=%d:%d[C1];[C1][Rc]overlay=%d:%d,"
            "fade=t=in:st=0:d=0.4,fade=t=out:st=9.6:d=0.4,setsar=1[C]" % (COLW, COLW, W, H, LX, CY, RX, CY))
    segD = ("[2:v]trim=25.0:33.7,setpts=1.6*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration=4.1,split[d0][d1];"
            "[d0]%s[dbg];[d1]scale=-2:%d[dfg];[dbg][dfg]overlay=(W-w)/2:0,fade=t=in:st=0:d=0.5,fade=t=out:st=17.3:d=0.7,setsar=1[D]" % (pb, H))
    segE = "color=c=0x0a0d18:s=%dx%d:d=%.1f,format=yuv420p,setsar=1[E]" % (W, H, T_LEN - T_END)
    grade = "eq=contrast=1.05:saturation=1.08,vignette=angle=PI/4.6,noise=alls=5:allf=t+u,format=yuv420p[v]"
    graph = ";".join([segA, segT, segB, segC, segD, segE, "[A][T][B][C][D][E]concat=n=6:v=1:a=0," + grade])
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write(graph)
        script = fh.name
    os.makedirs(REN, exist_ok=True)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', tour, '-i', e1, '-i', e2, '-/filter_complex', script, '-map', '[v]',
           '-r', str(FPS), '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p']
    if TEST:
        cmd += ['-t', str(TEST)]
    cmd.append(BASE_MP4)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.unlink(script)
    if r.returncode:
        print(r.stderr[-800:]); sys.exit(1)
    print('PICTURE_DONE', BASE_MP4)


# ======================================================================================
# stage 2: text layer
# ======================================================================================
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def vis_window(t, a, b, fi=0.35, fo=0.35):
    if t < a or t > b:
        return 0.0
    return min(ease((t - a) / fi), ease((b - t) / fo))


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, int(size))


def text_halo(d, xy, text, fnt, fill, anchor='la', halo=170):
    x, y = xy
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        d.text((x + dx, y + dy), text, font=fnt, fill=(0, 0, 0, int(halo * fill[3] / 255)), anchor=anchor)
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def load_anchors(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


ANC1 = load_anchors(os.path.join(E1, 'renders', 'film1_v2_entry_anchors.json'))
ANC2 = load_anchors(os.path.join(E2, 'renders', 'film2_entry_anchors.json'))
ANCT = load_anchors(os.path.join(E1, 'renders', 'film1_v2_tour_anchors.json'))

F_LABEL = font(H * 0.033)
F_HEAD = font(H * 0.042)
F_COLHEAD = font(H * 0.036)
F_CAP = font(H * 0.030)
F_TITLE = font(H * 0.15)
F_SUB = font(H * 0.044)
F_SMALL = font(H * 0.028, bold=False)


class Geom:
    """Where an episode frame (1080x1920) sits in the film frame, and which margin its labels use."""
    def __init__(self, x, y, scale, side):
        self.x, self.y, self.s, self.side = x, y, scale, side

    def map(self, p):
        return self.x + p[0] * self.s, self.y + p[1] * self.s


G_LEFT = Geom(LX, CY, 0.5, 'left')
G_RIGHT = Geom(RX, CY, 0.5, 'right')
G_PB = Geom(PBX, 0, PBW / 1080.0, None)     # side chosen per label corner


def draw_margin_label(d, fr_ep, lab, geom, side=None, color=(255, 255, 255)):
    """Pointer ring on the subject, a leader into the margin beside the column, the label there."""
    f0, f1 = lab['frames']
    if fr_ep < f0 or fr_ep > f1:
        return
    pos = lab['pos'].get(str(fr_ep))
    if pos is None:
        return
    vis = min(ease((fr_ep - f0) / 8.0), ease((f1 - fr_ep) / 8.0))
    if vis <= 0:
        return
    side = side or geom.side or ('right' if lab['corner'].endswith('r') else 'left')
    ax, ay = geom.map(pos)
    a = int(255 * vis)
    pulse = 0.5 + 0.5 * math.sin(fr_ep * 0.35)
    r = H * 0.010 + H * 0.004 * pulse
    d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=color + (a,), width=3)
    d.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=color + (a,))
    text = lab['text']
    if not text:
        return
    fl = F_LABEL
    tw = d.textlength(text, font=fl)
    ly = min(max(ay, 70), H - 70)
    if side == 'left':
        ex = geom.x - 34                      # leader ends at the column's left edge, label beyond it
        tx = ex - 16
        anchor = 'rm'
        maxw = geom.x - 60
    else:
        ex = geom.x + 1080 * geom.s + 34
        tx = ex + 16
        anchor = 'lm'
        maxw = W - ex - 60
    if tw > maxw:
        fl = font(F_LABEL.size * maxw / tw)
    elbow = (ex + (40 if side == 'left' else -40), ly)
    end = (ex, ly)
    seg1 = math.hypot(elbow[0] - ax, elbow[1] - ay)
    seg2 = abs(end[0] - elbow[0])
    drawn = (seg1 + seg2) * ease((fr_ep - f0) / 8.0)
    lw = 3
    lc = (235, 245, 255, a)
    if drawn <= seg1:
        k = drawn / max(seg1, 1e-6)
        d.line([(ax, ay), (ax + (elbow[0] - ax) * k, ay + (elbow[1] - ay) * k)], fill=lc, width=lw)
    else:
        d.line([(ax, ay), elbow], fill=lc, width=lw)
        k = (drawn - seg1) / max(seg2, 1e-6)
        d.line([elbow, (elbow[0] + (end[0] - elbow[0]) * k, ly)], fill=lc, width=lw)
    if drawn >= (seg1 + seg2) * 0.95:
        text_halo(d, (tx, ly), text, fl, color + (a,), anchor=anchor)


def draw_burst(d, fr_ep, anc, key, f0, f1, geom):
    if fr_ep < f0 or fr_ep > f1:
        return
    pos = anc['labels'][key]['pos'].get(str(fr_ep))
    if pos is None:
        return
    ax, ay = geom.map(pos)
    for k in range(3):
        t = (fr_ep - f0 - k * 6) / float(f1 - f0 - 12)
        if 0 <= t <= 1:
            r = H * (0.02 + 0.17 * ease(t))
            a = int(255 * (1 - t) ** 1.5)
            d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=(255, 225, 160, a), width=max(2, int(4 * (1 - t) + 1)))


def headline(d, t, a, b, text, y=0.90, fnt=None, col=(255, 216, 110), x=W / 2, rise=18):
    v = vis_window(t, a, b)
    if v <= 0:
        return
    fnt = fnt or F_HEAD
    if d.textlength(text, font=fnt) > 0.8 * W:
        fnt = font(fnt.size * 0.8 * W / d.textlength(text, font=fnt))
    yy = H * y + rise * (1 - ease((t - a) / 0.35))
    text_halo(d, (x, yy), text, fnt, col + (int(255 * v),), anchor='mm')


def col_caption(d, t, a, b, text, geom, y=0.69, col=(255, 255, 255), fnt=None):
    """Caption inside a column (centred), for a beat that belongs to one side only."""
    v = vis_window(t, a, b)
    if v <= 0:
        return
    fnt = fnt or F_CAP
    cx = geom.x + 1080 * geom.s / 2
    maxw = 1080 * geom.s - 30
    if d.textlength(text, font=fnt) > maxw:
        fnt = font(fnt.size * maxw / d.textlength(text, font=fnt))
    yy = geom.y + COLH * y + 14 * (1 - ease((t - a) / 0.35))
    text_halo(d, (cx, yy), text, fnt, col + (int(255 * v),), anchor='mm')


def draw_title(img, d, t):
    """TWO FATES: letters spread apart as they fade in, a gold rule grows under them, then the subtitle."""
    lt = t - T_TITLE
    v = vis_window(t, T_TITLE + 0.15, T_SPLIT - 0.05, 0.6, 0.4)
    if v <= 0:
        return
    text = 'TWO FATES'
    spread = 0.10 + 0.08 * ease(lt / 2.6)         # tracking in em, keeps widening slowly
    size = F_TITLE.size * (0.96 + 0.04 * ease(lt / 2.6))
    fnt = font(size)
    widths = [d.textlength(ch, font=fnt) for ch in text]
    gap = size * spread
    total = sum(widths) + gap * (len(text) - 1)
    x = W / 2 - total / 2
    y = H * 0.40
    a = int(255 * v)
    for ch, w in zip(text, widths):
        if ch != ' ':
            text_halo(d, (x + w / 2, y), ch, fnt, (255, 255, 255, a), anchor='mm', halo=120)
        x += w + gap
    rule = ease((lt - 0.5) / 0.8) * v
    if rule > 0:
        hw = W * 0.14 * rule
        d.line([(W / 2 - hw, H * 0.515), (W / 2 + hw, H * 0.515)], fill=(255, 216, 110, int(255 * rule)), width=3)
    sv = vis_window(t, T_TITLE + 1.0, T_SPLIT - 0.05, 0.5, 0.4)
    if sv > 0:
        text_halo(d, (W / 2, H * 0.585 + 10 * (1 - ease((lt - 1.0) / 0.5))), 'SAME DRUG. SAME DOOR.', F_SUB,
                  (255, 216, 110, int(255 * sv)), anchor='mm')


TINT_L = Image.new('RGBA', (COLW, COLH), (40, 90, 200, 255))
TINT_R = Image.new('RGBA', (COLW, COLH), (230, 120, 40, 255))


def draw_divergence(img, d, t):
    """From HERE THEY PART: the left column cools, the right warms, and the seam between them lights up."""
    if t < 48.0 or t > T_REPLAY:
        return
    k = ease((t - 48.0) / 3.0)
    if k <= 0:
        return
    a = int(38 * k)
    for tint, x in ((TINT_L, LX), (TINT_R, RX)):
        layer = tint.copy()
        layer.putalpha(a)
        img.alpha_composite(layer, (x, CY))
    seam = vis_window(t, 48.0, 52.5, 0.6, 1.5)
    if seam > 0:
        glow = Image.new('RGBA', (60, COLH + 40), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.line([(30, 20), (30, COLH + 20)], fill=(255, 216, 110, int(220 * seam)), width=3)
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(glow, (W // 2 - 30, CY - 20))


def draw_col_headers(d, t):
    v = vis_window(t, T_SPLIT + 0.5, T_REPLAY - 0.3, 0.5, 0.3)
    if v <= 0:
        return
    dy = -16 * (1 - ease((t - T_SPLIT - 0.5) / 0.5))
    a = int(255 * v)
    text_halo(d, (LX + COLW / 2, CY - 26 + dy), 'WITH A BETA-LACTAMASE', F_COLHEAD, (255, 255, 255, a), anchor='mm')
    text_halo(d, (RX + COLW / 2, CY - 26 + dy), 'WITHOUT', F_COLHEAD, (255, 255, 255, a), anchor='mm')


THUMB1 = Image.open(os.path.join(E1, 'thumbs', 'thumb_A_porin.jpg')).convert('RGBA')
THUMB2 = Image.open(os.path.join(E2, 'thumbs', 'thumb_A_wall.jpg')).convert('RGBA')


def draw_endcard(img, d, t):
    """Next-episode line, the two Shorts as portrait cards (their real thumbnails), subscribe line."""
    v = vis_window(t, T_END + 0.3, T_LEN, 0.6, 0.8)
    if v <= 0:
        return
    a = int(255 * v)
    text_halo(d, (W / 2, H * 0.12), 'NEXT: HOW BACTERIA GET THE ENZYME', F_HEAD, (255, 255, 255, a), anchor='mm')
    text_halo(d, (W / 2, H * 0.19), 'and how they share it', F_SMALL, (255, 216, 110, a), anchor='mm')
    th_h = int(H * 0.52)
    for i, (th, label, x) in enumerate(((THUMB1, 'EPISODE 1   THE ENVELOPE', W * 0.36), (THUMB2, 'EPISODE 2   HITTING THE WALL', W * 0.64))):
        tv = vis_window(t, T_END + 0.9 + 0.25 * i, T_LEN, 0.5, 0.8)
        if tv <= 0:
            continue
        tw = int(th_h * th.width / th.height)
        timg = th.resize((tw, th_h), Image.LANCZOS)
        timg.putalpha(int(255 * tv))
        ty = int(H * 0.26 + 20 * (1 - ease((t - T_END - 0.9 - 0.25 * i) / 0.5)))
        img.alpha_composite(timg, (int(x - tw / 2), ty))
        d.rectangle([x - tw / 2 - 2, ty - 2, x + tw / 2 + 2, ty + th_h + 2], outline=(255, 255, 255, int(140 * tv)), width=2)
        text_halo(d, (x, ty + th_h + 30), label, F_SMALL, (235, 235, 235, int(255 * tv)), anchor='mm')
    sv = vis_window(t, T_END + 1.8, T_LEN, 0.5, 0.8)
    if sv > 0:
        text_halo(d, (W / 2, H * 0.90), 'Both are on the channel as Shorts.  Subscribe for episode 3.', F_SMALL,
                  (255, 216, 110, int(255 * sv)), anchor='mm')


def draw_frame(img, fr):
    """fr is the 1-based film frame."""
    t = (fr - 1) / FPS
    d = ImageDraw.Draw(img)
    # ---- intro: tour labels in the margins (left corners -> left margin, right -> right) ----
    if t < T_TITLE:
        for lab in ANCT['labels'].values():
            draw_margin_label(d, fr, lab, G_PB)
    # ---- title ----
    draw_title(img, d, t)
    # ---- split ----
    if T_SPLIT <= t < T_REPLAY:
        fe = fr - int(T_SPLIT * FPS)           # episode frame (1-based) in both columns
        draw_divergence(img, d, t)
        d = ImageDraw.Draw(img)
        draw_col_headers(d, t)
        if fe <= SPLIT_L_SECS * FPS:
            draw_margin_label(d, fe, ANC1['labels']['drug'], G_LEFT)
            draw_margin_label(d, fe, ANC1['labels']['tem1'], G_LEFT)
            draw_burst(d, fe, ANC1, 'bond', 562, 596, G_LEFT)
        draw_margin_label(d, fe, ANC2['labels']['porin'], G_RIGHT)
        draw_margin_label(d, fe, ANC2['labels']['pbp'], G_RIGHT)
        draw_margin_label(d, fe, ANC2['labels']['gap'], G_RIGHT)
        draw_burst(d, fe, ANC2, 'bond', 662, 696, G_RIGHT)
        headline(d, t, 35.0, 47.0, 'SAME ENTRY, FRAME FOR FRAME')
        headline(d, t, 48.0, 52.0, 'HERE THEY PART')
        col_caption(d, t, 44.5, 47.5, 'NO ENZYME THIS TIME', G_RIGHT, y=0.69, col=(255, 216, 110))
        col_caption(d, t, 59.0, T_REPLAY - 0.3, 'THE CELL CARRIES ON', G_LEFT)
        col_caption(d, t, 60.5, T_REPLAY - 0.3, 'THE WALL STOPS GROWING', G_RIGHT, col=(255, 216, 110))
    # ---- replay ----
    if T_REPLAY <= t < T_OUTRO:
        lt = t - T_REPLAY
        # ep frames in the half-speed replay: ep1 18.0 s + lt/2 ; ep2 21.0 s + lt/2
        fe1 = int(18.0 * FPS + lt * FPS / 2) + 1
        fe2 = int(21.0 * FPS + lt * FPS / 2) + 1
        draw_burst(d, fe1, ANC1, 'bond', 562, 596, G_LEFT)
        draw_burst(d, fe2, ANC2, 'bond', 662, 696, G_RIGHT)
        headline(d, t, 65.0, 68.5, 'THE SAME CHEMISTRY, TWICE')
        col_caption(d, t, 69.5, T_OUTRO - 0.3, 'RELEASED. HARMLESS.', G_LEFT, y=0.08)
        col_caption(d, t, 69.5, T_OUTRO - 0.3, 'LOCKED. FOR GOOD.', G_RIGHT, y=0.08)
        text_halo(d, (LX + COLW / 2, CY - 26), 'WITH A BETA-LACTAMASE', F_COLHEAD, (255, 255, 255, int(255 * vis_window(t, T_REPLAY + 0.3, T_OUTRO - 0.3))), anchor='mm')
        text_halo(d, (RX + COLW / 2, CY - 26), 'WITHOUT', F_COLHEAD, (255, 255, 255, int(255 * vis_window(t, T_REPLAY + 0.3, T_OUTRO - 0.3))), anchor='mm')
    # ---- outro ----
    if T_OUTRO <= t < T_END:
        headline(d, t, 84.0, 86.8, 'ONE ENZYME MADE THE DIFFERENCE', y=0.88)
        headline(d, t, 87.0, T_END - 0.5, 'THAT IS WHAT RESISTANCE IS', y=0.88)
    # ---- end card ----
    if t >= T_END - 0.2:
        draw_endcard(img, d, t)


def stage_text():
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', BASE_MP4, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                          stdout=subprocess.PIPE, bufsize=10 ** 8)
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium',
                           '-pix_fmt', 'yuv420p', SILENT], stdin=subprocess.PIPE)
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


# ======================================================================================
# stage 3: audio
# ======================================================================================
def stage_audio():
    D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', SILENT],
                             capture_output=True, text=True).stdout.strip())
    narr = sorted(glob.glob(os.path.join(EP, 'narration', '*.wav')))
    times = [1.0, 4.8, 13.5, 21.0, 30.3, 33.5, 44.5, 41.0, 51.0, 52.3, 61.4, 67.0, 72.3, 80.5, 93.0]   # NARRATION.md
    sfx = {'ring': os.path.join(SFXD, 'ring_break.wav'), 'amb': os.path.join(SFXD, 'ambience.wav'),
           'boom': os.path.join(SFXD, 'boom.wav'), 'whoosh': os.path.join(SFXD, 'whoosh.wav'), 'riser': os.path.join(SFXD, 'riser.wav')}
    cues = [('ring', T_SPLIT + 18.7, 0.8), ('ring', T_SPLIT + 22.1, 0.8), ('ring', T_REPLAY + RING_REPLAY[0], 0.7), ('ring', T_REPLAY + RING_REPLAY[1], 0.7),
            ('riser', T_TITLE - 2.5, 0.5), ('boom', T_TITLE, 0.9), ('whoosh', T_SPLIT - 0.15, 0.7),
            ('whoosh', T_REPLAY - 0.1, 0.5), ('boom', 48.0, 0.45), ('whoosh', T_OUTRO - 0.1, 0.4)]
    inputs = ['-i', SILENT, '-i', MUSIC]
    names = ['ring', 'amb', 'boom', 'whoosh', 'riser']
    for nm in names:
        inputs += ['-i', sfx[nm]]
    idx = {nm: 2 + i for i, nm in enumerate(names)}
    fil = ["[1:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,afade=t=out:st=%.2f:d=3,loudnorm=I=%d:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=%.2f[m0]"
           % (D, D - 3, -20 if narr else -18, D)]
    # ambience: very low, under everything, fades with the picture
    fil.append("[%d:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2,afade=t=out:st=%.2f:d=2,volume=-34dB[amb]" % (idx['amb'], D, D - 2))
    sx = []
    for i, (nm, t, vol) in enumerate(cues):
        fil.append("[%d:a]adelay=%d|%d,volume=%.2f[s%d]" % (idx[nm], int(t * 1000), int(t * 1000), vol, i))
        sx.append("[s%d]" % i)
    nxt = len(names) + 2
    if narr:
        for i, f in enumerate(narr):
            inputs += ['-i', f]
            t = times[i]
            fil.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=%d|%d,volume=6dB[n%d]" % (nxt + i, int(t * 1000), int(t * 1000), i))
        fil.append("".join("[n%d]" % i for i in range(len(narr))) + "amix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%.2f,asplit[nark][nar]" % (len(narr), D))   # pad: sidechaincompress stops when the key ends
        fil.append("[m0][nark]sidechaincompress=threshold=0.01:ratio=10:attack=60:release=700[md]")
        mix_in, n_mix = "[md][amb]" + "".join(sx) + "[nar]", 3 + len(sx)
    else:
        mix_in, n_mix = "[m0][amb]" + "".join(sx), 2 + len(sx)
    fil.append(mix_in + "amix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%.2f,atrim=0:%.2f,alimiter=limit=0.95[a]" % (n_mix, D, D))
    cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ";".join(fil), '-map', '0:v', '-map', '[a]',
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print(r.stderr[-800:]); sys.exit(1)
    print('AUDIO_DONE', OUT, 'narration clips:', len(narr))


if __name__ == '__main__':
    if STAGE in ('picture', 'all'):
        stage_picture()
    if STAGE in ('text', 'all'):
        stage_text()
    if STAGE in ('audio', 'all'):
        stage_audio()
