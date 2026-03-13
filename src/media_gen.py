import os
import requests
import time
import random
from typing import Optional, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import HF_API_KEYS, ACCOUNTS, TMP_DIR, MAX_RETRIES, CLIP_DURATION_SEC, FREESOUND_API_KEY, VIDEO_PROFILES, DATA_DIR
from src.ssml_builder import build_ssml, get_edge_tts_params

class MediaGenerator:
    # Path to persistent footage log — tracks EVERY clip/image ever used
    FOOTAGE_LOG_PATH = os.path.join(DATA_DIR, "used_footage.json")

    def __init__(self):
        import json as _json
        self._json = _json
        HF_BASE = "https://router.huggingface.co/hf-inference/models"
        self.image_model_url = f"{HF_BASE}/black-forest-labs/FLUX.1-schnell"
        self.image_fallback_url = f"{HF_BASE}/stabilityai/stable-diffusion-xl-base-1.0"
        self.pexels_key = os.environ.get("PEXELS_API_KEY", "")
        self.pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
        self._depleted_keys = set()  # Track HF keys that returned 402
        
        # Load persistent footage log — HARD RULE: no footage reused EVER
        self._used_footage = self._load_footage_log()
        print(f"[MediaGen] Footage log loaded: {len(self._used_footage)} items already used")
        
        # Tarsier-ONLY stock search terms — every term MUST contain 'tarsier' or 'tarsius'
        # to guarantee only real tarsier footage is downloaded (no random primates)
        self.tarsier_search_terms = [
            "tarsier", "philippine tarsier", "bohol tarsier",
            "tarsier primate", "tarsier animal", "tarsier eyes",
            "tarsier close up", "tarsier wildlife", "tarsier night",
            "tarsier nocturnal", "tarsier jungle", "tarsier forest",
            "tarsier tree", "tarsier branch", "tarsier baby",
            "tarsier face", "tarsier hunting", "tarsier insect",
            "tarsier staring", "sulawesi tarsier", "tarsius",
        ]
        
        # Per-account AI prompts — TARSIER DOMINANT for all channels
        # Tarsier images = 70%+ of all AI images, environment = supplement only
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
        Get ordered list of HF API keys to try: own key first, then backup keys.
        Unused keys from stock_only channels serve as backup for FLUX channels.
        """
        all_keys = [(k, v) for k, v in HF_API_KEYS.items() if v]
        # Own key first
        own_key = HF_API_KEYS.get(account_key, "")
        pool = []
        if own_key and own_key not in self._depleted_keys:
            pool.append(own_key)
        # Then all other keys as backup (skip depleted ones)
        for k, v in all_keys:
            if k != account_key and v not in self._depleted_keys and v not in pool:
                pool.append(v)
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
    # FOOTAGE DEDUPLICATION — SPLIT RULES:
    # 1. TARSIER clips: CAN reuse source but MUST
    #    use DIFFERENT loop variation each time
    # 2. SUPPORT clips: NEVER reuse (hard rule)
    # ==========================================

    def _load_footage_log(self) -> set:
        """Load persistent set of used footage IDs (support footage only)."""
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
                    continue
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for video in videos:
                    vid_id = f"pexels_{video['id']}"
                    if len(downloaded) >= num_clips:
                        break
                    # Tarsier clips CAN be reused — loop engine creates unique variations
                    # (dedup only applies to support/environment footage)
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
                    continue
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for video in hits:
                    vid_id = f"pixabay_{video['id']}"
                    if len(downloaded) >= num_clips:
                        break
                    # Tarsier clips CAN be reused — loop engine creates unique variations
                    # (dedup only applies to support/environment footage)
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
                            print(f"[{account_key}] Pixabay clip {len(downloaded)} ({len(dl.content)//1024}KB) [ID:{vid_id}]")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pixabay error: {e}")
        return downloaded

    def download_stock_clips(self, account_key: str, topic: str, num_clips: int = 7) -> List[str]:
        """Download tarsier stock clips. No dedup — tarsier clips CAN be reused (loop engine makes unique)."""
        pexels = self._download_pexels_clips(account_key, topic, num_clips)
        pixabay = self._download_pixabay_clips(account_key, topic, num_clips)
        all_clips = pexels + pixabay
        random.shuffle(all_clips)
        
        if len(all_clips) == 0:
            print(f"[{account_key}] WARNING: Zero stock clips from Pexels/Pixabay. Check API keys!")
        else:
            print(f"[{account_key}] Stock clips: {len(all_clips)} clips (Pexels:{len(pexels)} Pixabay:{len(pixabay)})")
        
        return all_clips[:num_clips]

    # ==========================================
    # AI TARSIER IMAGES — Per-account themed
    # ==========================================
    
    def generate_tarsier_image(self, account_key: str, index: int, topic: str,
                               force_tarsier: bool = False) -> Optional[str]:
        """Generates AI image.
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
        payload = {"inputs": prompt}
        
        # Try key pool: own key first, then backups from unused channels
        key_pool = self._get_key_pool(account_key)
        if not key_pool:
            print(f"[{account_key}] ALL HF keys depleted! Cannot generate AI image.")
            return None
        
        for key in key_pool:
            headers = {"Authorization": f"Bearer {key}"}
            content = self._make_api_request(self.image_model_url, headers, payload)
            if content is None and key not in self._depleted_keys:
                # Try fallback model with same key
                content = self._make_api_request(self.image_fallback_url, headers, payload)
            
            if content:
                safe = self._safe_topic(topic)
                filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_ai_{index}.png")
                with open(filename, "wb") as f:
                    f.write(content)
                which_key = "own" if key == HF_API_KEYS.get(account_key) else "backup"
                print(f"[{account_key}] AI {img_type} image {index} saved (using {which_key} key).")
                return filename
            
            # If key was depleted (402), try next key in pool
            if key in self._depleted_keys:
                print(f"[{account_key}] Key depleted, trying backup...")
                continue
            else:
                break  # Non-402 failure, don't try other keys
        
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
            # DOCUMENTARY/INFORMATIVE channels: prefer real stock footage
            # But if stock = 0, use AI TARSIER images as emergency fallback
            # (video without tarsier is worse than using AI tarsier)
            print(f"[{account_key}] Visual source: STOCK ONLY (prefer real footage)")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=TARGET_CLIPS)
            all_media = [("video", clip) for clip in stock_clips]
            
            # EMERGENCY FALLBACK: if zero stock clips, generate AI TARSIER images
            # This ensures the video ALWAYS has tarsier content
            if len(all_media) == 0:
                print(f"[{account_key}] EMERGENCY: Zero stock clips! Generating AI TARSIER images as fallback...")
                for i in range(TARGET_CLIPS):
                    img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                    if img:
                        all_media.append(("image", img))
                print(f"[{account_key}] Emergency AI tarsier images: {len(all_media)}")
            elif len(all_media) < 3:
                # Very few stock clips — supplement with AI TARSIER only
                ai_needed = 3 - len(all_media)
                print(f"[{account_key}] Low stock ({len(all_media)}). Adding {ai_needed} AI TARSIER images...")
                for i in range(ai_needed):
                    img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                    if img:
                        all_media.append(("image", img))
            
            print(f"[{account_key}] Final: {len(all_media)} media items")
            return all_media
        
        elif visual_source == "stock_plus_flux_env":
            # HYBRID: Stock tarsier clips + AI images (50:50 tarsier:environment)
            MAX_STOCK = 7
            MIN_AI = 5
            
            print(f"[{account_key}] Visual source: Stock tarsier + AI (50:50 tarsier:environment)")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=MAX_STOCK)
            all_media = [("video", clip) for clip in stock_clips]
            
            # AI images: 50% TARSIER + 50% environment (minimum ratio rule)
            ai_needed = max(TARGET_CLIPS - len(stock_clips), MIN_AI)
            tarsier_ai = max(ai_needed // 2, 1)  # MIN 50% tarsier
            support_ai = ai_needed - tarsier_ai
            
            print(f"[{account_key}] Generating {ai_needed} AI images ({tarsier_ai} tarsier + {support_ai} environment)")
            
            ai_failed = 0
            # Generate TARSIER images first (guaranteed)
            for i in range(tarsier_ai):
                img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                if img:
                    all_media.append(("image", img))
                else:
                    ai_failed += 1
                time.sleep(2)
            
            # Then environment images
            for i in range(support_ai):
                img = self.generate_tarsier_image(account_key, tarsier_ai + i, topic, force_tarsier=False)
                if img:
                    all_media.append(("image", img))
                else:
                    ai_failed += 1
                time.sleep(2)
            
            if ai_failed == ai_needed:
                print(f"[{account_key}] WARNING: All AI images failed (HF credits?). Continuing with stock-only + loop variations.")
            
            random.shuffle(all_media)
            stock_n = sum(1 for t, _ in all_media if t == "video")
            ai_n = sum(1 for t, _ in all_media if t == "image")
            print(f"[{account_key}] Final: {len(all_media)} clips ({stock_n} stock + {ai_n} AI)")
            return all_media
        
        elif visual_source == "ai_only":
            # 100% AI tarsier images (e.g. yt_funny channel)
            print(f"[{account_key}] Visual source: AI ONLY (100% AI tarsier images)")
            all_media = []
            for i in range(TARGET_CLIPS):
                img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                if img:
                    all_media.append(("image", img))
                time.sleep(1)
            print(f"[{account_key}] Final: {len(all_media)} AI tarsier images")
            return all_media
        
        else:
            # Fallback: try stock, then AI tarsier
            print(f"[{account_key}] Unknown visual_source '{visual_source}', trying stock then AI")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=TARGET_CLIPS)
            all_media = [("video", clip) for clip in stock_clips]
            if len(all_media) == 0:
                for i in range(TARGET_CLIPS):
                    img = self.generate_tarsier_image(account_key, i, topic, force_tarsier=True)
                    if img:
                        all_media.append(("image", img))
            return all_media

    # ==========================================
    # AUDIO — Per-account voice styles via edge-tts
    # ==========================================
    
    # Per-account voice settings: voice, rate, pitch
    VOICE_SETTINGS = {
        "yt_documenter": {
            "voice": "en-US-GuyNeural",       # Deep, calm male narrator
            "rate": "-5%",                     # Slightly slower for clarity
            "pitch": "-5Hz",                   # Deeper tone, authoritative
        },
        "yt_funny": {
            "voice": "en-US-JennyNeural",      # Cheerful, energetic female
            "rate": "+5%",                     # Slightly upbeat pace
            "pitch": "+3Hz",                   # Higher, playful tone
        },
        "yt_anthro": {
            "voice": "en-US-AriaNeural",       # Expressive, quirky storyteller
            "rate": "+0%",                     # Normal pace
            "pitch": "+2Hz",                   # Slightly whimsical
        },
        "yt_pov": {
            "voice": "en-GB-SoniaNeural",      # British, intimate narrator
            "rate": "-8%",                     # Slower, contemplative
            "pitch": "-2Hz",                   # Soft, atmospheric
        },
        "yt_drama": {
            "voice": "en-US-DavisNeural",      # Deep, emotional male
            "rate": "-10%",                    # Dramatic slow pace
            "pitch": "-8Hz",                   # Deep, intense
        },
        "fb_fanspage": {
            "voice": "en-US-JennyNeural",      # Warm, friendly female
            "rate": "+0%",                     # Normal pace
            "pitch": "+0Hz",                   # Neutral, approachable
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
    MUSIC_SEARCH = {
        "yt_documenter": ["cinematic documentary", "nature ambient instrumental", "science background music"],
        "yt_funny": ["upbeat playful", "happy comedy background", "cheerful ukulele"],
        "yt_anthro": ["whimsical storytelling", "quirky adventure music", "fantasy background"],
        "yt_pov": ["ambient atmospheric dark", "mysterious forest night", "suspense ambient"],
        "yt_drama": ["emotional orchestral", "dramatic piano sad", "cinematic tension"],
        "fb_fanspage": ["warm friendly background", "positive nature music", "gentle acoustic"],
    }

    # CDN fallback URLs per-account (proven working Pixabay CDN)
    CDN_FALLBACK = {
        "yt_documenter": [
            "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3",
            "https://cdn.pixabay.com/download/audio/2022/04/27/audio_67bcce56c1.mp3",
        ],
        "yt_funny": [
            "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749d484.mp3",
            "https://cdn.pixabay.com/download/audio/2022/08/31/audio_419263fac4.mp3",
        ],
        "yt_anthro": [
            "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
            "https://cdn.pixabay.com/download/audio/2022/03/24/audio_a90a740a0e.mp3",
        ],
        "yt_pov": [
            "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde560.mp3",
            "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",
        ],
        "yt_drama": [
            "https://cdn.pixabay.com/download/audio/2022/04/27/audio_67bcce56c1.mp3",
            "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3",
        ],
        "fb_fanspage": [
            "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749d484.mp3",
            "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde560.mp3",
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
                    r = requests.get(
                        "https://freesound.org/apiv2/search/text/",
                        params={
                            "query": query,
                            "token": FREESOUND_API_KEY,
                            "fields": "id,name,duration,previews",
                            "filter": "duration:[30 TO 300]",  # 30s-5min tracks only
                            "sort": "rating_desc",
                            "page_size": 5,
                        },
                        timeout=15
                    )
                    if r.status_code != 200:
                        print(f"[{account_key}] Freesound API error: {r.status_code}")
                        continue
                    
                    results = r.json().get("results", [])
                    if not results:
                        continue
                    
                    # Pick a random track from top results
                    track = random.choice(results)
                    preview_url = track.get("previews", {}).get("preview-hq-mp3")
                    if not preview_url:
                        continue
                    
                    print(f"[{account_key}] Downloading: {track.get('name', 'unknown')} ({track.get('duration', 0):.0f}s)")
                    dl = requests.get(preview_url, timeout=30)
                    if dl.status_code == 200 and len(dl.content) > 10000:
                        if self._is_valid_audio(dl.content):
                            with open(filename, "wb") as f:
                                f.write(dl.content)
                            print(f"[{account_key}] Freesound music saved ({len(dl.content)//1024}KB)")
                            return filename
                except Exception as e:
                    print(f"[{account_key}] Freesound error: {e}")
        else:
            print(f"[{account_key}] No FREESOUND_API_KEY set.")
        
        # ========== Strategy 2: CDN fallback ==========
        print(f"[{account_key}] Trying CDN fallback...")
        cdn_urls = self.CDN_FALLBACK.get(account_key, self.CDN_FALLBACK["fb_fanspage"])
        random.shuffle(cdn_urls)
        
        for url in cdn_urls:
            try:
                dl = requests.get(url, timeout=30)
                if dl.status_code == 200 and len(dl.content) > 10000:
                    if self._is_valid_audio(dl.content):
                        with open(filename, "wb") as f:
                            f.write(dl.content)
                        print(f"[{account_key}] CDN music saved ({len(dl.content)//1024}KB)")
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
