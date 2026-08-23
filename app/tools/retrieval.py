"""RAG tool over the store's help docs (returns, refunds, shipping, etc.)."""
from langchain.tools import tool
from app.vectorstore import vectorstore
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import os
# Cosine-distance-ish score threshold. Docs closer than this are considered
# genuinely relevant; anything worse means "we don't have that covered" —
# without this, similarity_search always returns *something*, which is how
# the agent ends up fabricating an answer to an uncovered question.
_RELEVANCE_THRESHOLD = float(os.getenv("relevance_threshold", "0.4"))

@tool
def search_policy_docs(query: str) -> str:
    """Search store policy docs (returns, refunds, shipping) for an answer.

    Always use this for any policy question before answering. If it comes
    back with 'NO_RELEVANT_INFO', tell the user honestly that you don't
    have that information — do not invent a policy.
    """
    results = vectorstore.similarity_search_with_score(query, k=2)
    relevant = [doc.page_content for doc, score in results if score >= _RELEVANCE_THRESHOLD]
    if not relevant:
        return "NO_RELEVANT_INFO"
    return "\n".join(relevant)
