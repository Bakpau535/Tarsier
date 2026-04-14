import os
import requests
import time
import random
from typing import Optional, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import HF_API_KEYS, ACCOUNTS, TMP_DIR, MAX_RETRIES, CLIP_DURATION_SEC, FREESOUND_API_KEY, VIDEO_PROFILES, DATA_DIR, CF_ACCOUNTS, CF_ACCOUNTS_BACKUP
from src.ssml_builder import build_ssml, get_edge_tts_params

class MediaGenerator:
    # Path to persistent footage log — tracks EVERY clip/image ever used
    FOOTAGE_LOG_PATH = os.path.join(DATA_DIR, "used_footage.json")
    # Path to persistent music log — tracks EVERY music track ever used
    MUSIC_LOG_PATH = os.path.join(DATA_DIR, "used_music.json")

    def __init__(self):
        import json as _json
        self._json = _json
        HF_BASE = "https://router.huggingface.co/hf-inference/models"
        self.image_model_url = f"{HF_BASE}/black-forest-labs/FLUX.1-schnell"
        self.image_fallback_url = f"{HF_BASE}/stabilityai/stable-diffusion-xl-base-1.0"
        self.pexels_key = os.environ.get("PEXELS_API_KEY", "")
        self.pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
        self._depleted_keys = set()  # Track HF keys that returned 402
        self._depleted_cf = set()   # Track CF accounts that hit quota
        
        # Cloudflare Workers AI model
        self.cf_model = "@cf/black-forest-labs/flux-1-schnell"
        self.cf_fallback_model = "@cf/bytedance/stable-diffusion-xl-lightning"
        
        # Load persistent footage log — HARD RULE: no footage reused EVER
        self._used_footage = self._load_footage_log()
        print(f"[MediaGen] Footage log loaded: {len(self._used_footage)} items already used")
        
        # Load persistent music log — HARD RULE: no music reused
        self._used_music = self._load_music_log()
        print(f"[MediaGen] Music log loaded: {len(self._used_music)} tracks already used")
        
        # === DIAGNOSTIC: Print API key status ===
        cf_count = sum(1 for v in CF_ACCOUNTS.values() if v.get('account_id') and v.get('api_token'))
        print(f"[MediaGen] CF_ACCOUNTS: {cf_count}/6 primary set (Cloudflare Workers AI)")
        print(f"[MediaGen] PEXELS_API_KEY: {'SET (' + self.pexels_key[:8] + '...)' if self.pexels_key else '*** MISSING ***'}")
        print(f"[MediaGen] PIXABAY_API_KEY: {'SET (' + self.pixabay_key[:8] + '...)' if self.pixabay_key else '*** MISSING ***'}")
        hf_count = sum(1 for v in HF_API_KEYS.values() if v)
        print(f"[MediaGen] HF_API_KEYS: {hf_count}/6 keys set (backup for CF)")
        print(f"[MediaGen] ==========================")
        
        # Tarsier-ONLY search terms — STRICT: only terms proven to return real tarsier photos.
        # REMOVED generic compound terms like 'tarsier tree', 'tarsier forest', 'tarsier jungle'
        # because Pexels/Pixabay split these into separate keywords → return monkeys/trees instead.
        self.tarsier_search_terms = [
            "tarsier", "tarsius",
            "philippine tarsier", "bohol tarsier", "sulawesi tarsier",
            "tarsier primate", "tarsier animal",
        ]
        
        # Support/environment search terms — SCENERY ONLY, NO ANIMALS
        # CRITICAL: terms must NOT return videos with monkeys/primates/birds/animals
        # REMOVED: 'tropical birds', 'jungle night', 'indonesia jungle' (return monkey videos)
        # KEPT: water, plants, sky, mist, trees — pure scenery
        self.support_search_terms = [
            "tropical waterfall", "forest stream", "rainforest mist",
            "tropical flowers close up", "mossy tree bark", "forest canopy leaves",
            "tropical rain drops", "jungle fog morning", "fern leaves close up",
            "tropical sunset ocean", "forest path empty", "green moss rocks",
            "tropical river", "bamboo forest", "palm tree wind",
        ]
        
        # Blocked words — reject any support video with these in URL/metadata
        self.support_blocked_words = [
            "monkey", "primate", "ape", "orangutan", "gorilla", "chimpanzee",
            "lemur", "macaque", "baboon", "gibbon", "marmoset",
            "bird", "parrot", "eagle", "owl", "hawk",
            "snake", "lizard", "frog", "spider", "scorpion",
            "cat", "dog", "bear", "tiger", "lion", "elephant",
            "animal", "wildlife", "creature", "pet",
        ]
        
        # Per-account AI prompts
        # 50:50 ratio: tarsier prompts + environment prompts
        # AI PROMPTS: VISUAL DESCRIPTION-FIRST (FLUX/SDXL don't know "tarsier")
        # IMPORTANT: This is about INDONESIAN tarsier (Sulawesi), NOT Philippine!
        # Every prompt MUST lead with visual description of the animal:
        # - Tiny furry primate, fits in human palm, weight only 80-160 grams
        # - ENORMOUS round glowing eyes (each eye bigger than its brain!)
        # - Long thin bony fingers with round disk pads gripping branches
        # - Small round head, large thin bat-like ears
        # - Dark grey-brown fur (Sulawesi species), nocturnal
        # - Very long thin tail (rat-like, mostly naked)
        # - Habitat: Sulawesi tropical rainforest, Indonesia
        self.tarsier_prompts = [
            "tiny furry primate with enormous round glowing golden eyes sitting on a tree branch at night in Indonesian tropical forest, the eyes are each bigger than its brain, small round head, dark grey-brown fur, large thin bat-like ears, macro photography, 4k, shallow depth of field",
            "extreme close up portrait of a small nocturnal primate with gigantic perfectly round amber eyes reflecting moonlight, tiny nose, dark grey-brown soft fur, thin bat ears, Sulawesi rainforest background, detailed texture, wildlife photography masterpiece",
            "adorable tiny monkey-like creature with huge round saucer eyes gripping a thin branch with long slender bony fingers that have round disk-shaped sticky pads, dark brown fur, dense Indonesian tropical forest background, national geographic style",
            "baby primate the size of a human fist with oversized round luminous amber eyes, dark fur, clinging to its mother on a mossy branch in Sulawesi Indonesia jungle, heartwarming wildlife moment, soft warm lighting, cute animal photography",
            "small furry nocturnal animal with the largest eyes relative to body size of any mammal, dark grey-brown fur, large thin ears, perched on a mossy branch in Indonesian rainforest, staring directly at camera with enormous round eyes, macro lens",
            "tiny big-eyed primate with dark fur hunting a grasshopper insect at night in Indonesian jungle, caught mid-leap between branches, motion blur, dynamic wildlife action shot, night vision style photography",
            "portrait of a miniature primate with round head and enormous owl-like golden eyes, thin bat-like ears slightly folded, dark brown fur, sitting quietly on a branch in Sulawesi forest, cinematic bokeh background, 4k photography",
            "two small nocturnal primates with huge glowing amber eyes and dark fur sitting together on a branch at night in Indonesian tropical forest, social bonding behavior, dual portrait, wildlife documentary photography",
            "sleeping tiny primate with dark grey-brown fur and its enormous eyes closed, curled up on a tree branch with its long thin naked tail hanging down, peaceful nighttime scene in Indonesian forest, soft moonlight",
            "small wide-eyed primate with head rotated nearly 180 degrees looking backwards showing enormous perfectly round amber eyes, dark fur, thin ears, eerie and fascinating anatomy, dark jungle background, macro photography",
            "extreme macro of tiny primate hands with very long thin bony fingers and round suction-cup-like disk pads gripping a mossy branch, dark fur on wrists, Indonesian rainforest, detailed biology photography",
            "miniature dark-furred primate silhouette with enormous round glowing eyes against full moon, tropical tree branches, dramatic nocturnal Indonesian wildlife scene, cinematic style",
            "wide-eyed tiny furry primate with surprised expression and comically huge round glowing eyes, dark grey-brown fur, thin ears pointing up, adorable funny animal portrait, bright tropical background, viral photography style",
            "nocturnal primate with giant round amber eyes and dark fur eating a cricket insect while perched on branch in Indonesian Sulawesi jungle at night, close-up of hunting behavior, wildlife research documentation",
            "stunning portrait of tiny primate with galaxy-like reflections in its enormous perfectly round golden eyes, dark grey-brown fur, thin bat ears, Indonesian rainforest background, artistic wildlife photography, vibrant colors",
        ]
        
        # Environment/support prompts — Sulawesi/Indonesia themed
        self.support_prompts = {
            "yt_documenter": [
                "dense tropical rainforest canopy of Sulawesi Indonesia at dawn, misty mountains, scientific expedition atmosphere, national geographic style",
                "Indonesian wildlife sanctuary entrance with tropical trees and conservation signs, Sulawesi jungle path",
            ],
            "yt_funny": [
                "colorful tropical jungle with funny tiny props, whimsical playful atmosphere, Indonesian forest",
                "bright cheerful forest clearing with miniature furniture, comedy set design, tropical setting",
            ],
            "yt_anthro": [
                "miniature office desk with tiny furniture, coffee cup, warm cozy lighting, whimsical scene",
                "tiny kitchen scene with miniature cooking utensils, warm homey atmosphere, storybook",
            ],
            "yt_pov": [
                "dark hollow tree interior looking out at moonlit Indonesian jungle, atmospheric night, no animals",
                "dense Sulawesi jungle canopy at night with glowing fireflies, cinematic night photography",
            ],
            "yt_drama": [
                "dead tree branch at sunset in Indonesian forest, dramatic golden hour lighting, cinematic wide shot",
                "misty Sulawesi forest path disappearing into darkness, emotional cinematic atmosphere",
            ],
            "fb_fanspage": [
                "lush green tropical rainforest of Sulawesi Indonesia, vibrant nature, shareable scenic photo",
                "Indonesian wildlife conservation center entrance with tropical trees, hopeful atmosphere",
            ],
        }

    def _get_headers(self, account_key: str) -> dict:
        """Each account uses its OWN HF API key."""
        api_key = HF_API_KEYS.get(account_key)
        if not api_key:
            raise ValueError(f"HF API Key missing for {account_key}")
        return {"Authorization": f"Bearer {api_key}"}

    def _get_key_pool(self, account_key: str) -> list:
        """
        Get HF API keys for this channel ONLY — 2 dedicated keys, NO cross-channel borrowing.
        Priority: own primary → own backup. That's it.
        """
        from src.config import HF_API_KEYS_BACKUP
        pool = []
        # Own primary key
        own_key = HF_API_KEYS.get(account_key, "")
        if own_key and own_key not in self._depleted_keys:
            pool.append(own_key)
        # Own backup key
        own_backup = HF_API_KEYS_BACKUP.get(account_key, "")
        if own_backup and own_backup not in self._depleted_keys and own_backup not in pool:
            pool.append(own_backup)
        return pool

    def _make_api_request(self, url: str, headers: dict, payload: dict,
                          max_retries: int = MAX_RETRIES, timeout: int = 120) -> Optional[bytes]:
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"API Error ({response.status_code}): {response.text[:200]}")
                    if response.status_code == 503 and "estimated_time" in response.text:
                        wait = min(response.json().get("estimated_time", 20), 60)
                        time.sleep(wait)
                        continue
                    if response.status_code in [402]:
                        # Mark this specific key as depleted
                        auth = headers.get("Authorization", "")
                        key = auth.replace("Bearer ", "") if auth else ""
                        if key:
                            self._depleted_keys.add(key)
                        print(f"HF KEY DEPLETED (402) — marked as exhausted, will try backup keys")
                        return None
                    if response.status_code in [410, 404]:
                        return None
                    if response.status_code in [429, 500, 502, 503]:
                        wait = min(60, 15 * (attempt + 1))
                        time.sleep(wait)
                        continue
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
            time.sleep(5)
        return None

    def _safe_topic(self, topic: str) -> str:
        return "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]

    # ==========================================
    # FOOTAGE DEDUPLICATION — ALL footage NEVER reused:
    # Tarsier clips, support clips, photos, music
    # All tracked in used_footage.json / used_music.json
    # ==========================================

    def _load_footage_log(self) -> set:
        """Load persistent set of ALL used footage IDs."""
        try:
            if os.path.exists(self.FOOTAGE_LOG_PATH):
                with open(self.FOOTAGE_LOG_PATH, "r") as f:
                    data = self._json.load(f)
                return set(data)
        except Exception as e:
            print(f"[MediaGen] Warning: Could not load footage log: {e}")
        return set()

    def _save_footage_log(self):
        """Save updated footage log to disk."""
        try:
            with open(self.FOOTAGE_LOG_PATH, "w") as f:
                self._json.dump(sorted(list(self._used_footage)), f, indent=2)
        except Exception as e:
            print(f"[MediaGen] Warning: Could not save footage log: {e}")

    def _load_music_log(self) -> set:
        """Load set of previously used music track IDs/URLs."""
        try:
            if os.path.exists(self.MUSIC_LOG_PATH):
                with open(self.MUSIC_LOG_PATH, "r") as f:
                    return set(self._json.load(f))
        except Exception as e:
            print(f"[MediaGen] Warning: Could not load music log: {e}")
        return set()

    def _save_music_log(self):
        """Save updated music log to disk."""
        try:
            with open(self.MUSIC_LOG_PATH, "w") as f:
                self._json.dump(sorted(list(self._used_music)), f, indent=2)
        except Exception as e:
            print(f"[MediaGen] Warning: Could not save music log: {e}")

    def _mark_music_used(self, music_id: str):
        """Mark a music track as used and persist."""
        self._used_music.add(music_id)
        self._save_music_log()

    def _is_footage_used(self, footage_id: str) -> bool:
        """Check if this SUPPORT footage has been used before."""
        return footage_id in self._used_footage

    def _mark_footage_used(self, footage_id: str):
        """Mark SUPPORT footage as used permanently."""
        self._used_footage.add(footage_id)
        self._save_footage_log()

    # ==========================================
    # STOCK VIDEO — Tarsier only
    # ==========================================

    def _download_pexels_clips(self, account_key: str, topic: str, num_clips: int) -> List[str]:
        if not self.pexels_key:
            return []
        print(f"[{account_key}] Searching Pexels for TARSIER clips...")
        headers = {"Authorization": self.pexels_key}
        downloaded = []
        for term in self.tarsier_search_terms:
            if len(downloaded) >= num_clips:
                break
            try:
                r = requests.get("https://api.pexels.com/videos/search", headers=headers,
                    params={"query": term, "per_page": 15, "size": "medium", "orientation": "landscape"}, timeout=15)
                if r.status_code != 200:
                    print(f"[{account_key}] Pexels tarsier search '{term}': HTTP {r.status_code}")
                    continue
                videos = r.json().get("videos", [])
                print(f"[{account_key}] Pexels tarsier search '{term}': {len(videos)} results")
                random.shuffle(videos)
                for video in videos:
                    vid_id = f"pexels_{video['id']}"
                    if len(downloaded) >= num_clips:
                        break
                    # ALL clips must be unique — no reuse within or across channels
                    if self._is_footage_used(vid_id):
                        continue
                    best_file = None
                    for vf in video.get("video_files", []):
                        if vf.get("width", 0) >= 720 and vf.get("file_type") == "video/mp4":
                            if best_file is None or vf.get("width", 0) <= 1920:
                                best_file = vf
                    if not best_file:
                        continue
                    try:
                        dl = requests.get(best_file["link"], timeout=30)
                        if dl.status_code == 200 and len(dl.content) > 10000:
                            safe = self._safe_topic(topic)
                            fp = os.path.join(TMP_DIR, f"{account_key}_{safe}_pexels_{len(downloaded)+1}.mp4")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            self._mark_footage_used(vid_id)
                            print(f"[{account_key}] Pexels clip {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{vid_id}]")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pexels error: {e}")
        return downloaded

    def _download_pixabay_clips(self, account_key: str, topic: str, num_clips: int) -> List[str]:
        if not self.pixabay_key:
            return []
        print(f"[{account_key}] Searching Pixabay for TARSIER clips...")
        downloaded = []
        for term in self.tarsier_search_terms:
            if len(downloaded) >= num_clips:
                break
            try:
                r = requests.get("https://pixabay.com/api/videos/",
                    params={"key": self.pixabay_key, "q": term, "per_page": 10,
                            "video_type": "film", "safesearch": "true"}, timeout=15)
                if r.status_code != 200:
                    print(f"[{account_key}] Pixabay tarsier search '{term}': HTTP {r.status_code}")
                    continue
                hits = r.json().get("hits", [])
                print(f"[{account_key}] Pixabay tarsier search '{term}': {len(hits)} results")
                random.shuffle(hits)
                for video in hits:
                    vid_id = f"pixabay_{video['id']}"
                    if len(downloaded) >= num_clips:
                        break
                    # ALL clips must be unique — no reuse within or across channels
                    if self._is_footage_used(vid_id):
                        continue
                    vid_url = None
                    for q in ["medium", "large", "small"]:
                        entry = video.get("videos", {}).get(q, {})
                        if entry.get("url"):
                            vid_url = entry["url"]
                            break
                    if not vid_url:
                        continue
                    try:
                        dl = requests.get(vid_url, timeout=30)
                        if dl.status_code == 200 and len(dl.content) > 10000:
                            safe = self._safe_topic(topic)
                            fp = os.path.join(TMP_DIR, f"{account_key}_{safe}_pixabay_{len(downloaded)+1}.mp4")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            self._mark_footage_used(vid_id)
                            print(f"[{account_key}] Pixabay clip {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{vid_id}]")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pixabay error: {e}")
        return downloaded

    def download_stock_clips(self, account_key: str, topic: str, num_clips: int = 7) -> List[str]:
        """Download TARSIER stock clips. All clips are deduped via used_footage.json — NEVER reused."""
        pexels = self._download_pexels_clips(account_key, topic, num_clips)
        pixabay = self._download_pixabay_clips(account_key, topic, num_clips)
        all_clips = pexels + pixabay
        random.shuffle(all_clips)
        
        if len(all_clips) == 0:
            print(f"[{account_key}] WARNING: Zero tarsier stock clips. Check API keys!")
        else:
            print(f"[{account_key}] Tarsier stock clips: {len(all_clips)} (Pexels:{len(pexels)} Pixabay:{len(pixabay)})")
        
        return all_clips[:num_clips]

    def _download_support_pexels(self, account_key: str, num_clips: int) -> List[str]:
        """Download SUPPORT/environment clips from Pexels WITH dedup — NEVER reuse."""
        if not self.pexels_key:
            return []
        print(f"[{account_key}] Searching Pexels for SUPPORT/environment clips...")
        headers = {"Authorization": self.pexels_key}
        downloaded = []
        terms = self.support_search_terms.copy()
        random.shuffle(terms)
        for term in terms:
            if len(downloaded) >= num_clips:
                break
            try:
                r = requests.get("https://api.pexels.com/videos/search", headers=headers,
                    params={"query": term, "per_page": 10, "size": "medium", "orientation": "landscape"}, timeout=15)
                if r.status_code != 200:
                    continue
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for video in videos:
                    vid_id = f"pexels_{video['id']}"
                    if len(downloaded) >= num_clips:
                        break
                    # STRICT DEDUP: support clips NEVER reused
                    if self._is_footage_used(vid_id):
                        continue
                    
                    # ANIMAL FILTER: reject videos that contain animals in metadata
                    video_url = video.get("url", "").lower()
                    video_tags = " ".join(str(t) for t in video.get("tags", [])).lower() if video.get("tags") else ""
                    video_meta = f"{video_url} {video_tags}"
                    has_animal = False
                    for blocked in self.support_blocked_words:
                        if blocked in video_meta:
                            print(f"[{account_key}] REJECTED support clip {vid_id}: contains '{blocked}'")
                            has_animal = True
                            break
                    if has_animal:
                        continue
                    
                    best_file = None
                    for vf in video.get("video_files", []):
                        if vf.get("width", 0) >= 720 and vf.get("file_type") == "video/mp4":
                            if best_file is None or vf.get("width", 0) <= 1920:
                                best_file = vf
                    if not best_file:
                        continue
                    try:
                        dl = requests.get(best_file["link"], timeout=30)
                        if dl.status_code == 200 and len(dl.content) > 10000:
                            safe = self._safe_topic(term)
                            fp = os.path.join(TMP_DIR, f"{account_key}_support_pexels_{vid_id}_{len(downloaded)+1}.mp4")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            # Mark as PERMANENTLY used — never download again
                            self._mark_footage_used(vid_id)
                            print(f"[{account_key}] Support clip {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{vid_id}]")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Support download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Support Pexels error: {e}")
        return downloaded

    def download_support_clips(self, account_key: str, num_clips: int = 6) -> List[str]:
        """Download SUPPORT clips with STRICT dedup — these are NEVER reused."""
        clips = self._download_support_pexels(account_key, num_clips)
        if len(clips) == 0:
            print(f"[{account_key}] WARNING: Zero NEW support clips available (all already used).")
        else:
            print(f"[{account_key}] Support clips: {len(clips)} NEW unique clips")
        return clips[:num_clips]

    # ==========================================
    # REAL TARSIER PHOTOS — from Pexels/Pixabay Photos API
    # For formal channels: ZERO AI, only real photographs
    # Loop engine converts photos to video via Ken Burns/zoom/pan
    # ==========================================

    def _download_pexels_tarsier_photos(self, account_key: str, num_photos: int) -> List[str]:
        """Download REAL tarsier photos from Pexels Photos API."""
        if not self.pexels_key:
            return []
        print(f"[{account_key}] Searching Pexels PHOTOS for tarsier images...")
        headers = {"Authorization": self.pexels_key}
        downloaded = []
        for term in self.tarsier_search_terms:
            if len(downloaded) >= num_photos:
                break
            try:
                r = requests.get("https://api.pexels.com/v1/search", headers=headers,
                    params={"query": term, "per_page": 15, "orientation": "landscape"}, timeout=15)
                if r.status_code != 200:
                    continue
                photos = r.json().get("photos", [])
                random.shuffle(photos)
                for photo in photos:
                    if len(downloaded) >= num_photos:
                        break
                    photo_id = f"pexels_photo_{photo['id']}"
                    # Persistent dedup — never reuse same photo
                    if self._is_footage_used(photo_id):
                        continue
                    # VALIDATION: reject photos without 'tarsier' or 'tarsius' in alt text
                    alt_text = (photo.get("alt", "") or "").lower()
                    if "tarsier" not in alt_text and "tarsius" not in alt_text:
                        continue
                    # Get landscape-sized photo
                    src = photo.get("src", {})
                    photo_url = src.get("landscape") or src.get("large") or src.get("medium")
                    if not photo_url:
                        continue
                    try:
                        dl = requests.get(photo_url, timeout=30)
                        if dl.status_code == 200 and len(dl.content) > 5000:
                            fp = os.path.join(TMP_DIR, f"{account_key}_tarsier_photo_pexels_{photo['id']}.jpg")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            self._mark_footage_used(photo_id)
                            print(f"[{account_key}] Pexels PHOTO {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{photo_id}] alt:{alt_text[:40]}")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Photo download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pexels photos error: {e}")
        return downloaded

    def _download_pixabay_tarsier_photos(self, account_key: str, num_photos: int) -> List[str]:
        """Download REAL tarsier photos from Pixabay Photos API."""
        if not self.pixabay_key:
            return []
        print(f"[{account_key}] Searching Pixabay PHOTOS for tarsier images...")
        downloaded = []
        for term in self.tarsier_search_terms:
            if len(downloaded) >= num_photos:
                break
            try:
                r = requests.get("https://pixabay.com/api/",
                    params={"key": self.pixabay_key, "q": term, "per_page": 15,
                            "image_type": "photo", "orientation": "horizontal",
                            "min_width": 1280, "safesearch": "true"}, timeout=15)
                if r.status_code != 200:
                    continue
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for photo in hits:
                    if len(downloaded) >= num_photos:
                        break
                    photo_id = f"pixabay_photo_{photo['id']}"
                    # Persistent dedup — never reuse same photo
                    if self._is_footage_used(photo_id):
                        continue
                    # VALIDATION: reject photos without 'tarsier' or 'tarsius' in tags
                    tags = (photo.get("tags", "") or "").lower()
                    if "tarsier" not in tags and "tarsius" not in tags:
                        continue
                    photo_url = photo.get("largeImageURL") or photo.get("webformatURL")
                    if not photo_url:
                        continue
                    try:
                        dl = requests.get(photo_url, timeout=30)
                        if dl.status_code == 200 and len(dl.content) > 5000:
                            fp = os.path.join(TMP_DIR, f"{account_key}_tarsier_photo_pixabay_{photo['id']}.jpg")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            self._mark_footage_used(photo_id)
                            print(f"[{account_key}] Pixabay PHOTO {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{photo_id}] tags:{tags[:40]}")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Photo download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pixabay photos error: {e}")
        return downloaded

    def _download_wikimedia_tarsier_photos(self, account_key: str, num_photos: int) -> List[str]:
        """Download REAL tarsier photos from Wikimedia Commons API (FREE, no API key needed).
        Wikimedia Commons has extensive wildlife photography including many real tarsier images."""
        print(f"[{account_key}] Searching Wikimedia Commons for tarsier images...")
        downloaded = []
        
        # Multiple search strategies — CATEGORY-BASED is most reliable for real tarsier photos
        search_queries = [
            # Family-level category (guaranteed tarsier)
            {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:Tarsiidae",
             "gcmtype": "file", "gcmlimit": "30", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
            # Philippine tarsier (Carlito syrichta)
            {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:Carlito syrichta",
             "gcmtype": "file", "gcmlimit": "30", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
            # Sulawesi tarsier (Tarsius tarsier)
            {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:Tarsius tarsier",
             "gcmtype": "file", "gcmlimit": "30", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
            # Western tarsier
            {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:Cephalopachus bancanus",
             "gcmtype": "file", "gcmlimit": "20", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
            # Tarsier genus (Tarsius)
            {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:Tarsius",
             "gcmtype": "file", "gcmlimit": "30", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
            # Text search fallback (least reliable — only if categories empty)
            {"action": "query", "generator": "search", "gsrsearch": "tarsier primate Tarsiidae",
             "gsrnamespace": "6", "gsrlimit": "20", "prop": "imageinfo",
             "iiprop": "url|size|mime", "iiurlwidth": "1280", "format": "json"},
        ]
        
        seen_titles = set()
        for params in search_queries:
            if len(downloaded) >= num_photos:
                break
            try:
                r = requests.get("https://commons.wikimedia.org/w/api.php",
                                 params=params, timeout=15,
                                 headers={"User-Agent": "TarsierBot/1.0 (educational project)"})
                if r.status_code != 200:
                    print(f"[{account_key}] Wikimedia API error: {r.status_code}")
                    continue
                
                data = r.json()
                pages = data.get("query", {}).get("pages", {})
                page_list = list(pages.values())
                random.shuffle(page_list)
                
                for page in page_list:
                    if len(downloaded) >= num_photos:
                        break
                    title = page.get("title", "")
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    # VALIDATION: reject images without tarsier-related words in title
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in ["tarsier", "tarsius", "tarsiidae", "carlito syrichta"]):
                        continue
                    
                    # Persistent dedup — never reuse same photo across channels/runs
                    wiki_id = f"wiki_{title.replace(' ', '_')[:60]}"
                    if self._is_footage_used(wiki_id):
                        continue
                    
                    imageinfo = page.get("imageinfo", [{}])
                    if not imageinfo:
                        continue
                    info = imageinfo[0]
                    mime = info.get("mime", "")
                    
                    # Only accept JPEG/PNG images
                    if mime not in ("image/jpeg", "image/png"):
                        continue
                    
                    # Use thumbnail URL (sized to 1280px width) if available, else original
                    photo_url = info.get("thumburl") or info.get("url")
                    if not photo_url:
                        continue
                    
                    try:
                        dl = requests.get(photo_url, timeout=30,
                                          headers={"User-Agent": "TarsierBot/1.0 (educational project)"})
                        if dl.status_code == 200 and len(dl.content) > 5000:
                            ext = "jpg" if "jpeg" in mime else "png"
                            safe_title = title.replace(" ", "_").replace("/", "_")[:50]
                            fp = os.path.join(TMP_DIR, f"{account_key}_tarsier_wiki_{len(downloaded)+1}.{ext}")
                            with open(fp, "wb") as f:
                                f.write(dl.content)
                            downloaded.append(fp)
                            self._mark_footage_used(wiki_id)
                            print(f"[{account_key}] Wikimedia PHOTO {len(downloaded)} ({len(dl.content)//1024}KB) [{safe_title}]")
                            time.sleep(0.3)
                    except Exception as e:
                        print(f"[{account_key}] Wikimedia download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Wikimedia search error: {e}")
        
        return downloaded

    def download_tarsier_photos(self, account_key: str, num_photos: int = 10) -> List[str]:
        """Download REAL tarsier photos from Wikimedia > Pixabay > Pexels.
        Priority: Wikimedia (category-based, most reliable) > Pixabay (tag-validated) > Pexels (alt-validated)."""
        # Wikimedia FIRST — most reliable via taxonomy categories
        wikimedia = self._download_wikimedia_tarsier_photos(account_key, num_photos)
        pixabay = self._download_pixabay_tarsier_photos(account_key, num_photos)
        pexels = self._download_pexels_tarsier_photos(account_key, num_photos)
        # Wikimedia first (most reliable), then Pixabay, then Pexels (least reliable)
        all_photos = wikimedia + pixabay + pexels
        print(f"[{account_key}] Tarsier PHOTOS: {len(all_photos)} real photos (Wikimedia:{len(wikimedia)} Pixabay:{len(pixabay)} Pexels:{len(pexels)})")
        return all_photos[:num_photos]

    # ==========================================
    # AI TARSIER IMAGES — Per-account themed
    # Priority: Cloudflare → HuggingFace (backup)
    # ==========================================
    
    def _get_cf_pool(self, account_key: str) -> list:
        """Get Cloudflare accounts for this channel ONLY — 2 dedicated accounts."""
        pool = []
        primary = CF_ACCOUNTS.get(account_key, {})
        if primary.get('account_id') and primary.get('api_token'):
            cf_id = f"cf_{primary['account_id'][:8]}"
            if cf_id not in self._depleted_cf:
                pool.append(primary)
        backup = CF_ACCOUNTS_BACKUP.get(account_key, {})
        if backup.get('account_id') and backup.get('api_token'):
            cf_id = f"cf_{backup['account_id'][:8]}"
            if cf_id not in self._depleted_cf:
                pool.append(backup)
        return pool
    
    def _generate_cf_image(self, account_key: str, prompt: str, model: str = None) -> Optional[bytes]:
        """Generate image via Cloudflare Workers AI. Returns raw image bytes or None."""
        if model is None:
            model = self.cf_model
        
        cf_pool = self._get_cf_pool(account_key)
        if not cf_pool:
            return None
        
        for cf_creds in cf_pool:
            account_id = cf_creds['account_id']
            api_token = cf_creds['api_token']
            cf_id = f"cf_{account_id[:8]}"
            is_primary = cf_creds == CF_ACCOUNTS.get(account_key, {})
            key_type = "CF-primary" if is_primary else "CF-backup"
            
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
            payload = {"prompt": prompt}
            
            for attempt in range(2):  # 2 attempts per CF account
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        # CF returns raw image bytes for image models
                        content = response.content
                        if len(content) > 5000:
                            return content
                        else:
                            print(f"[{account_key}] {key_type} returned small response ({len(content)}B)")
                            continue
                    elif response.status_code == 429:
                        # Rate limited — wait and retry
                        print(f"[{account_key}] {key_type} rate limited (429), waiting 10s...")
                        time.sleep(10)
                        continue
                    elif response.status_code in [402, 403]:
                        # Quota exhausted or permission denied
                        self._depleted_cf.add(cf_id)
                        print(f"[{account_key}] {key_type} DEPLETED ({response.status_code}) — trying backup...")
                        break  # Move to next CF account
                    else:
                        err = response.text[:200] if response.text else "no details"
                        print(f"[{account_key}] {key_type} error ({response.status_code}): {err}")
                        if attempt == 0:
                            time.sleep(3)
                            continue
                        break
                except requests.exceptions.RequestException as e:
                    print(f"[{account_key}] {key_type} request error: {e}")
                    if attempt == 0:
                        time.sleep(3)
                        continue
                    break
        
        # Try fallback model if primary model failed
        if model == self.cf_model and self.cf_fallback_model:
            cf_pool_retry = self._get_cf_pool(account_key)
            if cf_pool_retry:
                print(f"[{account_key}] Trying CF fallback model: {self.cf_fallback_model}")
                return self._generate_cf_image(account_key, prompt, model=self.cf_fallback_model)
        
        return None
    
    def generate_tarsier_image(self, account_key: str, index: int, topic: str,
                               force_tarsier: bool = False) -> Optional[str]:
        """Generates AI image. Priority: Cloudflare → HuggingFace.
        70% chance = tarsier image (dominant)
        30% chance = environment/support image
        force_tarsier=True always generates tarsier.
        """
        import time as _time
        
        # 70% tarsier, 30% support (unless forced)
        use_tarsier = force_tarsier or (random.random() < 0.7)
        
        if use_tarsier:
            base_prompt = self.tarsier_prompts[index % len(self.tarsier_prompts)]
            img_type = "tarsier"
        else:
            support = self.support_prompts.get(account_key, self.support_prompts["fb_fanspage"])
            base_prompt = support[index % len(support)]
            img_type = "environment"
        
        # Make each prompt unique with topic + timestamp + seed
        seed = random.randint(1000, 9999)
        timestamp = int(_time.time())
        prompt = f"{base_prompt}, about {topic}, unique:{timestamp}_{seed}"
        
        print(f"[{account_key}] AI {img_type} image {index}: {base_prompt[:60]}... (seed:{seed})")
        
        safe = self._safe_topic(topic)
        filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_ai_{index}.png")
        
        # === PRIORITY 1: Cloudflare Workers AI ===
        cf_content = self._generate_cf_image(account_key, prompt)
        if cf_content:
            with open(filename, "wb") as f:
                f.write(cf_content)
            print(f"[{account_key}] AI {img_type} image {index} saved via CLOUDFLARE.")
            return filename
        
        # === PRIORITY 2: HuggingFace (backup) ===
        print(f"[{account_key}] CF failed, trying HF backup...")
        payload = {"inputs": prompt}
        key_pool = self._get_key_pool(account_key)
        if not key_pool:
            print(f"[{account_key}] ALL keys depleted (CF + HF)! Cannot generate AI image.")
            return None
        
        for key in key_pool:
            headers = {"Authorization": f"Bearer {key}"}
            content = self._make_api_request(self.image_model_url, headers, payload)
            if content is None and key not in self._depleted_keys:
                content = self._make_api_request(self.image_fallback_url, headers, payload)
            
            if content:
                with open(filename, "wb") as f:
                    f.write(content)
                which_key = "HF-own" if key == HF_API_KEYS.get(account_key) else "HF-backup"
                print(f"[{account_key}] AI {img_type} image {index} saved via {which_key}.")
                return filename
            
            if key in self._depleted_keys:
                continue
            else:
                break
        
        return None

    # ==========================================
    # MAIN: Per-account unique tarsier content
    # ==========================================
    
    def generate_all_clips(self, script_segments: List[str], account_key: str, topic: str) -> list:
        """
        Per-channel visual source rules from VIDEO_PROFILES:
        - stock_only: Pexels + Pixabay real tarsier footage ONLY. ZERO AI images.
        - stock_plus_flux_env: Stock tarsier + FLUX environment-only images.
        
        HARD RULE: No footage/image is EVER reused. When stock clips are exhausted
        (finite pool), ALL channels auto-switch to AI image generation which
        produces INFINITE unique images — each prompt includes topic, index, and
        timestamp so no two images are ever the same.
        """
        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        visual_source = profile.get("visual_source", "stock_only")
        TARGET_CLIPS = 12
        
        if visual_source == "stock_only":
            # ==========================================
            # FORMAL CHANNELS: 50:50 tarsier:support
            # MINIMUM 5 tarsier photos — request MORE from sources to guarantee this
            # Photos are INTERLEAVED evenly with support clips
            # NO photo repetition within 1 video
            # ==========================================
            HALF = TARGET_CLIPS // 2  # Target: 6 tarsier + 6 support
            MIN_TARSIER = 5  # Absolute minimum tarsier photos
            
            print(f"[{account_key}] Visual source: STOCK ONLY (target {HALF} tarsier + {HALF} support, min {MIN_TARSIER} tarsier)")
            
            # --- TARSIER: real photos + AI fill ---
            tarsier_media = []
            
            # Step 1: Get real tarsier PHOTOS — request MORE than needed to survive dedup
            tarsier_photos = self.download_tarsier_photos(account_key, num_photos=15)
            for photo in tarsier_photos:
                tarsier_media.append(("image", photo))
            real_photo_count = len(tarsier_media)
            print(f"[{account_key}] Real tarsier photos: {real_photo_count}")
            
            # Step 2: Fill remaining with AI-generated tarsier images
            # Must reach at least MIN_TARSIER
            target_tarsier = max(HALF, MIN_TARSIER)
            remaining = target_tarsier - len(tarsier_media)
            if remaining > 0:
                print(f"[{account_key}] Generating {remaining} AI tarsier images (need {target_tarsier}, have {len(tarsier_media)})...")
                for i in range(remaining):
                    img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                    if img:
                        tarsier_media.append(("image", img))
                    time.sleep(1)
            
            ai_count = len(tarsier_media) - real_photo_count
            print(f"[{account_key}] Tarsier total: {len(tarsier_media)} (real:{real_photo_count} AI:{ai_count})")
            
            # HARD CHECK: if still below minimum, log warning
            if len(tarsier_media) < MIN_TARSIER:
                print(f"[{account_key}] WARNING: Only {len(tarsier_media)} tarsier photos (minimum {MIN_TARSIER}). Video quality may suffer.")
            
            # --- SUPPORT: stock videos ---
            support_clips = self.download_support_clips(account_key, num_clips=HALF)
            support_media = [("video", clip) for clip in support_clips]
            
            # FALLBACK: if ZERO support stock, use AI environment
            if len(support_media) == 0:
                print(f"[{account_key}] FALLBACK: Zero support stock! Using AI environment images...")
                for i in range(HALF):
                    img = self.generate_tarsier_image(account_key, HALF + i, topic, force_tarsier=False)
                    if img:
                        support_media.append(("image", img))
                print(f"[{account_key}] AI environment fallback: {len(support_media)} images")
            
            t_count = len(tarsier_media)
            s_count = len(support_media)
            
            # INTERLEAVE EVENLY: distribute tarsier photos across all positions
            # Pattern: T S T S T S ... (not T T T T S S S S)
            all_media = []
            ti, si = 0, 0
            total_slots = t_count + s_count
            for slot in range(total_slots):
                # Alternate: even slots = tarsier, odd slots = support
                if slot % 2 == 0 and ti < t_count:
                    all_media.append(tarsier_media[ti])
                    ti += 1
                elif si < s_count:
                    all_media.append(support_media[si])
                    si += 1
                elif ti < t_count:
                    all_media.append(tarsier_media[ti])
                    ti += 1
                elif si < s_count:
                    all_media.append(support_media[si])
                    si += 1
            
            print(f"[{account_key}] Final: {len(all_media)} clips ({t_count} tarsier + {s_count} support) — interleaved evenly")
            return all_media
        
        elif visual_source == "stock_plus_flux_env":
            # ==========================================
            # SEMI-FORMAL (yt_anthro, yt_pov, yt_drama): Stock tarsier + AI 50:50
            # TARSIER: real photos (Pixabay/Wikimedia) + AI tarsier images
            # ENVIRONMENT: 100% AI generated (always fresh/unique)
            # Pexels VIDEO search disabled — returns non-tarsier content
            # ==========================================
            HALF = TARGET_CLIPS // 2
            MIN_TARSIER = 5
            
            print(f"[{account_key}] Visual source: Stock+AI 50:50 (target {HALF} tarsier + {HALF} env, min {MIN_TARSIER} tarsier)")
            
            # --- TARSIER: real photos + AI tarsier ---
            tarsier_media = []
            
            tarsier_photos = self.download_tarsier_photos(account_key, num_photos=15)
            for photo in tarsier_photos:
                tarsier_media.append(("image", photo))
            real_photo_count = len(tarsier_media)
            
            # Fill remaining with AI-generated tarsier (must reach MIN_TARSIER)
            target_tarsier = max(HALF, MIN_TARSIER)
            if len(tarsier_media) < target_tarsier:
                for i in range(target_tarsier - len(tarsier_media)):
                    img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                    if img:
                        tarsier_media.append(("image", img))
                    time.sleep(1)
            
            ai_tarsier_count = len(tarsier_media) - real_photo_count
            print(f"[{account_key}] Tarsier: {len(tarsier_media)} (real:{real_photo_count} AI:{ai_tarsier_count})")
            
            if len(tarsier_media) < MIN_TARSIER:
                print(f"[{account_key}] WARNING: Only {len(tarsier_media)} tarsier photos (minimum {MIN_TARSIER})")
            
            # --- ENVIRONMENT (AI generated, always new) ---
            support_media = []
            for i in range(HALF):
                img = self.generate_tarsier_image(account_key, HALF + i, topic, force_tarsier=False)
                if img:
                    support_media.append(("image", img))
                time.sleep(1)
            
            t_count = len(tarsier_media)
            s_count = len(support_media)
            
            # INTERLEAVE EVENLY: T S T S T S ...
            all_media = []
            ti, si = 0, 0
            total_slots = t_count + s_count
            for slot in range(total_slots):
                if slot % 2 == 0 and ti < t_count:
                    all_media.append(tarsier_media[ti])
                    ti += 1
                elif si < s_count:
                    all_media.append(support_media[si])
                    si += 1
                elif ti < t_count:
                    all_media.append(tarsier_media[ti])
                    ti += 1
                elif si < s_count:
                    all_media.append(support_media[si])
                    si += 1
            
            print(f"[{account_key}] Final: {len(all_media)} clips ({t_count} tarsier + {s_count} env) — interleaved evenly")
            return all_media
        
        elif visual_source == "ai_only":
            # ==========================================
            # NON-FORMAL: 50:50 AI tarsier + AI environment
            # ALL images are freshly generated (never reused)
            # FALLBACK: If AI fails → auto-switch to stock photos
            # ==========================================
            HALF = TARGET_CLIPS // 2
            
            print(f"[{account_key}] Visual source: AI 50:50 ({HALF} tarsier + {HALF} environment, all new)")
            
            all_media = []
            # Generate tarsier and environment in interleaved order
            for i in range(HALF):
                # Tarsier image
                img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                if img:
                    all_media.append(("image", img))
                time.sleep(1)
                # Environment image
                img = self.generate_tarsier_image(account_key, HALF + i, topic, force_tarsier=False)
                if img:
                    all_media.append(("image", img))
                time.sleep(1)
            
            # FALLBACK: If AI generated ZERO or too few images (HF keys depleted)
            # → switch to stock photos so the channel NEVER fails
            if len(all_media) < 3:
                print(f"[{account_key}] AI generated only {len(all_media)} images — ACTIVATING STOCK FALLBACK")
                
                # 50% tarsier photos from Wikimedia/Pixabay/Pexels
                tarsier_photos = self.download_tarsier_photos(account_key, num_photos=HALF)
                for photo in tarsier_photos:
                    all_media.append(("image", photo))
                print(f"[{account_key}] Stock fallback: {len(tarsier_photos)} real tarsier photos added")
                
                # 50% support/environment clips
                support_clips = self.download_support_clips(account_key, num_clips=HALF)
                for clip in support_clips:
                    all_media.append(("video", clip))
                print(f"[{account_key}] Stock fallback: {len(support_clips)} support clips added")
                
                # If STILL zero (all stock exhausted too), try AI environment as last resort
                if len(all_media) == 0:
                    print(f"[{account_key}] CRITICAL: Both AI and stock empty! Trying AI environment one more time...")
                    for i in range(TARGET_CLIPS):
                        img = self.generate_tarsier_image(account_key, 100 + i, topic, force_tarsier=False)
                        if img:
                            all_media.append(("image", img))
                        time.sleep(1)
            
            print(f"[{account_key}] Final: {len(all_media)} media items (AI preferred, stock fallback if needed)")
            return all_media
        
        else:
            # Fallback: 50:50
            print(f"[{account_key}] Unknown visual_source '{visual_source}', using 50:50 fallback")
            HALF = TARGET_CLIPS // 2
            all_media = []
            for i in range(HALF):
                img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                if img:
                    all_media.append(("image", img))
            for i in range(HALF):
                img = self.generate_tarsier_image(account_key, HALF + i, topic, force_tarsier=False)
                if img:
                    all_media.append(("image", img))
            return all_media

    # ==========================================
    # AUDIO — Per-account voice styles via edge-tts
    # ==========================================
    
    # Per-account voice settings: voice, rate, pitch
    # UPDATED: Fresh, modern voices — no more flat/boring delivery
    VOICE_SETTINGS = {
        "yt_documenter": {
            "voice": "en-US-AndrewNeural",       # Modern male, warm & clear (replaces flat GuyNeural)
            "rate": "+3%",                        # Slightly faster = more confident, not dragging
            "pitch": "+0Hz",                      # Natural tone, not artificially deep
        },
        "yt_funny": {
            "voice": "en-US-AnaNeural",           # Young, bright female — perfect for comedy
            "rate": "+10%",                       # Fast & punchy = comedy timing
            "pitch": "+5Hz",                      # Higher, playful energy
        },
        "yt_anthro": {
            "voice": "en-US-BrianNeural",         # Expressive male storyteller, natural cadence
            "rate": "+5%",                        # Upbeat storytelling pace
            "pitch": "+2Hz",                      # Warm, quirky
        },
        "yt_pov": {
            "voice": "en-US-MichelleNeural",      # Intimate, emotive female — diary/journal feel
            "rate": "-3%",                        # Slightly slower for atmosphere (not dragging)
            "pitch": "-1Hz",                      # Soft but not robotic
        },
        "yt_drama": {
            "voice": "en-US-AndrewNeural",        # Cinematic male — expressive range
            "rate": "+0%",                        # Normal pace, let drama breathe naturally
            "pitch": "-3Hz",                      # Slightly deep, but not exaggerated
        },
        "fb_fanspage": {
            "voice": "en-US-EmmaNeural",          # Energetic, friendly female — scroll-stopper
            "rate": "+8%",                        # Fast, punchy = Facebook engagement
            "pitch": "+3Hz",                      # Bright, confident
        },
    }

    def generate_voiceover(self, text: str, account_key: str, topic: str) -> Optional[str]:
        """Natural voiceover via edge-tts with SSML markup for per-channel intonation."""
        # Get SSML-aware parameters from ssml_builder
        edge_params = get_edge_tts_params(account_key)
        voice = edge_params["voice"]
        rate = edge_params["rate"]
        pitch = edge_params["pitch"]
        
        # Build SSML from plain text for better intonation
        ssml_text = build_ssml(text, account_key)
        
        print(f"[{account_key}] Generating voiceover: {voice} (rate={rate}, pitch={pitch}, SSML=ON)")
        try:
            import asyncio
            import edge_tts
            
            safe = self._safe_topic(topic)
            filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_audio.mp3")
            
            async def _generate():
                # Try SSML first for better intonation
                try:
                    tts = edge_tts.Communicate(
                        text=ssml_text,
                        voice=voice,
                    )
                    await tts.save(filename)
                except Exception:
                    # Fallback: plain text with rate/pitch params
                    tts = edge_tts.Communicate(
                        text=text[:1500],
                        voice=voice,
                        rate=rate,
                        pitch=pitch
                    )
                    await tts.save(filename)
            
            # Run async in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        pool.submit(asyncio.run, _generate()).result()
                else:
                    loop.run_until_complete(_generate())
            except RuntimeError:
                asyncio.run(_generate())
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                print(f"[{account_key}] Voiceover saved ({os.path.getsize(filename)//1024}KB, SSML)")
                return filename
        except Exception as e:
            print(f"[{account_key}] edge-tts error: {e}")
            # Fallback to gTTS
            try:
                from gtts import gTTS
                safe = self._safe_topic(topic)
                filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_audio.mp3")
                tts = gTTS(text=text[:1000], lang="en", slow=False)
                tts.save(filename)
                if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                    print(f"[{account_key}] Fallback gTTS voiceover saved")
                    return filename
            except Exception as e2:
                print(f"[{account_key}] gTTS fallback also failed: {e2}")
        return None

    # Per-account music search keywords for Freesound API
    # IMPORTANT: queries MUST include "music" to avoid ambient/nature sounds (crickets, rain, etc)
    MUSIC_SEARCH = {
        "yt_documenter": ["cinematic piano music", "documentary orchestral music", "nature film music instrumental"],
        "yt_funny": ["upbeat ukulele music", "happy comedy music instrumental", "cheerful fun music"],
        "yt_anthro": ["whimsical piano music", "storytelling guitar music", "adventure music instrumental"],
        "yt_pov": ["ambient piano music dark", "mysterious cello music", "suspense music instrumental"],
        "yt_drama": ["emotional piano music", "dramatic orchestral music sad", "cinematic strings music"],
        "fb_fanspage": ["gentle piano music calm", "positive acoustic guitar music", "soft background music instrumental"],
    }

    # CDN fallback URLs per-account — EVERY URL is unique, ZERO overlap between channels
    # RULE: No two channels may share the same CDN music URL
    CDN_FALLBACK = {
        "yt_documenter": [
            "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3",
            "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946bc34898.mp3",
            "https://cdn.pixabay.com/download/audio/2022/12/14/audio_5e3e4f6e22.mp3",
            "https://cdn.pixabay.com/download/audio/2023/03/08/audio_5b0c1e4f57.mp3",
            "https://cdn.pixabay.com/download/audio/2023/06/28/audio_5d9c5f0af9.mp3",
            "https://cdn.pixabay.com/download/audio/2024/01/10/audio_3a8e7d2b91.mp3",
        ],
        "yt_funny": [
            "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749d484.mp3",
            "https://cdn.pixabay.com/download/audio/2022/06/07/audio_b9bd4e1cf5.mp3",
            "https://cdn.pixabay.com/download/audio/2023/01/12/audio_3c2f4a6b83.mp3",
            "https://cdn.pixabay.com/download/audio/2023/04/19/audio_7c4b8d9e12.mp3",
            "https://cdn.pixabay.com/download/audio/2023/09/05/audio_8e2f1a3b67.mp3",
            "https://cdn.pixabay.com/download/audio/2024/02/15/audio_6c9b3e7d42.mp3",
        ],
        "yt_anthro": [
            "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
            "https://cdn.pixabay.com/download/audio/2022/09/18/audio_4c3f2b8d51.mp3",
            "https://cdn.pixabay.com/download/audio/2023/02/15/audio_6d1e9a4c73.mp3",
            "https://cdn.pixabay.com/download/audio/2023/05/22/audio_9f3b7c1e84.mp3",
            "https://cdn.pixabay.com/download/audio/2023/08/10/audio_2a5d8e6f19.mp3",
            "https://cdn.pixabay.com/download/audio/2024/03/20/audio_5d8a2e6f73.mp3",
        ],
        "yt_pov": [
            "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde560.mp3",
            "https://cdn.pixabay.com/download/audio/2022/07/14/audio_7b5e2a9d36.mp3",
            "https://cdn.pixabay.com/download/audio/2022/11/03/audio_1c8d4e5a73.mp3",
            "https://cdn.pixabay.com/download/audio/2023/03/21/audio_4f6a9b2c81.mp3",
            "https://cdn.pixabay.com/download/audio/2023/07/17/audio_8d3e1f5a29.mp3",
            "https://cdn.pixabay.com/download/audio/2024/04/08/audio_7e3b9a1d52.mp3",
        ],
        "yt_drama": [
            "https://cdn.pixabay.com/download/audio/2022/04/27/audio_67bcce56c1.mp3",
            "https://cdn.pixabay.com/download/audio/2022/08/22/audio_3b7c1d9e54.mp3",
            "https://cdn.pixabay.com/download/audio/2023/01/28/audio_5e2a8f4b61.mp3",
            "https://cdn.pixabay.com/download/audio/2023/06/05/audio_7c9d3a1e82.mp3",
            "https://cdn.pixabay.com/download/audio/2023/10/12/audio_2f4b6e8a93.mp3",
            "https://cdn.pixabay.com/download/audio/2024/05/14/audio_8a4c2d6e31.mp3",
        ],
        "fb_fanspage": [
            "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",
            "https://cdn.pixabay.com/download/audio/2022/06/22/audio_5e1c3b9a47.mp3",
            "https://cdn.pixabay.com/download/audio/2022/12/08/audio_8f2d6a4c15.mp3",
            "https://cdn.pixabay.com/download/audio/2023/04/03/audio_3a7e1c9d52.mp3",
            "https://cdn.pixabay.com/download/audio/2023/08/25/audio_6b4d2f8e71.mp3",
            "https://cdn.pixabay.com/download/audio/2024/06/18/audio_9b5e3a7c24.mp3",
        ],
    }

    def generate_music(self, account_key: str, topic: str, duration: int = 60) -> Optional[str]:
        """Downloads themed background music via Freesound API (primary) or CDN fallback."""
        safe = self._safe_topic(topic)
        filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_music.mp3")
        
        # ========== Strategy 1: Freesound API ==========
        if FREESOUND_API_KEY:
            queries = self.MUSIC_SEARCH.get(account_key, self.MUSIC_SEARCH["fb_fanspage"])
            random.shuffle(queries)
            
            for query in queries:
                try:
                    print(f"[{account_key}] Freesound search: '{query}'...")
                    # Randomize page to get different results each run
                    rand_page = random.randint(1, 5)
                    r = requests.get(
                        "https://freesound.org/apiv2/search/text/",
                        params={
                            "query": query,
                            "token": FREESOUND_API_KEY,
                            "fields": "id,name,duration,previews",
                            "filter": "duration:[45 TO 300]",  # 45s-5min tracks only (short clips are usually ambient/SFX)
                            "sort": "rating_desc",
                            "page_size": 15,
                            "page": rand_page,
                        },
                        timeout=15
                    )
                    if r.status_code != 200:
                        print(f"[{account_key}] Freesound API error: {r.status_code}")
                        continue
                    
                    results = r.json().get("results", [])
                    if not results:
                        continue
                    
                    # Filter out already-used tracks
                    fresh_results = [t for t in results if f"freesound_{t.get('id')}" not in self._used_music]
                    if not fresh_results:
                        print(f"[{account_key}] All {len(results)} Freesound results already used, trying next query...")
                        continue
                    
                    # Pick a random track from FRESH results only
                    track = random.choice(fresh_results)
                    preview_url = track.get("previews", {}).get("preview-hq-mp3")
                    if not preview_url:
                        continue
                    
                    track_id = f"freesound_{track.get('id')}"
                    print(f"[{account_key}] Downloading: {track.get('name', 'unknown')} ({track.get('duration', 0):.0f}s) [ID:{track_id}]")
                    dl = requests.get(preview_url, timeout=30)
                    if dl.status_code == 200 and len(dl.content) > 10000:
                        if self._is_valid_audio(dl.content):
                            with open(filename, "wb") as f:
                                f.write(dl.content)
                            self._mark_music_used(track_id)
                            print(f"[{account_key}] Freesound music saved ({len(dl.content)//1024}KB) — marked as used")
                            return filename
                except Exception as e:
                    print(f"[{account_key}] Freesound error: {e}")
        else:
            print(f"[{account_key}] No FREESOUND_API_KEY set.")
        
        # ========== Strategy 2: CDN fallback ==========
        print(f"[{account_key}] Trying CDN fallback...")
        cdn_urls = self.CDN_FALLBACK.get(account_key, self.CDN_FALLBACK["fb_fanspage"])
        # Filter out already-used CDN URLs
        fresh_cdns = [url for url in cdn_urls if f"cdn_{url[-20:]}" not in self._used_music]
        if not fresh_cdns:
            print(f"[{account_key}] All CDN music exhausted — no reuse allowed, trying ambient tone...")
            fresh_cdns = []  # Empty — will skip for loop, fall to Strategy 3
        else:
            random.shuffle(fresh_cdns)
        
        for url in fresh_cdns:
            try:
                dl = requests.get(url, timeout=30)
                if dl.status_code == 200 and len(dl.content) > 10000:
                    if self._is_valid_audio(dl.content):
                        with open(filename, "wb") as f:
                            f.write(dl.content)
                        cdn_id = f"cdn_{url[-20:]}"
                        self._mark_music_used(cdn_id)
                        print(f"[{account_key}] CDN music saved ({len(dl.content)//1024}KB) — marked as used")
                        return filename
            except Exception as e:
                print(f"[{account_key}] CDN error: {e}")
        
        # ========== Strategy 3: Generate ambient tone ==========
        try:
            print(f"[{account_key}] Generating ambient tone as last resort...")
            import wave
            import struct
            import math
            
            wav_file = filename.replace('.mp3', '.wav')
            sample_rate = 44100
            total_seconds = 90
            freq = 220.0
            
            with wave.open(wav_file, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for i in range(sample_rate * total_seconds):
                    t = i / sample_rate
                    volume = 0.15 * (0.5 + 0.5 * math.sin(2 * math.pi * 0.05 * t))
                    sample = volume * math.sin(2 * math.pi * freq * t)
                    sample += 0.05 * math.sin(2 * math.pi * freq * 1.5 * t)
                    packed = struct.pack('h', int(sample * 32767))
                    wf.writeframes(packed)
            
            print(f"[{account_key}] Ambient tone saved ({os.path.getsize(wav_file)//1024}KB)")
            return wav_file
        except Exception as e:
            print(f"[{account_key}] Ambient generation failed: {e}")
        
        print(f"[{account_key}] No music available.")
        return None

    def _is_valid_audio(self, content: bytes) -> bool:
        if len(content) < 100:
            return False
        if content[:3] == b'\xff\xd8\xff':  # JPEG
            return False
        if content[:4] == b'\x89PNG':  # PNG
            return False
        if content[:3] == b'GIF':
            return False
        if content[:5].lower() in [b'<!doc', b'<html']:
            return False
        return True

if __name__ == "__main__":
    pass
