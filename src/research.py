import wikipediaapi
import requests
import random
from typing import List, Dict
from bs4 import BeautifulSoup

class ResearchEngine:
    def __init__(self, user_agent: str = "TarsierBot/1.0 (contact@example.com)"):
        # --- Sumber 1: Wikipedia API → fakta dasar tarsier (Bagian 10) ---
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=user_agent,
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        
        # --- Variasi topik tersedia (Bagian 11) ---
        self.facets = [
            "Diet and hunting",
            "Physical characteristics",
            "Habitat and distribution",
            "Reproduction and lifecycle",
            "Conservation status",
            "Evolutionary history",
            "Behavior and social structure",
            "Predators and threats",
            "Species comparison",
            "Local myths and folklore",
            "Unique sensory abilities",
            "Nocturnal adaptations",
            "Ultrasonic communication",
            "Eye anatomy and vision",
            "Tarsier and human interaction",
            "Captivity and rescue programs",
            "Role in ecosystem",
            "Tarsier intelligence and cognition",
            "Jumping and locomotion mechanics",
            "Tarsier in popular culture",
            "Philippine Tarsier Foundation",
            "Sulawesi Tarsier species",
            "Tarsier skeleton and bone structure",
            "Tarsier vs other primates",
            "Baby tarsier development",
            "Tarsier sleeping habits",
            "Tarsier territorial behavior",
            "Threats from deforestation",
            "Tarsier brain and neuroscience",
            "Tarsier fur and grooming",
            "Fossil record of tarsiers",
            "Tarsier stress and mortality",
            "Night hunting strategies",
            "Tarsier dental formula and teeth",
            "Ecotourism and tarsier watching",
        ]
        
        # === THEME BANK (Blueprint Section 9) ===
        # Each video combines a FACET (fact topic) + THEME (emotional angle)
        # This creates unique content angles and prevents repetition
        self.theme_bank = {
            "emotion": [
                "loneliness", "exhaustion", "fear", "hope",
                "determination", "grief", "wonder", "anxiety",
                "peace", "rage", "nostalgia", "resilience",
            ],
            "situation": [
                "nighttime alone in the forest", "rainy season survival",
                "first time leaving the nest", "encounter with a predator",
                "searching for food in silence", "being separated from family",
                "discovering a new territory", "hiding from danger",
                "a mother protecting her baby", "the last one of its kind",
            ],
            "relatable": [
                "working overtime with no reward", "Monday morning energy",
                "overthinking at 3am", "pretending everything is fine",
                "that one friend who never shows up", "social anxiety",
                "trying to adult but failing", "procrastination master",
                "when the wifi goes down", "resting face that scares people",
            ],
            "fact": [
                "eyes bigger than brain", "nocturnal hunter",
                "360 degree head rotation", "ultrasonic communication",
                "suicide in captivity", "smallest primate in the world",
                "55 million years of evolution", "each eye weighs more than brain",
                "can jump 40x body length", "only fully carnivorous primate",
            ],
        }

    # --- Sumber 1: Wikipedia API → fakta dasar tarsier ---
    def fetch_base_facts(self, target_page: str = "Tarsier") -> str:
        """Fetches the summary from a Wikipedia page."""
        try:
            page = self.wiki.page(target_page)
            if not page.exists():
                return "Facts could not be found."
            return page.summary
        except Exception as e:
            print(f"Wikipedia fetch error: {e}")
            return "Facts could not be fetched due to a network error."

    def fetch_specific_section(self, target_page: str, section_keyword: str) -> str:
        """Fetches a specific section containing a keyword."""
        try:
            page = self.wiki.page(target_page)
            if not page.exists():
                return ""
            for section in page.sections:
                if section_keyword.lower() in section.title.lower():
                    return section.text
        except Exception as e:
            print(f"Wikipedia section fetch error: {e}")
        return ""

    # --- Sumber 2: Google Scholar → penelitian terbaru (Bagian 10) ---
    def fetch_google_scholar(self, query: str = "tarsier research") -> str:
        """
        Scrapes Google Scholar for recent tarsier research snippets.
        Uses BeautifulSoup for HTML parsing.
        """
        try:
            url = "https://scholar.google.com/scholar"
            params = {"q": query, "hl": "en", "as_sdt": "0,5"}
            headers = {"User-Agent": "TarsierBot/1.0"}
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Google Scholar returned status {response.status_code}")
                return ""
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for item in soup.select(".gs_ri")[:3]:  # Top 3 results
                title_tag = item.select_one(".gs_rt")
                snippet_tag = item.select_one(".gs_rs")
                if title_tag and snippet_tag:
                    results.append(f"- {title_tag.get_text()}: {snippet_tag.get_text()}")
            
            return "\n".join(results) if results else ""
        except Exception as e:
            print(f"Google Scholar scraping error: {e}")
            return ""

    # --- Sumber 3: IUCN Red List API → data status kepunahan terbaru (Bagian 10) ---
    def fetch_iucn_status(self) -> str:
        """
        Fetches tarsier conservation data from IUCN Red List API.
        Falls back to static data if API key is unavailable or request fails.
        """
        try:
            # IUCN API requires a token; attempt the request
            iucn_token = ""  # User can set IUCN_API_TOKEN in .env later
            if iucn_token:
                url = f"https://apiv3.iucnredlist.org/api/v3/species/Tarsius/assessments?token={iucn_token}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result"):
                        return str(data["result"][0])
            
            # Fallback: static IUCN data
            return (
                "Tarsiers are classified under varying threat levels by the IUCN Red List. "
                "The Philippine tarsier (Carlito syrichta) is listed as Near Threatened. "
                "The Siau Island tarsier (Tarsius tumpara) is Critically Endangered. "
                "Western tarsier (Cephalopachus bancanus) is Vulnerable. "
                "Habitat loss from deforestation and agricultural expansion is the primary threat across all species. "
                "Illegal pet trade further threatens wild populations."
            )
        except Exception as e:
            print(f"IUCN fetch error: {e}")
            return "Tarsiers are mostly classified as Vulnerable to Endangered due to habitat loss and fragmentation across Southeast Asia."

    # --- Sumber 4: News scraping → berita tarsier terkini (Bagian 10) ---
    def fetch_tarsier_news(self, query: str = "tarsier conservation news") -> str:
        """
        Scrapes recent news articles about tarsiers using web search.
        Uses BeautifulSoup for parsing.
        """
        try:
            url = "https://www.google.com/search"
            params = {"q": query, "tbm": "nws", "hl": "en"}
            headers = {"User-Agent": "TarsierBot/1.0"}
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"News search returned status {response.status_code}")
                return ""
            
            soup = BeautifulSoup(response.text, "html.parser")
            headlines = []
            for item in soup.select("div.BNeawe")[:5]:
                text = item.get_text().strip()
                if text and len(text) > 20:
                    headlines.append(f"- {text}")
            
            return "\n".join(headlines) if headlines else ""
        except Exception as e:
            print(f"News scraping error: {e}")
            return ""

    # Per-channel theme category preference — matches channel personality
    CHANNEL_THEMES = {
        "yt_documenter": ["fact", "situation"],              # NatGeo: facts + natural situations
        "yt_funny":      ["relatable", "fact"],              # Comedy: relatable humor + fun facts
        "yt_anthro":     ["emotion", "relatable"],           # Storytelling: emotions + relatable
        "yt_pov":        ["emotion", "situation"],           # Horror/immersive: dark emotion + tense situations
        "yt_drama":      ["emotion", "situation"],           # Dramatic: heavy emotion + dramatic situations
        "fb_fanspage":   ["fact", "relatable", "emotion"],   # Engagement: mix of all
    }

    def generate_random_topic(self, account_key: str = None) -> Dict[str, str]:
        """
        V2: Creates topic by combining FACET (fact) + THEME (emotional angle).
        Per-channel theme preference ensures each channel gets matching themes.
        35 facets × 42 themes = 1,470 unique combinations.
        """
        facet = random.choice(self.facets)
        
        # Pick theme category based on channel preference
        if account_key and account_key in self.CHANNEL_THEMES:
            theme_category = random.choice(self.CHANNEL_THEMES[account_key])
        else:
            theme_category = random.choice(list(self.theme_bank.keys()))
        theme = random.choice(self.theme_bank[theme_category])
        
        # Source 1: Wikipedia
        section_text = ""
        facet_words = facet.lower().split()
        for keyword in facet_words:
            if len(keyword) > 3:
                section_text = self.fetch_specific_section("Tarsier", keyword)
                if section_text:
                    break
        
        if not section_text:
            for alt_page in ["Philippine tarsier", "Tarsiidae", "Tarsier"]:
                for keyword in facet_words:
                    if len(keyword) > 3:
                        section_text = self.fetch_specific_section(alt_page, keyword)
                        if section_text:
                            break
                if section_text:
                    break
        
        base_summary = self.fetch_base_facts("Tarsier")
        
        # Source 2: Google Scholar
        scholar_text = self.fetch_google_scholar(f"tarsier {facet.lower()}")
        
        # Source 3: IUCN
        iucn_text = self.fetch_iucn_status()
        
        # Source 4: News
        news_text = self.fetch_tarsier_news(f"tarsier {facet.lower()}")
        
        # BUILD raw_facts — FACET + THEME front-loaded
        combined_text = f"MAIN TOPIC: {facet.upper()}\n"
        combined_text += f"EMOTIONAL THEME: {theme} (category: {theme_category})\n"
        combined_text += f"You MUST write about '{facet}' through the lens of '{theme}'.\n"
        combined_text += f"The emotional angle '{theme}' should color every sentence.\n\n"
        
        if section_text:
            combined_text += f"Topic Research ({facet}):\n{section_text[:1000]}\n\n"
        
        if scholar_text:
            combined_text += f"Recent Research on {facet}:\n{scholar_text[:500]}\n\n"
        
        combined_text += f"Background: {base_summary[:200]}...\n"
        combined_text += f"Conservation: {iucn_text[:200]}\n"
        
        if news_text:
            combined_text += f"News: {news_text[:300]}\n"
        
        topic_name = f"Tarsier {facet} x {theme}"
        
        return {
            "topic_name": topic_name,
            "raw_facts": combined_text,
            "theme": theme,
            "theme_category": theme_category,
        }

if __name__ == "__main__":
    # Test the research engine
    researcher = ResearchEngine()
    topic = researcher.generate_random_topic()
    print(f"Generated Topic: {topic['topic_name']}")
    print(f"Snippet: {topic['raw_facts'][:500]}...")
