"""Order lookup tool."""
from langchain.tools import tool
from app.data.data import ORDERS 


@tool
def get_order_status(order_id: str) -> str:
    """Look up the order status, ETA, and item for a given order ID.

    Use this whenever the user asks about an order (status, ETA, what was
    ordered). Always call this instead of guessing an order's status.
    """
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)
    if order is None:
        return f"No order found with ID '{order_id}'. Please double-check the order ID."
    return (
        f"Order {order_id}: status='{order['status']}', "
        f"eta='{order['eta']}', item='{order['item']}'."
    )
