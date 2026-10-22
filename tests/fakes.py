import re
import numpy as np
class KeywordEmbeddings:
    """Test double, deliberately not semantic or suitable for real research."""
    vocab = ["northstar","harbor","revenue","income","canada","forecast","distribution"]
    def embed_query(self,text):
        words=re.findall(r"[a-z]+",text.lower())
        return [float(words.count(w)) for w in self.vocab]
    def embed_documents(self,texts):
        return [self.embed_query(t) for t in texts]
