#!/usr/bin/env python3
"""고른 사진을 밴드에 올릴 순서대로 섹션별 폴더에 담아 zip으로 묶는다.

사용법:
    python package_for_band.py <사진 폴더> <섹션.json> <출력.zip>

섹션.json 형식 (글에 나오는 순서대로):
    [
      {"name": "찬양", "photos": ["001", "126"]},
      {"name": "대표기도", "photos": ["149"]},
      {"name": "감사한 마음", "photos": [["132@0.8", "018", "020"]]},
      {"name": "오감활동", "photos": [["047", "049", "051", "053"], "061", "113"]}
    ]

- photos 안에 목록을 넣으면 그 사진들을 한 장으로 묶은 이미지(콜라주)가 그 자리에 들어간다.
  - 4장: 2×2 바둑판. 3장: 첫 사진을 위에 넓게, 나머지 둘을 아래에 나란히. 2장: 좌우로 나란히.
  - 칸 사이와 가장자리에 흰 줄을 넣는다. 칸 비율은 사진 방향을 따른다(모두 세로면 3:4, 모두 가로면 4:3, 섞이면 1:1).
    그래서 세로 사진끼리, 가로 사진끼리 묶어야 잘리는 부분이 적다.
  - 칸에 맞추느라 잘라 낼 때는 가로는 가운데를, 세로는 위에서 40% 지점을 기준으로 자른다.
    "132@0.8"처럼 @ 뒤에 0(맨 위)~1(맨 아래)을 적으면 세로 기준을 바꾼다. 아이들이 사진 아래쪽에 있을 때 쓴다.

결과 zip 안의 구조:
    1_찬양/01_001.jpg, 1_찬양/02_126.jpg, 2_대표기도/01_149.jpg,
    3_감사한마음/01_묶음_132+018+020.jpg ...

- 폴더 앞 숫자는 글에서 섹션이 나오는 순서, 파일 앞 숫자는 그 섹션 안에서 올릴 순서다.
  뒤의 숫자는 원래 사진 번호라서 글 아래 "사진 넣는 곳" 목록과 맞춰 볼 수 있다.
- 시각을 '지금 직전'(한국 시각)부터 올릴 순서대로 1분씩 늘려 둔다. 갤러리의 최근 사진 쪽에 모이고,
  밴드 사진 선택 화면이 날짜순으로 보여 줘도 순서가 흐트러지지 않는다.
  - zip 안의 파일 시각: 안드로이드처럼 압축을 풀어 바로 갤러리에서 보는 경우에 쓰인다.
  - JPEG 안의 EXIF 촬영 시각: 아이폰·아이패드는 파일 앱의 사진을 '사진' 앱에 저장해야 밴드에서 고를 수 있는데,
    '사진' 앱은 파일 시각이 아니라 EXIF 촬영 시각으로 줄을 세운다. 줄인 사진은 EXIF가 지워져 있어서 새로 넣는다.
    픽셀은 다시 압축하지 않고 EXIF 조각만 끼워 넣는다.

Pillow가 필요하다(EXIF와 묶음 이미지를 만들 때 쓴다).
"""
import io
import json
import sys
import struct
import time
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

KST = 9 * 3600

EXTS = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".mp4", ".mov"]


def find(src: Path, stem: str) -> Path:
    for ext in EXTS:
        p = src / f"{stem}{ext}"
        if p.exists():
            return p
    hits = sorted(src.glob(f"{stem}.*"))
    if hits:
        return hits[0]
    raise FileNotFoundError(f"{stem} 사진을 {src}에서 찾지 못했습니다")


# 묶음 이미지 크기. 원본(긴 변 1280~1600)을 칸에 넣었을 때 거의 줄이지 않는 폭이다.
WIDTH = 1920
GAP = 10  # 칸 사이와 가장자리의 흰 줄 두께


