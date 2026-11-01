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
- 파일 시각을 '지금 직전'부터 올릴 순서대로 1분씩 늘려 둔다. 압축을 풀면 갤러리의 최근 사진 쪽에 모이고, 휴대폰 갤러리나 밴드 사진 선택 화면이
  날짜순으로 보여 줘도 순서가 흐트러지지 않는다.
"""
import json
import sys
import time
import zipfile
from pathlib import Path

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
                                       date_time=time.localtime(base + k * 60)[:6])
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, p.read_bytes())
                k += 1
            print(f"{folder}: {len(sec['photos'])}장")
    print(f"총 {k}장 → {out}")


if __name__ == "__main__":
    main()
