from typing import Any, Dict

from bs4 import BeautifulSoup

from crawlEdge.extractors.metadata import extract_meta_content
from crawlEdge.extractors.structured_data import iter_schema_items, normalize_schema_type


def extract_article_entities(structured_data: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, Any]:
    entities = {}
    for item in iter_schema_items(structured_data):
        if normalize_schema_type(item.get("@type")) not in ["article", "newsarticle", "blogposting"]:
            continue

        author = item.get("author")
        if isinstance(author, list):
            author = author[0] if author else None
        if isinstance(author, dict):
            entities["author"] = author.get("name")
        elif author:
            entities["author"] = author
        entities["published_date"] = item.get("datePublished") or item.get("dateCreated")
        entities["modified_date"] = item.get("dateModified")

    entities["author"] = entities.get("author") or extract_meta_content(soup, name="author")
    entities["published_date"] = entities.get("published_date") or extract_meta_content(soup, property="article:published_time")

    return {key: value for key, value in entities.items() if value not in [None, ""]}
