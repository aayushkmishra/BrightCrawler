# BrightEdge Crawler

## Assignment Notes: AI Usage, Methods, and Evaluation

AI tools used:

- Research: Grok, GPT Research
- Coding support: Codex, ChatGPT free tier
- Flowcharts and architecture diagrams: draw.io

Methods, services, and frameworks used:

- Python, FastAPI, Uvicorn, httpx, BeautifulSoup, lxml, trafilatura, price-parser
- Docker and Docker Compose for local reproducible execution
- Google Cloud Run for public container-based demo deployment
- Queue-based production design using Kafka/SQS/Pub/Sub-style systems
- Redis design for robots.txt caching, rate limiting, and deduplication pre-checks
- Object storage and metadata warehouse/lakehouse design for production scale
- Prometheus, Grafana, OpenTelemetry, and cloud logging for monitoring design

Evaluation approach:

- Validate crawler output against product and article URLs
- Confirm consistent metadata schema for success and failure responses
- Test invalid URLs, batch crawling, Docker runtime, and public Cloud Run endpoints
- Review design for reliability, performance, scale, cost, SLOs, SLAs, and operational monitoring

Proof of Concept and estimates are documented in:

- `design/Phase3.md`
- `design/AI_USAGE_AND_METHODS.txt`

A FastAPI-based URL crawler that fetches HTML pages, follows redirects, classifies page type, extracts metadata/content/entities, and presents the result in a simple local dashboard.

## What It Does

- Crawls a single URL or a bounded batch of URLs.
- Extracts metadata, JSON-LD/schema signals, clean body text, topics, SEO signals, and page-specific entities.
- Supports product and article/blog extraction paths.
- Saves crawl outputs as JSON files in `results/`.
- Serves a local dashboard at `/` for running crawls and reviewing saved results.
- Ships with Docker Compose for local container testing.

## Project Layout

```text
.
|-- main.py                  # FastAPI app, cache, persistence, API routes, dashboard serving
|-- crawl_bulk.py            # CLI runner for URL files
|-- crawlEdge/
|   |-- crawler.py           # Public crawler facade
|   |-- http_client.py       # URL validation, robots check, HTTP fetch
|   |-- parser.py            # HTML parsing and result assembly
|   |-- classifier.py        # Page type detection
|   |-- schemas.py           # Unified result shape
|   `-- extractors/          # Metadata, structured data, topic, product, article extractors
|-- static/index.html        # Local dashboard UI
|-- tests/                   # Unit and API tests
|-- design/                  # Architecture, scope, and exported diagrams
|-- Dockerfile
`-- docker-compose.yml
```

## Run Locally

```powershell
.\.brightedge\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

The dashboard starts empty and shows JSON outputs created in `results/` after you run crawls.

## Run With Docker

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8000/
```

Compose mounts `./results` into the container, so saved crawl outputs remain on your machine after the container stops.

## API

Health:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

Single crawl:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/crawl?url=https://example.com/page&force_refresh=true"
```

Batch crawl:

```powershell
Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri "http://127.0.0.1:8000/crawl/batch" `
  -Body '{"urls":["https://example.com/page-one","https://example.com/page-two"],"force_refresh":true}'
```

Saved results:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/results"
```

## CLI

```powershell
.\.brightedge\Scripts\python.exe crawl_bulk.py --input sample_urls.txt --output-dir results --force-refresh
```

`sample_urls.txt` is only a convenience input file for local testing. The app itself does not preload sample results.

## Important Options

- `respect_robots=true`: Enforce robots.txt before fetching.
- `force_refresh=true`: Bypass the in-memory TTL cache.
- Batch requests accept 1 to 25 URLs and run with bounded concurrency.

## Output Shape

Every response uses the same top-level schema, including failures:

```json
{
  "url": "https://final-url.example/page",
  "status_code": 200,
  "crawled_at": "2026-05-25T16:45:00.000000",
  "page_type": "product | article | blog | homepage | category | other",
  "metadata": {
    "title": "...",
    "meta_description": "...",
    "og_title": "...",
    "og_description": "...",
    "language": "en"
  },
  "structured_data": {
    "json-ld": [],
    "normalized": {},
    "raw_count": {}
  },
  "body_text": "clean main content...",
  "topics": ["topic", "keyword"],
  "extracted_entities": {},
  "seo_signals": {
    "word_count": 621,
    "has_schema_markup": true,
    "h1_count": 1,
    "canonical": "https://canonical-url.example/page",
    "redirect_chain": [],
    "redirect_count": 0
  },
  "error": null
}
```

## Tests

```powershell
.\.brightedge\Scripts\python.exe -m unittest discover -s tests -v
```

The tests cover product extraction, article extraction, invalid URL error shape, and concurrent API requests.

## Design Docs

See [design/README.md](design/README.md) for scope, architecture, design patterns, and exported flow diagrams.

## Flow Diagrams

![End-to-end crawler flow](design/assets/flow-e2e.png)

![HTML parsing process flow](design/assets/process-flow.png)

![Batch processing crawler sequence](design/assets/batch-processing-crawler.png)

![Crawler data flow](design/assets/data-flow-crawler.png)
