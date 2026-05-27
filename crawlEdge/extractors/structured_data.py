from typing import Any, Dict
import json

from bs4 import BeautifulSoup

try:
    import extruct
    from w3lib.html import get_base_url
except Exception:
    extruct = None
    get_base_url = None


def normalize_schema_type(item_type: Any) -> str:
    if isinstance(item_type, list):
        return normalize_schema_type(item_type[0]) if item_type else ""
    return str(item_type or "").lower()


def extract_json_ld(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    json_ld_list = []
    for script in soup.find_all("script", type=["application/ld+json", "application/json-ld"]):
        try:
            content = script.string.strip() if script.string else script.get_text(strip=True)
            if not content:
                continue
            data = json.loads(content)
            if isinstance(data, dict):
                json_ld_list.append(data)
            elif isinstance(data, list):
                json_ld_list.extend(data)
        except (TypeError, json.JSONDecodeError):
            continue
    return json_ld_list


def iter_schema_items(structured_data: Dict[str, Any]):
    for item in structured_data.get("json-ld", []):
        if not isinstance(item, dict):
            continue
        yield item
        graph = item.get("@graph")
        if isinstance(graph, list):
            for graph_item in graph:
                if isinstance(graph_item, dict):
                    yield graph_item


def normalize_structured_data(json_ld: list) -> Dict[str, Any]:
    normalized = {
        "types": [],
        "products": [],
        "articles": [],
        "breadcrumbs": [],
    }
    structured_data = {"json-ld": json_ld}

    for item in iter_schema_items(structured_data):
        item_type = normalize_schema_type(item.get("@type"))
        if item_type:
            normalized["types"].append(item_type)

        if item_type == "product":
            offers = item.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            brand = item.get("brand")
            aggregate_rating = item.get("aggregateRating", {})
            normalized["products"].append({
                "source": "schema",
                "name": item.get("name"),
                "brand": brand.get("name") if isinstance(brand, dict) else brand,
                "sku": item.get("sku"),
                "price": offers.get("price") if isinstance(offers, dict) else None,
                "currency": offers.get("priceCurrency") if isinstance(offers, dict) else None,
                "average_rating": aggregate_rating.get("ratingValue") if isinstance(aggregate_rating, dict) else None,
                "review_count": aggregate_rating.get("reviewCount") if isinstance(aggregate_rating, dict) else None,
            })

        if item_type in ["article", "newsarticle", "blogposting"]:
            author = item.get("author")
            if isinstance(author, list):
                author = author[0] if author else None
            normalized["articles"].append({
                "source": "schema",
                "headline": item.get("headline") or item.get("name"),
                "author": author.get("name") if isinstance(author, dict) else author,
                "published_date": item.get("datePublished"),
                "modified_date": item.get("dateModified"),
            })

        if item_type == "breadcrumblist":
            normalized["breadcrumbs"].append(item.get("itemListElement", []))

    normalized["types"] = sorted(set(normalized["types"]))
    return {key: value for key, value in normalized.items() if value}


def extract_structured_data(html: str, url: str) -> Dict[str, Any]:
    raw = {}
    if extruct and get_base_url:
        try:
            base_url = get_base_url(html, url)
            raw = extruct.extract(
                html,
                base_url=base_url,
                syntaxes=["json-ld", "microdata", "opengraph", "rdfa"],
                uniform=True,
            )
        except Exception:
            raw = {}

    if not raw:
        raw = {"json-ld": extract_json_ld(html)}

    json_ld = raw.get("json-ld") or extract_json_ld(html)
    return {
        "json-ld": json_ld,
        "normalized": normalize_structured_data(json_ld),
        "raw_count": {
            key: len(value) if isinstance(value, list) else 1
            for key, value in raw.items()
            if value
        },
    }
