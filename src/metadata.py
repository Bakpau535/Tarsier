import os
import json
import time
import re
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL,
                         GEMINI_API_KEY, METADATA_GENERATION_PROMPT, MAX_RETRIES)
from src.persona_prompts import METADATA_TITLE_PROMPTS

class MetadataGenerator:
    def __init__(self, dedicated_keys: list = None):
        """Initialize with Gemini (primary) + Groq (backup).
        
        Args:
            dedicated_keys: Optional dedicated Gemini keys (for monitoring).
        """
        # Use dedicated keys if provided, else use global GEMINI_API_KEY
        if dedicated_keys and any(dedicated_keys):
            self._gemini_key = next((k for k in dedicated_keys if k), "")
        else:
            self._gemini_key = GEMINI_API_KEY
        self._groq_key = GROQ_API_KEY
        self._gemini_blocked = False
        
        provider = "Gemini+Groq" if self._gemini_key else "Groq only"
        print(f"[MetadataGen] Initialized ({provider}).")

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

    def _call_gemini(self, prompt: str, account_key: str) -> dict:
        """Try Gemini for metadata (returns dict or None)."""
        if not self._gemini_key or self._gemini_blocked:
            return None
        try:
            from google import genai
            client = genai.Client(api_key=self._gemini_key)
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
                    print(f"[{account_key}] Gemini metadata SUCCESS")
                    return metadata
                except json.JSONDecodeError:
                    return None
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                        self._gemini_blocked = True
                        print(f"[{account_key}] Gemini metadata BLOCKED (403)")
                        return None
                    elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        time.sleep(10)
                        continue
                    else:
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(5)
                        continue
        except ImportError:
            self._gemini_blocked = True
        return None

    def _call_groq(self, prompt: str, account_key: str) -> dict:
        """Try Groq for metadata (returns dict or None)."""
        if not self._groq_key:
            return None
        
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
                print(f"[{account_key}] Calling Groq backup for metadata...")
                response = requests.post(
                    GROQ_BASE_URL, headers=headers, json=payload, timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    metadata = json.loads(text)
                    print(f"[{account_key}] Groq metadata SUCCESS")
                    return metadata
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "10"))
                    time.sleep(retry_after)
                    continue
                else:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
            except (json.JSONDecodeError, requests.exceptions.RequestException) as e:
                print(f"[{account_key}] Groq metadata error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
        return None

    def generate(self, script: str, account_key: str) -> dict:
        """Generate SEO metadata. Gemini primary → Groq backup → fallback."""
        print(f"[{account_key}] Generating metadata...")
        
        title_formula = METADATA_TITLE_PROMPTS.get(account_key, "")
        prompt = METADATA_GENERATION_PROMPT.replace("{script}", script).replace("{title_formula}", title_formula)
        
        # PRIMARY: Gemini
        result = self._call_gemini(prompt, account_key)
        if result:
            print(f"[INFO] [{account_key}] Metadata generated: {result.get('title', 'N/A')}")
            return result
        
        # BACKUP: Groq
        result = self._call_groq(prompt, account_key)
        if result:
            print(f"[INFO] [{account_key}] Metadata generated: {result.get('title', 'N/A')}")
            return result
        
        # FALLBACK: template
        print(f"[{account_key}] All LLMs unavailable for metadata — using fallback")
        return self._fallback_metadata(script)

if __name__ == "__main__":
    pass
