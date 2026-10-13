"""Cover images (1080x1920, TikTok) for both videos.

    python3 thumbnails.py bath     # output/thumbnail_bath_time_song.png
    python3 thumbnails.py farm     # output/thumbnail_la_derniere_pomme.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')


def bath():
    from bath_time import render, scenes
    from bath_time.characters import lilo, bobo, duck, boat
    from bath_time.gfx import bubble, sparkle, set_lighting, font
    render.set_format('vertical')
    set_lighting(*scenes.GRADES[2]['light'])
    fr = scenes.background(2)
    cx, cy = 900, 800      # scene sits low so the title has the top of the frame
    scenes.tub(fr, cx, cy, 640, 110, 260, part='back')
    lilo(fr, cx, 930, 1.25, outfit='bath', mouth=0.85, lh=(-118, -335), rh=(118, -335), crown=1.0, crown_t=1.0)
    scenes.water_surface(fr, cx, cy + 110 * 0.07, 640 * 0.95, 110 * 0.8, 760, 2.0, 1.0, 3)
    duck(fr, 780, 772, 1.1)
    boat(fr, 1050, 778, 0.9)
    scenes.tub(fr, cx, cy, 640, 110, 260, part='front')
    bobo(fr, 1185, 1070, 0.85, trunk=1.0, mouth=0.7, happy=True, ear=1.0)
    rng = np.random.default_rng(4)
    for _ in range(26):
        bubble(fr, rng.uniform(640, 1300), rng.uniform(40, 460), rng.uniform(14, 46), phase=rng.uniform(0, 1))
    for _ in range(8):
        sparkle(fr, rng.uniform(660, 1280), rng.uniform(60, 440), rng.uniform(10, 22))
    a = render.camera(fr, (980, 540, 1.0))
    a = render.grade(a, scenes.GRADES[2], 2, 30.0)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    pal = render.PALETTE
    for row, (word, y, size) in enumerate((("BATH", 180, 200), ("TIME", 375, 200))):
        f = font(size)
        widths = [f.getlength(c) for c in word]
        x = 540 - sum(widths) / 2
        for i, (c, wd) in enumerate(zip(word, widths)):
            render.draw_text_center(d, x + wd / 2, y + 10 * math.sin(i * 1.3 + row), c, size, pal[(i + row * 2) % len(pal)],
                                    stroke=(255, 255, 255), sw=14)
            x += wd
    render.draw_text_center(d, 540, 545, "SONG", 130, (255, 255, 255), stroke=(110, 70, 170), sw=12)
    d.rounded_rectangle([170, 1560, 910, 1680], radius=60, fill=(255, 120, 160, 235), outline=(255, 255, 255, 255), width=6)
    render.draw_text_center(d, 540, 1620, "Splash splash !", 76, (255, 255, 255), stroke=(150, 50, 100), sw=6)
    render.draw_text_center(d, 540, 1745, "avec Lilo & Bobo", 60, (255, 240, 150), stroke=(90, 60, 140), sw=6)
    path = os.path.join(OUT, 'thumbnail_bath_time_song.png')
    Image.alpha_composite(img, over).convert('RGB').save(path)
    return path


def farm():
    from farm import scenes, render
    from farm.chars import gaston, mimi, bernard, pico, apple
    from bath_time.gfx import sparkle, shape, glow, set_lighting
    set_lighting(key=(1.0, 0.92, 0.76), amb=(0.88, 0.86, 0.96), rim=(1.0, 0.88, 0.65))
    fr = scenes.farm_bg(560, 1050, 1.0, blur=4)
    scenes.speed_lines(fr, 540, 1000, 0.0, col=(255, 236, 170), alpha=0.35)
    # Pico on the fence post with the bitten apple, winking
    px, py = 540, 1150
    shape(fr, ('rrect', (px - 80, py - 10, px + 80, py + 400, 16)), (200, 150, 96), bevel=8, spec=0.2)
    glow(fr, px, py - 250, 420, (120, 90, 30), 0.8)
    pico(fr, px - 30, py, 2.6, wink=1, hands='down', brow=0.6, shadow=False)
    apple(fr, px + 150, py - 130, 110, bites=2)
    sparkle(fr, px + 120, py - 470, 40)
    sparkle(fr, px - 230, py - 360, 26)
    # the three victims, shocked
    gaston(fr, 160, 1880, 1.0, shock=1.0, wide=1.5, brow=-0.6, look=(0.6, -0.8), feathers_lost=1.0)
    bernard(fr, 930, 1900, 0.8, shock=1.0, wide=1.5, lid=0.0, brow=-0.5, ears=1.0, look=(-0.6, -0.8), fx=-1)
    mimi(fr, 560, 2040, 1.05, shock=1.0, wide=1.45, lid=0.0, brow=-0.5, look=(0, -1))
    a = render.camera(fr, (540, 1000, 1.0, 0))
    a = render.grade(a, 30.0, 'thumb')
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    render.text(d, 540, 210, "LA DERNIÈRE", 128, (255, 236, 120), stroke=(150, 30, 30), sw=12)
    render.text(d, 540, 390, "POMME", 220, (235, 50, 50), stroke=(255, 255, 255), sw=16)
    d.rounded_rectangle([110, 540, 970, 660], radius=60, fill=(20, 16, 24, 220), outline=(255, 220, 40, 255), width=6)
    render.text(d, 540, 600, "Qui va la manger ?", 74, (255, 220, 40), stroke=(20, 16, 24), sw=4)
    path = os.path.join(OUT, 'thumbnail_la_derniere_pomme.png')
    Image.alpha_composite(img, over).convert('RGB').save(path)
    return path


if __name__ == '__main__':
    print({'bath': bath, 'farm': farm}[sys.argv[1]]())
