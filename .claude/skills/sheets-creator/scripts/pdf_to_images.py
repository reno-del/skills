#!/usr/bin/env python3
"""Render each page of a PDF to PNG so the pages can be viewed as images.

Usage: pdf_to_images.py <input.pdf> <output_dir> [--dpi 200]
Prints the path of every PNG it writes, in page order.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def render_with_pdftoppm(pdf: Path, out_dir: Path, dpi: int) -> list[Path]:
    prefix = out_dir / "page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        check=True,
    )
    return sorted(out_dir.glob("page-*.png"))


def render_with_pypdfium2(pdf: Path, out_dir: Path, dpi: int) -> list[Path]:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    paths = []
    for i in range(len(doc)):
        image = doc[i].render(scale=dpi / 72).to_pil()
        path = out_dir / f"page-{i + 1:02d}.png"
        image.save(path)
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if shutil.which("pdftoppm"):
        paths = render_with_pdftoppm(args.pdf, args.out_dir, args.dpi)
    else:
        try:
            paths = render_with_pypdfium2(args.pdf, args.out_dir, args.dpi)
        except ImportError:
            print(
                "Neither pdftoppm (poppler-utils) nor pypdfium2 is available. "
                "Install one: `pip install pypdfium2`",
                file=sys.stderr,
            )
            return 1

    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
