"""Document-level Recall@K and MRR; offline results validate plumbing only."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from financial_rag.ingestion import parse_document,chunk_documents
from financial_rag.embeddings import CachedEmbeddings,openai_embeddings
from financial_rag.retrieval import Retriever
from financial_rag.generation import RAGService
from tests.fakes import KeywordEmbeddings
ROOT=Path(__file__).resolve().parents[1]
def metrics(ranked, relevant):
    unique=list(dict.fromkeys(ranked))
    recall=len(set(unique)&set(relevant))/len(set(relevant))
    rr=next((1/(i+1) for i,f in enumerate(unique) if f in relevant),0)
    return recall,rr

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["offline","openai"],default="offline");p.add_argument("--k",type=int,default=3);p.add_argument("--answers",action="store_true");p.add_argument("--output",default="reports/evaluation.json");a=p.parse_args()
    if a.k<1: p.error("k must be positive")
    if a.answers and a.mode!="openai": p.error("--answers requires --mode openai")
    documents=[]
    for f in sorted((ROOT/"data/sample").glob("*.txt")):
        documents.extend(parse_document(f.name,f.read_bytes()))
    r=Retriever(chunk_documents(documents),CachedEmbeddings(openai_embeddings()) if a.mode=="openai" else KeywordEmbeddings())
    rows=[]
    for q in json.loads((ROOT/"data/evaluation/questions.json").read_text()):
        ranked=[d.metadata["filename"] for d,_ in r.search(q["question"],a.k)]
        recall,rr=metrics(ranked,q["relevant_files"])
        row={**q,"retrieved_files":ranked,"recall_at_k":recall,"reciprocal_rank":rr}
        if a.answers:
            answer,evidence=RAGService(r).ask(q["question"],[])
            row.update(answer=answer.model_dump(),evidence=evidence,human_review=None)
        rows.append(row)
    report={"mode":a.mode,"k":a.k,"retrieval_unit":"unique document ranked by first retrieved chunk; cutoff applied to chunks", "warning":(
    "Tiny fictional fixture; keyword embeddings validate pipeline behavior, "
    "not OpenAI semantic retrieval or answer grounding."
    if a.mode == "offline" else
    "Tiny fictional fixture using OpenAI embeddings; retrieval metrics "
    "do not establish answer grounding or real-world accuracy."
),"recall_at_k":sum(x["recall_at_k"] for x in rows)/len(rows),"mrr":sum(x["reciprocal_rank"] for x in rows)/len(rows),"rows":rows}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
if __name__=="__main__": main()
