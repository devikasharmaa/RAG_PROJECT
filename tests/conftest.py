import hashlib
import io
import os
import sys
import tempfile

import numpy as np
import pytest
from pypdf import PdfWriter
from pypdf.generic import (ArrayObject, DecodedStreamObject, DictionaryObject,
                           NameObject)

# Tests must never touch the real data/ folder: point the app at a temp folder
# before any module under src/ is imported.
_TMP_DATA = tempfile.mkdtemp(prefix="rag-test-data-")
os.environ["RAG_DATA_DIR"] = _TMP_DATA

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC))


def make_pdf(pages):
    """Build a small text PDF in memory. `pages` is a list of strings, one per page."""
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        })
        lines = [text[i:i + 80] for i in range(0, len(text), 80)] or [""]
        ops = ["BT", "/F1 10 Tf", "14 TL", "40 750 Td"]
        for line in lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({safe}) Tj T*")
        ops.append("ET")
        stream = DecodedStreamObject()
        stream.set_data("\n".join(ops).encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def fake_embed(texts):
    """Deterministic stand-in for the sentence-transformer (no model download)."""
    vectors = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:4], "little")
        v = np.random.default_rng(seed).standard_normal(384)
        vectors.append(v / np.linalg.norm(v))
    return np.array(vectors, dtype="float32").reshape(len(texts), 384)


def fake_rerank(question, results, top_k=4):
    return results[:top_k]


class FakeOllamaResponse:
    status_code = 200
    ok = True

    def json(self):
        return {"message": {"content": "A fake answer [1]."}}


@pytest.fixture
def client(monkeypatch):
    """API client with the embedding model, re-ranker and Ollama faked out."""
    import vector_store
    import retriever
    import answer_generator
    import api
    from fastapi.testclient import TestClient

    monkeypatch.setattr(vector_store, "embed_texts", fake_embed)
    monkeypatch.setattr(retriever, "embed_texts", fake_embed)
    monkeypatch.setattr(answer_generator, "rerank", fake_rerank)
    # fake vectors score near 0, so turn off the 0.4 safety check to reach Ollama
    monkeypatch.setattr(answer_generator, "MIN_SCORE", -1)
    monkeypatch.setattr(answer_generator.requests, "post",
                        lambda *a, **k: FakeOllamaResponse())
    return TestClient(api.app)


@pytest.fixture
def small_pdf():
    return make_pdf([f"Page {i}. " + "CSS selectors pick elements to style. " * 6
                     for i in range(1, 4)])


@pytest.fixture
def big_pdf():
    return make_pdf([f"Page {i}. " + "Flexbox lays out items along one axis. " * 30
                     for i in range(1, 31)])
