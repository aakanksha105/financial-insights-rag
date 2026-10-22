import logging
import faiss
import numpy as np
from .config import AppError
logger = logging.getLogger(__name__)
class Retriever:
    """Normalized exact inner-product search equals cosine similarity. No pickle loading."""
    def __init__(self, documents, embeddings):
        if not documents:
            raise AppError("Upload at least one readable document.")
        self.documents = documents
        self.embeddings = embeddings
        try:
            vectors = np.asarray(embeddings.embed_documents([d.page_content for d in documents]), dtype="float32")
            if vectors.ndim != 2 or len(vectors) != len(documents) or not np.isfinite(vectors).all():
                raise ValueError("invalid vectors")
            faiss.normalize_L2(vectors)
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(vectors)
        except Exception as exc:
            logger.warning("Index creation failed: %s", type(exc).__name__)
            raise AppError("Embedding/index creation failed. Check API access and retry.") from exc
    def search(self, question, k=5):
        try:
            query = np.asarray([self.embeddings.embed_query(question)], dtype="float32")
            if query.shape[1] != self.index.d or not np.isfinite(query).all():
                raise ValueError("invalid query")
            faiss.normalize_L2(query)
            scores, ids = self.index.search(query, min(k, len(self.documents)))
            return [(self.documents[int(i)], float(s)) for i,s in zip(ids[0],scores[0]) if i >= 0]
        except Exception as exc:
            logger.warning("Retrieval failed: %s", type(exc).__name__)
            raise AppError("Retrieval failed. Please retry.") from exc
