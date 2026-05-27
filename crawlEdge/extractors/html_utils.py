from typing import Optional
import re

from bs4 import BeautifulSoup


def first_text(soup: BeautifulSoup, selectors: list) -> str:
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag:
            text = tag.get_text(" ", strip=True)
            if text:
                return text
    return ""


def parse_decimal(text: str) -> Optional[float]:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text.replace(",", ""))
    return float(match.group(1)) if match else None


def parse_int(text: str) -> Optional[int]:
    match = re.search(r"([0-9][0-9,]*)", text)
    return int(match.group(1).replace(",", "")) if match else None


def extract_table_like_value(body_text: str, labels: list) -> Optional[str]:
    for label in labels:
        match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*([^\|\n]+)", body_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
