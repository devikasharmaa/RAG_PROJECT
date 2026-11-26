import requests

import answer_generator
import config
import retriever
import vector_store


def upload(client, data, name="notes.pdf"):
    return client.post("/upload", files={"file": (name, data, "application/pdf")})


def no_index(monkeypatch):
    monkeypatch.setattr(retriever, "_state", None)
    monkeypatch.setattr(vector_store, "INDEX_PATH", "/nonexistent/faiss_index.bin")


# ---------- /upload ----------

def test_upload_ok(client, small_pdf):
    r = upload(client, small_pdf)
    assert r.status_code == 200
    assert r.json()["chunks"] > 0


def test_upload_rejects_non_pdf_name(client):
    assert upload(client, b"hello", name="notes.txt").status_code == 400


def test_upload_too_large_is_rejected(client):
    big = b"%PDF-" + b"0" * (config.MAX_UPLOAD_BYTES + 1)
    r = upload(client, big)
    assert r.status_code == 413
    assert "too large" in r.json()["detail"]


def test_upload_too_large_without_content_length_is_rejected(client):
    # A chunked upload has no Content-Length; the byte counter must still stop it
    def body():
        boundary = b"--b\r\n"
        yield boundary + b'Content-Disposition: form-data; name="file"; filename="x.pdf"\r\n\r\n'
        chunk = b"0" * (1024 * 1024)
        for _ in range(config.MAX_UPLOAD_MB + 2):
            yield chunk
        yield b"\r\n--b--\r\n"

    r = client.post("/upload", content=body(),
                    headers={"Content-Type": "multipart/form-data; boundary=b"})
    assert r.status_code == 413


def test_upload_corrupt_pdf(client):
    r = upload(client, b"this is not really a pdf")
    assert r.status_code == 400
    assert "could not be opened" in r.json()["detail"]


def test_upload_pdf_without_text(client):
    from conftest import make_pdf
    r = upload(client, make_pdf(["", ""]))
    assert r.status_code == 400
    assert "No readable text" in r.json()["detail"]


def test_upload_unexpected_error_is_not_disguised(client, small_pdf, monkeypatch):
    # A real bug must surface as a 500, not as "unreadable PDF"
    def broken(_texts):
        raise RuntimeError("bug in embedding code")
    monkeypatch.setattr(vector_store, "embed_texts", broken)
    from fastapi.testclient import TestClient
    real_server = TestClient(client.app, raise_server_exceptions=False)
    r = upload(real_server, small_pdf)
    assert r.status_code == 500
    assert "unreadable" not in r.text and "No readable text" not in r.text


def test_failed_upload_leaves_no_temp_files(client):
    upload(client, b"not a pdf")
    import os
    leftovers = [f for f in os.listdir(config.DOCUMENTS_DIR) if f.endswith(".part")]
    assert leftovers == []


# ---------- /ask ----------

def test_ask_ok(client, small_pdf):
    upload(client, small_pdf)
    r = client.post("/ask", json={"question": "What do CSS selectors do?"})
    assert r.status_code == 200
    assert r.json()["answer"] == "A fake answer [1]."
    assert r.json()["sources"]


def test_ask_empty_question(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_before_any_upload(client, monkeypatch):
    no_index(monkeypatch)
    r = client.post("/ask", json={"question": "anything"})
    assert r.status_code == 409
    assert "Upload a PDF first" in r.json()["detail"]


def test_ask_when_ollama_is_down(client, small_pdf, monkeypatch):
    upload(client, small_pdf)

    def refused(*a, **k):
        raise requests.exceptions.ConnectionError("connection refused")
    monkeypatch.setattr(answer_generator.requests, "post", refused)

    r = client.post("/ask", json={"question": "What do CSS selectors do?"})
    assert r.status_code == 503
    body = r.json()
    assert "not running" in body["detail"]
    assert body["sources"], "fallback should still return the passages it found"


def test_ask_when_model_not_downloaded(client, small_pdf, monkeypatch):
    upload(client, small_pdf)

    class NotFound:
        status_code = 404
        ok = False
    monkeypatch.setattr(answer_generator.requests, "post", lambda *a, **k: NotFound())

    r = client.post("/ask", json={"question": "What do CSS selectors do?"})
    assert r.status_code == 503
    assert "ollama pull" in r.json()["detail"]


def test_ask_when_ollama_times_out(client, small_pdf, monkeypatch):
    upload(client, small_pdf)

    def slow(*a, **k):
        raise requests.exceptions.ReadTimeout()
    monkeypatch.setattr(answer_generator.requests, "post", slow)

    r = client.post("/ask", json={"question": "What do CSS selectors do?"})
    assert r.status_code == 503
    assert "too long" in r.json()["detail"]
