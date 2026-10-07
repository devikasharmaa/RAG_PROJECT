import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import json

import faiss

from loader import load_pdf
from chunker import chunk_pages
from embeddings import embed_texts

INDEX_DIR = "data/index"
INDEX_PATH = os.path.join(INDEX_DIR, "faiss_index.bin")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks.json")


def build_index(pdf_path):
    pages = load_pdf(pdf_path)
    chunks = chunk_pages(pages)
    vectors = embed_texts([c["text"] for c in chunks])

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return index, chunks


def load_index():
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


if __name__ == "__main__":
    index, chunks = build_index("data/documents/sample1.pdf")
    print("FAISS index built successfully!")
    print("Total vectors stored:", index.ntotal)
    print("Saved to:", INDEX_DIR)