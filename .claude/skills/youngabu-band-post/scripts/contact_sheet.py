#!/usr/bin/env python3
"""사진 여러 장을 번호가 붙은 한 장짜리 모음 이미지(밀착 인화)로 만든다.

사진이 수십~수백 장일 때 한 장씩 열어 보는 대신, 25장씩 한눈에 보고
분류하고 고르기 위해 쓴다.

사용법:
    python contact_sheet.py <사진 폴더> <출력 폴더> [--cols 5] [--rows 5] [--size 300]

사진은 파일 이름 순서로 놓이고, 각 칸 왼쪽 위에 파일 이름(확장자 제외)이 찍힌다.
그래서 사진 파일 이름을 001.jpg, 002.jpg처럼 번호로 맞춰 두면 고르기 편하다.
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--size", type=int, default=300)
    a = ap.parse_args()

    files = sorted(f for f in Path(a.src).iterdir() if f.suffix.lower() in EXTS)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", a.size // 9)
    except OSError:
        font = ImageFont.load_default()

    per = a.cols * a.rows
    T = a.size
    for s in range(math.ceil(len(files) / per)):
        sheet = Image.new("RGB", (a.cols * T, a.rows * T), "white")
        d = ImageDraw.Draw(sheet)
        for k, f in enumerate(files[s * per:(s + 1) * per]):
            with Image.open(f) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((T - 6, T - 6))
                x, y = (k % a.cols) * T, (k // a.cols) * T
                sheet.paste(im, (x + (T - im.width) // 2, y + (T - im.height) // 2))
            label = f.stem
            box = d.textbbox((0, 0), label, font=font)
            d.rectangle((x, y, x + box[2] + 8, y + box[3] + 6), fill="black")
            d.text((x + 4, y + 2), label, fill="yellow", font=font)
        path = out / f"sheet{s + 1:02d}.jpg"
        sheet.save(path, quality=85)
        print(path)


if __name__ == "__main__":
    main()
