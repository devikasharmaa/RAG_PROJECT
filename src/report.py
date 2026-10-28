import json
import os
import re
from datetime import datetime

from answer_generator import CANDIDATES, MIN_SCORE, MODEL_NAME
from embeddings import MODEL_NAME as EMBEDDING_MODEL
from reranker import MODEL_NAME as RERANKER_MODEL
from vector_store import load_index

RESULTS_DIR = "results"

# `inline code` and ```code blocks``` inside an answer are shown exactly as written
CODE = re.compile(r"(```.*?```|`[^`\n]*`)", re.DOTALL)

LABELS = {
    "date": "Run on",
    "document": "Document",
    "chunks_in_index": "Chunks in the index",
    "answer_model": "Answer model (Ollama)",
    "judge_model": "Judge model (Ollama)",
    "embedding_model": "Embedding model",
    "reranker_model": "Re-ranker",
    "safety_threshold": "Safety threshold (refuse below this score)",
    "candidates_before_reranking": "Passages retrieved before re-ranking",
}


def run_info(document, judge_model=None):
    # The settings of this run, saved with the results so they can be checked
    _, chunks = load_index()
    info = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "document": document,
        "chunks_in_index": len(chunks),
        "answer_model": MODEL_NAME,
    }
    if judge_model:
        info["judge_model"] = judge_model
    info["embedding_model"] = EMBEDDING_MODEL
    info["reranker_model"] = RERANKER_MODEL
    info["safety_threshold"] = MIN_SCORE
    info["candidates_before_reranking"] = CANDIDATES
    return info


def source_summary(sources):
    # Page and scores of each passage, but not its text: the PDFs are not in the repository
    summary = []
    for s in sources:
        item = {"page": s["page"], "score": round(s["score"], 3)}
        if "rerank_score" in s:
            item["rerank_score"] = round(s["rerank_score"], 3)
        summary.append(item)
    return summary


def escape(text):
    # Show < > & as typed, instead of GitHub treating them as HTML
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    return escape(text).replace("\n", " ")


def cell(text):
    # Text for a Markdown table cell
    return inline(text).replace("|", "\\|")


def quote(text):
    # An answer as a Markdown quote block
    if not text.strip():
        return "> (empty answer)"
    parts = CODE.split(text)
    for i in range(0, len(parts), 2):  # even positions are outside code
        parts[i] = escape(parts[i])
    lines = "".join(parts).splitlines()
    return "\n".join("> " + line if line.strip() else ">" for line in lines)


def settings_table(info):
    lines = ["| Setting | Value |", "|---|---|"]
    for key, value in info.items():
        lines.append(f"| {LABELS.get(key, key)} | {cell(value)} |")
    return "\n".join(lines)


def save(name, data, markdown):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, name + ".md")
    json_path = os.path.join(RESULTS_DIR, name + ".json")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown + "\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Saved {md_path} and {json_path}")
