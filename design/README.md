# BrightEdge Crawler Design

This document describes the crawler scope, runtime flow, module boundaries, and design patterns used in the implementation.

## Scope

The crawler accepts absolute `http` or `https` URLs and returns a unified JSON result. It is designed for local testing and assessment use, with a simple dashboard and Dockerized runtime.

### In Scope

- Validate input URLs.
- Optionally enforce robots.txt.
- Fetch HTML/XML-like content with browser-like request headers.
- Follow redirects and report the redirect chain.
- Parse metadata, structured data, clean text, topics, and SEO signals.
- Classify page type as `product`, `article`, `blog`, `homepage`, or `other`.
- Extract product or article entities when the page type supports it.
- Cache API crawl results in memory for a short period.
- Save crawl outputs as JSON files in `results/`.
- Run single crawls, bounded batch crawls, and CLI bulk crawls.

### Out Of Scope

- JavaScript rendering with a browser engine.
- Distributed crawling or queue workers.
- Persistent database storage.
- Authentication, tenant management, or hosted production controls.
- ML/LLM-based extraction.
- Full site crawling from seed URLs.

## Main Components

| Component | File | Responsibility |
| --- | --- | --- |
| FastAPI app | `main.py` | API routes, TTL cache, batch concurrency, JSON persistence, static dashboard |
| Crawler facade | `crawlEdge/crawler.py` | Validates crawler workflow and exposes sync/async crawl functions |
| HTTP client | `crawlEdge/http_client.py` | URL validation, robots.txt check, HTTP fetch, redirect capture |
| Parser | `crawlEdge/parser.py` | Converts fetched HTML into the unified output schema |
| Classifier | `crawlEdge/classifier.py` | Detects page type using schema, URL patterns, and HTML hints |
| Extractor registry | `crawlEdge/extractors/registry.py` | Dispatches to page-specific entity extractors |
| Product extractor | `crawlEdge/extractors/product.py` | Product fields from schema and HTML fallbacks |
| Article extractor | `crawlEdge/extractors/article.py` | Article/blog author and publish metadata |
| Structured data extractor | `crawlEdge/extractors/structured_data.py` | JSON-LD/extruct extraction and normalized schema summary |
| Dashboard | `static/index.html` | Single crawl, batch crawl, saved result browsing |

## End-To-End Flow

![End-to-end crawler flow](assets/flow-e2e.png)

## HTML Parsing Flow

![HTML parsing process flow](assets/process-flow.png)

## Batch Crawl Flow

![Batch processing crawler sequence](assets/batch-processing-crawler.png)

## Design Patterns Used

### Facade

`crawlEdge/crawler.py` exposes `crawl_single_url` and `crawl_single_url_async` as the public crawler API. FastAPI and the CLI do not need to know the details of URL validation, robots checks, HTTP fetching, content-type filtering, or parsing.

### Pipeline

The crawler is structured as a linear pipeline:

```text
validate -> robots check -> fetch -> content-type check -> parse -> save -> return
```

Each step has a small responsibility and either passes data forward or returns a full error-shaped result.

### Strategy / Registry Dispatch

`crawlEdge/extractors/registry.py` chooses the correct entity extraction strategy based on `page_type`:

- `product` uses product extraction.
- `article` and `blog` use article extraction.
- Other page types return no page-specific entities.

This keeps page-specific logic out of the parser orchestration.

### Adapter

`crawlEdge/http_client.py` adapts `httpx` responses into the internal `FetchResponse` dataclass. The rest of the system receives a stable structure with `url`, `status_code`, `html`, `content_type`, and `redirect_chain`.

### Template Method Style

The sync and async crawler functions follow the same algorithm with different IO implementations. This keeps API and CLI behavior consistent while allowing FastAPI routes to use async IO.

### Normalized Result Schema

`crawlEdge/schemas.py` guarantees that success and failure responses share the same top-level keys. This makes the dashboard and API consumers simpler because they can render one schema shape consistently.

### Cache-Aside

`main.py` uses an in-memory TTL cache keyed by URL and robots setting. Requests check the cache first, and cache misses fetch fresh data and populate the cache.

### Bounded Concurrency

Batch requests use `asyncio.Semaphore(10)` to prevent a single request from creating unbounded outbound fetches.

## Data Flow Summary

![Crawler data flow](assets/data-flow-crawler.png)

## Failure Handling

The crawler avoids throwing raw errors to clients. Instead, failures are converted into the same unified schema:

- Invalid URL: `status_code = 0`
- Robots blocked: `status_code = 403`
- Unsupported content type: returned with fetched status code
- HTTP/network exception: converted via `response_status_from_error`
- Empty/bot-protected response: result includes parser warning in `error`

## Persistence Model

Results are written as timestamped JSON files in `results/`. There is no database. This keeps the local deployment simple and makes outputs easy to inspect, delete, or archive.

## Deployment Shape

The Docker deployment is a single container that serves both the dashboard and crawler API on port `8000`. The crawler writes JSON files to `/app/results`, which Docker Compose bind-mounts to the host `./results` directory.
