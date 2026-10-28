import json

import requests

from answer_generator import generate_answer, OLLAMA_URL, MODEL_NAME, IDK
from evaluate import DOCUMENT, TESTS
from report import cell, escape, inline, quote, run_info, save, settings_table, source_summary

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
        return None, [], 0
    unsupported = [c.get("claim", "") for c in claims
                   if str(c.get("supported")).lower() != "true"]
    score = (len(claims) - len(unsupported)) / len(claims)
    return score, unsupported, len(claims)


def relevancy(question, answer):
    result = ask_judge(RELEVANCY_PROMPT.format(question=question, answer=answer))
    try:
        rating = max(1.0, min(5.0, float(result.get("rating"))))
    except (TypeError, ValueError):
        return None, ""
    return (rating - 1) / 4, result.get("reason", "")  # 1-5 -> 0-1


def average(scores):
    return sum(scores) / len(scores) if scores else None


def rounded(score):
    return None if score is None else round(score, 3)


def run():
    info = run_info(DOCUMENT, judge_model=JUDGE_MODEL)
    faith_scores, rel_scores, results = [], [], []
    for t in TESTS:
        if not t["pages"]:
            continue  # only grade questions the notes can answer
        answer, sources = generate_answer(t["question"])
        if answer.startswith(IDK):
            print("SKIP (refused) |", t["question"])
            results.append({"question": t["question"], "skipped": True,
                            "answer": answer, "sources": source_summary(sources)})
            continue

        f, unsupported, claims = faithfulness(answer, sources)
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

        results.append({
            "question": t["question"],
            "faithfulness": rounded(f),
            "claims_checked": claims,
            "unsupported_claims": unsupported,
            "relevancy": rounded(r),
            "judge_reason": reason,
            "answer": answer,
            "sources": source_summary(sources),
        })

    faith, rel = average(faith_scores), average(rel_scores)
    if faith is not None:
        print(f"AVERAGE FAITHFULNESS: {faith:.2f}")
    if rel is not None:
        print(f"AVERAGE RELEVANCY:    {rel:.2f}")

    data = {"settings": info, "average_faithfulness": rounded(faith),
            "average_relevancy": rounded(rel), "results": results}
    save("answer_quality", data, to_markdown(info, results, faith, rel))


# ---------- results file ----------

def score_text(score):
    return "n/a" if score is None else f"{score:.2f}"


def claims_text(r):
    if not r["claims_checked"]:
        return "n/a"
    supported = r["claims_checked"] - len(r["unsupported_claims"])
    return f"{supported} of {r['claims_checked']}"


def to_markdown(info, results, faith, rel):
    lines = [
        "# Answer quality (RAGAS-style)",
        "",
        "Output of `python src/judge.py`. Only the questions the notes can answer are graded. "
        "The judge is the same local model that writes the answers.",
        "",
        "- **Faithfulness**: the answer is split into claims, and each claim is checked "
        "against the passages the answer was based on. The score is the share of claims supported.",
        "- **Relevancy**: the judge rates from 1 to 5 how well the answer addresses "
        "the question, converted to 0–1.",
        "",
        settings_table(info),
        "",
        "## Averages",
        "",
        "| Metric | Score |",
        "|---|---|",
        f"| Faithfulness | {score_text(faith)} |",
        f"| Relevancy | {score_text(rel)} |",
        "",
        "## Per question",
        "",
        "| # | Question | Faithfulness | Claims supported | Relevancy |",
        "|---|---|---|---|---|",
    ]
    for n, r in enumerate(results, start=1):
        if r.get("skipped"):
            lines.append(f"| {n} | {cell(r['question'])} | skipped: the system refused | | |")
        else:
            lines.append(
                f"| {n} | {cell(r['question'])} | {score_text(r['faithfulness'])} "
                f"| {claims_text(r)} | {score_text(r['relevancy'])} |"
            )

    lines += ["", "## Details", ""]
    for n, r in enumerate(results, start=1):
        lines += [f"### {n}. {escape(r['question'])}", ""]
        if r.get("skipped"):
            lines += ["Skipped: the system refused to answer.", "", quote(r["answer"]), ""]
            continue
        if r["claims_checked"]:
            lines.append(f"- Faithfulness: {score_text(r['faithfulness'])} "
                         f"({claims_text(r)} claims supported)")
        else:
            lines.append("- Faithfulness: n/a (the judge returned no claims)")
        relevancy_line = f"- Relevancy: {score_text(r['relevancy'])}"
        if r["judge_reason"]:
            relevancy_line += f". Judge's reason: {inline(r['judge_reason'])}"
        lines.append(relevancy_line)
        if r["unsupported_claims"]:
            lines.append("- Claims the judge marked as not supported:")
            lines += [f"  - {inline(c)}" for c in r["unsupported_claims"]]
        lines += ["", "**Answer:**", "", quote(r["answer"]), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    run()
