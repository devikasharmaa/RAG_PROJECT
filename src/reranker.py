import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        # CPU keeps GPU memory free for the Ollama model
        _model = CrossEncoder(MODEL_NAME, device="cpu")
    return _model


def rerank(question, results, top_k=4):
    if not results:
        return results
    pairs = [(question, r["text"]) for r in results]
    scores = get_model().predict(pairs)
    for r, s in zip(results, scores):
        r["rerank_score"] = float(s)
    results = sorted(results, key=lambda r: r["rerank_score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    from retriever import search

    question = "What are the three frameworks for AI and the law?"
    candidates = search(question, k=20)

    print("BEFORE re-ranking (top 4 from fast search):")
    for r in candidates[:4]:
        print(f"  chunk {r['chunk_id']} | page {r['page']} | {r['text'][:70]!r}")

    print("\nAFTER re-ranking (top 4):")
    for r in rerank(question, candidates):
        print(f"  chunk {r['chunk_id']} | page {r['page']} | {r['text'][:70]!r}")