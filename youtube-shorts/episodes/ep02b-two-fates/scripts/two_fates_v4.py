"""Episode 2b: Two Fates, v4. Same timeline and text system as v3, with the native landscape shots
from film2b_shots.py replacing the pillarboxed and column segments where a full frame exists:
  0-30     tf_intro      native 16:9 tour, labels drawn inline (ring + leader + text near the subject)
  30-33    title over the blurred tail of the tour
  33-64.5  split screen from the vertical entries (unchanged: frame-for-frame comparison)
  64.5-74.5  tf_macro1 | tf_macro2 at half speed, full frame: the two ring openings, close
  74.5-92.5  tf_carry | tf_lysis, full frame, same camera: the wall keeps growing / the wall fails
  92.5-102  end card (narration ends ~97 s, then music only so the viewer can click on)
Stages as in v3: --stage picture|text|audio|all. Outputs renders/two_fates_v4*.mp4.
"""
import os, sys, subprocess, tempfile, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import two_fates_v3 as v3
from two_fates_v3 import (W, H, FPS, REN, EP, ease, vis_window, font, text_halo, load_anchors, Geom, draw_margin_label,
                          draw_burst, headline, col_caption, draw_title, draw_divergence, draw_col_headers, draw_endcard,
                          ANC1, ANC2, G_LEFT, G_RIGHT, F_LABEL, F_COLHEAD, T_TITLE, T_SPLIT, T_REPLAY, T_OUTRO, T_END, T_LEN,
                          SPLIT_L_SECS, PING, COLW, LX, RX, CY)
from PIL import Image, ImageDraw, ImageFilter

BASE_MP4 = os.path.join(REN, 'two_fates_v4_base.mp4')
SILENT = os.path.join(REN, 'two_fates_v4_silent.mp4')
OUT = os.path.join(REN, 'two_fates_v4.mp4')
v3.BASE_MP4, v3.SILENT, v3.OUT = BASE_MP4, SILENT, OUT
intro = os.path.join(REN, 'tf_intro.mp4')
macro1, macro2 = os.path.join(REN, 'tf_macro1.mp4'), os.path.join(REN, 'tf_macro2.mp4')
carry, lysis = os.path.join(REN, 'tf_carry.mp4'), os.path.join(REN, 'tf_lysis.mp4')
for f in (intro, macro1, macro2, carry, lysis):
    assert os.path.exists(f), f
ANCI = load_anchors(os.path.join(REN, 'tf_intro_anchors.json'))
ANCM1 = load_anchors(os.path.join(REN, 'tf_macro1_anchors.json'))
ANCM2 = load_anchors(os.path.join(REN, 'tf_macro2_anchors.json'))
ANCL = load_anchors(os.path.join(REN, 'tf_lysis_anchors.json'))
G_FULL = Geom(0, 0, 1.0, None)
G_HL, G_HR = Geom(0, 0, 1.0, None), Geom(960, 0, 1.0, None)      # left / right half of the frame
SAFE_X, SAFE_Y = int(W * 0.05), int(H * 0.06)


