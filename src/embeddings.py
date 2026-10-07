import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        # device="cpu" keeps the GPU memory free for the Ollama model
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


def embed_texts(texts):
    vectors = get_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vectors.astype("float32")


if __name__ == "__main__":
    vectors = embed_texts([
        "What is the CSS box model?",
        "Every HTML element is a box with margin, border, padding and content.",
        "My favourite fruit is mango.",
    ])
    print("Shape:", vectors.shape)
    print("Question vs CSS sentence:", round(float(vectors[0] @ vectors[1]), 3))
    print("Question vs mango sentence:", round(float(vectors[0] @ vectors[2]), 3))