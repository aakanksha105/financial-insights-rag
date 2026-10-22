from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest
from financial_rag.generation import Answer, Claim
from financial_rag.ingestion import parse_document, chunk_documents
from pathlib import Path
from tests.fakes import KeywordEmbeddings


def test_streamlit_index_chat_and_delete():
    source=Path('data/sample/northstar_2024.txt')
    cid=chunk_documents(parse_document(source.name,source.read_bytes()))[0].metadata['chunk_id']
    chat=MagicMock()
    chat.with_structured_output.return_value.invoke.return_value=Answer(
        insufficient_evidence=False,
        claims=[Claim(text='Fictional Northstar reported USD 120 million revenue in 2024.',citation_ids=[cid])],
        explanation='This is a fictional fixture.')
    with patch('financial_rag.embeddings.openai_embeddings',return_value=KeywordEmbeddings()), patch('financial_rag.generation.ChatOpenAI',return_value=chat):
        app=AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py').run()
        assert not app.exception
        assert app.chat_input[0].disabled
        app.button[0].click().run()
        assert not app.exception
        assert not app.chat_input[0].disabled
        app.chat_input[0].set_value('Northstar revenue in 2024?').run()
        assert not app.exception
        assert len(app.chat_message)==2
        assert any('120 million' in x.value for x in app.markdown)
        app.button[2].click().run()
        assert not app.exception
        assert app.chat_input[0].disabled
