from embeddings import embed_texts
from vector_store import load_index

_index = None
_chunks = None


def reset_index():
    # Forget the loaded database so the next search reloads it from disk
    global _index, _chunks
    _index, _chunks = None, None


def search(query, k=3):
    global _index, _chunks
    if _index is None:
        _index, _chunks = load_index()

    query_vector = embed_texts([query])
    scores, ids = _index.search(query_vector, k)

    results = []
    for score, i in zip(scores[0], ids[0]):
        if i == -1:
            continue
        result = dict(_chunks[i])
        result["score"] = float(score)
        results.append(result)

    return results


if __name__ == "__main__":
    question = "What is CSS?"
    for r in search(question):
        print(f"Page {r['page']} | score {r['score']:.3f}")
        print(r["text"])
        print("----------------")