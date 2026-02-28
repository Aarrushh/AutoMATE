import unittest
from unittest.mock import patch, mock_open
import json
import sys
import os

# Add the project root to sys.path so we can import backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.scraper import ZapierScraper

class TestZapierScraper(unittest.TestCase):
    def test_load_existing_success(self):
        mock_data = {
            "data": [
                {"url": "https://zapier.com/templates/1", "name": "Template 1"},
                {"url": "https://zapier.com/templates/2", "name": "Template 2"}
            ]
        }
        json_data = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=json_data)):
            scraper = ZapierScraper()
            # load_existing is called in __init__

        self.assertEqual(len(scraper.templates), 2)
        self.assertEqual(scraper.total_scraped, 2)
        self.assertIn("https://zapier.com/templates/1", scraper.seen_urls)
        self.assertIn("https://zapier.com/templates/2", scraper.seen_urls)

    def test_load_existing_no_file(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            scraper = ZapierScraper()

        self.assertEqual(len(scraper.templates), 0)
        self.assertEqual(scraper.total_scraped, 0)
        self.assertEqual(len(scraper.seen_urls), 0)

    def test_load_existing_corrupt_json(self):
        with patch("builtins.open", mock_open(read_data="not a json")):
            scraper = ZapierScraper()

        self.assertEqual(len(scraper.templates), 0)
        self.assertEqual(scraper.total_scraped, 0)
        self.assertEqual(len(scraper.seen_urls), 0)

    def test_load_existing_missing_data_key(self):
        mock_data = {"other_key": []}
        json_data = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=json_data)):
            scraper = ZapierScraper()

        self.assertEqual(len(scraper.templates), 0)
        self.assertEqual(scraper.total_scraped, 0)
        self.assertEqual(len(scraper.seen_urls), 0)

    def test_load_existing_missing_url_field(self):
        mock_data = {
            "data": [
                {"name": "Template 1"} # Missing 'url'
            ]
        }
        json_data = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=json_data)):
            scraper = ZapierScraper()

        # In this case, self.templates is set, but then seen_urls fails.
        # So templates will be [ {"name": "Template 1"} ], but seen_urls will be set()
        # and total_scraped will be 0.
        self.assertEqual(len(scraper.templates), 1)
        self.assertEqual(scraper.total_scraped, 0)
        self.assertEqual(len(scraper.seen_urls), 0)

if __name__ == "__main__":
    unittest.main()
