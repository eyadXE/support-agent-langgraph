"""Refund tool. Moves money, so it must pause for human approval before
actually running. Uses LangGraph's interrupt() so the graph halts, a human
reviews the tool call, and execution resumes with their decision.

NOTE: the exact approval wiring (interrupt_before / interrupt() + Command,
tool-call-review middleware, etc.) depends on which langchain/langgraph
version create_agent gives you — check the installed version's docs for the
current "human-in-the-loop" API. The tool itself just needs to call
interrupt() before doing anything irreversible, as below.
"""
from langgraph.types import interrupt
from langchain.tools import tool
from app.data.data import ORDERS


@tool
def process_refund(order_id: str, reason: str = "") -> str:
    """Refund the customer for an order. This moves real money, so it will
    pause and require human approval before it actually executes.
    """
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)
    if order is None:
        return f"Cannot refund: no order found with ID '{order_id}'."

    decision = interrupt(
        {
            "action": "process_refund",
            "order_id": order_id,
            "item": order["item"],
            "reason": reason,
            "message": f"Approve refund for order {order_id} ({order['item']})?",
        }
    )

    approved = bool(decision.get("approved")) if isinstance(decision, dict) else bool(decision)

    if approved:
        # ... actual refund/payment API call would go here ...
        return f"Refund approved and processed for order {order_id}."
    else:
        return (
            f"Refund for order {order_id} was NOT approved. "
            "Do not tell the customer the money was refunded — offer to "
            "escalate to a human agent or suggest an alternative instead."
        )
