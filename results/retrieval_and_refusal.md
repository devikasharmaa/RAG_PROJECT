# Retrieval and refusal test

Output of `python src/evaluate.py`. 5 questions are answered in the notes: the system must answer, and the expected page must be among the pages it retrieved. 8 questions are not answered in the notes: the system must say it doesn't know.

| Setting | Value |
|---|---|
| Run on | 2026-10-29 02:25 |
| Document | Full Stack Development, Unit 2 notes (CSS) |
| Chunks in the index | 25 |
| Answer model (Ollama) | llama3.1:8b |
| Embedding model | all-MiniLM-L6-v2 |
| Re-ranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Safety threshold (refuse below this score) | 0.4 |
| Passages retrieved before re-ranking | 20 |

## Score: 12/13

| # | Question | Expected | Outcome | Pages retrieved | Top score | Result |
|---|---|---|---|---|---|---|
| 1 | What is CSS? | page 3 | answered | 3, 4, 4, 39 | 0.76 | PASS |
| 2 | What are the benefits of CSS? | pages 4, 5 | answered | 4, 4, 5, 4 | 0.71 | PASS |
| 3 | What happens when selectors have different specificity? | page 17 | answered | 10, 17, 12, 16 | 0.72 | PASS |
| 4 | What are CSS gradients? | pages 22, 23, 24, 25, 26 | answered | 22, 2, 3, 39 | 0.83 | PASS |
| 5 | How do you add inline CSS to an HTML element? | page 7 | answered | 7, 9, 6, 3 | 0.59 | PASS |
| 6 | Who won the cricket World Cup in 2011? | refusal | refused by the safety check | 1, 16, 9, 14 | 0.17 | PASS |
| 7 | How do I install Python on Windows? | refusal | refused by the safety check | 3, 4, 4, 4 | 0.02 | PASS |
| 8 | What is the CSS box model? | refusal | answered | 2, 3, 4, 4 | 0.60 | FAIL |
| 9 | What is cascading effect? | refusal | refused by the safety check | 4, 3, 7, 22 | 0.36 | PASS |
| 10 | What is the difference between relative and absolute positioning in CSS? | refusal | refused by the model | 52, 5, 4, 22 | 0.72 | PASS |
| 11 | What is the difference between inline, block, and inline-block elements in CSS? | refusal | refused by the model | 7, 4, 3, 5 | 0.47 | PASS |
| 12 | What is the difference between a class and an ID in CSS? | refusal | refused by the model | 4, 3, 6, 5 | 0.56 | PASS |
| 13 | What is the difference between a pseudo-class and a pseudo-element in CSS? | refusal | refused by the model | 6, 4, 10, 3 | 0.51 | PASS |

Top score is the highest similarity (0 to 1) between the question and a retrieved passage. Below 0.4, the system refuses without calling the model.

## Answers

### 1. What is CSS?

**PASS**, answered. Expected: page 3. Pages retrieved: 3, 4, 4, 39.

> CSS (Cascading Style Sheets) is the language we use to style an HTML document. [1]

### 2. What are the benefits of CSS?

**PASS**, answered. Expected: pages 4, 5. Pages retrieved: 4, 4, 5, 4.

> The benefits of CSS include:
> • Separation of Content and Presentation [1]
> • Consistency Across Pages [2]
> • Improved Page Load Times [2]
> • Enhanced User Experience [2]
> • Greater Design Flexibility [3]
> • Accessibility [3]

### 3. What happens when selectors have different specificity?

**PASS**, answered. Expected: page 17. Pages retrieved: 10, 17, 12, 16.

> When there are two or more CSS rules that point to the same element, the selector with the highest specificity will "win", and its style declaration will be applied to that HTML element. [1]

### 4. What are CSS gradients?

**PASS**, answered. Expected: pages 22, 23, 24, 25, 26. Pages retrieved: 22, 2, 3, 39.

> CSS gradients let you display smooth transitions between two or more specified colors. [1]

### 5. How do you add inline CSS to an HTML element?

**PASS**, answered. Expected: page 7. Pages retrieved: 7, 9, 6, 3.

> To use inline styles, add the style attribute to the relevant element. [1]

### 6. Who won the cricket World Cup in 2011?

**PASS**, refused by the safety check. Expected: refusal. Pages retrieved: 1, 16, 9, 14.

> I don't know. The document does not cover this.

### 7. How do I install Python on Windows?

**PASS**, refused by the safety check. Expected: refusal. Pages retrieved: 3, 4, 4, 4.

> I don't know. The document does not cover this.

### 8. What is the CSS box model?

**FAIL**, answered. Expected: refusal. Pages retrieved: 2, 3, 4, 4.

> The box model is mentioned as one of the topics in the syllabus for UNIT – II, which is about Introduction to CSS. [1]
>
> The box model is not explicitly defined in the provided context passages, but it is listed as one of the topics to be covered in the course.

### 9. What is cascading effect?

**PASS**, refused by the safety check. Expected: refusal. Pages retrieved: 4, 3, 7, 22.

> I don't know. The document does not cover this.

### 10. What is the difference between relative and absolute positioning in CSS?

**PASS**, refused by the model. Expected: refusal. Pages retrieved: 52, 5, 4, 22.

> I don't know. The document does not cover this.

### 11. What is the difference between inline, block, and inline-block elements in CSS?

**PASS**, refused by the model. Expected: refusal. Pages retrieved: 7, 4, 3, 5.

> I don't know. The document does not cover this.

### 12. What is the difference between a class and an ID in CSS?

**PASS**, refused by the model. Expected: refusal. Pages retrieved: 4, 3, 6, 5.

> I don't know. The document does not cover this.

### 13. What is the difference between a pseudo-class and a pseudo-element in CSS?

**PASS**, refused by the model. Expected: refusal. Pages retrieved: 6, 4, 10, 3.

> I don't know. The document does not cover this.

