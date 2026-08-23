import httpx

def search_products(query: str, delay_ms: int = 0):
    resp = httpx.get(
        "https://dummyjson.com/products/search",
        params={"q": query, "delay": delay_ms},
        timeout=5,  # your Step 5 timeout, below 5000ms cap
    )
    resp.raise_for_status()
    data = resp.json()
    return data["products"]  # empty list if no matches — that's your "no such item" case

    
def clean_data(product_NAME: str):
    """Clean the data to only include relevant fields."""
    data =search_products(product_NAME, delay_ms=1000)  # Example usage
    cleaned = []
    for item in data:
        cleaned.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "price": item.get("price"),
                "stock": item.get("stock"),
            }
        )
    return cleaned

# if __name__ == "__main__":
#     # Example usage
#     products = search_products("laptop", delay_ms=1000)
#     cleaned_products = clean_data(products)
#     print(cleaned_products)