# Phase 1 Planning Document - Core URL Crawler

## Purpose

This is the first planning document for Phase 1 of the BrightEdge engineering assignment. It defines the intended scope, architecture, implementation approach, and acceptance criteria for building the Part 1 core crawler.

This document was created before implementation and used as the development guide for the Phase 1 project.

## Assignment Phase

Part 1: Develop a core crawler that can crawl the content of a given URL.

The crawler should accept any absolute URL, retrieve the page content, classify the page, extract HTML metadata and body content, identify relevant topics, and return the result in a consistent machine-readable format.

## Phase 1 Goals

- Build a working crawler service for a single URL.
- Support product, article, blog, homepage, and generic page classification.
- Extract useful metadata such as title, description, Open Graph fields, language, canonical URL, and body text.
- Extract relevant topics from page content.
- Extract page-specific entities where possible, especially product and article fields.
- Return a unified JSON schema for both success and failure cases.
- Provide a small local API and UI for demonstration.
- Make the project runnable locally and through Docker.
- Keep the implementation generic, deterministic, and explainable.

## Proposed Capabilities

The Phase 1 crawler should include:

- URL validation for absolute `http` and `https` URLs.
- Optional robots.txt enforcement.
- HTTP fetching with redirect following.
- HTML/XML content-type validation.
- Metadata extraction.
- Structured data extraction from JSON-LD and related schema markup.
- Clean text extraction from noisy HTML.
- Page classification using schema hints, URL patterns, and HTML structure.
- Topic extraction using local deterministic logic.
- Product entity extraction for fields such as brand, price, rating, review count, availability, ASIN, and specifications where available.
- Article/blog entity extraction for fields such as author, published date, and modified date where available.
- SEO signal extraction, including word count, H1 count, schema presence, canonical URL, redirect chain, and redirect count.
- JSON result persistence for local inspection.
- Basic caching for repeated API requests.
- Batch crawling with bounded concurrency for local testing.

## Proposed System Shape

The Phase 1 implementation should be organized as a small FastAPI service with a modular crawler package.

Expected module responsibilities:

- `main.py`: API routes, request handling, caching, result persistence, and dashboard serving.
- `crawlEdge/crawler.py`: public crawler facade used by the API and CLI.
- `crawlEdge/http_client.py`: URL validation, robots checks, HTTP fetching, redirect handling, and content-type checks.
- `crawlEdge/parser.py`: HTML parsing and unified result assembly.
- `crawlEdge/classifier.py`: page type classification.
- `crawlEdge/schemas.py`: shared response schema builder.
- `crawlEdge/extractors/`: focused extraction modules for metadata, structured data, topics, product entities, and article entities.
- `static/index.html`: simple local dashboard for running crawls and viewing saved outputs.
- `tests/`: unit and API tests for important crawler behavior.
- `design/`: documentation and flow diagrams.

## Intended Pipeline

The crawler should follow this high-level pipeline:

```text
validate URL -> optional robots check -> fetch HTML -> validate content type -> parse HTML -> classify page -> extract entities/topics/signals -> save JSON -> return response
```

Each pipeline step should have a narrow responsibility. If a step fails, the service should return the same top-level response shape with an `error` field populated.

## API Plan

The service should expose:

- `GET /`: local dashboard.
- `GET /health`: health status.
- `GET /crawl`: crawl one URL.
- `POST /crawl/batch`: crawl a small list of URLs with bounded concurrency.
- `GET /api/results`: list saved crawl outputs.
- `GET /api/results/{filename}`: load one saved crawl output.

## Expected Output Schema

Every crawler result should include:

- `url`
- `status_code`
- `crawled_at`
- `page_type`
- `metadata`
- `structured_data`
- `body_text`
- `topics`
- `extracted_entities`
- `seo_signals`
- `error`

The same schema should be used for valid crawls, invalid URLs, blocked pages, unsupported content types, and fetch failures.

## Design Patterns To Use

- Facade: expose crawler behavior through a small public interface.
- Pipeline: keep crawl stages ordered and easy to reason about.
- Strategy or registry dispatch: select entity extraction logic based on page type.
- Adapter: normalize HTTP client responses into an internal fetch result.
- Cache-aside: check the API cache before crawling and populate it after fresh fetches.
- Bounded concurrency: limit simultaneous batch crawls with an async semaphore.
- Normalized schema: keep downstream UI and API consumers simple.

## Local Demonstration Plan

The Phase 1 project should include a local dashboard that:

- Starts empty.
- Lets a reviewer run a single crawl.
- Lets a reviewer run a small batch crawl.
- Displays summary metrics, topics, extracted details, content preview, and raw JSON.
- Shows only real outputs created under `results/`.

## Testing Plan

Phase 1 should include tests for:

- Product page parsing and entity extraction.
- Article page parsing and entity extraction.
- Invalid URL behavior.
- Full error schema behavior.
- Async API concurrency behavior.

## Acceptance Criteria

Phase 1 is considered complete when:

- The crawler accepts a URL and returns the unified result schema.
- Metadata, body text, topics, page type, and SEO signals are present when available.
- Product and article entity extraction works for representative pages.
- Invalid inputs and fetch errors return structured errors.
- The local dashboard can run crawls and show saved results.
- Docker Compose can run the service locally.
- Tests pass.
- Documentation explains the architecture and flow.

## AI Assistance Plan

Permitted usage:

- Reviewing the code structure.
- Drafting implementation changes.
- Creating API/UI scaffolding.
- Cleaning and updating documentation.
- Creating architecture notes.
- Running tests and smoke checks.
- Iterating on fixes based on review feedback.

## Known Constraints

- Some commercial websites may return bot-protection, region-specific, or JavaScript-heavy responses.
- The Phase 1 crawler will parse fetched HTML and will not render JavaScript through a browser engine.
- The implementation is intended for local/API demonstration.
