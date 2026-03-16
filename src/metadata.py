import os
import json
import time
import re
from google import genai

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GEMINI_API_KEYS, GEMINI_KEY_MAP, GEMINI_KEY_MAP_BACKUP, METADATA_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import METADATA_TITLE_PROMPTS

class MetadataGenerator:
    def __init__(self):
        if not GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        self._key_to_client = {}
        for k in GEMINI_API_KEYS:
            if k and k not in self._key_to_client:
                self._key_to_client[k] = genai.Client(api_key=k)
        # Also add backup keys to client pool
        for k in GEMINI_KEY_MAP_BACKUP.values():
            if k and k not in self._key_to_client:
                self._key_to_client[k] = genai.Client(api_key=k)
        self._depleted_keys = set()
        print(f"[MetadataGen] Initialized with {len(self._key_to_client)} unique Gemini API key(s).")

    def _get_key_pool(self, account_key: str) -> list:
        """Get Gemini keys for this channel ONLY — 2 dedicated keys, NO cross-channel borrowing."""
        own_key = GEMINI_KEY_MAP.get(account_key, "")
        own_backup = GEMINI_KEY_MAP_BACKUP.get(account_key, "")
        pool = []
        if own_key and own_key not in self._depleted_keys:
            pool.append(own_key)
        if own_backup and own_backup not in self._depleted_keys and own_backup not in pool:
            pool.append(own_backup)
        return pool

    def _fallback_metadata(self, script: str) -> dict:
        return {
            "title": "Tarsier Facts",
            "description": script[:500],
            "hashtags": ["#tarsier", "#nature", "#wildlife", "#conservation", "#animals"],
            "tags": ["tarsier", "animal", "wildlife", "nature", "primate",
                     "conservation", "endangered", "nocturnal", "southeast asia", "documentary"],
            "category": "Pets & Animals",
            "language": "en"
        }

    def generate(self, script: str, account_key: str) -> dict:
        """Uses Gemini with per-channel key assignment to generate SEO metadata."""
        print(f"[{account_key}] Generating metadata...")
        title_formula = METADATA_TITLE_PROMPTS.get(account_key, "")
        prompt = METADATA_GENERATION_PROMPT.replace("{script}", script).replace("{title_formula}", title_formula)
        
        key_pool = self._get_key_pool(account_key)
        if not key_pool:
            print(f"[{account_key}] ALL Gemini keys depleted for metadata!")
            return self._fallback_metadata(script)

        for key in key_pool:
            client = self._key_to_client.get(key)
            if not client:
                continue
            
            is_own = key == GEMINI_KEY_MAP.get(account_key, "")
            key_type = "own" if is_own else "backup"
            
            for attempt in range(MAX_RETRIES):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )
                    metadata = json.loads(response.text)
                    return metadata

                except json.JSONDecodeError as e:
                    print(f"Error parsing Gemini metadata JSON: {e}")
                    return self._fallback_metadata(script)

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        self._depleted_keys.add(key)
                        print(f"[{account_key}] {key_type} key EXHAUSTED for metadata, trying next...")
                        break  # Move to next key
                    else:
                        print(f"Error calling Gemini for metadata: {e}")
                        return self._fallback_metadata(script)

        return self._fallback_metadata(script)

if __name__ == "__main__":
    pass
