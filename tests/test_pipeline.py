from pathlib import Path
from unittest.mock import MagicMock
import pytest
from financial_rag.ingestion import parse_document, chunk_documents
from financial_rag.config import AppError, Settings
from financial_rag.retrieval import Retriever
from financial_rag.embeddings import CachedEmbeddings
from financial_rag.generation import RAGService, Answer, Claim, tokens, history_context
from tests.fakes import KeywordEmbeddings

def docs():
    return chunk_documents(parse_document("northstar.txt",b"Northstar revenue USD 120 million."))
@pytest.mark.parametrize("name,data,expected",[("a.txt",b"hello", "hello"),("a.md",b"# Revenue", "Revenue"),("a.html",b"<script>bad()</script><p>Revenue 10</p>","Revenue 10"),("a.csv",b"year,revenue\n2024,10", "2024 | 10")])
def test_parsers(name,data,expected):
    d=parse_document(name,data)[0]
    assert expected in d.page_content
    assert d.metadata["page"]==1
    assert "bad()" not in d.page_content
@pytest.mark.parametrize("name,data",[("a.docx",b"x"),("a.pdf",b"bad"),("a.txt",b""),("a.txt",b"\xff")])
def test_bad_files(name,data):
    with pytest.raises(AppError): parse_document(name,data)
def test_pdf():
    from reportlab.pdfgen.canvas import Canvas
    from io import BytesIO
    b=BytesIO();c=Canvas(b);c.drawString(20,700,"Revenue USD 120 million");c.showPage();c.save()
    assert "120" in parse_document("report.pdf",b.getvalue())[0].page_content

def test_chunks_stable_deduplicated_and_bounded():
    d=parse_document("x.txt",("Revenue growth. "*300).encode())
    cfg=Settings(chunk_tokens=60,overlap_tokens=10)
    a=chunk_documents(d+d,cfg);b=chunk_documents(d,cfg)
    assert [x.metadata["chunk_id"] for x in a]==[x.metadata["chunk_id"] for x in b]
    assert all(tokens(x.page_content)<=60 for x in a)
    assert len(a)>1

def test_retrieval_and_cache():
    fake=MagicMock(wraps=KeywordEmbeddings());e=CachedEmbeddings(fake)
    a=docs();b=chunk_documents(parse_document("harbor.txt",b"Harbor income EUR 8 million."))
    r=Retriever(a+b,e);r2=Retriever(a+b,e)
    assert fake.embed_documents.call_count==1
    found=r.search("Northstar revenue",1)
    assert found[0][0].metadata["filename"]=="northstar.txt"
    r.search("Northstar revenue",1)
    assert fake.embed_query.call_count==1

def test_provider_failure():
    fake=MagicMock();fake.embed_documents.side_effect=RuntimeError("secret provider details")
    with pytest.raises(AppError,match="Embedding/index"): Retriever(docs(),fake)

def test_citations_and_followup():
    r=Retriever(docs(),KeywordEmbeddings());chat=MagicMock()
    cid=docs()[0].metadata["chunk_id"]
    chat.with_structured_output.return_value.invoke.return_value=Answer(insufficient_evidence=False,claims=[Claim(text="Revenue was 120 million.",citation_ids=[cid])],explanation="Reported value.")
    service=RAGService(r,chat=chat)
    answer,evidence=service.ask("Revenue?",[])
    assert answer.claims[0].citation_ids[0]==evidence[0]["id"]
    chat.invoke.return_value.content="Northstar revenue in 2024"
    service.ask("What about 2024?",[{"role":"user","content":"Northstar?"}])
    assert chat.invoke.call_count==1
    chat.with_structured_output.return_value.invoke.return_value.claims[0].citation_ids=["invented"]
    with pytest.raises(AppError,match="source references"): service.ask("Revenue?",[])

def test_abstention_and_model_failure():
    chat=MagicMock();chat.with_structured_output.return_value.invoke.return_value=Answer(insufficient_evidence=True,claims=[],explanation="No forecast supplied.")
    s=RAGService(Retriever(docs(),KeywordEmbeddings()),chat=chat)
    assert s.ask("2028 forecast?",[])[0].insufficient_evidence
    chat.with_structured_output.return_value.invoke.side_effect=TimeoutError()
    with pytest.raises(AppError,match="Model request failed"): s.ask("Revenue?",[])

def test_budgets_and_empty_index():
    with pytest.raises(AppError): Retriever([],KeywordEmbeddings())
    s=RAGService(Retriever(docs(),KeywordEmbeddings()),chat=MagicMock())
    with pytest.raises(AppError): s.ask("word "*1000,[])
    assert tokens(history_context([{"role":"user","content":"word "*100}],10))<=10
