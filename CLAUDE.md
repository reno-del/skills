# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of Claude Code agent skills. There is no build, lint or test toolchain; the "code" is mostly `SKILL.md` files plus small helper scripts. User-facing communication and skill content are in Korean.

## Layout

Two kinds of skills live here, and they are stored differently:

- **Installed third-party skills** (e.g. `find-skills` from `vercel-labs/skills`) are installed with the `skills` CLI:
  ```bash
  npx -y skills add <github-url> --skill <name> -y
  ```
  The CLI writes the real files to `.agents/skills/<name>/`, symlinks `.claude/skills/<name>` to them, and records the source and hash in `skills-lock.json`. Don't hand-edit these; reinstall instead.
- **Skills authored in this repo** (e.g. `sheets-creator`) live directly in `.claude/skills/<name>/`:
  - `SKILL.md`: YAML frontmatter (`name`, `description`) plus instructions
  - `scripts/`: helper scripts the skill calls
  - `references/`: material the skill reads while it runs
  - `evals/<case>/`: test cases in the `claude plugin eval` layout (`prompt.md`, `case.yaml`, `graders/NN-*.md`, `files/` + `place-files.sh` for inputs)

## Working on skills

- Create and iterate on skills with the `skill-creator` skill. Its flow is: draft, run with-skill vs. baseline subagents, grade, review, revise.
- Keep eval run outputs in a sibling workspace outside the repo (e.g. `/home/user/skills-workspace/iteration-N/`), not in the repo.
- Validate a skill's frontmatter with skill-creator's `python3 -m scripts.quick_validate <skill-dir>`, run from the skill-creator directory.
- Run evals from a terminal (optional, billed model runs): from the skill dir, `claude plugin eval . --allow-tools Write,Edit,Bash --scaffold`.

## sheets-creator

Turns sheet-music scans (image/PDF) into slide-ready lyric `.txt` files for worship screens. The spec is the user's own sample, `references/example.txt`; when the rules in `SKILL.md` and that file disagree, the sample wins. Key output rules:

- Blank-line-separated blocks, each exactly 2 lines, padded with `-`.
- Every song starts with a title block (`title` / `-`).
- Lyrics are expanded in song-form order.
- No part labels, song-form line, chords or handwritten memos.
- Erased song-form items and lyric-less parts are dropped.

`scripts/pdf_to_images.py <pdf> <out_dir> [--dpi N]` renders PDF pages to PNG via `pdftoppm`, falling back to `pypdfium2`.

The one eval case (`naui-baekseongi-pdf`) is the song that also appears in `references/example.txt`, so it can't tell whether the skill generalizes. New eval cases should use songs not in the example.
