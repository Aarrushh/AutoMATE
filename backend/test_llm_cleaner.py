import os
import unittest
from unittest.mock import patch, MagicMock
from llm_cleaner import LLMNormalizer, AppCache, NormalizedApps

class TestLLMNormalizer(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_app_cache.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.normalizer = LLMNormalizer(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_cache_mechanism(self):
        cache = AppCache(self.db_path)
        cache.set("Google Sheets (Beta)", "Google Sheets")
        self.assertEqual(cache.get("Google Sheets (Beta)"), "Google Sheets")
        self.assertIsNone(cache.get("Non-existent"))

    @patch("llm_cleaner.completion")
    def test_clean_apps_with_llm_call(self, mock_completion):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"trigger_app": "Gmail", "action_apps": ["Airtable", "Webhooks"]}'))
        ]
        mock_completion.return_value = mock_response

        dirty_trigger = "Gmail (0.1.0)"
        dirty_actions = ["Airtable v2", "Webhook by Zapier"]

        result = self.normalizer.clean_apps(dirty_trigger, dirty_actions)

        self.assertEqual(result.trigger_app, "Gmail")
        self.assertEqual(result.action_apps, ["Airtable", "Webhooks"])

        # Verify it's cached
        self.assertEqual(self.normalizer.cache.get(dirty_trigger), "Gmail")
        self.assertEqual(self.normalizer.cache.get("Airtable v2"), "Airtable")
        self.assertEqual(self.normalizer.cache.get("Webhook by Zapier"), "Webhooks")

        # Second call should not trigger LLM (mock_completion should only be called once)
        result2 = self.normalizer.clean_apps(dirty_trigger, dirty_actions)
        self.assertEqual(result2.trigger_app, "Gmail")
        mock_completion.assert_called_once()

    @patch("llm_cleaner.completion")
    def test_clean_apps_fallback(self, mock_completion):
        mock_completion.side_effect = Exception("API Error")

        dirty_trigger = "Dirty Trigger"
        dirty_actions = ["Dirty Action"]

        result = self.normalizer.clean_apps(dirty_trigger, dirty_actions)

        self.assertEqual(result.trigger_app, dirty_trigger)
        self.assertEqual(result.action_apps, dirty_actions)

if __name__ == "__main__":
    unittest.main()
