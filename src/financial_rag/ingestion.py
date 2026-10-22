import csv
import hashlib
import io
import re
from pathlib import Path
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from .config import AppError, Settings

def parse_document(name: str, data: bytes, source_url: str = "") -> list[Document]:
    cfg = Settings()
    if not data or len(data) > cfg.max_file_bytes:
        raise AppError("File is empty or exceeds the 10 MiB limit.")
    suffix = Path(name).suffix.lower()
    doc_id = hashlib.sha256(data).hexdigest()[:20]
    metadata = {"document_id": doc_id, "filename": Path(name).name, "source_url": source_url}
    try:
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ValueError("encrypted")
            pages = [(i+1, p.extract_text() or "") for i,p in enumerate(reader.pages)]
        else:
            text = data.decode("utf-8-sig")
            if suffix in {".html", ".htm"}:
                soup = BeautifulSoup(text, "html.parser")
                for tag in soup(["script", "style", "nav"]):
                    tag.decompose()
                text = soup.get_text(" ", strip=True)
            elif suffix == ".csv":
                text = "\n".join(" | ".join(row) for row in csv.reader(io.StringIO(text)))
            elif suffix not in {".txt", ".md"}:
                raise ValueError("unsupported")
            pages = [(1,text)]
        result = []
        for page,text in pages:
            text = re.sub(r"[ \t]+", " ", text.replace("\x00", "")).strip()
            if text:
                result.append(Document(page_content=text, metadata={**metadata,"page":page}))
        if not result:
            raise ValueError("no text")
        return result
    except Exception as exc:
        raise AppError("Cannot parse file. Use a text PDF (OCR is not supported), UTF-8 text, HTML, Markdown, or CSV.") from exc

def chunk_documents(documents: list[Document], settings: Settings = Settings()) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base", chunk_size=settings.chunk_tokens,
        chunk_overlap=settings.overlap_tokens)
    chunks = splitter.split_documents(documents)
    seen = set()
    result = []
    for doc in chunks:
        key = f"{doc.metadata['document_id']}:{doc.metadata['page']}:{doc.page_content}"
        cid = hashlib.sha256(key.encode()).hexdigest()[:24]
        if cid not in seen:
            seen.add(cid)
            doc.metadata["chunk_id"] = cid
            result.append(doc)
    if len(result) > settings.max_chunks:
        raise AppError("Corpus exceeds 1,500 chunks. Upload fewer or smaller documents.")
    return result
