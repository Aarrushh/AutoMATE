import unittest
from unittest.mock import MagicMock, patch, mock_open, AsyncMock
import json
import asyncio
from backend.scraper import ZapierScraper

class TestZapierScraper(unittest.TestCase):

    @patch("backend.scraper.OUTPUT_FILE", "test_templates.json")
    def test_load_existing_success(self):
        data = {"data": [{"url": "http://test.com", "name": "test"}]}
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            scraper = ZapierScraper()
            self.assertEqual(len(scraper.templates), 1)
            self.assertIn("http://test.com", scraper.seen_urls)

    @patch("backend.scraper.OUTPUT_FILE", "non_existent.json")
    def test_load_existing_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            scraper = ZapierScraper()
            self.assertEqual(len(scraper.templates), 0)

    @patch("backend.scraper.OUTPUT_FILE", "invalid.json")
    def test_load_existing_invalid_json(self):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            # Currently it has a bare except: pass, so it should not raise but templates should be empty
            scraper = ZapierScraper()
            self.assertEqual(len(scraper.templates), 0)

    def test_discover_categories_success(self):
        scraper = ZapierScraper()
        mock_page = AsyncMock()

        mock_link = AsyncMock()
        mock_link.inner_text.return_value = "Category 1"
        mock_link.get_attribute.return_value = "/templates/cat1"

        mock_page.query_selector_all.return_value = [mock_link]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            categories = loop.run_until_complete(scraper.discover_categories(mock_page))
        finally:
            loop.close()

        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], ("Category 1", "https://zapier.com/templates/cat1"))

    def test_discover_categories_exception(self):
        scraper = ZapierScraper()
        mock_page = AsyncMock()
        mock_page.query_selector_all.side_effect = Exception("Playwright error")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            categories = loop.run_until_complete(scraper.discover_categories(mock_page))
        finally:
            loop.close()

        self.assertEqual(categories, [])

if __name__ == "__main__":
    unittest.main()
