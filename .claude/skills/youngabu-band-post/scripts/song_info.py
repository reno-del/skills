#!/usr/bin/env python3
"""찬양 음원(mp3, m4a)에서 곡 제목과 가사를 뽑아 references/songs/에 넣을 txt를 만든다.

사용법:
    python song_info.py <음원 파일들...> [--out <폴더>] [--transcribe] [--model small]

Claude는 음원을 직접 들을 수 없다. 그래서 가사를 글자로 바꿔 두고 그 글자를 읽어서 쓴다.
  1. 파일 태그에 든 제목과 가사를 읽는다(mp3는 ID3 TIT2·USLT, m4a는 ©nam·©lyr).
     음원 사이트에서 받은 파일에는 가사가 들어 있는 경우가 많고, 이때가 가장 정확하다.
  2. 태그에 제목이 없으면 파일 이름(확장자 뺀 것)을 제목으로 쓴다.
  3. 태그에 가사가 없고 --transcribe를 주면 faster-whisper로 노래를 받아 적는다.
     노래는 말보다 알아듣기 어려워서 틀린 글자가 많다. 그래서 '음성 인식(확인 전)'으로 표시한다.
     가사 슬라이드나 사용자에게 확인을 받으면 손으로 고치고 '사용자 확인'으로 바꾼다.
     모델은 처음 쓸 때 huggingface.co에서 받는다. 이 호스트가 막힌 환경에서는 실패한다.

--out을 주면 <폴더>/<제목>.txt로 저장하고, 주지 않으면 화면에 출력한다.
같은 이름의 파일이 이미 있으면 덮어쓰지 않는다(손으로 고친 가사를 지키려고).
가사를 못 뽑은 곡은 저장하지 않는다(빈 파일이 남으면 나중에 가사를 넣을 때 건너뛰게 되므로).

만드는 txt 형식:
    # 곡 제목
    출처: mp3 태그 가사 | 음성 인식(확인 전) | 가사 없음
    원본: 파일이름.mp3

    (가사, 한 줄에 한 소절)

필요한 것: mutagen (pip install mutagen). --transcribe에는 faster-whisper (pip install faster-whisper).
"""
import argparse
import re
import sys
from pathlib import Path

EXTS = {".mp3", ".m4a", ".mp4", ".aac"}


def read_tags(path):
    """(제목, 가수, 가사) 중 태그에 있는 것만 채워서 돌려준다."""
    try:
        from mutagen import File
    except ImportError:
        sys.exit("mutagen이 없습니다. pip install mutagen")

    title = artist = lyrics = None
    audio = File(path)
    if audio is None or audio.tags is None:
        return title, artist, lyrics
    tags = audio.tags

    if hasattr(tags, "getall"):  # ID3 (mp3)
        if tags.getall("TIT2"):
            title = str(tags.getall("TIT2")[0])
        if tags.getall("TPE1"):
            artist = str(tags.getall("TPE1")[0])
        texts = [f.text for f in tags.getall("USLT") if f.text and f.text.strip()]
        if texts:
            lyrics = max(texts, key=len)
    else:  # MP4 (m4a)
        def first(key):
            v = tags.get(key)
            return str(v[0]) if v else None
        title = first("\xa9nam")
        artist = first("\xa9ART")
        lyrics = first("\xa9lyr")
    return title, artist, lyrics


def transcribe(path, model_name):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper가 없습니다. pip install faster-whisper")
    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    except Exception as e:  # 모델을 받지 못함(네트워크 차단 등)
        sys.exit(
            f"음성 인식 모델({model_name})을 불러오지 못했습니다: {e}\n"
            "모델은 huggingface.co에서 받습니다. 이 호스트가 막혀 있으면 환경의 네트워크 설정에 추가해야 합니다."
        )
    segments, _ = model.transcribe(str(path), language="ko", beam_size=5)
    return "\n".join(s.text.strip() for s in segments if s.text.strip())


def clean_lyrics(text):
    """줄 끝 공백과 연달아 나오는 빈 줄을 정리한다. 반복 소절은 그대로 둔다."""
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    out = []
    for ln in lines:
        if ln == "" and (not out or out[-1] == ""):
            continue
        out.append(ln)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def safe_name(title):
    return re.sub(r'[\\/:*?"<>|]', "_", title).strip() or "제목없음"


def main():
    if len(sys.argv) == 1:
        print(__doc__)
        sys.exit(0)
    ap = argparse.ArgumentParser(description="찬양 음원에서 제목과 가사를 뽑는다.")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, help="txt를 저장할 폴더 (보통 references/songs)")
    ap.add_argument("--transcribe", action="store_true", help="태그에 가사가 없으면 음성 인식으로 받아 적기")
    ap.add_argument("--model", default="small", help="faster-whisper 모델 (tiny, base, small, medium, large-v3)")
    args = ap.parse_args()

    files = []
    for p in args.files:
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS)
        elif p.exists():
            files.append(p)
        else:
            print(f"없는 파일: {p}", file=sys.stderr)
    if not files:
        sys.exit("읽을 음원이 없습니다.")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)

    for f in files:
        title, artist, lyrics = read_tags(f)
        title = (title or f.stem).strip()
        if lyrics:
            source = "mp3 태그 가사"
        elif args.transcribe:
            lyrics = transcribe(f, args.model)
            source = "음성 인식(확인 전)" if lyrics else "가사 없음"
        else:
            source = "가사 없음"
        lyrics = clean_lyrics(lyrics or "")

        head = [f"# {title}", f"출처: {source}", f"원본: {f.name}"]
        if artist:
            head.append(f"가수: {artist}")
        body = "\n".join(head) + "\n\n" + (lyrics + "\n" if lyrics else "")

        if args.out and source == "가사 없음":
            print(f"저장 안 함(가사 없음): {f.name}")
        elif args.out:
            dest = args.out / f"{safe_name(title)}.txt"
            if dest.exists():
                print(f"건너뜀(이미 있음): {dest}")
                continue
            dest.write_text(body, encoding="utf-8")
            print(f"저장: {dest}  [{source}]")
        else:
            print(body)
            print("-" * 40)
        if source == "가사 없음":
            print(f"  ↳ {f.name}: 태그에 가사가 없습니다. --transcribe로 받아 적거나, 가사를 직접 받아 넣으세요.",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
