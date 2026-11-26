import threading

from embeddings import embed_texts
from vector_store import build_index, load_index

# The loaded index and its chunks are kept together as ONE tuple, so a search
# always sees a matching pair. Swapping the tuple is a single assignment, which
# is atomic in Python, so searches never need to wait for the lock.
_state = None
# Only one thread at a time may build or load the index (and write its files).
_lock = threading.Lock()


def _get_state():
    global _state
    state = _state
    if state is None:
        with _lock:
            if _state is None:  # another thread may have loaded it while we waited
                _state = load_index()
            state = _state
    return state


def replace_index(pdf_path):
    """Build an index for a new PDF and switch searches over to it.

    Questions asked while this runs keep using the old index, so they neither
    fail nor wait. Two uploads at once are handled one after the other.
    """
    global _state
    with _lock:
        index, chunks = build_index(pdf_path)
        _state = (index, chunks)
    return chunks


def search(query, k=3):
    index, chunks = _get_state()  # local copies: an upload can't change them mid-search

    query_vector = embed_texts([query])
    scores, ids = index.search(query_vector, k)

    results = []
    for score, i in zip(scores[0], ids[0]):
        if i == -1:
            continue
        result = dict(chunks[i])
        result["score"] = float(score)
        results.append(result)

    return results


if __name__ == "__main__":
    question = "What is CSS?"
    for r in search(question):
        print(f"Page {r['page']} | score {r['score']:.3f}")
        print(r["text"])
        print("----------------")
