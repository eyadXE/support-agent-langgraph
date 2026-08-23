"""Stock lookup tool — mock version (Step 1-3). Replaced with a live API
call in Step 4/5 (see stock_live.py once that step is built)."""
from langchain.tools import tool
from app.data.data import STOCKS
from app.data.api_data import clean_data

@tool
def get_stock_status(item_name: str) -> str:
    """Check how many units of an item are currently in stock.

    Use this whenever the user asks if something is in stock or how many
    are available. Always call this instead of guessing quantities.
    """
    data = clean_data(item_name)
    if not data:
        return f"No stock information found for '{item_name}'. Please double-check the item name."
    stock_info = data[0]  # Assuming we take the first matching product
    return (
        f"Item '{stock_info['title']}': "
        f"Description: '{stock_info['description']}', "
        f"Price: ${stock_info['price']}, "
        f"Stock: {stock_info['stock']} units available.",
        f"there is another {len(data) - 1} item(s) that match your query. Please specify if you want information on a different item."
    ) 

if __name__ == "__main__":
    print(get_stock_status.invoke({"item_name": "laptop"}))