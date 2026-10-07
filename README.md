# Smart Document Q&A (RAG Pipeline)

Upload a PDF, ask a question in plain English, and get an answer grounded in the document, with the page numbers it came from. Everything runs locally on a laptop: no paid API, no data leaves the machine.

## How it works

```
PDF
 └─ loader.py        read text page by page (keeps page numbers)
 └─ chunker.py       split pages into ~500-character chunks, drop title-only chunks
 └─ embeddings.py    turn each chunk into a 384-number vector (all-MiniLM-L6-v2)
 └─ vector_store.py  store vectors in a FAISS index

Question
 └─ retriever.py         fast search: top 20 chunks by cosine similarity
 └─ answer_generator.py  safety check: refuse if best score < 0.4
 └─ reranker.py          cross-encoder re-orders the 20, keeps the best 4
 └─ answer_generator.py  llama3.1:8b (via Ollama) writes an answer with [1], [2] citations
```

## Project structure

```
RAG_PROJECT/
├── data/
│   ├── documents/        PDFs (sample1.pdf = FSD Unit 2 notes)
│   └── index/            FAISS index + chunks.json (generated, not in git)
├── src/
│   ├── loader.py         PDF → pages
│   ├── chunker.py        pages → chunks
│   ├── embeddings.py     chunks → vectors
│   ├── vector_store.py   build / load the FAISS index
│   ├── retriever.py      vector search
│   ├── reranker.py       cross-encoder re-ranking
│   ├── answer_generator.py   prompt + Ollama call + safety check
│   ├── api.py            FastAPI app (/ask, /upload, /health, demo page)
│   ├── evaluate.py       retrieval + refusal test set
│   └── judge.py          RAGAS-style faithfulness and relevancy scores
├── static/index.html     demo web page
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment, then install packages:
```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```
2. Install [Ollama](https://ollama.com) and download the model:
```bash
   ollama pull llama3.1:8b
```

## Run

Build the index for the sample notes:
```bash
python src/vector_store.py
```

Start the server and open http://127.0.0.1:8000/ in a browser:
```bash
python -m uvicorn api:app --app-dir src
```

API endpoints (interactive docs at http://127.0.0.1:8000/docs):

| Endpoint | What it does |
|---|---|
| `POST /ask` | `{"question": "..."}` → answer + sources (page, score, text) |
| `POST /upload` | upload a PDF; replaces the current index |
| `GET /health` | check the server is running |

Upload from the terminal:
```bash
curl -F "file=@/path/to/file.pdf" http://127.0.0.1:8000/upload
```

## Evaluation

### 1. Retrieval and refusal tests (`python src/evaluate.py`)

13 hand-written questions about the FSD notes: 5 answerable (with the expected page) and 8 that the notes do not answer (the system should say "I don't know").

| Version | Score |
|---|---|
| Flan-T5 (first version) | answers too short to be useful |
| llama3.2 (3B) | 11/13 |
| llama3.1 (8B) | 12/13 |
| llama3.1 (8B) + re-ranker | 12/13 |

The one remaining "fail" (CSS box model) is a correct answer phrased in a way the keyword checker does not recognise: the model says the topic is only listed in the syllabus, not explained.

### 2. Answer quality (`python src/judge.py`)

RAGAS-style metrics, implemented directly with llama3.1:8b as the judge:

- **Faithfulness**: the answer is split into claims; each claim is checked against the retrieved sources.
- **Relevancy**: the judge rates 1–5 how well the answer addresses the question (converted to 0–1).

| Metric | Score |
|---|---|
| Faithfulness (automatic) | 0.95 |
| Relevancy (automatic) | 0.95 |
| Faithfulness after manually checking every flagged claim | 1.00 |

Both claims the judge flagged as unsupported were found in the notes (pages 4 and 22), so they were judge errors.

## Design decisions and findings

- **Page-by-page chunking** so every chunk keeps its page number for citations.
- **Title-only chunks removed** (under 60 characters). 43 of the original 68 chunks were slide titles whose content is a picture; they matched questions strongly but contained no answer.
- **Safety threshold 0.4**, chosen by testing: real matches scored 0.65+, while off-topic questions scored 0.17–0.36. Below the threshold the system refuses without calling the model.
- **Re-ranker added** after a retrieval miss on a second PDF (AI Ethics): the chunk listing "three frameworks for AI and the law" was not in the top 4. After re-ranking it moved to #1 and the question was answered correctly.
- **llama3.2 (3B) vs llama3.1 (8B)**: the smaller model filled in explanations from its own knowledge when a topic was only mentioned (e.g. relative vs absolute positioning). The 8B model correctly refused.
- **Embeddings run on CPU** so the 8B model has enough GPU memory on an M2 MacBook Air.
- **`OMP_NUM_THREADS=1`** is set in code to stop a crash caused by PyTorch and FAISS both using OpenMP on macOS.

## Known limitations

- **Text inside images is not read.** About two-thirds of the sample notes are image-based slides, so topics like the box model cannot be answered. Fix: add OCR.
- **PDF only.** Word (.docx) support is not built yet.
- **Citations are page-level**, not section-level.
- **One document at a time.** Uploading a new PDF replaces the index.
- **The judge is the same small model** that writes the answers, and it is noisy: the same answer received different faithfulness scores across runs. A larger, separate judge model would be more reliable.
- **Small test set** (13 questions on one document).
- **Slow on a laptop**: the first question after a break can take a few minutes while the model loads.

## Next steps

- OCR for image-based pages
- Word document support
- Section-level citations (detect headings while loading)
- Larger evaluation set across several documents
- Official RAGAS library with a stronger judge model