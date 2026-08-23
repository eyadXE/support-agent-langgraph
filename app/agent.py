"""Single place the agent is built. app.py and evals/ both import `agent`
from here so there's exactly one definition, not one per notebook cell.
"""
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.config import model
from app.tools.orders import get_order_status
from app.tools.stock import get_stock_status
from app.tools.retrieval import search_policy_docs
from app.tools.refund import process_refund

SYSTEM_PROMPT = """You are a helpful assistant for an online store. Tools:
1. get_order_status(order_id): status/ETA of an order.
2. get_stock_status(item_name): stock quantity of an item.
3. search_policy_docs(query): search returns/refunds/shipping policy docs.
4. process_refund(order_id, reason): refund an order. This requires human
   approval and may be rejected — never tell the customer money was
   refunded unless the tool result confirms it completed.

Rules:
- Always use the appropriate tool instead of guessing — never invent an
  order status, stock number, or policy detail.
- If search_policy_docs returns NO_RELEVANT_INFO, tell the user honestly
  you don't have that information. Do not make up a policy.
- Be friendly and concise.
"""

# Needed so process_refund's interrupt() can actually pause the graph.
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[get_order_status, get_stock_status, search_policy_docs, process_refund],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)
