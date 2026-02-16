import unittest
import json
import logging
import os
import sys
from unittest.mock import patch, mock_open

# Add backend directory to sys.path so we can import scraper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper import ZapierScraper

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestZapierScraperLoadExisting(unittest.TestCase):

    def setUp(self):
        # Reset the logger handlers to ensure clean state
        self.logger = logging.getLogger('scraper')
        self.logger.setLevel(logging.INFO)

    @patch("builtins.open", new_callable=mock_open, read_data='{"data": [{"url": "http://example.com"}]}')
    def test_load_existing_success(self, mock_file):
        """Test successful loading of existing templates."""
        scraper = ZapierScraper()
        self.assertEqual(len(scraper.templates), 1)
        self.assertEqual(scraper.total_scraped, 1)
        self.assertIn("http://example.com", scraper.seen_urls)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_existing_file_not_found(self, mock_file):
        """Test handling of FileNotFoundError."""
        with self.assertLogs('scraper', level='INFO') as cm:
            scraper = ZapierScraper()
            self.assertTrue(any("No existing templates found" in o for o in cm.output))
        self.assertEqual(len(scraper.templates), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_load_existing_json_error(self, mock_file):
        """Test handling of JSONDecodeError."""
        # Mock json.load to raise JSONDecodeError because mock_open read_data isn't parsed by real json.load in the mock context unless we mock json.load too or just let it fail.
        # Actually, if we use real json.load on mock_open file object, it might fail if read_data is invalid json.
        # But let's be explicit and mock json.load for clarity or just rely on the read_data.
        # Let's rely on read_data="invalid json" causing json.load to raise JSONDecodeError.

        with self.assertLogs('scraper', level='WARNING') as cm:
            scraper = ZapierScraper()
            self.assertTrue(any("Existing templates file is corrupted" in o for o in cm.output))
        self.assertEqual(len(scraper.templates), 0)

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_load_existing_generic_error(self, mock_file):
        """Test handling of other exceptions."""
        with self.assertLogs('scraper', level='ERROR') as cm:
            scraper = ZapierScraper()
            self.assertTrue(any("Error loading existing templates" in o for o in cm.output))
        self.assertEqual(len(scraper.templates), 0)

if __name__ == "__main__":
    unittest.main()
