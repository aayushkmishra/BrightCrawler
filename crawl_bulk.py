import argparse
import json
import os
from datetime import datetime

from main import crawl_and_save, sanitize_filename


def read_urls(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def summarize(result: dict) -> dict:
    entities = result.get("extracted_entities", {})
    seo = result.get("seo_signals", {})
    return {
        "url": result.get("url"),
        "status_code": result.get("status_code"),
        "page_type": result.get("page_type"),
        "title": result.get("metadata", {}).get("title"),
        "word_count": seo.get("word_count"),
        "brand": entities.get("brand"),
        "price": entities.get("price"),
        "currency": entities.get("currency"),
        "average_rating": entities.get("average_rating"),
        "review_count": entities.get("review_count"),
        "author": entities.get("author"),
        "published_date": entities.get("published_date"),
        "error": result.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk crawl URLs from a text file.")
    parser.add_argument("--input", default="sample_urls.txt", help="Input file with one URL per line.")
    parser.add_argument("--output-dir", default="results", help="Directory for crawl output.")
    parser.add_argument("--respect-robots", action="store_true", help="Respect robots.txt.")
    parser.add_argument("--force-refresh", action="store_true", help="Bypass in-memory cache.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    urls = read_urls(args.input)
    results = [
        crawl_and_save(url, respect_robots=args.respect_robots, force_refresh=args.force_refresh)
        for url in urls
    ]
    summary = [summarize(result) for result in results]

    for original_url, result in zip(urls, results):
        filename = os.path.join(args.output_dir, f"{sanitize_filename(original_url)}.json")
        clean_result = dict(result)
        clean_result.pop("saved_file", None)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(clean_result, f, indent=2, ensure_ascii=False)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(args.output_dir, f"bulk_summary_{timestamp}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps({
        "input": args.input,
        "summary_file": summary_path,
        "requested_count": len(urls),
        "success_count": sum(1 for result in results if result.get("error") is None),
        "error_count": sum(1 for result in results if result.get("error") is not None),
    }, indent=2))


if __name__ == "__main__":
    main()
