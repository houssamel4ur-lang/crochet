#!/usr/bin/env python3
"""Original illustrated WebP graphics for the CozyLoops starfish baby crochet editorial.
Illustrations only: these do not depict a fitted or physically tested baby garment.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from math import sin, cos, pi
import random

OUT = Path(__file__).resolve().parents[1] / "assets"
OUT.mkdir(exist_ok=True)
W, H = 1200, 760

def start(seed):
    rng = random.Random(seed)
    im = Image.new("RGB", (W, H), (248, 243, 234))
    d = ImageDraw.Draw(im)
    for y in range(H):
        v = int(3 * sin(y / 75))
        d.line((0, y, W, y), fill=(248 + v, 243 + v, 234 + v))
    for _ in range(1700):
        x, y = rng.randrange(W), rng.randrange(H)
        a = rng.randrange(1, 4)
        d.ellipse((x, y, x + a, y + a), fill=(244, 236, 225))
    d.polygon([(0, 0), (170, 0), (0, 190)], fill=(240, 221, 216))
    d.line((0, 170, 170, 0), fill=(230, 206, 203), width=4)
    return im, d

def star(cx, cy, outer, inner):
    return [(int(cx + (outer if i % 2 == 0 else inner) * cos(-pi / 2 + i*pi/5)),
             int(cy + (outer if i % 2 == 0 else inner) * sin(-pi / 2 + i*pi/5)))
            for i in range(10)]

def shadow(im, points, blur=27):
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    d.polygon([(x + 12, y + 20) for x, y in points], fill=(77, 65, 47, 75))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    im.paste(layer, (0, 0), layer)

def crochet(im, points, seed=11):
    mask = Image.new("L", (W, H))
    ImageDraw.Draw(mask).polygon(points, fill=255)
    shade = Image.new("RGB", (W, H), (246, 203, 106))
    sh = ImageDraw.Draw(shade)
    for y in range(0, H, 9):
        v = int(13 * sin(y / 21))
        sh.line((0, y, W, y), fill=(246, 203 + v//2, 106 + v//3), width=3)
    im.paste(shade, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.line(points + [points[0]], fill=(195, 139, 61), width=9, joint="curve")
    d.line(points + [points[0]], fill=(255, 225, 151), width=4, joint="curve")
    rng = random.Random(seed)
    tex = Image.new("RGBA", (W, H))
    t = ImageDraw.Draw(tex)
    for y in range(60, H-50, 14):
        for x in range(90, W-90, 18):
            xx = x + (7 if (y//14) % 2 else 0) + rng.randrange(-2, 3)
            t.arc((xx-8, y-4, xx+8, y+9), 180, 360, fill=(150, 105, 50, 100), width=2)
            t.arc((xx-5, y+1, xx+5, y+12), 0, 180, fill=(255, 244, 196, 215), width=2)
    tex.putalpha(Image.composite(tex.getchannel("A"), Image.new("L", (W, H)), mask))
    im.paste(tex, (0, 0), tex)
    return ImageDraw.Draw(im)

def yarn_ball(im, x, y, r, color):
    d = ImageDraw.Draw(im)
    d.ellipse((x-r+6, y-r+12, x+r+8, y+r+12), fill=(226, 212, 194))
    d.ellipse((x-r, y-r, x+r, y+r), fill=color, outline=(197, 154, 91), width=4)
    for s in range(-r+12, r-10, 12):
        delta = (r*r - s*s)**0.5
        d.arc((x-delta, y+s-9, x+delta, y+s+9), 0, 180, fill=(255, 229, 164), width=3)
        d.arc((x-delta, y+s-5, x+delta, y+s+10), 180, 360, fill=(173, 131, 69), width=2)
    d.ellipse((x-20, y-16, x+20, y+16), outline=(176,133,75), width=5)

def flowers(d, coords):
    for x, y in coords:
        d.ellipse((x-6, y-6, x+6, y+6), fill=(230, 183, 174))
        for k in range(5):
            a = k*2*pi/5
            px, py = x+13*cos(a), y+13*sin(a)
            d.ellipse((px-7, py-7, px+7, py+7),
                      fill=(255, 252, 244), outline=(216, 209, 196))

def save(im, filename):
    im.save(OUT / filename, "WEBP", quality=86, method=6)

im, d = start(2)
points = star(617, 399, 322, 181)
shadow(im, points)
d = crochet(im, points, 41)
cx, cy = 615, 216
d.ellipse((cx-98, cy-70, cx+98, cy+98), fill=(210, 153, 80), outline=(240, 204, 136), width=10)
d.ellipse((cx-75, cy-51, cx+75, cy+77), fill=(249, 239, 219), outline=(254, 222, 155), width=7)
d.arc((514, 288, 717, 361), 185, 355, fill=(201,151,79), width=7)
yarn_ball(im, 168, 581, 74, (241,201,113))
flowers(d, [(1020,142),(1060,170),(1000,185)])
save(im, "starfish-baby-crochet-outfit.webp")

im, d = start(7)
a = star(400, 370, 250, 136)
b = star(821, 380, 236, 123)
shadow(im, a, 22)
shadow(im, b, 22)
crochet(im, a, 17)
d = crochet(im, b, 29)
d.ellipse((769, 327, 873, 433), outline=(249,236,204), width=10)
d.line((626,146,660,146),fill=(144,151,132),width=4)
d.polygon([(662,146),(649,139),(649,153)], fill=(144,151,132))
flowers(d, [(1043,630),(1080,667)])
save(im, "starfish-baby-panels-construction.webp")

im, d = start(12)
yarn_ball(im, 321, 355, 185, (243,201,104))
yarn_ball(im, 493, 530, 103, (232,187,175))
d.line((602,583,952,220), fill=(108,132,130), width=18)
d.line((952,220,1007,197), fill=(130,132,132), width=9)
d.arc((998,179,1022,208),-40,145,fill=(124,123,116),width=7)
swatch = [(695,490),(973,448),(1018,650),(736,688)]
shadow(im, swatch, 16)
d = crochet(im, swatch, 5)
d.arc((983,456,1108,613),40,160,fill=(237,225,192),width=12)
flowers(d,[(1014,126),(1064,160)])
save(im, "starfish-baby-yarn-tools.webp")
