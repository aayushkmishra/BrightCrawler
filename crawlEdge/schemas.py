from datetime import datetime
from typing import Any, Dict, Optional


EMPTY_METADATA = {
    "title": "",
    "meta_description": "",
    "og_title": "",
    "og_description": "",
    "language": None,
}

EMPTY_SEO_SIGNALS = {
    "word_count": 0,
    "has_schema_markup": False,
    "h1_count": 0,
    "canonical": None,
    "redirect_chain": [],
    "redirect_count": 0,
}


def build_result(
    url: str,
    status_code: int = 0,
    page_type: str = "other",
    metadata: Optional[Dict[str, Any]] = None,
    structured_data: Optional[Dict[str, Any]] = None,
    body_text: Optional[str] = None,
    topics: Optional[list] = None,
    extracted_entities: Optional[Dict[str, Any]] = None,
    seo_signals: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "url": url,
        "status_code": status_code,
        "crawled_at": datetime.utcnow().isoformat(),
        "page_type": page_type,
        "metadata": metadata or EMPTY_METADATA.copy(),
        "structured_data": structured_data or {"json-ld": [], "normalized": {}, "raw_count": {}},
        "body_text": body_text,
        "topics": topics or [],
        "extracted_entities": extracted_entities or {},
        "seo_signals": seo_signals or EMPTY_SEO_SIGNALS.copy(),
        "error": error,
    }
