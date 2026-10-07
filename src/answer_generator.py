import requests
from retriever import search
from reranker import rerank

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"
MIN_SCORE = 0.4
MIN_CHUNK_LENGTH = 60
CANDIDATES = 20
IDK = "I don't know. The document does not cover this."

SYSTEM_PROMPT = (
    "You answer questions using ONLY the numbered context passages given. "
    "Rules: 1) Use only facts from the passages, never your own knowledge. "
    "2) After each sentence or bullet, cite the passage it came from, like [1] or [2]. "
    "3) ONLY if none of the passages answer the question, reply with just this "
    "one sentence and nothing else: "
    "\"I don't know. The document does not cover this.\" "
    "4) If you did answer the question, never add that sentence."
)


def build_context(results):
    return "\n\n".join(
        f"[{n}] (Page {r['page']})\n{r['text']}"
        for n, r in enumerate(results, start=1)
    )


def generate_answer(question, k=4):
    # 1) Fast search: grab many candidates, drop title-only chunks
    candidates = search(question, k=CANDIDATES)
    candidates = [r for r in candidates if len(r["text"]) >= MIN_CHUNK_LENGTH]

    # 2) Safety check: if nothing in the document matches well, don't ask the AI
    if not candidates or candidates[0]["score"] < MIN_SCORE:
        return IDK, candidates[:k]

    # 3) Re-rank: a smarter model picks the best k chunks
    results = rerank(question, candidates, top_k=k)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",
         "content": f"Context:\n{build_context(results)}\n\nQuestion: {question}"},
    ]

    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "messages": messages,
              "stream": False, "options": {"temperature": 0}},
        timeout=300,
    )
    response.raise_for_status()
    answer = response.json()["message"]["content"].strip()

    return answer, results


if __name__ == "__main__":
    question = "What are the three frameworks for AI and the law?"
    answer, sources = generate_answer(question)

    print("ANSWER:")
    print(answer)
    print("\nSOURCES:")
    for n, s in enumerate(sources, start=1):
        print(f"[{n}] Page {s['page']} (score {s['score']:.2f}): {s['text'][:100]}...")