def cover(im: Image.Image, w: int, h: int, ay: float) -> Image.Image:
    """칸(w×h)을 꽉 채우도록 줄이고 넘치는 부분을 잘라 낸다. ay는 세로로 자를 기준(0 위, 1 아래)."""
    s = max(w / im.width, h / im.height)
    nw, nh = max(w, round(im.width * s)), max(h, round(im.height * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, round((nh - h) * ay)
    return im.crop((x, y, x + w, y + h))


def ratio(ims) -> float:
    """칸의 세로/가로 비율. 모두 세로 사진이면 4/3, 모두 가로면 3/4, 섞이면 1."""
    portrait = [im.height > im.width for im in ims]
    return 4 / 3 if all(portrait) else 3 / 4 if not any(portrait) else 1.0


def collage(src: Path, items) -> bytes:
    """사진 2~4장을 흰 줄로 나눈 한 장의 JPEG로 묶는다."""
    ims, anchors = [], []
    for item in items:
        stem, _, a = str(item).partition("@")
        ims.append(ImageOps.exif_transpose(Image.open(find(src, stem))).convert("RGB"))
        anchors.append(float(a) if a else 0.4)
    n, g, W = len(ims), GAP, WIDTH
    cw = (W - 3 * g) // 2  # 반 폭 칸
    if n == 2:
        ch = round(cw * ratio(ims))
        cells = [(g, g, cw, ch), (2 * g + cw, g, cw, ch)]
    elif n == 3:
        # 레퍼런스처럼 위에 넓은 칸 하나, 아래에 칸 둘. 위 칸은 가로 사진이면 4:3, 세로 사진을 넣으면 3:2로 자른다.
        tw = W - 2 * g
        th = round(tw * (3 / 4 if ims[0].width > ims[0].height else 2 / 3))
        ch = round(cw * ratio(ims[1:]))
        cells = [(g, g, tw, th), (g, 2 * g + th, cw, ch), (2 * g + cw, 2 * g + th, cw, ch)]
    elif n == 4:
        ch = round(cw * ratio(ims))
        cells = [(g + c * (cw + g), g + r * (ch + g), cw, ch) for r in range(2) for c in range(2)]
    else:
        raise ValueError(f"묶음은 2~4장이어야 합니다: {items}")
    H = max(y + h for _, y, _, h in cells) + g
    canvas = Image.new("RGB", (W, H), "white")
    for im, ay, (x, y, w, h) in zip(ims, anchors, cells):
        canvas.paste(cover(im, w, h, ay), (x, y))
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def with_exif_time(data: bytes, t: float) -> bytes:
    """JPEG 바이트에서 기존 EXIF(APP1)를 빼고, 한국 시각 t를 촬영 시각으로 담은 EXIF를 SOI 바로 뒤에 넣는다."""
    if data[:2] != b"\xff\xd8":
        return data  # JPEG가 아니면 그대로
    stamp = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(t + KST))
    exif = Image.Exif()
    exif[0x0132] = stamp  # DateTime
    sub = exif.get_ifd(0x8769)
    sub[0x9003] = stamp  # DateTimeOriginal
    sub[0x9004] = stamp  # DateTimeDigitized
    sub[0x9011] = "+09:00"  # OffsetTimeOriginal
    payload = exif.tobytes()  # b"Exif\0\0" + TIFF
    app1 = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    # SOI 뒤의 헤더 조각들을 훑으며 기존 EXIF APP1만 뺀다. SOS(이미지 데이터)부터는 그대로 붙인다.
    out, i = [data[:2], app1], 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xDA:
            break
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        seg = data[i:i + 2 + length]
        if not (marker == 0xE1 and seg[4:10] == b"Exif\0\0"):
            out.append(seg)
        i += 2 + length
    out.append(data[i:])
    return b"".join(out)


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    src, sections, out = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), Path(sys.argv[3])
    total = sum(len(sec["photos"]) for sec in sections)  # 묶음은 한 장으로 센다
    # 갤러리에서 최근 사진 쪽에 모여 보이도록, 지금 시각 바로 전부터 1분 간격으로 찍는다.
    base = time.time() - (total + 1) * 60
    k = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for i, sec in enumerate(sections, 1):
            folder = f"{i}_{sec['name'].replace(' ', '')}"
            groups = 0
            for j, item in enumerate(sec["photos"], 1):
                if isinstance(item, list):
                    name = "묶음_" + "+".join(str(x).partition("@")[0] for x in item) + ".jpg"
                    data = collage(src, item)
                    groups += 1
                else:
                    p = find(src, str(item))
                    name, data = f"{p.stem}{p.suffix.lower()}", p.read_bytes()
                info = zipfile.ZipInfo(f"{folder}/{j:02d}_{name}",
                                       date_time=time.gmtime(base + k * 60 + KST)[:6])
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, with_exif_time(data, base + k * 60))
                k += 1
            print(f"{folder}: {len(sec['photos'])}장" + (f" (묶음 {groups}장 포함)" if groups else ""))
    print(f"총 {k}장 → {out}")


if __name__ == "__main__":
    main()
