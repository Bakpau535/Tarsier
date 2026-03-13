import os
import requests
import time
import random
from typing import Optional, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import HF_API_KEYS, ACCOUNTS, TMP_DIR, MAX_RETRIES, CLIP_DURATION_SEC, FREESOUND_API_KEY, VIDEO_PROFILES
from src.ssml_builder import build_ssml, get_edge_tts_params

class MediaGenerator:
    def __init__(self):
        HF_BASE = "https://router.huggingface.co/hf-inference/models"
        self.image_model_url = f"{HF_BASE}/black-forest-labs/FLUX.1-schnell"
        self.image_fallback_url = f"{HF_BASE}/stabilityai/stable-diffusion-xl-base-1.0"
        self.pexels_key = os.environ.get("PEXELS_API_KEY", "")
        self.pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
        
        # Tarsier-only stock search terms
        self.tarsier_search_terms = [
            "tarsier", "philippine tarsier", "bohol tarsier",
            "tarsier primate", "tarsier animal", "tarsier eyes",
            "tarsier close up", "tarsier wildlife", "tarsier night"
        ]
        
        # Per-account AI prompts — FLUX AI rules from correction plan:
        # - Channels with flux_allowed=False: only stock footage, no AI images
        # - Channels with flux_allowed=True: ENVIRONMENT ONLY, never tarsier/animal
        # - yt_documenter, yt_funny, fb_fanspage = ZERO FLUX
        # - yt_anthro, yt_pov, yt_drama = FLUX for environment/backgrounds only
        self.account_prompts = {
            "yt_documenter": [
                "4k macro photography of a Philippine tarsier, huge round eyes, scientific documentary style, shallow depth of field",
                "extreme close up of tarsier skull anatomy overlay, enormous eye sockets visible, educational nature documentary",
                "tarsier gripping a branch with elongated finger bones visible, detailed fur texture, biology textbook style photo",
                "side profile of a tarsier showing ear rotation, nocturnal adaptations, national geographic scientific photography",
                "tarsier hunting an insect at night, infrared camera style, wildlife research documentation",
                "comparison shot of tarsier eye vs its brain size, ultra detailed macro, science illustration style",
                "tarsier perched on a branch in bohol philippines, habitat conservation signage visible, documentary field shot",
            ],
            "yt_funny": [
                "adorable baby tarsier with comically huge surprised eyes, cute funny expression, bright colorful background",
                "tarsier looking shocked with mouth open, meme-worthy expression, hilarious cute animal photo",
                "tiny tarsier yawning dramatically showing tiny teeth, sleepy funny face, warm sunset lighting",
                "tarsier peeking from behind a leaf with one enormous eye visible, funny hide and seek, playful",
                "two tarsiers staring at each other with huge round eyes, funny standoff, comedy wildlife moment",
                "tarsier sitting on a branch looking confused, head tilted sideways, adorable goofy expression",
                "tarsier caught mid-sneeze, funny blurry action shot, cute hilarious animal moment",
            ],
            # FLUX-allowed channels: ENVIRONMENT ONLY prompts (no tarsier/animal keywords)
            "yt_anthro": [
                "miniature office desk with tiny furniture, coffee cup, papers, warm cozy lighting, whimsical fantasy scene",
                "tiny kitchen scene with miniature cooking utensils, warm homey atmosphere, storybook illustration",
                "miniature school classroom with tiny chairs and chalkboard, playful colorful fantasy setting",
                "tiny living room with miniature sofa and TV, cozy evening lighting, whimsical interior design",
                "miniature bicycle on a forest path, fairy tale atmosphere, no animals, just props",
                "tiny chef kitchen with miniature utensils and ingredients, warm lighting, whimsical food scene",
                "miniature newspaper and tiny park bench, intellectual setting, artistic urban miniature",
            ],
            "yt_pov": [
                # ENVIRONMENT ONLY — atmospheric forest scenes for POV channel
                "dark hollow tree interior looking out at moonlit jungle, atmospheric horror style, no animals",
                "dense jungle canopy at night with glowing insects, cinematic night photography, empty forest",
                "moonlit forest floor with fallen leaves and moss, moody atmospheric, mysterious empty path",
                "silhouette of tree branches against full moon, dark fantasy nature, no animals visible",
                "rainy tropical forest with water droplets on leaves, POV from under a leaf, moody atmosphere",
                "starry sky through dense forest canopy, cosmic dreamy feeling, peaceful night scene",
                "misty morning forest with sunbeams through trees, ethereal atmospheric, no animals",
            ],
            "yt_drama": [
                # ENVIRONMENT ONLY — dramatic scenes for drama channel
                "dead tree branch at sunset, dramatic golden hour lighting, cinematic wide shot, lonely landscape",
                "destroyed forest clearing with lone standing tree, environmental drama, post-apocalyptic nature",
                "dark forest with approaching storm clouds, ominous atmosphere, dramatic lighting",
                "misty forest path disappearing into darkness, emotional cinematic, no animals",
                "burning forest in background, environmental tragedy, dramatic wide angle, no animals",
                "rain falling on broken tree branches, sad atmosphere, moody cinematic photography",
                "sunrise over deforested hillside, environmental contrast, dramatic documentary style",
            ],
            "fb_fanspage": [
                "stunning portrait of a tarsier with galaxy eyes, viral social media worthy, vibrant colorful background",
                "world record smallest primate comparison with coin, fascinating scale photo, shareable viral content",
                "infographic style tarsier facts overlay, bold text, social media optimized, educational viral content",
                "incredible macro shot of tarsier fingers gripping branch, amazing detail, viral worthy photography",
                "baby tarsier first time opening eyes, heartwarming moment, emotional viral animal content",
                "tarsier conservation success story image, hopeful green scene, inspiring shareable content",
                "split screen tarsier vs human eye comparison, mind blowing facts style, social media optimized",
            ],
        }

    def _get_headers(self, account_key: str) -> dict:
        """Each account uses its OWN HF API key."""
        api_key = HF_API_KEYS.get(account_key)
        if not api_key:
            raise ValueError(f"HF API Key missing for {account_key}")
        return {"Authorization": f"Bearer {api_key}"}

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
                        print(f"HF CREDITS DEPLETED (402) — falling back to stock-only mode")
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
    # STOCK VIDEO — Tarsier only
    # ==========================================

    def _download_pexels_clips(self, account_key: str, topic: str, num_clips: int) -> List[str]:
        if not self.pexels_key:
            return []
        print(f"[{account_key}] Searching Pexels for TARSIER clips...")
        headers = {"Authorization": self.pexels_key}
        downloaded = []
        used_ids = set()
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
                    if len(downloaded) >= num_clips or video["id"] in used_ids:
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
                            used_ids.add(video["id"])
                            print(f"[{account_key}] Pexels clip {len(downloaded)} ({len(dl.content)//1024}KB)")
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
        used_ids = set()
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
                    if len(downloaded) >= num_clips or video["id"] in used_ids:
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
                            used_ids.add(video["id"])
                            print(f"[{account_key}] Pixabay clip {len(downloaded)} ({len(dl.content)//1024}KB)")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"[{account_key}] Download error: {e}")
            except Exception as e:
                print(f"[{account_key}] Pixabay error: {e}")
        return downloaded

    def download_stock_clips(self, account_key: str, topic: str, num_clips: int = 7) -> List[str]:
        pexels = self._download_pexels_clips(account_key, topic, num_clips)
        pixabay = self._download_pixabay_clips(account_key, topic, num_clips)
        all_clips = pexels + pixabay
        random.shuffle(all_clips)
        print(f"[{account_key}] Stock clips: {len(all_clips)} (Pexels:{len(pexels)} Pixabay:{len(pixabay)})")
        return all_clips[:num_clips]

    # ==========================================
    # AI TARSIER IMAGES — Per-account themed
    # ==========================================
    
    def generate_tarsier_image(self, account_key: str, index: int, topic: str) -> Optional[str]:
        """Generates AI image using FLUX.
        RULES from correction plan:
        - flux_allowed=False channels: still generate tarsier images (stock footage preferred, AI as supplement)
        - flux_allowed=True channels: generate ENVIRONMENT ONLY (no tarsier/animal)
        """
        account = ACCOUNTS.get(account_key, {})
        
        prompts = self.account_prompts.get(account_key, self.account_prompts["fb_fanspage"])
        base_prompt = prompts[index % len(prompts)]
        
        # Add topic + random seed to make each image unique across runs
        seed = random.randint(1000, 9999)
        prompt = f"{base_prompt}, related to {topic}, seed:{seed}"
        
        # Enforce FLUX rules: if flux_allowed=True, ensure no animal keywords
        if account.get("flux_allowed", False):
            # Double-check: strip any animal keywords that might have slipped in
            forbidden_words = ["tarsier", "animal", "primate", "creature", "monkey", "ape"]
            for word in forbidden_words:
                prompt = prompt.replace(word, "scene")
            img_type = "environment"
        else:
            img_type = "tarsier"
        
        print(f"[{account_key}] AI {img_type} image {index}: {base_prompt[:50]}... (seed:{seed})")
        headers = self._get_headers(account_key)
        payload = {"inputs": prompt}
        
        content = self._make_api_request(self.image_model_url, headers, payload)
        if content is None:
            content = self._make_api_request(self.image_fallback_url, headers, payload)
        
        if content:
            safe = self._safe_topic(topic)
            filename = os.path.join(TMP_DIR, f"{account_key}_{safe}_ai_{index}.png")
            with open(filename, "wb") as f:
                f.write(content)
            print(f"[{account_key}] AI {img_type} image {index} saved.")
            return filename
        return None

    # ==========================================
    # MAIN: Per-account unique tarsier content
    # ==========================================
    
    def generate_all_clips(self, script_segments: List[str], account_key: str, topic: str) -> list:
        """
        Per-channel visual source rules from VIDEO_PROFILES:
        - stock_only: Pexels + Pixabay real tarsier footage ONLY. ZERO AI images.
        - stock_plus_flux_env: Stock tarsier + FLUX environment-only images.
        """
        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        visual_source = profile.get("visual_source", "stock_only")
        TARGET_CLIPS = 12
        
        if visual_source == "stock_only":
            # STOCK ONLY: download as many tarsier clips as possible, ZERO AI
            print(f"[{account_key}] Visual source: STOCK ONLY (Pexels+Pixabay real footage, ZERO FLUX)")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=TARGET_CLIPS)
            all_media = [("video", clip) for clip in stock_clips]
            
            # If stock is insufficient, the loop_engine will expand these via variations
            # in assemble.py — we do NOT fall back to AI images
            if len(all_media) < 3:
                print(f"[{account_key}] WARNING: Only {len(all_media)} stock clips found. Loop engine will expand.")
            
            stock_n = len(all_media)
            print(f"[{account_key}] Final: {stock_n} stock clips (ZERO AI - correction plan rule)")
            return all_media
        
        elif visual_source == "stock_plus_flux_env":
            # HYBRID: Stock tarsier clips + FLUX environment-only images
            MAX_STOCK = 7
            MIN_ENV_AI = 5
            
            print(f"[{account_key}] Visual source: Stock tarsier + FLUX environment-only")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=MAX_STOCK)
            all_media = [("video", clip) for clip in stock_clips]
            
            # AI environment images — NEVER tarsier, only backgrounds/atmosphere
            ai_needed = max(TARGET_CLIPS - len(stock_clips), MIN_ENV_AI)
            print(f"[{account_key}] Generating {ai_needed} ENVIRONMENT-ONLY AI images (ZERO tarsier)...")
            ai_failed = 0
            for i in range(ai_needed):
                img = self.generate_tarsier_image(account_key, i, topic)
                if img:
                    all_media.append(("image", img))
                else:
                    ai_failed += 1
                time.sleep(2)
            
            # If ALL AI images failed (e.g. HF credits depleted), continue with stock only
            if ai_failed == ai_needed:
                print(f"[{account_key}] WARNING: All AI images failed (HF credits?). Continuing with stock-only + loop variations.")
            
            random.shuffle(all_media)
            stock_n = sum(1 for t, _ in all_media if t == "video")
            ai_n = sum(1 for t, _ in all_media if t == "image")
            print(f"[{account_key}] Final: {len(all_media)} clips ({stock_n} stock tarsier + {ai_n} AI environment)")
            return all_media
        
        else:
            # Fallback: stock only
            print(f"[{account_key}] Unknown visual_source '{visual_source}', defaulting to stock_only")
            stock_clips = self.download_stock_clips(account_key, topic, num_clips=TARGET_CLIPS)
            return [("video", clip) for clip in stock_clips]

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
