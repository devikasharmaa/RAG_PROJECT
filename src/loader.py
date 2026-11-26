import re
from pypdf import PdfReader


def clean_text(text):
    text = re.sub(r"[\uf000-\uf8ff]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def load_pdf(file_path):
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append({
                "page": page_number + 1,
                "text": clean_text(text),
            })

    return pages


if __name__ == "__main__":
    from config import DEFAULT_PDF

    pages = load_pdf(DEFAULT_PDF)
    print("Total pages:", len(pages))
    print(pages[0])