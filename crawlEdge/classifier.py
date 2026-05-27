from bs4 import BeautifulSoup

from crawlEdge.extractors.structured_data import iter_schema_items, normalize_schema_type


def detect_page_type(soup: BeautifulSoup, url: str, structured_data: dict) -> str:
    schema_types = [
        normalize_schema_type(item.get("@type"))
        for item in iter_schema_items(structured_data)
        if item.get("@type")
    ]
    url_lower = url.lower()

    if any(item_type in ["product", "offer"] for item_type in schema_types):
        return "product"
    if any(item_type in ["newsarticle", "article", "blogposting"] for item_type in schema_types):
        return "article"
    if any(marker in url_lower for marker in ["/dp/", "/gp/product", "/product"]):
        return "product"
    if any(marker in url_lower for marker in ["blog", "article", "/news/", "/tech/"]):
        return "article"
    if soup.find("article"):
        return "blog"
    if url_lower.endswith("/") and len(url_lower.split("/")) <= 4:
        return "homepage"
    return "other"
