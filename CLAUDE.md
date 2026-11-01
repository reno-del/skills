# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 저장소

Claude Code 스킬 모음이다. 빌드, 린트, 테스트 설정은 없다. 스킬은 `SKILL.md`(맨 위에 `name`, `description`)와 선택 폴더 `scripts/`, `references/`로 이루어진다.

스킬은 두 종류이고, 관리 방법이 다르다.

- **외부에서 설치한 스킬**: `claude-md-improver`, `find-skills`
  - `npx skills add <owner/repo@skill>`로 설치했고, 출처와 해시가 `skills-lock.json`에 기록된다.
  - 같은 내용이 `.claude/skills/`와 `.agents/skills/` 두 곳에 들어 있다.
  - 직접 고치지 말고 `npx skills update`로 갱신한다. 손으로 고치면 lock 파일의 해시와 어긋난다.
- **이 저장소에서 만든 스킬**: `sheets-creator`, `youngabu-band-post`
  - `.claude/skills/`에만 있고 `skills-lock.json`에는 없다. 여기서 직접 고친다.
  - 새 스킬도 `.claude/skills/<이름>/`에 만든다.

## 직접 만든 스킬을 쓰고 고칠 때

- **언어**: 사용자는 한국어로 소통하고, 스킬 본문과 description도 한국어로 쓴다.
- **description**: 무엇을 하는지와 함께, 사용자가 "스킬"이라고 말하지 않아도 켜져야 하는 상황과 실제 요청 예시를 넣는다. `sheets-creator`와 `youngabu-band-post`의 description이 이 형식이다.
- **본문**: 규칙만 나열하지 말고, 그 규칙이 왜 필요한지(실제 사용자가 결과를 어떻게 쓰는지)를 적는다.
- **스크립트**: 파이썬 단독 실행 스크립트이고, 사용법은 파일 맨 위 docstring에 있다. 인자 없이 실행하면 docstring을 출력한다.
  - `youngabu-band-post/scripts/*`는 Pillow가 필요하다. heic 사진을 읽으려면 pillow-heif도 있어야 한다.
  - `sheets-creator/scripts/pdf_to_images.py`는 pypdfium2가 필요하다.
  - 테스트 코드는 없다. 고친 뒤에는 작업용 임시 폴더의 샘플 이미지로 직접 실행해서 확인한다.

## youngabu-band-post 구조

예수인교회 영아부 밴드에 올릴 주일 예배 스케치 글을 사진으로부터 만든다. 흐름은 `SKILL.md`의 1~5단계를 따른다.

1. **사진 받기**: 사진이 많으면 사용자의 Artifact 페이지 "영아부 사진 보내기"로 받는다. 이 페이지는 사진을 줄여 PDF 몇 개와 목록 JSON으로 올린다.
2. **사진 꺼내기**: 올라온 PDF를 asset으로 받아 `pdfimages -j`로 사진을 꺼낸다. 받은 순서대로 `001.jpg`처럼 번호를 붙인다.
3. **훑어보기와 골라내기**: `contact_sheet.py`로 25장씩 번호가 찍힌 모음 이미지를 만들어 훑는다. `find_similar.py`로 연속 사진 묶음을 찾는다.
   - `find_similar.py`는 파일 이름 순서를 촬영 순서로 본다. 줄인 사진은 EXIF가 지워져 있어서, 순서상 이웃한 사진끼리 비교하는 규칙이 가장 많이 잡는다.
4. **글 쓰기**: 말투와 섹션 구성은 `references/examples.md`(실제 밴드 글을 옮겨 적은 것)를 따른다.
5. **결과 내기**: 결과물은 두 가지다.
   - 밴드에 바로 붙여 넣을 글: `📷`, `○○○` 같은 작업용 표시가 없어야 한다.
   - `package_for_band.py`로 만든 zip: 고른 사진을 섹션 순서대로 폴더에 나눠 담는다.
   - 밴드 API는 사진과 영상을 받지 않는 것으로 보이고, 이 환경에서는 band.us 접속도 막혀 있다. 그래서 자동으로 올리지 않는다.

## 주의

- **아이 사진과 이름을 저장소에 넣지 않는다.** 이 저장소는 공개 저장소(`reno-del/skills`)다.
  - 사진은 작업용 임시 폴더에서만 다루고, 결과 zip은 SendUserFile로 보낸다.
  - `references/examples.md`처럼 실제 글을 옮길 때는 아이와 선생님 이름을 `○○○`로 가린다.
- `README.md`에는 제목 한 줄뿐이다.
