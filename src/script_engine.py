from google import genai
import sys
import os
import time
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GEMINI_API_KEYS, GEMINI_KEY_MAP, GEMINI_KEY_MAP_BACKUP, ACCOUNTS, SCRIPT_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import PERSONA_BRIEFS
from src.similarity_checker import check_script_similarity, get_most_similar_channel
from src.fallback_scripts import get_fallback_script

class ScriptEngine:
    def __init__(self):
        if not GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        # Build client pool — one client per unique key
        self._key_to_client = {}
        for k in GEMINI_API_KEYS:
            if k and k not in self._key_to_client:
                self._key_to_client[k] = genai.Client(api_key=k)
        # Also add backup keys to client pool
        for k in GEMINI_KEY_MAP_BACKUP.values():
            if k and k not in self._key_to_client:
                self._key_to_client[k] = genai.Client(api_key=k)
        self._depleted_keys = set()  # Track keys that returned 429
        print(f"[ScriptEngine] Initialized with {len(self._key_to_client)} unique Gemini API key(s).")

    def _get_key_pool(self, account_key: str) -> list:
        """
        Get Gemini keys for this channel ONLY — 2 dedicated keys, NO cross-channel borrowing.
        Priority: own primary → own backup. That's it.
        """
        own_key = GEMINI_KEY_MAP.get(account_key, "")
        own_backup = GEMINI_KEY_MAP_BACKUP.get(account_key, "")
        pool = []
        # Own primary key
        if own_key and own_key not in self._depleted_keys:
            pool.append(own_key)
        # Own backup key
        if own_backup and own_backup not in self._depleted_keys and own_backup not in pool:
            pool.append(own_backup)
        return pool

    def _call_gemini(self, prompt: str, account_key: str) -> str:
        """Gemini API call with per-channel key assignment and fallback pool."""
        key_pool = self._get_key_pool(account_key)
        if not key_pool:
            print(f"[{account_key}] ALL Gemini keys depleted!")
            return ""
        
        last_error = ""
        
        for key in key_pool:
            client = self._key_to_client.get(key)
            if not client:
                continue
            
            key_label = f"key-{list(self._key_to_client.keys()).index(key)+1}"
            is_own = key == GEMINI_KEY_MAP.get(account_key, "")
            key_type = "own" if is_own else "backup"
            
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"[{account_key}] Calling Gemini ({key_type} {key_label}, attempt {attempt+1}/{MAX_RETRIES})...")
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    if response and response.text:
                        return response.text.strip()
                    else:
                        print(f"[{account_key}] Gemini returned empty response ({key_label})")
                        last_error = "Empty response from Gemini"
                        break  # Try next key

                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    print(f"[{account_key}] Gemini error ({key_type} {key_label}): {error_msg[:200]}")

                    if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                        self._depleted_keys.add(key)
                        print(f"[{account_key}] {key_type} {key_label} BLOCKED (403) — permanently dead, trying backup...")
                        break  # Immediately move to next key, no retry
                    elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        self._depleted_keys.add(key)
                        print(f"[{account_key}] {key_type} {key_label} EXHAUSTED, trying backup in 5s...")
                        time.sleep(5)
                        break  # Move to next key in pool
                    else:
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(10)
                        continue

        print(f"[{account_key}] FINAL FAILURE: All keys exhausted. Last error: {last_error[:300]}")
        return ""

    def generate_script(self, topic_info: str, account_key: str, force_mashup: bool = False) -> tuple:
        """
        Generates a narration script using the channel's UNIQUE persona brief.
        Returns: (script_text, template_id)
          - template_id is None when Gemini generates fresh script
          - template_id is stable ID (e.g. 'fb_yt_documenter_3') when fallback used
        RESILIENCE: If ALL Gemini keys fail, uses pre-written fallback templates.
        This method NEVER returns empty — pipeline is guaranteed to continue.
        """
        if account_key not in ACCOUNTS:
            raise ValueError(f"Account key '{account_key}' is invalid.")

        # If force_mashup, skip Gemini entirely — go straight to mashup template
        if force_mashup:
            print(f"[{account_key}] Force mashup requested — generating unique mashup script")
            fallback, template_id = get_fallback_script(account_key, topic_info, force_mashup=True)
            print(f"[{account_key}] Mashup script loaded ({len(fallback)} chars).")
            return fallback, template_id

        # Get the full persona brief for this channel
        persona_brief = PERSONA_BRIEFS.get(account_key, "")
        if not persona_brief:
            print(f"[{account_key}] WARNING: No persona brief found, using generic prompt")
            persona_brief = f"Write a script about Tarsiers in the style: {ACCOUNTS[account_key]['concept']}"

        # Use .replace() instead of .format() to avoid crashes from curly braces in persona text
        prompt = SCRIPT_GENERATION_PROMPT.replace("{persona_brief}", persona_brief).replace("{topic}", topic_info)

        result = self._call_gemini(prompt, account_key)
        if result:
            print(f"[{account_key}] Script generated via Gemini ({len(result)} chars).")
            return result, None  # No template_id for Gemini-generated scripts
        
        # FALLBACK: All Gemini keys exhausted → use pre-written template
        print(f"[{account_key}] Gemini unavailable — using FALLBACK SCRIPT TEMPLATE")
        fallback, template_id = get_fallback_script(account_key, topic_info)
        print(f"[{account_key}] Fallback script loaded ({len(fallback)} chars).")
        return fallback, template_id

    def generate_all_styles(self, raw_facts: str) -> dict:
        """
        Generates 6 different scripts — one per channel — then checks similarity.
        If any pair exceeds 40% similarity, the most generic one is regenerated.
        Max 3 similarity retries before accepting.
        """
        scripts = {}
        for account_key in ACCOUNTS.keys():
            print(f"Generating script for {account_key}...")
            script, _ = self.generate_script(raw_facts, account_key)
            scripts[account_key] = script

        # Similarity check — max 40% between any pair
        for retry in range(3):
            all_ok, violations = check_script_similarity(scripts)
            if all_ok:
                print(f"[ScriptEngine] All scripts sufficiently different!")
                break
            
            # Regenerate the most similar channel's script
            worst_channel = get_most_similar_channel(scripts)
            print(f"[ScriptEngine] Retry {retry+1}/3: Regenerating script for {worst_channel}")
            script, _ = self.generate_script(raw_facts, worst_channel)
            scripts[worst_channel] = script
        
        return scripts

if __name__ == "__main__":
    engine = ScriptEngine()
    test_facts = "Tarsiers have enormous eyes; each eyeball is approximately the same volume as its entire brain."
    print("Testing Documenter Generation:")
    print(engine.generate_script(test_facts, "yt_documenter"))

