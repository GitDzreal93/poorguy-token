#!/usr/bin/env python3
"""Render the poorguy-token GitHub social preview (1280x640 PNG).

Run:  python3 scripts/render_social_preview.py
Out:  assets/social-preview.png
"""
import math
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640

# palette (GitHub dark)
BG_TOP = (13, 17, 23)
BG_BOT = (1, 4, 9)
INK = (240, 246, 252)
INK2 = (201, 209, 217)
MUTE = (139, 148, 158)
DIM = (110, 118, 129)
GREEN = (63, 185, 80)
LINE = (48, 54, 61)
ACCENT = (88, 166, 255)

F_ROUND = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
F_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
F_MONO = "/System/Library/Fonts/SFNSMono.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked(draw, xy, text, fnt, fill, tracking=2, anchor="lm"):
    x, y = xy
    if anchor in ("lm", "lt"):
        widths = [draw.textlength(c, font=fnt) for c in text]
        total = sum(widths) + tracking * (len(text) - 1)
        if anchor == "lm":
            x = xy[0] - total / 2
        cx = x
        for c, w in zip(text, widths):
            draw.text((cx, y), c, font=fnt, fill=fill, anchor="lm")
            cx += w + tracking
    else:
        draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def coin(draw, cx, cy, r, color):
    # coin ring (the "money" half of the metaphor)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=6)
    t = max(5, r // 5)
    # bold down-arrow inside (the "tokens going down" half)
    draw.line([(cx, cy - r * 0.52), (cx, cy + r * 0.26)], fill=color, width=t)
    draw.line([(cx - r * 0.34, cy + r * 0.04), (cx, cy + r * 0.44)],
              fill=color, width=t)
    draw.line([(cx + r * 0.34, cy + r * 0.04), (cx, cy + r * 0.44)],
              fill=color, width=t)
    # round the joins
    for jx, jy in [(cx, cy - r * 0.52), (cx, cy + r * 0.44)]:
        draw.ellipse([jx - t / 2, jy - t / 2, jx + t / 2, jy + t / 2], fill=color)


def chip(draw, x, y, text, fnt, pad_x=14, pad_y=9, h=34):
    w = draw.textlength(text, font=fnt) + pad_x * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                           outline=LINE, width=2)
    draw.text((x + w / 2, y + h / 2), text, font=fnt, fill=INK2, anchor="mm")
    return w


def main():
    img = Image.new("RGB", (W, H), BG_BOT)
    draw = ImageDraw.Draw(img)

    # vertical gradient background
    for y in range(H):
        t = y / (H - 1)
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    PAD = 84

    # top row: coin + kicker
    coin(draw, PAD + 28, 96, 28, INK)
    tracked(draw, (PAD + 80, 96), "THE TOKEN-SAVING BRAIN",
            font(F_BOLD, 19), MUTE, tracking=4)

    # wordmark
    wm_fnt = font(F_ROUND, 116)
    draw.text((PAD - 3, 168), "poorguy", font=wm_fnt, fill=INK, anchor="lm")
    poorguy_w = draw.textlength("poorguy", font=wm_fnt)
    draw.text((PAD - 3 + poorguy_w, 168), "-token", font=wm_fnt, fill=GREEN, anchor="lm")

    # tagline
    draw.text((PAD, 268), "Read less  ·  Write less  ·",
              font=font(F_BOLD, 33), fill=INK2, anchor="lm")
    draw.text((PAD, 312), "Never make the same mistake twice.",
              font=font(F_BOLD, 33), fill=INK2, anchor="lm")

    # axis chips
    chips = ["READ LESS", "WRITE LESS", "REMEMBER", "ENFORCE", "MEASURE"]
    cx = PAD
    cy = 372
    cf = font(F_BOLD, 17)
    for c in chips:
        cw = chip(draw, cx, cy, c, cf)
        cx += cw + 12

    # bottom row: hosts + honest badge
    hf = font(F_BOLD, 22)
    draw.text((PAD, 478), "Claude Code", font=hf, fill=INK, anchor="lm")
    ccw = draw.textlength("Claude Code", font=hf)
    draw.ellipse([PAD + ccw + 22, 478 - 5, PAD + ccw + 22 + 8, 478 + 3], fill=GREEN)
    draw.text((PAD + ccw + 38, 478), "Codex", font=hf, fill=INK, anchor="lm")

    bf = font(F_MONO, 17)
    bw = draw.textlength("no fake benchmarks", font=bf) + 28
    draw.rounded_rectangle([PAD, 520, PAD + bw, 558], radius=19, fill=GREEN)
    draw.text((PAD + bw / 2, 539), "no fake benchmarks", font=bf,
              fill=(6, 10, 14), anchor="mm")

    # right-side: descending "tokens used" sparkline (cost going down)
    sx0, sy0 = 858, 250
    sw, sh = 342, 170
    random.seed(7)
    pts = []
    n = 22
    val = 0.10
    for i in range(n):
        # ascending value => y grows => line descends (tokens going down ↘)
        val = min(0.95, val + 0.045 + random.uniform(-0.05, 0.05))
        x = sx0 + i / (n - 1) * sw
        y = sy0 + val * sh
        pts.append((x, y))
    # area fill
    poly = [(sx0, sy0 + sh)] + pts + [(sx0 + sw, sy0 + sh)]
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon(poly, fill=(63, 185, 80, 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=GREEN, width=4)
    draw.ellipse([pts[-1][0] - 8, pts[-1][1] - 8, pts[-1][0] + 8, pts[-1][1] + 8],
                 fill=GREEN)
    # labels
    draw.text((sx0 + sw / 2, sy0 - 28), "tokens used", font=font(F_MONO, 20),
              fill=MUTE, anchor="mm")
    draw.text((sx0 + sw, sy0 + sh + 16), "↓  with poorguy",
              font=font(F_BOLD, 18), fill=GREEN, anchor="rm")

    img.save("assets/social-preview.png", "PNG", optimize=True)
    print("wrote assets/social-preview.png", img.size)


if __name__ == "__main__":
    main()
