#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K1 字卡數字 1-10 —— 用「十格框 (ten-frame)」表示，程式繪製，數目 100% 準確。
頂行（1-5）藍色、底行（6-10）橙色，一眼睇到 5 的結構（例如 7 = 滿一行 5 + 2）。
用法： python3 make_tenframes.py   → 產生 img/01.jpg … img/10.jpg
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")

def tenframe(n, out):
    S = 1024; ss = 2; W = S * ss
    img = Image.new("RGB", (W, W), (255, 255, 255))
    d = ImageDraw.Draw(img)
    cols, rows = 5, 2
    cell = 150 * ss
    gw, gh = cols * cell, rows * cell
    x0 = (W - gw) // 2
    y0 = (W - gh) // 2
    frame = (150, 168, 190)
    light = (205, 216, 230)
    # 外框
    d.rounded_rectangle([x0, y0, x0 + gw, y0 + gh], radius=18 * ss, outline=frame, width=5 * ss)
    # 直線（分 5 格）
    for c in range(1, cols):
        x = x0 + c * cell
        d.line([(x, y0), (x, y0 + gh)], fill=light, width=3 * ss)
    # 中間橫線（分上下兩行，強調 5 的結構）
    d.line([(x0, y0 + cell), (x0 + gw, y0 + cell)], fill=frame, width=4 * ss)
    # 圓點（counters）
    top_col = (76, 176, 224)    # 藍：1-5
    bot_col = (245, 166, 35)    # 橙：6-10
    r = 52 * ss
    for i in range(n):
        rr, cc = divmod(i, cols)
        cx = x0 + cc * cell + cell // 2
        cy = y0 + rr * cell + cell // 2
        col = top_col if rr == 0 else bot_col
        dark = tuple(int(v * 0.82) for v in col)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=dark, width=4 * ss)
    img.resize((S, S), Image.LANCZOS).save(out, quality=92)
    print("✓", os.path.basename(out), "= 十格框", n)

if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    for n in range(1, 11):
        tenframe(n, os.path.join(IMG, "%02d.jpg" % n))
