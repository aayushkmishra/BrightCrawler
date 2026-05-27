from typing import Any, Dict, Optional
import re

from bs4 import BeautifulSoup

from crawlEdge.extractors.html_utils import (
    extract_table_like_value,
    first_text,
    parse_decimal,
    parse_int,
)
from crawlEdge.extractors.metadata import extract_meta_content
from crawlEdge.extractors.structured_data import iter_schema_items, normalize_schema_type

try:
    from price_parser import Price
except Exception:
    Price = None


def parse_price_text(price_text: str) -> Dict[str, Any]:
    if not price_text:
        return {}

    if Price:
        parsed = Price.fromstring(price_text)
        if parsed.amount_float is not None:
            return {
                "price": parsed.amount_float,
                "currency": parsed.currency,
                "price_text": clean_price_text(price_text),
            }

    amount = parse_decimal(price_text)
    if amount is None:
        return {}
    currency = "USD" if "$" in price_text else None
    if "INR" in price_text or "\u20b9" in price_text:
        currency = "INR"
    return {
        "price": amount,
        "currency": currency,
        "price_text": clean_price_text(price_text),
    }


def compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value not in [None, "", [], {}]
    }

def clean_price_text(price_text: str) -> str:
    text = re.sub(r"\s+", " ", price_text).strip()
    match = re.search(r"((?:INR|\$|\u20b9|USD|EUR|GBP)\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
    return match.group(1).strip() if match else text[:80]


def extract_candidate_prices(soup: BeautifulSoup, max_prices: int = 8) -> list:
    candidates = []
    seen = set()
    for tag in soup.select(".a-price .a-offscreen, span.a-offscreen"):
        text = tag.get_text(" ", strip=True)
        parsed = parse_price_text(text)
        if not parsed:
            continue
        key = (parsed.get("price"), parsed.get("currency"), parsed.get("price_text"))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "price": parsed.get("price"),
            "currency": parsed.get("currency"),
            "price_text": parsed.get("price_text"),
            "source": "visible_price_candidate",
        })
        if len(candidates) >= max_prices:
            break
    return candidates


def extract_product_specifications(body_text: str) -> Dict[str, str]:
    allowed_labels = {
        "brand": "brand",
        "brand name": "brand",
        "color": "color",
        "material": "material",
        "product dimensions": "product_dimensions",
        "specific uses for product": "specific_uses",
        "wattage": "wattage",
        "slot count": "slot_count",
        "special features": "special_features",
        "voltage": "voltage",
        "number of settings": "number_of_settings",
        "number of programs": "number_of_programs",
        "display type": "display_type",
        "style": "style",
        "finish type": "finish_type",
        "item dimensions d x w x h": "item_dimensions",
        "item weight": "item_weight",
        "model number": "model_number",
        "manufacturer": "manufacturer",
        "part number": "part_number",
        "item type name": "item_type_name",
        "unit count": "unit_count",
        "included components": "included_components",
        "asin": "asin",
        "upc": "upc",
    }
    specs = {}
    for label, value in re.findall(r"\|\s*([^|\n]{2,80}?)\s*\|\s*([^|\n]{1,200}?)\s*\|", body_text):
        label = re.sub(r"\s+", " ", label).strip()
        value = re.sub(r"\s+", " ", value).strip()
        normalized_label = label.lower()
        if not label or not value or set(label) <= {"-"} or set(value) <= {"-"}:
            continue
        if normalized_label not in allowed_labels:
            continue
        specs.setdefault(allowed_labels[normalized_label], value)
    return specs


def extract_price_from_primary_dom(soup: BeautifulSoup) -> Dict[str, Any]:
    price_roots = [
        "#corePriceDisplay_desktop_feature_div",
        "#corePrice_feature_div",
        "#corePrice_desktop",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#price",
    ]
    for selector in price_roots:
        root = soup.select_one(selector)
        if not root:
            continue
        price_texts = [
            tag.get_text(" ", strip=True)
            for tag in root.select(".a-price:not(.a-text-price) .a-offscreen, .priceToPay .a-offscreen")
            if tag.get_text(" ", strip=True)
        ]
        price_texts = list(dict.fromkeys(price_texts))
        if not price_texts:
            continue

        parsed = {}
        for price_text in price_texts:
            parsed = parse_price_text(price_text)
            if parsed:
                break
        if parsed:
            return parsed
    return {}


