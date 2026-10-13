import re


def extract_model_name(product_name: str) -> str:
    """Extract the iPhone model from a product title."""
    match = re.search(r'iPhone\s+\d+([a-zA-Z\s]+)?', product_name, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return "Unknown"
