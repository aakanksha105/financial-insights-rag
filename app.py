import logging
from pathlib import Path
from urllib.parse import urlparse
import streamlit as st
from financial_rag.config import AppError, Settings
from financial_rag.ingestion import parse_document, chunk_documents
from financial_rag.embeddings import CachedEmbeddings, openai_embeddings
from financial_rag.retrieval import Retriever
from financial_rag.generation import RAGService
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
st.set_page_config(page_title="LedgerLens | Financial Research", page_icon="📊", layout="wide")
st.markdown("""<style>.stApp{background:#f7f9fc}h1,h2,h3{color:#17324d}.stChatMessage{border:1px solid #e1e7ef;border-radius:12px} .block-container{padding-top:2rem}</style>""", unsafe_allow_html=True)
st.title("LedgerLens")
st.caption("FINANCIAL INSIGHTS RAG ASSISTANT · Source-first document research")
st.info("Upload filings, annual reports, or saved news. Ask about reported figures and trends. Answers use uploaded evidence only; this is not live market data or investment advice.")
ss = st.session_state
if "messages" not in ss:
    ss.messages = []

def render_answer(payload):
    answer, evidence = payload
    if answer.insufficient_evidence:
        st.warning("Insufficient source evidence")
    for claim in answer.claims:
        st.markdown(claim.text.replace("$", r"\$"))
        source_map = {e["id"]: e["metadata"] for e in evidence}
        labels = []
        for cid in claim.citation_ids:
            metadata = source_map[cid]
            labels.append(
                f"{metadata['filename']} · page {metadata['page']}"
            )
        st.caption("Sources: " + "; ".join(dict.fromkeys(labels)))
    st.markdown("**Model explanation / uncertainty**")
    st.markdown(answer.explanation.replace("$", r"\$"))
    with st.expander("Retrieved evidence and source documents"):
        for e in evidence:
            m=e["metadata"]
            st.markdown(f"**{m['filename']} · page/section {m['page']}**")
            st.caption(e["id"])
            st.write(e["text"])
            url=m.get("source_url", "")
            if urlparse(url).scheme in {"https", "http"}:
                st.link_button("Open original source", url)
            data=ss.get("originals",{}).get(m["document_id"])
            if data:
                st.download_button("Download cited document", data, m["filename"], key=f"{ss.get('render_id',0)}-{e['id']}")

with st.sidebar:
    st.header("Research workspace")
    uploads=st.file_uploader("Documents (up to 12; 10 MiB each)", type=["pdf","txt","md","html","htm","csv"], accept_multiple_files=True)
    url=st.text_input("Original source URL (optional; applied to uploads)")
    sample=st.checkbox("Include fictional sample corpus", value=True)
    st.caption("Files and selected text are sent to OpenAI when indexed/queried. Use only documents you are allowed to process. Session data is temporary.")
    if st.button("Build / replace research index", type="primary"):
        try:
            with st.spinner("Parsing and embedding documents…"):
                files=[(u.name,u.getvalue(),url) for u in uploads]
                if sample:
                    files += [(p.name,p.read_bytes(),"") for p in sorted(Path("data/sample").glob("*.txt"))]
                if len(files)>Settings().max_files:
                    raise AppError("Choose at most 12 documents.")
                docs=[]; originals={}
                for name,data,source in files:
                    parsed=parse_document(name,data,source)
                    docs.extend(parsed); originals[parsed[0].metadata["document_id"]]=data
                chunks=chunk_documents(docs)
                if "embeddings" not in ss:
                    ss.embeddings=CachedEmbeddings(openai_embeddings())
                retriever=Retriever(chunks,ss.embeddings)
                ss.service=RAGService(retriever)
                ss.originals=originals
                ss.messages=[]
                st.success(f"Indexed {len(chunks)} chunks from {len(originals)} documents.")
        except AppError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Setup failed. Check OPENAI_API_KEY in your environment.")
    if st.button("Clear conversation"):
        ss.messages=[]
    if st.button("Delete workspace"):
        for key in ["service","embeddings","originals","messages"]:
            ss.pop(key,None)
        ss.messages=[]
        st.rerun()
    st.caption("Try: What was Northstar's 2024 revenue? → How did that compare with 2023?")

for i,msg in enumerate(ss.messages):
    with st.chat_message(msg["role"]):
        if msg["role"]=="assistant":
            ss.render_id=i
            render_answer(msg["payload"])
        else:
            st.write(msg["content"])
question=st.chat_input("Ask a financial research question", disabled="service" not in ss)
if question:
    with st.chat_message("user"):
        st.write(question)
    try:
        with st.spinner("Retrieving evidence and checking citations…"):
            payload=ss.service.ask(question,[{"role":m["role"],"content":m["content"]} for m in ss.messages])
        ss.messages.append({"role":"user","content":question})
        answer,evidence=payload
        content=" ".join(c.text for c in answer.claims)+" "+answer.explanation
        ss.messages.append({"role":"assistant","content":content,"payload":payload})
        # Bound stored conversation as well as prompt history.
        ss.messages=ss.messages[-20:]
        st.rerun()
    except AppError as exc:
        st.error(str(exc))
