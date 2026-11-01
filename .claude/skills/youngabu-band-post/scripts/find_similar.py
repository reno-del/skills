#!/usr/bin/env python3
"""비슷한 사진(연속 촬영, 같은 장면)을 묶어서 보여 준다.

사용법:
    python find_similar.py <사진 폴더 또는 파일들...> [--threshold 12] [--seconds 10]

두 사진이 다음 중 하나면 같은 묶음으로 본다.
  - 이미지 해시(dHash) 차이가 threshold 이하 (구도가 거의 같음)
  - 촬영 시각 차이가 seconds 이하이고 해시 차이가 threshold*2 이하 (연속 촬영)

필요한 것: Pillow (pip install pillow). heic는 pillow-heif가 있으면 읽는다.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ExifTags

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}


def dhash(img, size=8):
    g = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.tobytes())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return bits


def taken_at(img):
    try:
        exif = img.getexif()
        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        sub = exif.get_ifd(0x8769) if hasattr(exif, "get_ifd") else {}
        val = sub.get(36867) or tags.get("DateTime")
        return datetime.strptime(val, "%Y:%m:%d %H:%M:%S") if val else None
    except Exception:
        return None


def collect(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--threshold", type=int, default=12)
    ap.add_argument("--seconds", type=int, default=10)
    a = ap.parse_args()

    info = []
    for f in collect(a.paths):
        try:
            with Image.open(f) as im:
                info.append((f, dhash(im), taken_at(im)))
        except Exception as e:
            print(f"# 읽지 못함: {f} ({e})", file=sys.stderr)

    parent = list(range(len(info)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(info)):
        for j in range(i + 1, len(info)):
            d = bin(info[i][1] ^ info[j][1]).count("1")
            ti, tj = info[i][2], info[j][2]
            close = ti and tj and abs((ti - tj).total_seconds()) <= a.seconds
            if d <= a.threshold or (close and d <= a.threshold * 2):
                parent[find(i)] = find(j)

    groups = {}
    for i in range(len(info)):
        groups.setdefault(find(i), []).append(info[i][0])

    dup = [g for g in groups.values() if len(g) > 1]
    print(f"사진 {len(info)}장, 비슷한 묶음 {len(dup)}개")
    for n, g in enumerate(dup, 1):
        print(f"\n[묶음 {n}] {len(g)}장")
        for f in g:
            print(f"  {f}")


if __name__ == "__main__":
    main()
