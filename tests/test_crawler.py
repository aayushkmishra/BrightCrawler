import unittest

from crawlEdge.crawler import crawl_single_url, parse_html


PRODUCT_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <title>Cuisinart Compact Toaster</title>
    <meta name="description" content="A compact two-slice toaster for small kitchens.">
    <meta property="og:title" content="Cuisinart Toaster">
    <link rel="canonical" href="https://example.com/products/toaster">
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Cuisinart CPT-122",
        "brand": {"@type": "Brand", "name": "Cuisinart"},
        "sku": "B009GQ034C",
        "offers": {"@type": "Offer", "price": "49.99", "priceCurrency": "USD"}
      }
    </script>
  </head>
  <body>
    <h1>Cuisinart CPT-122 Compact Toaster</h1>
    <main>
      This compact kitchen toaster has wide slots for bread and bagels. It includes
      defrost, reheat, and shade controls for everyday breakfast use.
    </main>
  </body>
</html>
"""


ARTICLE_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <title>How AI Is Changing Software Work</title>
    <meta name="description" content="A technology article about AI and software teams.">
    <meta name="author" content="Lisa Example">
    <meta property="article:published_time" content="2025-09-23T14:00:00Z">
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "How AI Is Changing Software Work",
        "author": {"@type": "Person", "name": "Lisa Example"},
        "datePublished": "2025-09-23T14:00:00Z"
      }
    </script>
  </head>
  <body>
    <article>
      <h1>How AI Is Changing Software Work</h1>
      Software engineers are adopting AI tools for testing, coding, review, and
      documentation while teams rethink quality practices.
    </article>
  </body>
</html>
"""


AMAZON_LIKE_PRODUCT_HTML = """
<!doctype html>
<html lang="en-us">
  <head>
    <title>Amazon.com: Cuisinart Toaster</title>
    <meta name="description" content="Online shopping for kitchen appliances.">
  </head>
  <body>
    <h1 id="productTitle">Cuisinart CPT-122 2-Slice Compact Plastic Toaster</h1>
    <div id="averageCustomerReviews">4.0 4.0 out of 5 stars</div>
    <span id="acrCustomerReviewText">(25,140)</span>
    <div id="availability">No featured offers available</div>
    <div id="corePrice_feature_div">
      <span class="a-price"><span class="a-offscreen">$54.99</span></span>
    </div>
    <main>
      | Brand | Cuisinart |
      | Model Number | CPT-122 |
      | ASIN | B009GQ034C |
      No featured offers available.
    </main>
  </body>
</html>
"""


class CrawlerParserTests(unittest.TestCase):
    def test_product_page_schema_and_entities(self):
        result = parse_html(PRODUCT_HTML, "https://example.com/products/toaster")

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["page_type"], "product")
        self.assertEqual(result["metadata"]["title"], "Cuisinart Compact Toaster")
        self.assertEqual(result["extracted_entities"]["brand"], "Cuisinart")
        self.assertEqual(result["extracted_entities"]["price"], "49.99")
        self.assertTrue(result["seo_signals"]["has_schema_markup"])
        self.assertIn("normalized", result["structured_data"])

    def test_article_page_schema_and_entities(self):
        result = parse_html(ARTICLE_HTML, "https://example.com/news/ai-software-work")

        self.assertEqual(result["page_type"], "article")
        self.assertEqual(result["extracted_entities"]["author"], "Lisa Example")
        self.assertEqual(result["extracted_entities"]["published_date"], "2025-09-23T14:00:00Z")
        self.assertGreater(result["seo_signals"]["word_count"], 10)
        self.assertIsNone(result["error"])

    def test_invalid_url_returns_full_error_schema(self):
        result = crawl_single_url("not-a-url")

        self.assertEqual(result["status_code"], 0)
        self.assertEqual(result["page_type"], "other")
        self.assertIsNotNone(result["error"])
        self.assertIn("metadata", result)
        self.assertIn("seo_signals", result)

    def test_product_html_fallback_entities_without_schema(self):
        result = parse_html(
            AMAZON_LIKE_PRODUCT_HTML,
            "https://www.amazon.com/example/dp/B009GQ034C",
        )

        self.assertEqual(result["page_type"], "product")
        self.assertEqual(result["extracted_entities"]["brand"], "Cuisinart")
        self.assertEqual(result["extracted_entities"]["asin"], "B009GQ034C")
        self.assertEqual(result["extracted_entities"]["price"], 54.99)
        self.assertEqual(result["extracted_entities"]["average_rating"], 4.0)
        self.assertEqual(result["extracted_entities"]["review_count"], 25140)
        self.assertEqual(result["structured_data"]["normalized"]["products"][0]["source"], "html_fallback")


if __name__ == "__main__":
    unittest.main()
