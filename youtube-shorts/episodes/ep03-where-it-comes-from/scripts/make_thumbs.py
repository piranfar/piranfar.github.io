"""Episode 3 thumbnails from the rendered picture layers (no HUD text in them).

  python episodes/ep03-where-it-comes-from/scripts/make_thumbs.py

Landscape A: the plasmid with the bla gene lit (frame 33 s of ep3_wide_base.mp4), headline WHERE RESISTANCE COMES FROM.
Landscape B: the two cells and the pilus (55 s), headline BACTERIA HAVE SEX.
Vertical (Short): the plasmid frame of film3_short.mp4 (20 s), headline IT WAS HANDED IT.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(EP, 'renders')
T = os.path.join(EP, 'thumbs')
FONT_B = 'C:/Windows/Fonts/segoeuib.ttf'
GOLD = (255, 204, 77)
WHITE = (245, 245, 245)


def frame(video, t, out):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i', video, '-frames:v', '1', out], check=True)
    return Image.open(out).convert('RGB')


def text_block(im, lines, y0, align='left', margin=0.06, shadow=True):
    W, H = im.size
    d = ImageDraw.Draw(im)
    y = y0
    for txt, size_frac, color in lines:
        f = ImageFont.truetype(FONT_B, int(H * size_frac))
        tw = d.textlength(txt, font=f)
        maxw = W * (1 - 2 * margin)
        if tw > maxw:                      # shrink to fit the width
            f = ImageFont.truetype(FONT_B, int(H * size_frac * maxw / tw))
            tw = d.textlength(txt, font=f)
        x = int(W * margin) if align == 'left' else (W - tw) / 2
        if shadow:
            for dx, dy in ((3, 3), (-2, 2), (2, -2), (-2, -2)):
                d.text((x + dx, y + dy), txt, font=f, fill=(0, 0, 0))
        d.text((x, y), txt, font=f, fill=color)
        y += int(H * size_frac * 1.12)
    return y


def darken_band(im, y0, y1, alpha=150):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle((0, y0, im.size[0], y1), fill=(5, 8, 18, alpha))
    ov = ov.filter(ImageFilter.GaussianBlur(40))
    return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')


def landscape(src, t, headline, sub, out):
    im = frame(src, t, os.path.join(T, '_tmp.png'))
    W, H = im.size
    im = darken_band(im, int(H * 0.55), H, 190)
    y = int(H * 0.60)
    y = text_block(im, [(headline, 0.13, GOLD)], y)
    text_block(im, [(sub, 0.055, WHITE)], y + int(H * 0.01))
    text_block(im, [('EPISODE 3', 0.045, WHITE)], int(H * 0.05))
    im.save(out, quality=92)
    print(out, im.size)


def vertical(src, t, head_lines, sub, out):
    im = frame(src, t, os.path.join(T, '_tmp.png'))
    W, H = im.size
    im = darken_band(im, int(H * 0.58), int(H * 0.88), 190)
    y = int(H * 0.62)
    y = text_block(im, [(l, 0.075, GOLD) for l in head_lines], y, align='center')
    text_block(im, [(sub, 0.032, WHITE)], y + int(H * 0.005), align='center')
    im.save(out, quality=92)
    print(out, im.size)


os.makedirs(T, exist_ok=True)
landscape(os.path.join(R, 'ep3_wide_base.mp4'), 33.0, 'WHERE RESISTANCE COMES FROM',
          'one gene on a ring of DNA, and it travels', os.path.join(T, 'thumb_A_gene.jpg'))
landscape(os.path.join(R, 'ep3_wide_base.mp4'), 55.0, 'BACTERIA HAVE SEX',
          'how one cell hands resistance to its neighbour', os.path.join(T, 'thumb_B_pilus.jpg'))
vertical(os.path.join(R, 'film3_short.mp4'), 20.0, ['IT WAS', 'HANDED IT'], 'where resistance comes from',
         os.path.join(T, 'thumb_short.jpg'))
os.remove(os.path.join(T, '_tmp.png'))