def extract_schema_product_entities(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    entities = {}
    for item in iter_schema_items(structured_data):
        if normalize_schema_type(item.get("@type")) not in ["product", "offer"]:
            continue

        brand = item.get("brand")
        if isinstance(brand, dict):
            entities["brand"] = brand.get("name")
        elif brand:
            entities["brand"] = brand

        aggregate_rating = item.get("aggregateRating")
        if isinstance(aggregate_rating, dict):
            entities["average_rating"] = aggregate_rating.get("ratingValue")
            entities["review_count"] = aggregate_rating.get("reviewCount")

        offers = item.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            entities["price"] = offers.get("price") or offers.get("lowPrice")
            entities["currency"] = offers.get("priceCurrency")
            entities["availability"] = offers.get("availability")

    return {key: value for key, value in entities.items() if value not in [None, ""]}


def extract_html_product_entities(
    soup: BeautifulSoup,
    body_text: str,
    title: str,
    final_url: str,
) -> Dict[str, Any]:
    product_name = first_text(soup, ["#productTitle", "h1"]) or title
    rating_text = first_text(soup, ["#averageCustomerReviews", "#acrPopover", "[itemprop='ratingValue']"])
    review_text = first_text(soup, ["#acrCustomerReviewText", "[itemprop='reviewCount']"])
    availability = first_text(soup, ["#availability", "#outOfStock", "#merchant-info"])
    asin_match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", final_url, re.IGNORECASE)
    specifications = extract_product_specifications(body_text)
    primary_price = extract_price_from_primary_dom(soup)

    entities = {
        "name": product_name,
        "asin": asin_match.group(1).upper() if asin_match else extract_table_like_value(body_text, ["ASIN"]),
        "brand": extract_table_like_value(body_text, ["Brand", "Brand Name"]) or extract_meta_content(soup, property="product:brand"),
        "manufacturer": extract_table_like_value(body_text, ["Manufacturer"]),
        "model_number": extract_table_like_value(body_text, ["Model Number"]),
        "upc": extract_table_like_value(body_text, ["UPC"]),
        "color": extract_table_like_value(body_text, ["Color"]),
        "material": extract_table_like_value(body_text, ["Material"]),
        "availability": availability,
        "average_rating": parse_decimal(rating_text),
        "review_count": parse_int(review_text),
        "specifications": specifications,
    }
    entities.update(primary_price)

    if "no featured offers available" in body_text.lower():
        entities["offer_status"] = "no_featured_offer"
        if "price" not in entities:
            entities["price_unavailable_reason"] = "No featured offer is available for this product response"

    return compact_dict(entities)


def extract_product_entities(
    structured_data: Dict[str, Any],
    soup: BeautifulSoup,
    body_text: str,
    title: str,
    final_url: str,
) -> Dict[str, Any]:
    entities = extract_schema_product_entities(structured_data)
    html_entities = extract_html_product_entities(soup, body_text, title, final_url)
    for key, value in html_entities.items():
        entities.setdefault(key, value)
    if not entities.get("brand") and title:
        entities["brand"] = title.split()[0].replace("Amazon.com:", "").strip(" :-")
    return compact_dict(entities)


def add_product_to_normalized_structured_data(structured_data: Dict[str, Any], entities: Dict[str, Any]) -> None:
    if not entities:
        return

    normalized = structured_data.setdefault("normalized", {})
    products = normalized.setdefault("products", [])
    if products:
        products[0].update({
            key: value
            for key, value in entities.items()
            if key not in products[0] or not products[0][key]
        })
        products[0].setdefault("source", "schema_or_html")
        return

    products.append(compact_dict({
        "source": "html_fallback",
        "name": entities.get("name"),
        "brand": entities.get("brand"),
        "sku": entities.get("asin") or entities.get("model_number"),
        "price": entities.get("price"),
        "currency": entities.get("currency"),
        "average_rating": entities.get("average_rating"),
        "review_count": entities.get("review_count"),
        "availability": entities.get("availability"),
        "offer_status": entities.get("offer_status"),
        "price_unavailable_reason": entities.get("price_unavailable_reason"),
    }))
