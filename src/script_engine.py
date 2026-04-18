import requests
import sys
import os
import time
import re
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL, ACCOUNTS, SCRIPT_GENERATION_PROMPT, MAX_RETRIES
from src.persona_prompts import PERSONA_BRIEFS
from src.similarity_checker import check_script_similarity, get_most_similar_channel
from src.fallback_scripts import get_fallback_script

class ScriptEngine:
    def __init__(self):
        if not GROQ_API_KEY:
            print("[ScriptEngine] WARNING: No GROQ_API_KEY — will use fallback scripts only.")
        self._groq_key = GROQ_API_KEY
        print(f"[ScriptEngine] Initialized with Groq ({GROQ_MODEL}).")

    def _call_llm(self, prompt: str, account_key: str) -> str:
        """Call Groq API (OpenAI-compatible) for text generation."""
        if not self._groq_key:
            print(f"[{account_key}] No Groq API key available!")
            return ""
        
        headers = {
            "Authorization": f"Bearer {self._groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a creative wildlife documentary scriptwriter."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.85,
            "max_tokens": 2048,
        }
        
        last_error = ""
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[{account_key}] Calling Groq ({GROQ_MODEL}, attempt {attempt+1}/{MAX_RETRIES})...")
                response = requests.post(
                    GROQ_BASE_URL, headers=headers, json=payload, timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    if text:
                        return text
                    else:
                        print(f"[{account_key}] Groq returned empty content")
                        last_error = "Empty response"
                elif response.status_code == 429:
                    # Rate limited — wait and retry
                    retry_after = int(response.headers.get("retry-after", "10"))
                    print(f"[{account_key}] Groq rate limited (429), waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code in [401, 403]:
                    err = response.text[:200]
                    print(f"[{account_key}] Groq AUTH error ({response.status_code}): {err}")
                    last_error = f"Auth error: {err}"
                    break  # Don't retry auth errors
                else:
                    err = response.text[:200]
                    print(f"[{account_key}] Groq error ({response.status_code}): {err}")
                    last_error = err
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                        continue
                    
            except requests.exceptions.RequestException as e:
                print(f"[{account_key}] Groq request error: {e}")
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                    continue
        
        print(f"[{account_key}] FINAL FAILURE: Groq exhausted. Last error: {last_error[:300]}")
        return ""

    def generate_script(self, topic_info: str, account_key: str, force_mashup: bool = False) -> tuple:
        """
        Generate a video script for the given topic and account.
        Returns (script_text, was_fallback: bool)
        """
        persona = PERSONA_BRIEFS.get(account_key, "")
        full_prompt = SCRIPT_GENERATION_PROMPT.replace("{topic}", topic_info).replace("{persona}", persona)
        
        if force_mashup:
            print(f"[{account_key}] Force mashup requested — generating unique mashup script")
            result = ""
        else:
            result = self._call_llm(full_prompt, account_key)

        if result:
            # Clean up any markdown formatting
            result = re.sub(r'^```[\w]*\n?', '', result, flags=re.MULTILINE)
            result = re.sub(r'\n?```$', '', result, flags=re.MULTILINE)
            return result.strip(), False
        else:
            # Fallback to template scripts
            print(f"[{account_key}] Groq unavailable — using FALLBACK SCRIPT TEMPLATE")
            fallback = get_fallback_script(topic_info, account_key)
            return fallback, True

    def generate_with_dedup(self, topic_info: str, account_key: str, 
                           existing_scripts: dict = None, force_mashup: bool = False) -> tuple:
        """Generate script and check for duplicates against other channels."""
        script, was_fallback = self.generate_script(topic_info, account_key, force_mashup)
        
        if existing_scripts and not was_fallback:
            similarity, similar_to = check_script_similarity(script, existing_scripts)
            if similarity > 0.85:
                print(f"[{account_key}] Script too similar to {similar_to} ({similarity:.0%})")
                # Regenerate with temperature boost hint
                script2, was_fb2 = self.generate_script(topic_info, account_key)
                if script2 and not was_fb2:
                    script = script2
                    was_fallback = was_fb2
        
        return script, was_fallback

if __name__ == "__main__":
    pass
