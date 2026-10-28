"""
Optional text embeddings (sentence-transformers all-MiniLM-L6-v2, 384 dims).

Imported lazily so the API runs without torch. Install with
`pip install -r requirements-ml.txt` to enable seeding embeddings, PDF
ingestion embeddings and semantic search.
"""
from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"


def available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    return _model().encode(text).tolist()
