import fitz  # PyMuPDF


def extract_text(pdf_path: str) -> tuple[str, int]:
    """PDF에서 텍스트를 추출한다. (전체 텍스트, 페이지 수)를 반환."""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    full_text = "\n".join(pages)
    return full_text, len(pages)
