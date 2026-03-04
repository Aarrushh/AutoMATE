import asyncio
import os
import sys
import json
import unittest

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from make_scraper import MakeScraper
from schema import AutomationTemplate

class TestMakeScraper(unittest.IsolatedAsyncioTestCase):
    async def test_scrape_mock_detail(self):
        # Path to mock file
        mock_file_path = os.path.abspath("tests/mock_make_detail.html")
        mock_url = f"file://{mock_file_path}"

        scraper = MakeScraper(headless=True)
        # We need to ensure the browser is started if we are calling scrape_template_detail directly
        # but scrape_template_detail handles it if we use 'async with' or call start()

        async with scraper:
            template = await scraper.scrape_template_detail(mock_url)

        self.assertIsNotNone(template)
        self.assertIsInstance(template, AutomationTemplate)
        self.assertEqual(template.title, "Save Typeform responses to Google Sheets")
        self.assertEqual(template.description, "Automatically save every new Typeform response to a Google Sheets spreadsheet.")
        self.assertEqual(template.trigger_app, "Typeform")
        self.assertIn("Google Sheets", template.action_apps)
        self.assertEqual(template.source_platform, "Make.com")
        self.assertEqual(template.complexity_score, 1) # (2 apps + 1) // 2 = 1
        self.assertEqual(template.maintenance_level, "LOW")
        self.assertEqual(template.monthly_opex, 0.0)

if __name__ == "__main__":
    unittest.main()
