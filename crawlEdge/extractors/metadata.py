from typing import Dict

from bs4 import BeautifulSoup


def extract_meta_content(soup: BeautifulSoup, **attrs) -> str:
    tag = soup.find("meta", attrs=attrs)
    return tag.get("content", "").strip() if tag and tag.get("content") else ""


PUBLIC_META_KEYS = {
    "title",
    "description",
    "keywords",
    "author",
    "robots",
    "viewport",
    "og:title",
    "og:description",
    "og:type",
    "og:url",
    "og:image",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "article:published_time",
    "article:modified_time",
    "product:brand",
    "product:price:amount",
    "product:price:currency",
}


def extract_meta_tags(soup: BeautifulSoup, public_only: bool = True) -> Dict[str, str]:
    tags = {}
    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property") or tag.get("itemprop")
        value = tag.get("content")
        if key and value:
            key = key.strip()
            if public_only and key not in PUBLIC_META_KEYS:
                continue
            tags[key] = value.strip()
    return tags


def extract_metadata(soup: BeautifulSoup) -> Dict[str, object]:
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = extract_meta_content(soup, name="description")
    return {
        "title": title,
        "description": meta_desc,
        "meta_description": meta_desc,
        "og_title": extract_meta_content(soup, property="og:title") or title,
        "og_description": extract_meta_content(soup, property="og:description") or meta_desc,
        "language": soup.html.get("lang") if soup.html else None,
    }
