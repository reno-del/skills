#!/usr/bin/env python3
"""고른 사진을 밴드에 올릴 순서대로 섹션별 폴더에 담아 zip으로 묶는다.

사용법:
    python package_for_band.py <사진 폴더> <섹션.json> <출력.zip>

섹션.json 형식 (글에 나오는 순서대로):
    [
      {"name": "찬양", "photos": ["001", "126"]},
      {"name": "대표기도", "photos": ["149"]}
    ]

결과 zip 안의 구조:
    1_찬양/01_001.jpg, 1_찬양/02_126.jpg, 2_대표기도/01_149.jpg ...

- 폴더 앞 숫자는 글에서 섹션이 나오는 순서, 파일 앞 숫자는 그 섹션 안에서 올릴 순서다.
  뒤의 숫자는 원래 사진 번호라서 글 아래 "사진 넣는 곳" 목록과 맞춰 볼 수 있다.
- 시각을 '지금 직전'(한국 시각)부터 올릴 순서대로 1분씩 늘려 둔다. 갤러리의 최근 사진 쪽에 모이고,
  밴드 사진 선택 화면이 날짜순으로 보여 줘도 순서가 흐트러지지 않는다.
  - zip 안의 파일 시각: 안드로이드처럼 압축을 풀어 바로 갤러리에서 보는 경우에 쓰인다.
  - JPEG 안의 EXIF 촬영 시각: 아이폰·아이패드는 파일 앱의 사진을 '사진' 앱에 저장해야 밴드에서 고를 수 있는데,
    '사진' 앱은 파일 시각이 아니라 EXIF 촬영 시각으로 줄을 세운다. 줄인 사진은 EXIF가 지워져 있어서 새로 넣는다.
    픽셀은 다시 압축하지 않고 EXIF 조각만 끼워 넣는다.

Pillow가 필요하다(EXIF를 만들 때만 쓴다).
"""
import json
import sys
import struct
import time
import zipfile
from pathlib import Path

from PIL import Image

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
    total = sum(len(sec["photos"]) for sec in sections)
    # 갤러리에서 최근 사진 쪽에 모여 보이도록, 지금 시각 바로 전부터 1분 간격으로 찍는다.
    base = time.time() - (total + 1) * 60
    k = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for i, sec in enumerate(sections, 1):
            folder = f"{i}_{sec['name'].replace(' ', '')}"
            for j, stem in enumerate(sec["photos"], 1):
                p = find(src, str(stem))
                info = zipfile.ZipInfo(f"{folder}/{j:02d}_{p.stem}{p.suffix.lower()}",
                                       date_time=time.gmtime(base + k * 60 + KST)[:6])
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, with_exif_time(p.read_bytes(), base + k * 60))
                k += 1
            print(f"{folder}: {len(sec['photos'])}장")
    print(f"총 {k}장 → {out}")


if __name__ == "__main__":
    main()
