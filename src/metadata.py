import os
import json
import time
import re
from google import genai

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GEMINI_API_KEYS, METADATA_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import METADATA_TITLE_PROMPTS

class MetadataGenerator:
    def __init__(self):
        if not GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        self.clients = [genai.Client(api_key=k) for k in GEMINI_API_KEYS]
        self.current_key_index = 0
        self.model = "gemini-2.5-flash"
        print(f"[MetadataGen] Initialized with {len(self.clients)} Gemini API key(s).")

    def _rotate_key(self):
        """Pindah ke key berikutnya."""
        self.current_key_index = (self.current_key_index + 1) % len(self.clients)
        print(f"[MetadataGen] Rotated to Gemini key #{self.current_key_index + 1}")

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
        """
        Uses Gemini with key rotation to generate SEO optimized metadata.
        Bagian 6: Judul, Deskripsi, Hashtag, Tags, Kategori, Bahasa.
        """
        print(f"[{account_key}] Generating metadata...")
        # Inject per-channel title formula
        title_formula = METADATA_TITLE_PROMPTS.get(account_key, "")
        prompt = METADATA_GENERATION_PROMPT.format(script=script, title_formula=title_formula)
        
        keys_tried = 0
        total_keys = len(self.clients)

        for attempt in range(MAX_RETRIES * total_keys):
            client = self.clients[self.current_key_index]
            try:
                response = client.models.generate_content(
                    model=self.model,
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
                    keys_tried += 1
                    if keys_tried < total_keys:
                        print(f"[{account_key}] Key #{self.current_key_index + 1} rate limited → rotating...")
                        self._rotate_key()
                        continue
                    else:
                        retry_match = re.search(r'retry in (\d+\.?\d*)', error_msg, re.IGNORECASE)
                        wait_secs = float(retry_match.group(1)) + 2 if retry_match else 20
                        print(f"[{account_key}] All keys exhausted. Waiting {wait_secs:.0f}s...")
                        time.sleep(wait_secs)
                        keys_tried = 0
                        self._rotate_key()
                        continue
                else:
                    print(f"Error calling Gemini for metadata: {e}")
                    return self._fallback_metadata(script)

        return self._fallback_metadata(script)

if __name__ == "__main__":
    pass
