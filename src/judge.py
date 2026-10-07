import json

import requests

from answer_generator import generate_answer, OLLAMA_URL, MODEL_NAME, IDK
from evaluate import TESTS

JUDGE_MODEL = MODEL_NAME

FAITHFULNESS_PROMPT = """You are checking whether an answer is supported by source passages.

Passages:
{context}

Answer:
{answer}

Split the answer into short factual claims. For each claim, decide whether the
passages directly support it. Reply in JSON with one key, "claims": a list of
objects, each with the keys "claim" (text) and "supported" (true or false)."""

RELEVANCY_PROMPT = """Question: {question}
Answer: {answer}

Rate how well the answer addresses the question on a scale of 1 to 5:
1 = off-topic, 2 = mostly off-topic, 3 = partly answers,
4 = mostly answers, 5 = fully answers.
First write a one-sentence reason, then the rating.
Reply in JSON with the keys "reason" (text) and "rating" (a number 1-5)."""


def ask_judge(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={"model": JUDGE_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "stream": False, "format": "json",
              "options": {"temperature": 0}},
        timeout=300,
    )
    response.raise_for_status()
    try:
        return json.loads(response.json()["message"]["content"])
    except json.JSONDecodeError:
        return {}


def faithfulness(answer, sources):
    context = "\n\n".join(f"[{n}] {s['text']}" for n, s in enumerate(sources, 1))
    claims = ask_judge(FAITHFULNESS_PROMPT.format(context=context, answer=answer)).get("claims", [])
    if not claims:
        return None, []
    unsupported = [c.get("claim", "") for c in claims
                   if str(c.get("supported")).lower() != "true"]
    score = (len(claims) - len(unsupported)) / len(claims)
    return score, unsupported


def relevancy(question, answer):
    result = ask_judge(RELEVANCY_PROMPT.format(question=question, answer=answer))
    try:
        rating = max(1.0, min(5.0, float(result.get("rating"))))
    except (TypeError, ValueError):
        return None, ""
    return (rating - 1) / 4, result.get("reason", "")  # 1-5 -> 0-1


def run():
    faith_scores, rel_scores = [], []
    for t in TESTS:
        if not t["pages"]:
            continue  # only grade questions the notes can answer
        answer, sources = generate_answer(t["question"])
        if answer.startswith(IDK):
            print("SKIP (refused) |", t["question"])
            continue

        f, unsupported = faithfulness(answer, sources)
        r, reason = relevancy(t["question"], answer)
        if f is not None:
            faith_scores.append(f)
        if r is not None:
            rel_scores.append(r)

        f_text = "n/a" if f is None else f"{f:.2f}"
        r_text = "n/a" if r is None else f"{r:.2f}"
        print(f"faithfulness {f_text} | relevancy {r_text} | {t['question']}")
        if reason:
            print(f"   judge's reason: {reason}")
        for claim in unsupported:
            print(f"   NOT SUPPORTED: {claim}")
        print()

    if faith_scores:
        print(f"AVERAGE FAITHFULNESS: {sum(faith_scores) / len(faith_scores):.2f}")
    if rel_scores:
        print(f"AVERAGE RELEVANCY:    {sum(rel_scores) / len(rel_scores):.2f}")


if __name__ == "__main__":
    run()