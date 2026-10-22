from langchain_openai import OpenAIEmbeddings
from .config import Settings

def openai_embeddings(settings: Settings = Settings()):
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        chunk_size=8,
        max_retries=6,
        request_timeout=60,
    )


class CachedEmbeddings:
    """Session-local cache; never shares private uploaded text between users."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.cache = {}
    def embed_documents(self, texts):
        missing = list(dict.fromkeys(t for t in texts if t not in self.cache))
        if missing:
            vectors = self.delegate.embed_documents(missing)
            if len(vectors) != len(missing):
                raise ValueError("embedding response length mismatch")
            self.cache.update(zip(missing, vectors))
        return [self.cache[t] for t in texts]
    def embed_query(self, text):
        if text not in self.cache:
            self.cache[text] = self.delegate.embed_query(text)
        return self.cache[text]
