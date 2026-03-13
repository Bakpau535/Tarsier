from google import genai
import sys
import os
import time
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GEMINI_API_KEYS, ACCOUNTS, SCRIPT_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import PERSONA_BRIEFS
from src.similarity_checker import check_script_similarity, get_most_similar_channel

class ScriptEngine:
    def __init__(self):
        if not GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        self.clients = [genai.Client(api_key=k) for k in GEMINI_API_KEYS]
        self.current_key_index = 0
        self.model = "gemini-2.5-flash"
        print(f"[ScriptEngine] Initialized with {len(self.clients)} Gemini API key(s).")

    def _rotate_key(self):
        """Rotate to next API key round-robin."""
        self.current_key_index = (self.current_key_index + 1) % len(self.clients)
        print(f"[ScriptEngine] Rotated to Gemini key #{self.current_key_index + 1}")

    def _call_gemini(self, prompt: str, account_key: str) -> str:
        """Gemini API call with key rotation and retry logic."""
        keys_tried = 0
        total_keys = len(self.clients)
        last_error = ""

        for attempt in range(MAX_RETRIES * total_keys):
            client = self.clients[self.current_key_index]
            try:
                print(f"[{account_key}] Calling Gemini (key #{self.current_key_index + 1}, attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
                else:
                    print(f"[{account_key}] Gemini returned empty response (key #{self.current_key_index + 1})")
                    last_error = "Empty response from Gemini"
                    self._rotate_key()
                    continue

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                print(f"[{account_key}] Gemini error (key #{self.current_key_index + 1}): {error_msg[:200]}")

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    keys_tried += 1
                    if keys_tried < total_keys:
                        print(f"[{account_key}] Key #{self.current_key_index + 1} rate limited. Rotating...")
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
                    print(f"[{account_key}] Non-rate-limit error: {error_msg[:300]}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                    continue

        print(f"[{account_key}] FINAL FAILURE: All {MAX_RETRIES * total_keys} attempts failed. Last error: {last_error[:300]}")
        return ""

    def generate_script(self, topic_info: str, account_key: str) -> str:
        """
        Generates a narration script using the channel's UNIQUE persona brief.
        Each channel gets a completely different structure, tone, and style.
        """
        if account_key not in ACCOUNTS:
            raise ValueError(f"Account key '{account_key}' is invalid.")

        # Get the full persona brief for this channel
        persona_brief = PERSONA_BRIEFS.get(account_key, "")
        if not persona_brief:
            print(f"[{account_key}] WARNING: No persona brief found, using generic prompt")
            persona_brief = f"Write a script about Tarsiers in the style: {ACCOUNTS[account_key]['concept']}"

        # Use .replace() instead of .format() to avoid crashes from curly braces in persona text
        prompt = SCRIPT_GENERATION_PROMPT.replace("{persona_brief}", persona_brief).replace("{topic}", topic_info)

        result = self._call_gemini(prompt, account_key)
        if result:
            print(f"[{account_key}] Script generated ({len(result)} chars).")
        else:
            print(f"[{account_key}] ERROR: Script generation returned empty. Check Gemini API keys.")
        return result

    def generate_all_styles(self, raw_facts: str) -> dict:
        """
        Generates 6 different scripts — one per channel — then checks similarity.
        If any pair exceeds 40% similarity, the most generic one is regenerated.
        Max 3 similarity retries before accepting.
        """
        scripts = {}
        for account_key in ACCOUNTS.keys():
            print(f"Generating script for {account_key}...")
            script = self.generate_script(raw_facts, account_key)
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
            scripts[worst_channel] = self.generate_script(raw_facts, worst_channel)
        
        return scripts

if __name__ == "__main__":
    engine = ScriptEngine()
    test_facts = "Tarsiers have enormous eyes; each eyeball is approximately the same volume as its entire brain."
    print("Testing Documenter Generation:")
    print(engine.generate_script(test_facts, "yt_documenter"))

