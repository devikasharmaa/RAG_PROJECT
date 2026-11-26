from loader import clean_text, load_pdf


def test_removes_private_use_icon_characters():
    # Slide PDFs often contain icon-font glyphs in the U+F000–U+F8FF range
    assert clean_text(" Bullet point") == "Bullet point"
    assert clean_text("ab") == "a b"


def test_collapses_spaces_and_tabs():
    assert clean_text("CSS   is\t\tfun") == "CSS is fun"


def test_keeps_newlines():
    assert clean_text("line one\nline two") == "line one\nline two"


def test_strips_ends():
    assert clean_text("  padded  \n") == "padded"


def test_empty_string():
    assert clean_text("") == ""


def test_load_pdf_keeps_page_numbers_and_skips_blank_pages(tmp_path):
    from conftest import make_pdf
    path = tmp_path / "doc.pdf"
    path.write_bytes(make_pdf(["First page text", "", "Third page text"]))

    pages = load_pdf(str(path))

    assert [p["page"] for p in pages] == [1, 3]
    assert "First page" in pages[0]["text"]
