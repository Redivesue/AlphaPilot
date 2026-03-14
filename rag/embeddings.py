"""
Embedding function for factor vector search.
"""

from core.config import EMBEDDING_MODEL


def get_embedding_function(model_name: str = None):
    """Lazy load sentence-transformers for local embeddings."""
    model_name = model_name or EMBEDDING_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)

        def embed(texts):
            if isinstance(texts, str):
                texts = [texts]
            embs = model.encode(texts)
            return [e.tolist() for e in embs]

        return embed
    except Exception as e:
        raise RuntimeError(
            f"Failed to load sentence-transformers: {e}. Install: pip install sentence-transformers"
        ) from e
