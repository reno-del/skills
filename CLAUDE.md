# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 저장소

Claude Code 스킬 모음이다. 빌드, 린트, 테스트 설정은 없다. 스킬은 `SKILL.md`(맨 위에 `name`, `description`)와 선택 폴더 `scripts/`, `references/`로 이루어진다.

스킬은 두 종류이고, 관리 방법이 다르다.

- **외부에서 설치한 스킬**: `claude-md-improver`, `find-skills`
  - `npx skills add <owner/repo@skill>`로 설치했고, 출처와 해시가 `skills-lock.json`에 기록된다.
  - 같은 내용이 `.claude/skills/`와 `.agents/skills/` 두 곳에 들어 있다.
  - 직접 고치지 말고 `npx skills update`로 갱신한다. 손으로 고치면 lock 파일의 해시와 어긋난다.
  - `npx skills update`는 `.claude/skills/<이름>`을 `.agents/skills/<이름>`을 가리키는 심볼릭 링크로 바꾼다. 갱신한 뒤에는 링크를 지우고 `.agents/skills/<이름>`을 복사해 넣어 두 곳에 실제 파일이 있게 유지한다. 그다음 `npx skills check`로 최신인지 확인한다.
- **이 저장소에서 만든 스킬**: `sheets-creator`, `youngabu-band-post`
  - `.claude/skills/`에만 있고 `skills-lock.json`에는 없다. 여기서 직접 고친다.
  - 새 스킬도 `.claude/skills/<이름>/`에 만든다.

## 직접 만든 스킬을 쓰고 고칠 때

- **언어**: 사용자는 한국어로 소통하고, 스킬 본문과 description도 한국어로 쓴다.
- **description**: 무엇을 하는지와 함께, 사용자가 "스킬"이라고 말하지 않아도 켜져야 하는 상황과 실제 요청 예시를 넣는다. `sheets-creator`와 `youngabu-band-post`의 description이 이 형식이다.
- **본문**: 규칙만 나열하지 말고, 그 규칙이 왜 필요한지(실제 사용자가 결과를 어떻게 쓰는지)를 적는다.
- **스크립트**: 파이썬 단독 실행 스크립트이고, 사용법은 파일 맨 위 docstring에 있다. 인자 없이 실행하면 docstring을 출력한다.
  - `youngabu-band-post/scripts/`의 사진 스크립트는 Pillow가 필요하다. heic 사진을 읽으려면 pillow-heif도 있어야 한다.
  - `youngabu-band-post/scripts/song_info.py`는 mutagen이 필요하다. `--transcribe`(노래 받아 적기)에는 faster-whisper와 ffmpeg가 필요하다. 모델은 `--model large-v3-turbo`를 쓴다.
    - 모델은 처음 한 번 huggingface.co에서 받고, 파일은 us.aws.cdn.hf.co에서 내려온다. 이 환경에는 두 호스트를 허용해 두었다.
    - xethub 호스트는 막혀 있으니 `HF_HUB_DISABLE_XET=1`을 붙여 받는다. 받은 뒤에는 `HF_HUB_OFFLINE=1`로 돌린다.
  - `sheets-creator/scripts/pdf_to_images.py`는 pypdfium2가 필요하다.
  - 테스트 코드는 없다. 고친 뒤에는 작업용 임시 폴더의 샘플 이미지로 직접 실행해서 확인한다.

## sheets-creator 구조

악보 이미지나 PDF에서 가사를 뽑아 예배 자막용 txt를 만든다. 출력 형식의 기준은 `references/example.txt`(사용자가 직접 정리한 세 곡짜리 콘티)다. `SKILL.md`의 규칙과 이 예시가 다르면 예시를 따른다. 규칙을 고칠 때도 예시와 어긋나지 않게 한다.

## youngabu-band-post 구조

예수인교회 영아부 밴드에 올릴 주일 예배 스케치 글을 사진으로부터 만든다. 흐름은 `SKILL.md`의 1~5단계를 따른다.

1. **사진 받기**: 사진이 많으면 사용자의 Artifact 페이지 "영아부 사진 보내기"로 받는다. 이 페이지는 사진을 줄여 PDF 몇 개와 목록 JSON으로 올린다.
2. **사진 꺼내기**: 올라온 PDF를 asset으로 받아 `pdfimages -j`로 사진을 꺼낸다. 받은 순서대로 `001.jpg`처럼 번호를 붙인다.
3. **훑어보기와 골라내기**: `contact_sheet.py`로 25장씩 번호가 찍힌 모음 이미지를 만들어 훑는다. `find_similar.py`로 연속 사진 묶음을 찾는다.
   - `find_similar.py`는 파일 이름 순서를 촬영 순서로 본다. 줄인 사진은 EXIF가 지워져 있어서, 순서상 이웃한 사진끼리 비교하는 규칙이 가장 많이 잡는다.
   - 사진은 고르기 전에 옷차림으로 아이 목록부터 만들고, 덜 나온 아이 사진을 먼저 고른다. 한 아이가 주인공인 사진은 2장까지다.
4. **글 쓰기**: 말투와 섹션 구성은 `references/examples.md`(실제 밴드 글을 옮겨 적은 것)를 따른다.
   - 찬양 섹션은 그 주에 부른 곡의 가사로 매주 새로 쓴다. 곡은 가사 슬라이드 글자로 `references/songs/`(곡마다 가사 txt)에서 찾는다. 지난주와 겹치지 않게 `references/praise_log.md`를 보고 소절을 고르고, 글을 낸 뒤 한 줄을 더한다.
   - 찬양 음원(mp3, m4a)을 받으면 `song_info.py`로 가사를 뽑아 `references/songs/`에 txt로 넣는다. 단톡방에서 받은 파일은 태그가 비어 있고 업로드하면 한글 파일 이름도 `_`로 바뀌므로, 보통 `--transcribe`로 받아 적고 곡 제목은 사용자에게 묻는다.
5. **결과 내기**: 결과물은 두 가지다.
   - 밴드에 바로 붙여 넣을 글: `📷`, `○○○` 같은 작업용 표시가 없어야 한다.
   - `package_for_band.py`로 만든 zip: 고른 사진을 섹션 순서대로 폴더에 나눠 담는다.
   - 밴드 API는 사진과 영상을 받지 않는 것으로 보이고, 이 환경에서는 band.us 접속도 막혀 있다. 그래서 자동으로 올리지 않는다.

## 주의

- **아이 사진과 이름을 저장소에 넣지 않는다.** 이 저장소는 공개 저장소(`reno-del/skills`)다.
  - 사진은 작업용 임시 폴더에서만 다루고, 결과 zip은 SendUserFile로 보낸다.
  - `references/examples.md`처럼 실제 글을 옮길 때는 아이와 선생님 이름을 `○○○`로 가린다.
- **찬양 음원 파일(mp3 등)을 저장소에 넣지 않는다.** 공개 저장소라 저작권 문제가 생긴다. 뽑은 가사 txt만 `youngabu-band-post/references/songs/`에 넣는다.
- `README.md`에는 제목 한 줄뿐이다.