# ======================================================================================
def stage_picture():
    slide_l = "'%d-%d*pow(1-min(1\\,t/0.7)\\,2)'" % (LX, LX + COLW)
    slide_r = "'%d+%d*pow(1-min(1\\,t/0.7)\\,2)'" % (RX, W - RX)
    segA = "[0:v]trim=0:30,setpts=PTS-STARTPTS,fade=t=in:st=0:d=1.2,fade=t=out:st=29.3:d=0.7,setsar=1[A]"
    segT = ("[0:v]trim=27:30,setpts=PTS-STARTPTS,gblur=sigma=50,eq=brightness=-0.40:saturation=0.5,"
            "fade=t=in:st=0:d=0.6,fade=t=out:st=2.6:d=0.4,setsar=1[T]")
    segB = ("[1:v]trim=0:%.1f,setpts=PTS-STARTPTS[L0];[1:v]trim=%.1f:%.1f,setpts=PTS-STARTPTS,reverse[Lr];"
            "[1:v]trim=%.1f:%.1f,setpts=PTS-STARTPTS[Lf];[L0][Lr][Lf]concat=n=3:v=1:a=0,trim=0:31.5,scale=%d:-2[L];"
            "[2:v]trim=0:31.5,setpts=PTS-STARTPTS,scale=%d:-2[R];color=c=0x0a0d18:s=%dx%d:d=31.5,format=yuv420p[Bbg];"
            "[Bbg][L]overlay=x=%s:y=%d[B1];[B1][R]overlay=x=%s:y=%d,fade=t=out:st=31.1:d=0.4,setsar=1[B]"
            % (SPLIT_L_SECS, SPLIT_L_SECS - PING, SPLIT_L_SECS, SPLIT_L_SECS - PING, SPLIT_L_SECS, COLW, COLW, W, H,
               slide_l, CY, slide_r, CY))
    # the two macro shots, 5 s each, played at half speed side by side; a 4 px seam between them
    segC = ("[3:v]setpts=2*(PTS-STARTPTS),scale=958:1080[Mc1];[4:v]setpts=2*(PTS-STARTPTS),scale=958:1080[Mc2];"
            "color=c=0x0a0d18:s=%dx%d:d=10,format=yuv420p[Cbg];[Cbg][Mc1]overlay=0:0[C1];[C1][Mc2]overlay=962:0,"
            "fade=t=in:st=0:d=0.4,fade=t=out:st=9.6:d=0.4,setsar=1[C]" % (W, H))
    segD = ("[5:v]setpts=PTS-STARTPTS,scale=958:1080[Dc1];[6:v]setpts=PTS-STARTPTS,scale=958:1080[Dc2];"
            "color=c=0x0a0d18:s=%dx%d:d=18,format=yuv420p[Dbg];[Dbg][Dc1]overlay=0:0[D1];[D1][Dc2]overlay=962:0,"
            "fade=t=in:st=0:d=0.5,fade=t=out:st=17.3:d=0.7,setsar=1[D]" % (W, H))
    segE = "color=c=0x0a0d18:s=%dx%d:d=%.1f,format=yuv420p,setsar=1[E]" % (W, H, T_LEN - T_END)
    grade = "eq=contrast=1.05:saturation=1.08,vignette=angle=PI/4.6,noise=alls=5:allf=t+u,format=yuv420p[v]"
    graph = ";".join([segA, segT, segB, segC, segD, segE, "[A][T][B][C][D][E]concat=n=6:v=1:a=0," + grade])
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write(graph)
        script = fh.name
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', intro, '-i', v3.e1, '-i', v3.e2, '-i', macro1, '-i', macro2, '-i', carry, '-i', lysis,
           '-/filter_complex', script, '-map', '[v]', '-r', str(FPS), '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
           '-pix_fmt', 'yuv420p']
    if v3.TEST:
        cmd += ['-t', str(v3.TEST)]
    cmd.append(BASE_MP4)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.unlink(script)
    if r.returncode:
        print(r.stderr[-800:]); sys.exit(1)
    print('PICTURE_DONE', BASE_MP4)


# ======================================================================================
def draw_inline_label(d, fr_ep, lab, geom, half_w=W, color=(255, 255, 255)):
    """Full-frame shots have no margin: ring on the subject, short leader, label beside it (corner picks the side)."""
    f0, f1 = lab['frames']
    if fr_ep < f0 or fr_ep > f1:
        return
    pos = lab['pos'].get(str(fr_ep))
    if pos is None:
        return
    vis = min(ease((fr_ep - f0) / 8.0), ease((f1 - fr_ep) / 8.0))
    if vis <= 0:
        return
    ax, ay = geom.map(pos)
    a = int(255 * vis)
    pulse = 0.5 + 0.5 * math.sin(fr_ep * 0.35)
    r = H * 0.010 + H * 0.004 * pulse
    d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=color + (a,), width=3)
    d.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=color + (a,))
    text = lab['text']
    if not text:
        return
    right = lab['corner'].endswith('r')
    up = lab['corner'].startswith('t')
    dx, dy = W * 0.11, H * 0.14
    ex = ax + (dx if right else -dx)
    ey = ay + (-dy if up else dy)
    # keep the label inside the half it belongs to (and the frame)
    x0 = geom.x + SAFE_X
    x1 = geom.x + half_w - SAFE_X
    tw = d.textlength(text, font=F_LABEL)
    fl = F_LABEL
    if tw > half_w * 0.42:
        fl = font(F_LABEL.size * half_w * 0.42 / tw)
        tw = d.textlength(text, font=fl)
    if right:
        tx = min(max(ex + 12, x0), x1 - tw)
    else:
        tx = max(min(ex - 12 - tw, x1 - tw), x0)
    ty = min(max(ey, SAFE_Y + 20), H - SAFE_Y - 20)
    end = (tx - 12, ty) if right else (tx + tw + 12, ty)
    elbow = (end[0] - 36, ty) if right else (end[0] + 36, ty)
    seg1 = math.hypot(elbow[0] - ax, elbow[1] - ay)
    seg2 = abs(end[0] - elbow[0])
    drawn = (seg1 + seg2) * ease((fr_ep - f0) / 8.0)
    lc = (235, 245, 255, a)
    if drawn <= seg1:
        k = drawn / max(seg1, 1e-6)
        d.line([(ax, ay), (ax + (elbow[0] - ax) * k, ay + (elbow[1] - ay) * k)], fill=lc, width=3)
    else:
        d.line([(ax, ay), elbow], fill=lc, width=3)
        k = (drawn - seg1) / max(seg2, 1e-6)
        d.line([elbow, (elbow[0] + (end[0] - elbow[0]) * k, ty)], fill=lc, width=3)
    if drawn >= (seg1 + seg2) * 0.95:
        text_halo(d, (tx, ty), text, fl, color + (a,), anchor='lm')


