from langchain_text_splitters import RecursiveCharacterTextSplitter
from loader import load_pdf


def chunk_pages(pages, chunk_size=500, chunk_overlap=50, min_length=60):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    for page in pages:
        for piece in splitter.split_text(page["text"]):
            # Skip title-only chunks (slides where the content is a picture)
            if len(piece) < min_length:
                continue
            chunks.append({
                "chunk_id": len(chunks),
                "page": page["page"],
                "text": piece,
            })

    return chunks


if __name__ == "__main__":
    pages = load_pdf("data/documents/sample1.pdf")
    chunks = chunk_pages(pages)
    print("Total chunks:", len(chunks))
    print("First chunk:", chunks[0])