"""Builds an in-memory vector store over HELP_DOCS, once, on import.

Kept separate from the retrieval tool so embedding only happens once per
process (agent.py / app.py / evals import `vectorstore` and it's cached
at module load, not rebuilt per request).
"""
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings  # free, runs locally, no API key

from app.data.data import HELP_DOCS

# Small, fast, well-tested sentence-embedding model. Downloads once (~80MB)
# from Hugging Face on first run and is cached locally after that.
_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

_docs = [Document(page_content=text) for text in HELP_DOCS]

vectorstore = InMemoryVectorStore.from_documents(_docs, _embeddings)


def search_docs(query: str, k: int = 2):
    """Return the top-k most relevant help-doc chunks for a query."""
    return vectorstore.similarity_search(query, k=k)
