import os
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from answer_generator import generate_answer
from retriever import reset_index
from vector_store import build_index

UPLOAD_DIR = "data/documents"

app = FastAPI(title="RAG Document Q&A")


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400,
                            detail="Only PDF files are supported for now.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, os.path.basename(file.filename))
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        _, chunks = build_index(path)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. If it is a scanned "
                   "document, it has no text layer to search.",
        )

    reset_index()
    return {"filename": file.filename, "chunks": len(chunks)}


@app.post("/ask")
def ask(q: Question):
    answer, sources = generate_answer(q.question)
    return {
        "question": q.question,
        "answer": answer,
        "sources": [
            {"number": n, "page": s["page"],
             "score": round(s["score"], 3), "text": s["text"]}
            for n, s in enumerate(sources, start=1)
        ],
    }