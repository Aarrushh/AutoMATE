import json
import sqlite3
from typing import List, Dict, Any, Optional
import litellm

class AppCache:
    def __init__(self, db_path: str = "app_cache.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def set(self, key: str, value: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        self.conn.commit()

class LLMNormalizer:
    def __init__(self, cache: AppCache = None):
        self.cache = cache or AppCache()
        self.model = "gpt-4o-mini"

    def normalize(self, raw_trigger: str, raw_actions: List[str]) -> Dict[str, Any]:
        cache_key = f"{raw_trigger}|{','.join(raw_actions)}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        prompt = f"""
        Clean and normalize these app names. Remove versioning (v1, v2), Beta labels, and platform suffixes.
        Trigger: {raw_trigger}
        Actions: {', '.join(raw_actions)}

        Return ONLY valid JSON in this format:
        {{"trigger_app": "Clean Name", "action_apps": ["Clean Name 1", "Clean Name 2"]}}
        """

        try:
            import os
            if not os.environ.get("OPENAI_API_KEY"):
                raise ValueError("No API Key")

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            # Basic JSON extraction if LLM adds markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            self.cache.set(cache_key, result)
            return result
        except Exception:
            # Fallback
            return {
                "trigger_app": raw_trigger.split(".")[0].replace("-", " ").title(),
                "action_apps": [a.split(".")[0].replace("-", " ").title() for a in raw_actions]
            }

    async def normalize_async(self, raw_trigger: str, raw_actions: List[str]) -> Dict[str, Any]:
        # Simple wrapper for sync method in this context
        return self.normalize(raw_trigger, raw_actions)