def draw_seam(img, t, a, b, strength=1.0):
    v = vis_window(t, a, b, 0.5, 0.5) * strength
    if v <= 0:
        return
    glow = Image.new('RGBA', (40, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line([(20, 0), (20, H)], fill=(255, 216, 110, int(150 * v)), width=2)
    glow = glow.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(glow, (W // 2 - 20, 0))


def half_headers(d, t, a, b, left='WITH THE ENZYME', right='WITHOUT'):
    v = vis_window(t, a, b, 0.5, 0.4)
    if v <= 0:
        return
    al = int(255 * v)
    text_halo(d, (480, SAFE_Y + 18), left, F_COLHEAD, (255, 255, 255, al), anchor='mm')
    text_halo(d, (1440, SAFE_Y + 18), right, F_COLHEAD, (255, 255, 255, al), anchor='mm')


def draw_frame(img, fr):
    t = (fr - 1) / FPS
    d = ImageDraw.Draw(img)
    if t < T_TITLE:
        for lab in ANCI['labels'].values():
            draw_inline_label(d, fr, lab, G_FULL)
    draw_title(img, d, t)
    if T_SPLIT <= t < T_REPLAY:
        fe = fr - int(T_SPLIT * FPS)
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
    if T_REPLAY <= t < T_OUTRO:
        lt = t - T_REPLAY
        fm = int(lt * FPS / 2) + 1                      # macro frame (half speed)
        draw_burst(d, fm, ANCM1, 'bond', 68, 104, G_HL)
        draw_burst(d, fm, ANCM2, 'bond', 68, 104, G_HR)
        draw_seam(img, t, T_REPLAY + 0.3, T_OUTRO - 0.3, 0.6)
        d = ImageDraw.Draw(img)
        half_headers(d, t, T_REPLAY + 0.3, T_OUTRO - 0.3, 'IN THE ENZYME', 'ON THE TARGET')
        headline(d, t, 65.0, 68.8, 'THE SAME CHEMISTRY, TWICE')
        headline(d, t, 70.8, T_OUTRO - 0.3, 'RELEASED. HARMLESS.', y=0.90, x=480, col=(255, 255, 255))
        headline(d, t, 70.8, T_OUTRO - 0.3, 'LOCKED. FOR GOOD.', y=0.90, x=1440, col=(255, 255, 255))
    if T_OUTRO <= t < T_END:
        fo = fr - int(T_OUTRO * FPS)                    # shot frame, 1-based
        draw_seam(img, t, T_OUTRO + 0.3, T_END - 0.5, 0.5)
        d = ImageDraw.Draw(img)
        half_headers(d, t, T_OUTRO + 0.4, T_END - 0.5, 'WITH THE ENZYME', 'WITHOUT')
        for lab in ANCL['labels'].values():
            draw_inline_label(d, fo, lab, G_HR, half_w=960)
        headline(d, t, 76.0, 79.5, 'THE WALL KEEPS GROWING', y=0.90, x=480, col=(255, 255, 255))
        headline(d, t, 84.0, 86.8, 'ONE ENZYME MADE THE DIFFERENCE', y=0.90)
        headline(d, t, 87.0, T_END - 0.5, 'THAT IS WHAT RESISTANCE IS', y=0.90)
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


def stage_audio():
    # ring SFX now sit where the macro shots open the ring (macro frame ~72 at half speed = 4.8 s in)
    v3.RING_REPLAY = (4.7, 5.0)
    v3.stage_audio()


if __name__ == '__main__':
    if v3.STAGE in ('picture', 'all'):
        stage_picture()
    if v3.STAGE in ('text', 'all'):
        stage_text()
    if v3.STAGE in ('audio', 'all'):
        stage_audio()
