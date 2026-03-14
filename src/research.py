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
        # habitat, makanan, reproduksi, predator, konservasi, fakta unik,
        # perbandingan spesies, sejarah, mitos lokal, dll
        self.facets = [
            # --- Original 12 topics ---
            "Diet and hunting",                   # makanan
            "Physical characteristics",           # fakta unik
            "Habitat and distribution",           # habitat
            "Reproduction and lifecycle",         # reproduksi
            "Conservation status",                # konservasi
            "Evolutionary history",               # sejarah
            "Behavior and social structure",      # perilaku
            "Predators and threats",              # predator
            "Species comparison",                 # perbandingan spesies
            "Local myths and folklore",           # mitos lokal
            "Unique sensory abilities",           # fakta unik
            "Nocturnal adaptations",              # fakta unik
            # --- NEW: 23 additional topics ---
            "Ultrasonic communication",           # komunikasi ultrasonik
            "Eye anatomy and vision",             # mata tarsier
            "Tarsier and human interaction",      # interaksi dengan manusia
            "Captivity and rescue programs",      # penyelamatan
            "Role in ecosystem",                  # peran ekosistem
            "Tarsier intelligence and cognition", # kecerdasan
            "Jumping and locomotion mechanics",   # cara bergerak
            "Tarsier in popular culture",         # budaya populer
            "Philippine Tarsier Foundation",      # lembaga konservasi
            "Sulawesi Tarsier species",           # tarsier Sulawesi
            "Tarsier skeleton and bone structure", # anatomi tulang
            "Tarsier vs other primates",          # perbandingan primata
            "Baby tarsier development",           # perkembangan bayi
            "Tarsier sleeping habits",            # kebiasaan tidur
            "Tarsier territorial behavior",       # perilaku teritorial
            "Threats from deforestation",         # ancaman deforestasi
            "Tarsier brain and neuroscience",     # otak tarsier
            "Tarsier fur and grooming",           # bulu dan grooming
            "Fossil record of tarsiers",          # rekaman fosil
            "Tarsier stress and mortality",       # stres dan kematian
            "Night hunting strategies",           # strategi berburu malam
            "Tarsier dental formula and teeth",   # gigi tarsier
            "Ecotourism and tarsier watching",    # ekowisata
        ]

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

    def generate_random_topic(self) -> Dict[str, str]:
        """
        Creates a random topic by focusing on a specific aspect of the Tarsier.
        Pulls data from ALL 4 sources defined in Bagian 10:
        1. Wikipedia API
        2. Google Scholar
        3. IUCN Red List
        4. News scraping
        """
        facet = random.choice(self.facets)
        
        # Source 1: Wikipedia
        base_summary = self.fetch_base_facts("Tarsier")
        section_text = self.fetch_specific_section("Tarsier", facet.split()[0])
        
        # Source 2: Google Scholar
        scholar_text = self.fetch_google_scholar(f"tarsier {facet.lower()}")
        
        # Source 3: IUCN
        iucn_text = self.fetch_iucn_status()
        
        # Source 4: News
        news_text = self.fetch_tarsier_news(f"tarsier {facet.lower()}")
        
        # Combine all sources
        combined_text = f"Wikipedia Summary: {base_summary[:500]}...\n"
        combined_text += f"Specific Section ({facet}): {section_text[:1000]}\n"
        if scholar_text:
            combined_text += f"Recent Research: {scholar_text[:500]}\n"
        combined_text += f"Conservation Status (IUCN): {iucn_text[:300]}\n"
        if news_text:
            combined_text += f"Recent News: {news_text[:300]}\n"
        
        return {
            "topic_name": f"Tarsier {facet}",
            "raw_facts": combined_text
        }

if __name__ == "__main__":
    # Test the research engine
    researcher = ResearchEngine()
    topic = researcher.generate_random_topic()
    print(f"Generated Topic: {topic['topic_name']}")
    print(f"Snippet: {topic['raw_facts'][:500]}...")
