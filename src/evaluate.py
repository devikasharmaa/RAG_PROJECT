from answer_generator import generate_answer
from report import cell, escape, quote, run_info, save, settings_table, source_summary

# The questions below were written for this document
DOCUMENT = "Full Stack Development, Unit 2 notes (CSS)"

REFUSAL_PHRASES = ["i don't know", "does not cover", "no mention", "not mentioned"]

# Each test: a question + the page(s) where the answer is in your PDF.
# Empty pages [] means the answer is NOT in your notes, so it should say "I don't know".
TESTS = [
    {"question": "What is CSS?", "pages": [3]},
    {"question": "What are the benefits of CSS?", "pages": [4, 5]},
    {"question": "What happens when selectors have different specificity?", "pages": [17]},
    {"question": "What are CSS gradients?", "pages": [22, 23, 24, 25, 26]},
    {"question": "How do you add inline CSS to an HTML element?", "pages": [7]},
    {"question": "Who won the cricket World Cup in 2011?", "pages": []},
    {"question": "How do I install Python on Windows?", "pages": []},
    {"question": "What is the CSS box model?", "pages": []},
    {"question": "What is cascading effect?", "pages": []},
    {"question": "What is the difference between relative and absolute positioning in CSS?", "pages": []},
    {"question": "What is the difference between inline, block, and inline-block elements in CSS?", "pages": []},
    {"question": "What is the difference between a class and an ID in CSS?", "pages": []},
    {"question": "What is the difference between a pseudo-class and a pseudo-element in CSS?", "pages": []},
]


def outcome(refused, sources):
    if not refused:
        return "answered"
    # Re-ranked sources mean the question passed the safety check, so the model refused
    if any("rerank_score" in s for s in sources):
        return "refused by the model"
    return "refused by the safety check"


def run():
    info = run_info(DOCUMENT)
    results = []
    for t in TESTS:
        answer, sources = generate_answer(t["question"])
        found_pages = [s["page"] for s in sources]
        refused = any(p in answer.lower() for p in REFUSAL_PHRASES)

        if t["pages"]:
            ok = (not refused) and any(p in found_pages for p in t["pages"])
        else:
            ok = refused

        print("PASS" if ok else "FAIL", "|", t["question"])
        print("   expected pages:", t["pages"] or "none (should refuse)",
              "| found:", found_pages)
        print("   answer:", answer[:150].replace("\n", " "))
        print()

        results.append({
            "question": t["question"],
            "expected_pages": t["pages"],
            "pages_found": found_pages,
            "outcome": outcome(refused, sources),
            "passed": ok,
            "answer": answer,
            "sources": source_summary(sources),
        })

    passed = sum(r["passed"] for r in results)
    print(f"SCORE: {passed}/{len(TESTS)}")

    data = {"settings": info, "score": f"{passed}/{len(TESTS)}", "results": results}
    save("retrieval_and_refusal", data, to_markdown(info, results, passed))


# ---------- results file ----------

def pages_text(pages):
    return ", ".join(str(p) for p in pages) if pages else "none"


def expected_text(pages):
    if not pages:
        return "refusal"
    return ("page " if len(pages) == 1 else "pages ") + pages_text(pages)


def to_markdown(info, results, passed):
    answerable = sum(1 for r in results if r["expected_pages"])
    lines = [
        "# Retrieval and refusal test",
        "",
        "Output of `python src/evaluate.py`. "
        f"{answerable} questions are answered in the notes: the system must answer, "
        "and the expected page must be among the pages it retrieved. "
        f"{len(results) - answerable} questions are not answered in the notes: "
        "the system must say it doesn't know.",
        "",
        settings_table(info),
        "",
        f"## Score: {passed}/{len(results)}",
        "",
        "| # | Question | Expected | Outcome | Pages retrieved | Top score | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(results, start=1):
        scores = [s["score"] for s in r["sources"]]
        top = f"{max(scores):.2f}" if scores else "n/a"
        result = "PASS" if r["passed"] else "FAIL"
        lines.append(
            f"| {n} | {cell(r['question'])} | {expected_text(r['expected_pages'])} "
            f"| {r['outcome']} | {pages_text(r['pages_found'])} | {top} | {result} |"
        )
    lines += [
        "",
        "Top score is the highest similarity (0 to 1) between the question and a retrieved "
        f"passage. Below {info['safety_threshold']}, the system refuses without calling the model.",
        "",
        "## Answers",
        "",
    ]
    for n, r in enumerate(results, start=1):
        lines += [
            f"### {n}. {escape(r['question'])}",
            "",
            f"**{'PASS' if r['passed'] else 'FAIL'}**, {r['outcome']}. "
            f"Expected: {expected_text(r['expected_pages'])}. "
            f"Pages retrieved: {pages_text(r['pages_found'])}.",
            "",
            quote(r["answer"]),
            "",
        ]
    return "\n".join(lines)


if __name__ == "__main__":
    run()
