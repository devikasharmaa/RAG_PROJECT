from answer_generator import generate_answer

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


def run():
    passed = 0
    for t in TESTS:
        answer, sources = generate_answer(t["question"])
        found_pages = [s["page"] for s in sources]
        refused = any(p in answer.lower() for p in REFUSAL_PHRASES)

        if t["pages"]:
            ok = (not refused) and any(p in found_pages for p in t["pages"])
        else:
            ok = refused

        if ok:
            passed += 1
        print("PASS" if ok else "FAIL", "|", t["question"])
        print("   expected pages:", t["pages"] or "none (should refuse)",
              "| found:", found_pages)
        print("   answer:", answer[:150].replace("\n", " "))
        print()

    print(f"SCORE: {passed}/{len(TESTS)}")


if __name__ == "__main__":
    run()