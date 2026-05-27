from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cachetools import TTLCache
import time
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from crawlEdge.crawler import crawl_single_url, crawl_single_url_async

app = FastAPI(title="BrightEdge - Production Crawler")
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
STATIC_DIR = BASE_DIR / "static"

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cache = TTLCache(maxsize=1000, ttl=3600)

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class BatchCrawlRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=25, description="URLs to crawl")
    respect_robots: bool = Field(False, description="Respect robots.txt")
    force_refresh: bool = Field(False, description="Bypass cache and fetch fresh results")


def sanitize_filename(url: str) -> str:
    """Create safe filename from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_")
    path = parsed.path.strip("/").replace("/", "_")[:100]  # limit length
    return f"{domain}_{path}" if path else domain


def cache_key(url: str, respect_robots: bool) -> str:
    return f"{respect_robots}:{url}"


def save_result(result: dict, url: str, output_dir: str | Path = RESULTS_DIR) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(url)
    filename = output_path / f"{safe_name}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return str(filename)


def list_result_files() -> list[dict]:
    files = []
    if not RESULTS_DIR.exists():
        return files
    for path in RESULTS_DIR.glob("*.json"):
        if path.name.startswith("bulk_summary_"):
            continue
        stat = path.stat()
        files.append({
            "id": path.name,
            "filename": path.name,
            "source": "saved",
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size_bytes": stat.st_size,
        })
    return sorted(files, key=lambda item: item["updated_at"], reverse=True)


def resolve_result_file(result_id: str) -> Path:
    filename = Path(result_id).name
    if filename != result_id:
        raise FileNotFoundError(result_id)
    path = (RESULTS_DIR / filename).resolve()
    if RESULTS_DIR.resolve() not in path.parents or path.suffix.lower() != ".json":
        raise FileNotFoundError(result_id)
    return path


def crawl_and_save(url: str, respect_robots: bool = False, force_refresh: bool = False) -> dict:
    start = time.time()
    key = cache_key(url, respect_robots)

    if not force_refresh and key in cache:
        cached = dict(cache[key])
        cached["cache_hit"] = True
        return cached

    result = crawl_single_url(url, respect_robots=respect_robots)
    result["processing_time_ms"] = round((time.time() - start) * 1000, 2)
    result["cache_hit"] = False

    try:
        result["saved_file"] = save_result(result, url)
    except Exception as e:
        result["saved_file"] = f"Failed to save: {str(e)}"

    cache[key] = result
    return result


async def crawl_and_save_async(url: str, respect_robots: bool = False, force_refresh: bool = False) -> dict:
    start = time.time()
    key = cache_key(url, respect_robots)

    if not force_refresh and key in cache:
        cached = dict(cache[key])
        cached["cache_hit"] = True
        return cached

    result = await crawl_single_url_async(url, respect_robots=respect_robots)
    result["processing_time_ms"] = round((time.time() - start) * 1000, 2)
    result["cache_hit"] = False

    try:
        result["saved_file"] = await asyncio.to_thread(save_result, result, url)
    except Exception as e:
        result["saved_file"] = f"Failed to save: {str(e)}"

    cache[key] = result
    return result


async def crawl_with_semaphore(url: str, respect_robots: bool, force_refresh: bool, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        return await crawl_and_save_async(
            url,
            respect_robots=respect_robots,
            force_refresh=force_refresh,
        )


@app.get("/crawl")
@limiter.limit("10/minute")
async def crawl_url(request: Request,
                    url: str = Query(..., description="Full URL to crawl"),
                    respect_robots: bool = Query(False, description="Respect robots.txt"),
                    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh result")):
    result = await crawl_and_save_async(url, respect_robots=respect_robots, force_refresh=force_refresh)
    return JSONResponse(content=result)


@app.post("/crawl/batch")
@limiter.limit("3/minute")
async def crawl_batch(request: Request, payload: BatchCrawlRequest):
    start = time.time()
    semaphore = asyncio.Semaphore(10)
    results = await asyncio.gather(*[
        crawl_with_semaphore(
            url,
            payload.respect_robots,
            payload.force_refresh,
            semaphore,
        )
        for url in payload.urls
    ])
    response = {
        "requested_count": len(payload.urls),
        "success_count": sum(1 for result in results if result.get("error") is None),
        "error_count": sum(1 for result in results if result.get("error") is not None),
        "processing_time_ms": round((time.time() - start) * 1000, 2),
        "results": results,
    }
    return JSONResponse(content=response)


@app.get("/api/results")
async def api_results():
    return {"results": list_result_files()}


@app.get("/api/results/{result_id}")
async def api_result_detail(result_id: str):
    try:
        path = resolve_result_file(result_id)
        with open(path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "Result file not found"})
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "Result file is not valid JSON"})


@app.get("/health")
async def health():
    return {"status": "healthy", "cache_size": len(cache),
            "results_count": len(os.listdir(RESULTS_DIR)) if RESULTS_DIR.exists() else 0}


@app.get("/")
async def dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "BrightEdge crawler API is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
