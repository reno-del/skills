"""PDF 악보를 페이지별 PNG로 바꾼다.

사용법: python pdf_to_images.py <악보.pdf> <출력 폴더> [배율]

pdftoppm(poppler)이 있으면 쓰고, 없으면 pypdfium2를 쓴다.
배율 기본값 2.0 (약 144dpi): 음표 아래 작은 가사를 읽을 만한 크기.
"""
import os
import shutil
import subprocess
import sys


def with_pdftoppm(pdf, out_dir, scale):
    dpi = str(int(72 * scale))
    subprocess.run(
        ["pdftoppm", "-png", "-r", dpi, pdf, os.path.join(out_dir, "page")],
        check=True,
    )


def with_pypdfium2(pdf, out_dir, scale):
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf)
    for i in range(len(doc)):
        doc[i].render(scale=scale).to_pil().save(
            os.path.join(out_dir, f"page-{i + 1}.png")
        )


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pdf, out_dir = sys.argv[1], sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    os.makedirs(out_dir, exist_ok=True)

    if shutil.which("pdftoppm"):
        with_pdftoppm(pdf, out_dir, scale)
    else:
        try:
            with_pypdfium2(pdf, out_dir, scale)
        except ImportError:
            sys.exit("pdftoppm도 pypdfium2도 없습니다. `pip install pypdfium2` 후 다시 실행하세요.")

    for name in sorted(os.listdir(out_dir)):
        if name.endswith(".png"):
            print(os.path.join(out_dir, name))


if __name__ == "__main__":
    main()
