from dataclasses import dataclass
from typing import List, Optional
import urllib.parse
import urllib.robotparser
import asyncio

import httpx


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Sec-Ch-Ua": '"Chromium";v="146", "Not;A=Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


@dataclass
class FetchResponse:
    url: str
    status_code: int
    html: str
    content_type: str
    redirect_chain: List[str]


def is_valid_http_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)


def can_fetch_robots(url: str, respect: bool = True) -> bool:
    if not respect:
        return True
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(BROWSER_HEADERS["User-Agent"], url)
    except Exception:
        return True


async def can_fetch_robots_async(url: str, respect: bool = True) -> bool:
    return await asyncio.to_thread(can_fetch_robots, url, respect)


def response_status_from_error(error: Exception) -> int:
    response = getattr(error, "response", None)
    if response is not None:
        return response.status_code
    return 0


def fetch_html(url: str, timeout: float = 20.0) -> FetchResponse:
    with httpx.Client(timeout=timeout, follow_redirects=True, max_redirects=10) as client:
        response = client.get(url, headers=BROWSER_HEADERS)
        response.raise_for_status()
        final_url = str(response.url)
        redirect_chain = [str(history.url) for history in response.history] + [final_url]
        return FetchResponse(
            url=final_url,
            status_code=response.status_code,
            html=response.text,
            content_type=response.headers.get("content-type", ""),
            redirect_chain=redirect_chain,
        )


async def fetch_html_async(url: str, timeout: float = 20.0) -> FetchResponse:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=10) as client:
        response = await client.get(url, headers=BROWSER_HEADERS)
        response.raise_for_status()
        final_url = str(response.url)
        redirect_chain = [str(history.url) for history in response.history] + [final_url]
        return FetchResponse(
            url=final_url,
            status_code=response.status_code,
            html=response.text,
            content_type=response.headers.get("content-type", ""),
            redirect_chain=redirect_chain,
        )


def is_supported_html_content(content_type: Optional[str]) -> bool:
    if not content_type:
        return True
    return "html" in content_type or "xml" in content_type
