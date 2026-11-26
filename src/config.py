"""Paths and limits in one place. Each can be changed with an environment variable."""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Anchored to the project folder, so the app works from any working directory
DATA_DIR = os.getenv("RAG_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
INDEX_DIR = os.path.join(DATA_DIR, "index")
DEFAULT_PDF = os.path.join(DOCUMENTS_DIR, "sample1.pdf")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

MAX_UPLOAD_MB = int(os.getenv("RAG_MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
