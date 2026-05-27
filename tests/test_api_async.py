import asyncio
import unittest
from unittest.mock import patch

import httpx

from main import app
from crawlEdge.schemas import build_result


class AsyncApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_ten_concurrent_crawl_requests(self):
        async def fake_crawl(url: str, respect_robots: bool = False):
            await asyncio.sleep(0.01)
            return build_result(url=url, status_code=200, page_type="other")

        transport = httpx.ASGITransport(app=app)
        with (
            patch("main.crawl_single_url_async", side_effect=fake_crawl),
            patch("main.save_result", return_value="test-result.json"),
        ):
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                responses = await asyncio.gather(*[
                    client.get(
                        "/crawl",
                        params={
                            "url": f"https://example.com/product/{index}",
                            "force_refresh": "true",
                        },
                    )
                    for index in range(10)
                ])

        self.assertEqual(len(responses), 10)
        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertTrue(all("page_type" in response.json() for response in responses))


if __name__ == "__main__":
    unittest.main()
