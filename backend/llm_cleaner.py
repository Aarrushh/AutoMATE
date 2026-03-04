import sqlite3
import json
from pydantic import BaseModel
from typing import List, Optional
from litellm import completion

class NormalizedApps(BaseModel):
    trigger_app: str
    action_apps: List[str]

class AppCache:
    def __init__(self, db_path: str = "app_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    dirty_name TEXT PRIMARY KEY,
                    clean_name TEXT NOT NULL
                )
            """)
            conn.commit()

    def get(self, dirty_name: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT clean_name FROM cache WHERE dirty_name = ?", (dirty_name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def set(self, dirty_name: str, clean_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (dirty_name, clean_name) VALUES (?, ?)",
                (dirty_name, clean_name)
            )
            conn.commit()

class LLMNormalizer:
    def __init__(self, model: str = "gpt-4o-mini", db_path: str = "app_cache.db"):
        self.model = model
        self.cache = AppCache(db_path)
        self.system_prompt = (
            "You are a strict data normalization service. "
            "Convert dirty app names from automation platforms into their canonical, clean versions. "
            "Remove versioning (v2), environment tags (Beta), and platform suffixes (by Zapier). "
            "Example: 'Google Sheets (Beta)' -> 'Google Sheets', 'Airtable v2' -> 'Airtable', "
            "'Webhook by Zapier' -> 'Webhooks', 'Gmail (0.1.0)' -> 'Gmail'. "
            "Return ONLY a JSON object with 'trigger_app' and 'action_apps' keys."
        )

    def clean_apps(self, dirty_trigger: str, dirty_actions: List[str]) -> NormalizedApps:
        # Check cache for trigger
        clean_trigger = self.cache.get(dirty_trigger)

        # Check cache for actions
        all_actions_cached = True
        clean_actions = []
        for action in dirty_actions:
            cached = self.cache.get(action)
            if cached:
                clean_actions.append(cached)
            else:
                all_actions_cached = False
                break

        # If everything is cached, return early
        if clean_trigger and all_actions_cached and len(clean_actions) == len(dirty_actions):
            return NormalizedApps(trigger_app=clean_trigger, action_apps=clean_actions)

        prompt = f"Trigger: {dirty_trigger}\nActions: {', '.join(dirty_actions)}"

        try:
            # LiteLLM supports response_format with Pydantic for certain providers (like OpenAI)
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=NormalizedApps
            )

            raw_content = response.choices[0].message.content
            data = json.loads(raw_content)

            # Validate with Pydantic
            normalized = NormalizedApps(**data)

            # Update cache
            self.cache.set(dirty_trigger, normalized.trigger_app)
            # Make sure we have the same number of actions
            if len(dirty_actions) == len(normalized.action_apps):
                for dirty, clean in zip(dirty_actions, normalized.action_apps):
                    self.cache.set(dirty, clean)

            return normalized

        except Exception as e:
            # Fallback to dirty names if LLM fails
            print(f"LLM cleaning failed: {e}")
            # Try to return at least what we have from cache
            return NormalizedApps(
                trigger_app=clean_trigger or dirty_trigger,
                action_apps=clean_actions if all_actions_cached else dirty_actions
            )
