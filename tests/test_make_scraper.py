import unittest
import asyncio
import os
import json
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from make_scraper import MakeScraper

class TestMakeScraper(unittest.TestCase):
    def setUp(self):
        # Create a mock output file to avoid overwriting real data if any
        self.output_file = "tests/test_output.json"
        # Monkey patch OUTPUT_FILE in MakeScraper
        # But OUTPUT_FILE is a global variable in make_scraper.py
        # We can't easily patch it unless we reload the module or patch it where it is used.
        # However, MakeScraper reads/writes to OUTPUT_FILE.
        # I'll just change the constant in the imported module.
        import make_scraper
        make_scraper.OUTPUT_FILE = self.output_file

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_scrape_mock_page(self):
        # Path to mock file
        mock_file_path = os.path.abspath("tests/mock_make_page.html")
        mock_url = f"file://{mock_file_path}"

        scraper = MakeScraper()

        # Run scrape
        asyncio.run(scraper.scrape(urls=[mock_url]))

        # Verify results
        with open(self.output_file, "r") as f:
            data = json.load(f)

        self.assertEqual(data["total_count"], 2)
        items = data["data"]
        self.assertEqual(len(items), 2)

        # Check first item (Template)
        item1 = next(i for i in items if "Google Sheets" in i["name"])
        self.assertEqual(item1["name"], "Google Sheets to Slack Notification")
        self.assertIn("Google Sheets", item1["tools"])
        self.assertIn("Slack", item1["tools"])
        self.assertEqual(len(item1["tools"]), 2)
        self.assertEqual(item1["type"], "Multi-product solution")
        self.assertEqual(item1["financials"]["complexity_tier"], "Low") # 2 tools < 3
        # Cost: 2 * 9/10000 * 100 = 0.18
        self.assertAlmostEqual(item1["financials"]["estimated_operating_cost_per_month"], 0.18, places=4)

        # Check second item (Integration)
        item2 = next(i for i in items if "Complex" in i["name"])
        self.assertEqual(item2["name"], "Complex Workflow")
        self.assertEqual(len(item2["tools"]), 4) # Salesforce, HubSpot, Gmail, Slack
        self.assertEqual(item2["type"], "Multi-product solution")
        self.assertEqual(item2["financials"]["complexity_tier"], "Mid") # 4 tools <= 5
        # Cost: 4 * 9/10000 * 100 = 0.36
        self.assertAlmostEqual(item2["financials"]["estimated_operating_cost_per_month"], 0.36, places=4)

if __name__ == "__main__":
    unittest.main()
