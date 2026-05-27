from typing import Any, Dict

from bs4 import BeautifulSoup

from crawlEdge.extractors.article import extract_article_entities
from crawlEdge.extractors.product import (
    add_product_to_normalized_structured_data,
    extract_product_entities,
)


def extract_entities_for_page(
    page_type: str,
    structured_data: Dict[str, Any],
    soup: BeautifulSoup,
    body_text: str,
    title: str,
    final_url: str,
) -> Dict[str, Any]:
    if page_type == "product":
        entities = extract_product_entities(structured_data, soup, body_text, title, final_url)
        add_product_to_normalized_structured_data(structured_data, entities)
        return entities

    if page_type in ["article", "blog"]:
        return extract_article_entities(structured_data, soup)

    return {}
