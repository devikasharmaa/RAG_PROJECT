import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import json
import tempfile

import faiss

from config import DEFAULT_PDF, INDEX_DIR
from loader import load_pdf
from chunker import chunk_pages
from embeddings import embed_texts

INDEX_PATH = os.path.join(INDEX_DIR, "faiss_index.bin")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks.json")


class NoTextError(ValueError):
    """The PDF opened fine but has no searchable text (e.g. a scanned document)."""


class IndexNotFoundError(FileNotFoundError):
    """No index has been built yet."""


def _atomic_write(path, write):
    # Write to a temp file in the same folder, then rename it over the old file.
    # A rename is atomic, so nobody ever reads a half-written file.
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    os.close(fd)
    try:
        write(tmp)
        os.replace(tmp, path)
    except BaseException:
        os.remove(tmp)
        raise


def build_index(pdf_path):
    pages = load_pdf(pdf_path)
    chunks = chunk_pages(pages)
    if not chunks:
        raise NoTextError(pdf_path)
    vectors = embed_texts([c["text"] for c in chunks])

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    os.makedirs(INDEX_DIR, exist_ok=True)

    def write_chunks(tmp):
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

    _atomic_write(INDEX_PATH, lambda tmp: faiss.write_index(index, tmp))
    _atomic_write(CHUNKS_PATH, write_chunks)

    return index, chunks


def load_index():
    if not (os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH)):
        raise IndexNotFoundError(INDEX_DIR)
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


if __name__ == "__main__":
    index, chunks = build_index(DEFAULT_PDF)
    print("FAISS index built successfully!")
    print("Total vectors stored:", index.ntotal)
    print("Saved to:", INDEX_DIR)
