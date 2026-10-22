import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    chat_model: str = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
    chunk_tokens: int = 450
    overlap_tokens: int = 70
    evidence_tokens: int = 5000
    history_tokens: int = 1800
    max_question_tokens: int = 600
    top_k: int = 5
    max_files: int = 12
    max_file_bytes: int = 10 * 1024 * 1024
    max_chunks: int = 1500
class AppError(Exception):
    """Safe error suitable for display; never contains provider details or keys."""
