"""Mock data: orders, stock, and help docs used for RAG."""

ORDERS = {
    "A1234": {"status": "shipped", "eta": "Tuesday", "item": "laptop"},
    "B5678": {"status": "processing", "eta": "not shipped", "item": "red mug"},
}

# Mock stock levels. Keys are normalized (lowercase, stripped) at lookup time.
STOCKS = {
    "jackets": 10,
    "hoodies": 5,
    "mugs": 20,
    "t-shirts": 15,
}

HELP_DOCS = [
    "Returns: items can be returned within 30 days of delivery for a full refund, if unworn with tags attached.",
    "Refunds go to the original payment method and take 5-7 business days after we receive the returned item.",
    "Shipping: standard is 3-5 business days; express is 1-2 days ($12).",
]


