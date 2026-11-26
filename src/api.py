import logging
import os
import shutil
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pypdf.errors import FileNotDecryptedError, PdfReadError

from answer_generator import LLMUnavailableError, generate_answer
from config import DOCUMENTS_DIR, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB, STATIC_DIR
from retriever import replace_index
from upload_limit import MaxBodySizeMiddleware
from vector_store import IndexNotFoundError, NoTextError

log = logging.getLogger("rag")

app = FastAPI(title="RAG Document Q&A")
# Reject oversized uploads while they are still arriving, before they fill the disk
app.add_middleware(MaxBodySizeMiddleware, max_bytes=MAX_UPLOAD_BYTES,
                   paths={"/upload"})


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def format_sources(sources):
    return [
        {"number": n, "page": s["page"],
         "score": round(s["score"], 3), "text": s["text"]}
        for n, s in enumerate(sources, start=1)
    ]


@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400,
                            detail="Only PDF files are supported for now.")

    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    # Save under a unique temp name first, so two uploads never write the same file
    fd, tmp_path = tempfile.mkstemp(dir=DOCUMENTS_DIR, suffix=".pdf.part")
    try:
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            chunks = replace_index(tmp_path)
        except FileNotDecryptedError:
            raise HTTPException(status_code=400,
                                detail="This PDF is password-protected. Remove "
                                       "the password and upload it again.")
        except PdfReadError:
            raise HTTPException(status_code=400,
                                detail="This file could not be opened as a PDF. "
                                       "It may be damaged or not really a PDF.")
        except NoTextError:
            raise HTTPException(status_code=400,
                                detail="No readable text found in this PDF. If it "
                                       "is a scanned document, it has no text "
                                       "layer to search.")
        # Any other error is a bug: let it reach the log as a 500, don't hide it

        final_path = os.path.join(DOCUMENTS_DIR, os.path.basename(file.filename))
        os.replace(tmp_path, final_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"filename": file.filename, "chunks": len(chunks)}


@app.post("/ask")
def ask(q: Question):
    try:
        answer, sources = generate_answer(q.question)
    except IndexNotFoundError:
        raise HTTPException(status_code=409,
                            detail="No document has been indexed yet. "
                                   "Upload a PDF first.")
    except LLMUnavailableError as e:
        log.warning("LLM unavailable: %s", e)
        # Fallback: still return the passages we found, so the user can read them
        return JSONResponse(status_code=503, content={
            "question": q.question,
            "detail": str(e),
            "sources": format_sources(e.sources),
        })

    return {
        "question": q.question,
        "answer": answer,
        "sources": format_sources(sources),
    }
