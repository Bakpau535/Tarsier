import requests
import sys
import os
import time
import re
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL,
                         GEMINI_API_KEY, ACCOUNTS, SCRIPT_GENERATION_PROMPT, MAX_RETRIES)
from src.persona_prompts import PERSONA_BRIEFS
from src.similarity_checker import check_script_similarity, get_most_similar_channel
from src.fallback_scripts import get_fallback_script

class ScriptEngine:
    def __init__(self):
        self._gemini_key = GEMINI_API_KEY
        self._groq_key = GROQ_API_KEY
        self._gemini_blocked = False  # Track if Gemini is permanently blocked
        
        if self._gemini_key:
            print(f"[ScriptEngine] PRIMARY: Gemini 2.5 Flash (key: {self._gemini_key[:12]}...)")
        if self._groq_key:
            print(f"[ScriptEngine] BACKUP: Groq ({GROQ_MODEL})")
        if not self._gemini_key and not self._groq_key:
            print("[ScriptEngine] WARNING: No API keys — will use fallback scripts only.")

    def _call_gemini(self, prompt: str, account_key: str) -> str:
        """Call Gemini API (primary provider)."""
        if not self._gemini_key or self._gemini_blocked:
            return ""
        
        try:
            from google import genai
            client = genai.Client(api_key=self._gemini_key)
            
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"[{account_key}] Calling Gemini (attempt {attempt+1}/{MAX_RETRIES})...")
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    if response and response.text:
                        print(f"[{account_key}] Gemini SUCCESS")
                        return response.text.strip()
                    else:
                        print(f"[{account_key}] Gemini returned empty response")
                        return ""
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                        self._gemini_blocked = True
                        print(f"[{account_key}] Gemini BLOCKED (403) — switching to Groq backup")
                        return ""
                    elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        print(f"[{account_key}] Gemini rate limited, waiting 10s...")
                        time.sleep(10)
                        continue
                    else:
                        print(f"[{account_key}] Gemini error: {error_msg[:200]}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(5)
                        continue
        except ImportError:
            print(f"[{account_key}] google-genai not installed — skipping Gemini")
            self._gemini_blocked = True
        
        return ""

    def _call_groq(self, prompt: str, account_key: str) -> str:
        """Call Groq API (backup provider)."""
        if not self._groq_key:
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
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[{account_key}] Calling Groq backup ({GROQ_MODEL}, attempt {attempt+1}/{MAX_RETRIES})...")
                response = requests.post(
                    GROQ_BASE_URL, headers=headers, json=payload, timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    if text:
                        print(f"[{account_key}] Groq SUCCESS")
                        return text
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "10"))
                    print(f"[{account_key}] Groq rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"[{account_key}] Groq error ({response.status_code}): {response.text[:200]}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f"[{account_key}] Groq request error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
        return ""

    def _call_llm(self, prompt: str, account_key: str) -> str:
        """Try Gemini first (primary), then Groq (backup)."""
        # PRIMARY: Gemini
        result = self._call_gemini(prompt, account_key)
        if result:
            return result
        
        # BACKUP: Groq
        result = self._call_groq(prompt, account_key)
        if result:
            return result
        
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
            return result.strip(), None
        else:
            # Fallback to template scripts
            print(f"[{account_key}] All LLMs unavailable — using FALLBACK SCRIPT TEMPLATE")
            fallback_script, template_id = get_fallback_script(account_key, topic_info, force_mashup=force_mashup)
            return fallback_script, template_id

    def generate_with_dedup(self, topic_info: str, account_key: str, 
                           existing_scripts: dict = None, force_mashup: bool = False) -> tuple:
        """Generate script and check for duplicates against other channels."""
        script, was_fallback = self.generate_script(topic_info, account_key, force_mashup)
        
        if existing_scripts and not was_fallback:
            similarity, similar_to = check_script_similarity(script, existing_scripts)
            if similarity > 0.85:
                print(f"[{account_key}] Script too similar to {similar_to} ({similarity:.0%})")
                script2, was_fb2 = self.generate_script(topic_info, account_key)
                if script2 and not was_fb2:
                    script = script2
                    was_fallback = was_fb2
        
        return script, was_fallback

if __name__ == "__main__":
    pass
