import unittest
from backend.github_scraper import GitHubScraper

class TestGitHubScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = GitHubScraper(target_volume=10)

    def test_parse_stars(self):
        self.assertEqual(self.scraper.parse_stars("1.5k"), 1500)
        self.assertEqual(self.scraper.parse_stars("1,200"), 1200)
        self.assertEqual(self.scraper.parse_stars("500"), 500)
        self.assertEqual(self.scraper.parse_stars("invalid"), 0)

    def test_enrich_and_classify_serverless(self):
        self.scraper.repos = [{
            "name": "test-repo",
            "description": "desc",
            "stars": 100,
            "language": "Python",
            "url": "http://github.com/test",
            "tags": ["automation"],
            "tools": ["Python", "automation"],
            "has_dockerfile": False
        }]
        enriched = self.scraper.enrich_and_classify()
        self.assertEqual(enriched[0]["estimated_infrastructure_cost_monthly"], 0.00)
        self.assertEqual(enriched[0]["deployment_complexity_score"], 1)
        self.assertEqual(enriched[0]["type"], "Script-based Automation")

    def test_enrich_and_classify_container(self):
        self.scraper.repos = [{
            "name": "test-repo-docker",
            "description": "desc",
            "stars": 500,
            "language": "Go",
            "url": "http://github.com/test-docker",
            "tags": ["docker"],
            "tools": ["Go", "docker"],
            "has_dockerfile": True
        }]
        enriched = self.scraper.enrich_and_classify()
        self.assertEqual(enriched[0]["estimated_infrastructure_cost_monthly"], 10.00)
        self.assertEqual(enriched[0]["deployment_complexity_score"], 3)
        self.assertEqual(enriched[0]["type"], "Open Source Workflow")

    def test_enrich_and_classify_high_trust(self):
        self.scraper.repos = [{
            "name": "popular-repo",
            "description": "desc",
            "stars": 2000,
            "language": "Java",
            "url": "http://github.com/popular",
            "tags": ["workflow"],
            "tools": ["Java", "workflow"],
            "has_dockerfile": False
        }]
        enriched = self.scraper.enrich_and_classify()
        self.assertEqual(enriched[0]["type"], "High-Trust Community Solution")
        self.assertEqual(enriched[0]["estimated_infrastructure_cost_monthly"], 5.00)
        self.assertEqual(enriched[0]["deployment_complexity_score"], 2)

if __name__ == "__main__":
    unittest.main()
