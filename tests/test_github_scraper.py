import unittest
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.github_scraper import GitHubScraper

class TestGitHubScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = GitHubScraper()

    def test_cost_calculation_python_serverless(self):
        # Python without docker should be serverless ($0)
        res = self.scraper.cost_calculation("Python", ["automation"], "Simple script")
        self.assertEqual(res["estimated_operating_cost_per_month"], 0.0)
        self.assertEqual(res["infra_type"], "Serverless")

    def test_cost_calculation_docker_container(self):
        # Any language with docker should be container ($10)
        res = self.scraper.cost_calculation("Go", ["docker", "automation"], "Containerized app")
        self.assertEqual(res["estimated_operating_cost_per_month"], 10.0)
        self.assertEqual(res["infra_type"], "Container")

    def test_cost_calculation_vps_default(self):
        # Other languages without docker should be VPS ($5)
        res = self.scraper.cost_calculation("Java", ["automation"], "Standard app")
        self.assertEqual(res["estimated_operating_cost_per_month"], 5.0)
        self.assertEqual(res["infra_type"], "VPS")

    def test_type_classification_high_trust(self):
        res = self.scraper.type_classification(1500, "Go")
        self.assertEqual(res, "High-Trust Community Solution")

    def test_type_classification_script(self):
        res = self.scraper.type_classification(500, "Python")
        self.assertEqual(res, "Script-based Automation")

    def test_type_classification_default(self):
        res = self.scraper.type_classification(100, "TypeScript")
        self.assertEqual(res, "Open Source Workflow")

    def test_parse_stars(self):
        self.assertEqual(self.scraper.parse_stars("1,234 stars"), 1234)
        self.assertEqual(self.scraper.parse_stars("1.5k stars"), 1500)
        self.assertEqual(self.scraper.parse_stars("150k"), 150000)

if __name__ == '__main__':
    unittest.main()
