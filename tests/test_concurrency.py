"""Concurrent /upload and /ask must never crash or mix two documents.

Uploads keep swapping between a 3-page and a 30-page PDF while several threads
ask questions. Without a lock, an /ask can see the new FAISS index with the old
chunk list (IndexError), or a half-written chunks.json, and return a 500.
"""
from concurrent.futures import ThreadPoolExecutor


def test_upload_and_ask_at_the_same_time(client, small_pdf, big_pdf):
    first = client.post("/upload", files={"file": ("small.pdf", small_pdf, "application/pdf")})
    assert first.status_code == 200

    def upload(i):
        pdf, name = (big_pdf, "big.pdf") if i % 2 == 0 else (small_pdf, "small.pdf")
        return client.post("/upload", files={"file": (name, pdf, "application/pdf")})

    def ask(i):
        return client.post("/ask", json={"question": f"What does CSS do? ({i})"})

    with ThreadPoolExecutor(max_workers=12) as pool:
        uploads = [pool.submit(upload, i) for i in range(20)]
        asks = [pool.submit(ask, i) for i in range(200)]
        upload_codes = [f.result().status_code for f in uploads]
        ask_responses = [f.result() for f in asks]

    assert set(upload_codes) == {200}
    errors = [r.status_code for r in ask_responses if r.status_code != 200]
    assert errors == [], f"{len(errors)} of {len(ask_responses)} questions failed: {set(errors)}"

    for r in ask_responses:
        for s in r.json()["sources"]:
            # each source must be a real chunk of one of the two PDFs
            assert "CSS selectors" in s["text"] or "Flexbox" in s["text"]
