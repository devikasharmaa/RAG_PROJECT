from chunker import chunk_pages

LONG = "Selectors choose which HTML elements a CSS rule applies to. " * 30


def test_long_page_is_split_within_chunk_size():
    chunks = chunk_pages([{"page": 1, "text": LONG}], chunk_size=500)
    assert len(chunks) > 1
    assert all(len(c["text"]) <= 500 for c in chunks)


def test_every_chunk_keeps_its_page_number():
    pages = [{"page": 4, "text": LONG}, {"page": 9, "text": LONG}]
    chunks = chunk_pages(pages)
    assert {c["page"] for c in chunks} == {4, 9}
    # chunks from page 4 come before chunks from page 9
    page_order = [c["page"] for c in chunks]
    assert page_order == sorted(page_order)


def test_title_only_chunks_are_dropped():
    pages = [{"page": 1, "text": "Unit 2: CSS"},  # a slide title, < 60 chars
             {"page": 2, "text": LONG}]
    chunks = chunk_pages(pages)
    assert all(c["page"] == 2 for c in chunks)


def test_min_length_boundary():
    exactly_60 = "x" * 60
    assert len(chunk_pages([{"page": 1, "text": exactly_60}])) == 1
    assert chunk_pages([{"page": 1, "text": "x" * 59}]) == []


def test_chunk_ids_are_sequential():
    chunks = chunk_pages([{"page": 1, "text": LONG}, {"page": 2, "text": LONG}])
    assert [c["chunk_id"] for c in chunks] == list(range(len(chunks)))


def test_overlap_repeats_text_between_neighbouring_chunks():
    words = " ".join(f"w{i}" for i in range(400))
    chunks = chunk_pages([{"page": 1, "text": words}], chunk_size=200, chunk_overlap=50)
    first_tail = chunks[0]["text"].split()[-1]
    assert first_tail in chunks[1]["text"]


def test_no_pages_gives_no_chunks():
    assert chunk_pages([]) == []
