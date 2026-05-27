from typing import Any, Dict

from crawlEdge.http_client import (
    can_fetch_robots_async,
    can_fetch_robots,
    fetch_html_async,
    fetch_html,
    is_supported_html_content,
    is_valid_http_url,
    response_status_from_error,
)
from crawlEdge.parser import parse_html
from crawlEdge.schemas import build_result


def crawl_single_url(url: str, respect_robots: bool = False) -> Dict[str, Any]:
    if not is_valid_http_url(url):
        return build_result(
            url=url,
            status_code=0,
            error="Invalid URL. Only absolute http(s) URLs are supported.",
        )

    if not can_fetch_robots(url, respect_robots):
        return build_result(url=url, status_code=403, error="Blocked by robots.txt")

    try:
        fetched = fetch_html(url)
        if not is_supported_html_content(fetched.content_type):
            return build_result(
                url=fetched.url,
                status_code=fetched.status_code,
                error=f"Unsupported content type: {fetched.content_type}",
            )

        return parse_html(
            html=fetched.html,
            final_url=fetched.url,
            status_code=fetched.status_code,
            redirect_chain=fetched.redirect_chain,
        )
    except Exception as error:
        return build_result(
            url=url,
            status_code=response_status_from_error(error),
            error=str(error),
        )


async def crawl_single_url_async(url: str, respect_robots: bool = False) -> Dict[str, Any]:
    if not is_valid_http_url(url):
        return build_result(
            url=url,
            status_code=0,
            error="Invalid URL. Only absolute http(s) URLs are supported.",
        )

    if not await can_fetch_robots_async(url, respect_robots):
        return build_result(url=url, status_code=403, error="Blocked by robots.txt")

    try:
        fetched = await fetch_html_async(url)
        if not is_supported_html_content(fetched.content_type):
            return build_result(
                url=fetched.url,
                status_code=fetched.status_code,
                error=f"Unsupported content type: {fetched.content_type}",
            )

        return parse_html(
            html=fetched.html,
            final_url=fetched.url,
            status_code=fetched.status_code,
            redirect_chain=fetched.redirect_chain,
        )
    except Exception as error:
        return build_result(
            url=url,
            status_code=response_status_from_error(error),
            error=str(error),
        )
