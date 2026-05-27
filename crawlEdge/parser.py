from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from trafilatura import extract
from trafilatura.settings import DEFAULT_CONFIG

from crawlEdge.classifier import detect_page_type
from crawlEdge.extractors.metadata import extract_metadata
from crawlEdge.extractors.registry import extract_entities_for_page
from crawlEdge.extractors.structured_data import extract_json_ld, extract_structured_data
from crawlEdge.extractors.topics import extract_topics
from crawlEdge.schemas import build_result


def is_probably_blocked_or_empty(soup: BeautifulSoup, clean_text: str) -> bool:
    title = soup.title.string.strip().lower() if soup.title and soup.title.string else ""
    page_text = soup.get_text(" ", strip=True).lower()
    block_markers = [
        "access denied",
        "enable javascript",
        "unusual traffic",
        "captcha",
        "verify you are human",
    ]
    has_block_marker = any(marker in f"{title} {page_text}" for marker in block_markers)
    has_useful_markup = bool(title or soup.find("h1") or extract_json_ld(str(soup)))
    return len(clean_text.split()) < 20 and (has_block_marker or not has_useful_markup)


def build_seo_signals(
    soup: BeautifulSoup,
    clean_text: str,
    structured_data: Dict[str, Any],
    final_url: str,
    redirect_chain: Optional[list],
) -> Dict[str, Any]:
    canonical = soup.find("link", rel="canonical")
    canonical_href = canonical.get("href") if canonical and canonical.get("href") else None
    chain = redirect_chain or [final_url]
    return {
        "word_count": len(clean_text.split()) if clean_text else 0,
        "has_schema_markup": len(structured_data.get("json-ld", [])) > 0,
        "h1_count": len(soup.find_all("h1")),
        "canonical": canonical_href,
        "redirect_chain": chain,
        "redirect_count": max(len(chain) - 1, 0),
    }


def parse_html(
    html: str,
    final_url: str,
    status_code: int = 200,
    redirect_chain: Optional[list] = None,
) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    clean_text = extract(html, url=final_url, config=DEFAULT_CONFIG) or ""
    metadata = extract_metadata(soup)
    structured_data = extract_structured_data(html, final_url)
    page_type = detect_page_type(soup, final_url, structured_data)
    title = str(metadata.get("title") or "")

    entities = extract_entities_for_page(
        page_type=page_type,
        structured_data=structured_data,
        soup=soup,
        body_text=clean_text,
        title=title,
        final_url=final_url,
    )

    error = None
    if is_probably_blocked_or_empty(soup, clean_text):
        error = "Fetched page appears to be an empty, JavaScript-only, or bot-protection response"

    return build_result(
        url=final_url,
        status_code=status_code,
        page_type=page_type,
        metadata=metadata,
        structured_data=structured_data,
        body_text=clean_text[:12000] if clean_text else None,
        topics=extract_topics(clean_text or title, title),
        extracted_entities=entities,
        seo_signals=build_seo_signals(soup, clean_text, structured_data, final_url, redirect_chain),
        error=error,
    )
