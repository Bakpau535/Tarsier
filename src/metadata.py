import os
import json
import time
import re
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL, METADATA_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import METADATA_TITLE_PROMPTS

class MetadataGenerator:
    def __init__(self, dedicated_keys: list = None):
        """Initialize with Groq API key.
        
        Args:
            dedicated_keys: Ignored (kept for backward compatibility with monitoring).
        """
        self._groq_key = GROQ_API_KEY
        if not self._groq_key:
            print("[MetadataGen] WARNING: No GROQ_API_KEY — will use fallback metadata.")
        print(f"[MetadataGen] Initialized with Groq ({GROQ_MODEL}).")

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
        """Uses Groq (Llama 3.3) to generate SEO metadata."""
        print(f"[{account_key}] Generating metadata...")
        
        if not self._groq_key:
            print(f"[{account_key}] No Groq key for metadata — using fallback")
            return self._fallback_metadata(script)
        
        title_formula = METADATA_TITLE_PROMPTS.get(account_key, "")
        prompt = METADATA_GENERATION_PROMPT.replace("{script}", script).replace("{title_formula}", title_formula)
        
        headers = {
            "Authorization": f"Bearer {self._groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are an SEO expert for YouTube wildlife content. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    GROQ_BASE_URL, headers=headers, json=payload, timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    metadata = json.loads(text)
                    print(f"[INFO] [{account_key}] Metadata generated: {metadata.get('title', 'N/A')}")
                    return metadata
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "10"))
                    print(f"[{account_key}] Groq rate limited for metadata, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code in [401, 403]:
                    print(f"[{account_key}] Groq AUTH error for metadata ({response.status_code})")
                    break
                else:
                    err = response.text[:200]
                    print(f"[{account_key}] Groq metadata error ({response.status_code}): {err}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                        continue
                    
            except json.JSONDecodeError as e:
                print(f"[{account_key}] Error parsing Groq metadata JSON: {e}")
                return self._fallback_metadata(script)
                
            except requests.exceptions.RequestException as e:
                print(f"[{account_key}] Groq metadata request error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                    continue
        
        return self._fallback_metadata(script)

if __name__ == "__main__":
    pass
