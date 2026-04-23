"""
Visual Engine — Per-Channel Image Styling System
Transforms raw tarsier images into channel-specific art styles.
V3: Background removal (rembg) + themed background per channel via CF Workers AI.

Channels:
  yt_documenter: REAL photo — slight color grade only (no BG change)
  yt_funny:      Meme bright — tarsier on colorful abstract BG
  yt_anthro:     Cartoon     — cartoon tarsier on illustrated world BG
  yt_pov:        Dark horror — tarsier on dark misty forest BG
  yt_drama:      Cinematic   — tarsier on dramatic landscape BG
  fb_fanspage:   Bold vivid  — tarsier on vibrant nature BG
"""
import os
import io
import random
import requests
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
from typing import List, Tuple, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import ACCOUNTS, TMP_DIR, CF_ACCOUNTS, CF_ACCOUNTS_BACKUP, HF_API_KEYS, HF_API_KEYS_BACKUP


# ========================================
# THEMED BACKGROUND PROMPTS PER CHANNEL
# CF Workers AI generates these as backgrounds
# ========================================

# NEGATIVE PROMPT appended to all BG generation requests
_BG_NEGATIVE = "no humans, no people, no person, no face, no hands, no text, no watermark"

THEMED_BG_PROMPTS = {
    "yt_funny": [
        "bright colorful abstract pop art background, vibrant neon colors, comic book style, fun playful, empty scene, no characters",
        "pastel rainbow gradient background with geometric shapes, cute kawaii style, sparkles, cheerful mood, empty background",
        "yellow and orange comic burst explosion background, meme style, bold rays, internet humor, no characters",
        "tropical jungle clearing with funny oversized flowers, whimsical cartoon style, bright colors, empty scene",
    ],
    "yt_anthro": [
        "cartoon illustration of a cozy forest treehouse interior, warm colors, studio ghibli style, empty room",
        "cartoon city street at night, warm streetlights, illustrated, digital painting, anime style, empty scene",
        "cartoon tropical jungle clearing, warm sunlight, children book illustration, whimsical, empty scene",
        "illustrated cozy coffee shop interior, warm lighting, cartoon style, empty scene, no characters",
    ],
    "yt_pov": [
        "dark misty tropical forest at night, moonlight through trees, horror atmosphere, fog, eerie, empty scene",
        "dark jungle path at midnight, bioluminescent mushrooms, creepy fog, horror movie lighting, empty path",
        "abandoned dark rainforest, twisted trees, heavy fog, blue moonlight, terrifying atmosphere, no characters",
        "dense dark forest with glowing eyes in shadows, horror atmosphere, moonlit clearing, empty scene",
    ],
    "yt_drama": [
        "dramatic sunset over tropical forest, golden hour, cinematic lighting, volumetric rays, empty landscape",
        "stormy sky over dense jungle, dramatic lightning, cinematic wide shot, epic atmosphere, no characters",
        "misty mountain forest at dawn, dramatic clouds, warm golden light breaking through, emotional, empty scene",
        "tropical rainforest canopy from above, golden hour light rays, cinematic drone shot, empty landscape",
    ],
    "fb_fanspage": [
        "vibrant tropical forest background, lush green leaves, bright sunlight, professional nature photography, empty scene",
        "beautiful tropical rainforest canopy, vivid colors, sharp detail, national geographic style, no characters",
        "stunning green jungle background, rays of light, emerald leaves, ultra high quality, empty scene",
        "tropical paradise forest clearing, crystal clear stream, lush vegetation, professional photo, empty scene",
    ],
}


# ========================================
# PER-CHANNEL VISUAL STYLE DEFINITIONS
# ========================================

VISUAL_STYLES = {
    "yt_documenter": {
        "name": "documentary",
        "saturation": 0.80,         # desaturated = NatGeo real
        "contrast": 1.20,
        "brightness": 1.0,
        "sharpness": 1.4,
        "color_tint": (12, 8, -5),  # warm golden tone
        "grain": 12,               # noticeable film grain
        "vignette": 0.15,
        "special": None,
    },
    "yt_funny": {
        "name": "meme_bright",
        "saturation": 1.80,          # EXTREMELY saturated = meme
        "contrast": 1.45,
        "brightness": 1.20,
        "sharpness": 1.6,
        "color_tint": (15, 15, -5),  # warm yellow push
        "grain": 0,
        "vignette": 0,
        "special": "funny_crop",
    },
    "yt_anthro": {
        "name": "cartoon",
        "saturation": 1.60,           # very vivid cartoon
        "contrast": 1.30,
        "brightness": 1.15,
        "sharpness": 0.5,             # soft = illustrated feel
        "color_tint": (5, 15, 20),    # cool blue-green tint
        "grain": 0,
        "vignette": 0,
        "special": "cartoon",
    },
    "yt_pov": {
        "name": "dark_horror",
        "saturation": 0.20,            # almost B&W
        "contrast": 1.50,
        "brightness": 0.55,            # VERY DARK
        "sharpness": 1.3,
        "color_tint": (-15, -8, 10),   # cold blue tint
        "grain": 30,                   # heavy noise grain
        "vignette": 0.50,              # VERY heavy vignette
        "special": None,
    },
    "yt_drama": {
        "name": "cinematic",
        "saturation": 0.85,
        "contrast": 1.25,
        "brightness": 0.90,
        "sharpness": 1.1,
        "color_tint": (15, 8, -8),     # strong warm cinematic
        "grain": 15,
        "vignette": 0.25,
        "special": None,               # DISABLED — full vertical screen
    },
    "fb_fanspage": {
        "name": "bold_vivid",
        "saturation": 1.40,       # vivid pop
        "contrast": 1.25,
        "brightness": 1.10,
        "sharpness": 1.5,         # extra sharp
        "color_tint": (8, 8, 0),
        "grain": 0,
        "vignette": 0.08,
        "special": None,
    },
}


def _remove_background(img: Image.Image) -> Image.Image:
    """Remove background from tarsier photo using rembg AI.
    Returns RGBA image with transparent background.
    Falls back to elliptical mask if rembg unavailable."""
    try:
        from rembg import remove
        # Convert to bytes for rembg
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        result = remove(buf.read())
        return Image.open(io.BytesIO(result)).convert("RGBA")
    except Exception as e:
        print(f"[VisualEngine] rembg failed ({e}), using elliptical mask fallback")
        return _elliptical_mask_fallback(img)


def _elliptical_mask_fallback(img: Image.Image) -> Image.Image:
    """Create elliptical soft-edge mask (fallback when rembg unavailable)."""
    w, h = img.size
    rgba = img.convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    # Ellipse covers center 70% of image
    margin_x, margin_y = int(w * 0.15), int(h * 0.10)
    draw.ellipse([margin_x, margin_y, w - margin_x, h - margin_y], fill=255)
    # Blur edges for soft transition
    mask = mask.filter(ImageFilter.GaussianBlur(radius=30))
    rgba.putalpha(mask)
    return rgba


def _try_cf_generate(account_id: str, api_token: str, prompt: str, width: int, height: int, label: str) -> Optional[Image.Image]:
    """Try generating background via Cloudflare Workers AI. Returns Image or None.
    Supports both raw binary image AND JSON-wrapped base64 response formats.
    Retries once on HTTP 500 (transient server error)."""
    import time
    import base64
    for attempt in range(2):  # Max 2 attempts
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
            headers = {"Authorization": f"Bearer {api_token}"}
            # FLUX requires standard dimensions (multiples of 8, within model limits)
            # Force standard square 1024x1024 — resized to target after generation
            payload = {"prompt": f"{prompt}. {_BG_NEGATIVE}", "width": 1024, "height": 1024}
            
            if attempt == 0:
                print(f"[VisualEngine] {label}: {prompt[:50]}...")
            else:
                print(f"[VisualEngine] {label}: retry after 500...")
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code == 200:
                ct = resp.headers.get("content-type", "")
                
                # FORMAT 1: Raw binary image (old CF behavior)
                if ct.startswith("image"):
                    bg = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    bg = bg.resize((width, height), Image.LANCZOS)
                    print(f"[VisualEngine] {label} SUCCESS (raw image)")
                    return bg
                
                # FORMAT 2: JSON-wrapped base64 image (new CF behavior 2026+)
                # Response: {"result":{"image":"/9j/4AAQSkZJRg..."}}
                if "json" in ct:
                    try:
                        data = resp.json()
                        img_b64 = ""
                        # Try nested format: {"result":{"image":"..."}}
                        if isinstance(data, dict):
                            result = data.get("result", data)
                            if isinstance(result, dict):
                                img_b64 = result.get("image", "")
                            elif isinstance(result, str):
                                img_b64 = result
                        
                        if img_b64 and len(img_b64) > 1000:
                            img_bytes = base64.b64decode(img_b64)
                            bg = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                            bg = bg.resize((width, height), Image.LANCZOS)
                            print(f"[VisualEngine] {label} SUCCESS (base64 JSON)")
                            return bg
                        else:
                            # JSON but no valid image data — real error
                            body_preview = resp.text[:200]
                            print(f"[VisualEngine] {label} JSON response but no image data: {body_preview}")
                            return None
                    except Exception as e:
                        print(f"[VisualEngine] {label} JSON parse error: {e}")
                        return None
                
                # FORMAT 3: Unknown content-type with large body — try as raw image
                if len(resp.content) > 5000:
                    try:
                        bg = Image.open(io.BytesIO(resp.content)).convert("RGB")
                        bg = bg.resize((width, height), Image.LANCZOS)
                        print(f"[VisualEngine] {label} SUCCESS (raw content)")
                        return bg
                    except Exception:
                        pass
                
                print(f"[VisualEngine] {label} HTTP 200 but unrecognized format (ct={ct}, size={len(resp.content)})")
                return None
                
            elif resp.status_code == 500 and attempt == 0:
                print(f"[VisualEngine] {label} got HTTP 500, retrying in 5s...")
                time.sleep(5)
                continue
            else:
                print(f"[VisualEngine] {label} failed (HTTP {resp.status_code})")
                return None
        except Exception as e:
            print(f"[VisualEngine] {label} error: {e}")
            return None
    return None


def _try_hf_generate(hf_key: str, prompt: str, width: int, height: int, label: str) -> Optional[Image.Image]:
    """Try generating background via HuggingFace Inference API. Returns Image or None.
    Supports both raw binary image AND JSON-wrapped base64 response formats."""
    import base64
    try:
        # UPDATED 2026-04-23: Use router endpoint (api-inference deprecated → 404)
        hf_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
        hf_headers = {"Authorization": f"Bearer {hf_key}"}
        # FLUX.1 uses simple prompt (negative prompt embedded in text)
        hf_payload = {"inputs": f"{prompt}. {_BG_NEGATIVE}"}
        
        print(f"[VisualEngine] {label}...")
        resp = requests.post(hf_url, headers=hf_headers, json=hf_payload, timeout=120)
        
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "")
            
            # FORMAT 1: Raw binary image (typical HF behavior)
            if ct.startswith("image") or (len(resp.content) > 5000 and "json" not in ct):
                try:
                    bg = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    bg = bg.resize((width, height), Image.LANCZOS)
                    print(f"[VisualEngine] {label} SUCCESS (raw image)")
                    return bg
                except Exception:
                    pass
            
            # FORMAT 2: JSON-wrapped base64 (if HF changes format like CF did)
            if "json" in ct or resp.content[:1] == b'{':
                try:
                    data = resp.json()
                    img_b64 = ""
                    if isinstance(data, dict):
                        # Try common JSON structures
                        for key in ["image", "generated_image", "output"]:
                            if key in data and isinstance(data[key], str) and len(data[key]) > 1000:
                                img_b64 = data[key]
                                break
                        if not img_b64:
                            result = data.get("result", data)
                            if isinstance(result, dict):
                                img_b64 = result.get("image", "")
                    elif isinstance(data, list) and data:
                        img_b64 = data[0].get("image", "") if isinstance(data[0], dict) else ""
                    
                    if img_b64 and len(img_b64) > 1000:
                        img_bytes = base64.b64decode(img_b64)
                        bg = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        bg = bg.resize((width, height), Image.LANCZOS)
                        print(f"[VisualEngine] {label} SUCCESS (base64 JSON)")
                        return bg
                except Exception as e:
                    print(f"[VisualEngine] {label} JSON parse failed: {e}")
            
            print(f"[VisualEngine] {label} HTTP 200 but no valid image (ct={ct}, size={len(resp.content)})")
        elif resp.status_code == 402:
            print(f"[VisualEngine] {label} DEPLETED (402)")
        else:
            print(f"[VisualEngine] {label} failed (HTTP {resp.status_code})")
    except Exception as e:
        print(f"[VisualEngine] {label} error: {e}")
    return None


def _generate_themed_background(account_key: str, width: int, height: int, index: int = 0) -> Image.Image:
    """Generate a themed background.
    Full 4-layer fallback: CF Primary → CF Backup → HF Primary → HF Backup → gradient.
    Each channel has 2 CF accounts + 2 HF keys = 4 chances before gradient."""
    prompts = THEMED_BG_PROMPTS.get(account_key, [])
    if not prompts:
        return _gradient_fallback(account_key, width, height)
    
    prompt = prompts[index % len(prompts)]
    
    # === LAYER 1: CF Primary ===
    cf1 = CF_ACCOUNTS.get(account_key, {})
    if cf1.get("account_id") and cf1.get("api_token"):
        result = _try_cf_generate(cf1["account_id"], cf1["api_token"], prompt, width, height, f"CF-1 {account_key}")
        if result:
            return result
    
    # === LAYER 2: CF Backup ===
    cf2 = CF_ACCOUNTS_BACKUP.get(account_key, {})
    if cf2.get("account_id") and cf2.get("api_token"):
        result = _try_cf_generate(cf2["account_id"], cf2["api_token"], prompt, width, height, f"CF-2 {account_key}")
        if result:
            return result
    
    # === LAYER 3: HF Primary ===
    hf1 = HF_API_KEYS.get(account_key, "")
    if hf1:
        result = _try_hf_generate(hf1, prompt, width, height, f"HF-1 {account_key}")
        if result:
            return result
    
    # === LAYER 4: HF Backup ===
    hf2 = HF_API_KEYS_BACKUP.get(account_key, "")
    if hf2:
        result = _try_hf_generate(hf2, prompt, width, height, f"HF-2 {account_key}")
        if result:
            return result
    
    # === LAYER 5: Gradient (last resort) ===
    print(f"[VisualEngine] ALL 4 APIs failed for {account_key}, using gradient fallback")
    return _gradient_fallback(account_key, width, height)


def _gradient_fallback(account_key: str, width: int, height: int) -> Image.Image:
    """Generate a solid gradient background as fallback."""
    GRADIENTS = {
        "yt_funny":    ((255, 200, 50), (255, 100, 50)),    # Yellow → Orange
        "yt_anthro":   ((255, 200, 130), (230, 160, 80)),   # Warm peach → Amber
        "yt_pov":      ((10, 10, 30), (20, 40, 50)),        # Near black → Dark blue
        "yt_drama":    ((30, 20, 10), (80, 50, 20)),        # Dark → Warm brown
        "fb_fanspage": ((20, 80, 20), (50, 150, 50)),       # Dark green → Forest
    }
    top, bottom = GRADIENTS.get(account_key, ((30, 30, 30), (60, 60, 60)))
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        arr[y, :] = [int(top[c] + (bottom[c] - top[c]) * ratio) for c in range(3)]
    return Image.fromarray(arr)


def _composite_on_background(tarsier_rgba: Image.Image, background: Image.Image) -> Image.Image:
    """Place tarsier (with transparent BG) centered on themed background."""
    bg = background.copy().convert("RGBA")
    fg = tarsier_rgba.copy()
    
    # Resize tarsier to fit ~85% of background
    bg_w, bg_h = bg.size
    fg_w, fg_h = fg.size
    scale = min(bg_w * 0.85 / fg_w, bg_h * 0.85 / fg_h)
    new_w, new_h = int(fg_w * scale), int(fg_h * scale)
    fg = fg.resize((new_w, new_h), Image.LANCZOS)
    
    # Center position
    x = (bg_w - new_w) // 2
    y = (bg_h - new_h) // 2
    
    bg.paste(fg, (x, y), fg)  # Use alpha channel as mask
    return bg.convert("RGB")


def apply_channel_style(image_path: str, account_key: str, output_path: str,
                        image_index: int = 0) -> str:
    """Apply per-channel visual style to an image.
    V3: Background removal + themed background + color styling.
    
    Flow for non-documenter channels:
    1. Remove background from tarsier photo (rembg)
    2. Generate themed background (CF Workers AI)
    3. Composite tarsier onto themed BG
    4. Apply channel color filters
    
    Documenter keeps original photo (real footage look).
    """
    try:
        img = Image.open(image_path).convert("RGB")
        style = VISUAL_STYLES.get(account_key, VISUAL_STYLES["fb_fanspage"])
        w, h = img.size
        
        print(f"[VisualEngine] Applying '{style['name']}' style to {os.path.basename(image_path)}")
        
        # ====== V3: BACKGROUND REPLACEMENT (non-documenter only) ======
        if account_key != "yt_documenter" and account_key in THEMED_BG_PROMPTS:
            print(f"[VisualEngine] [{account_key}] Background replacement...")
            # Step A: Remove background
            tarsier_rgba = _remove_background(img)
            # Step B: Generate themed background
            themed_bg = _generate_themed_background(account_key, w, h, image_index)
            # Step C: Composite
            img = _composite_on_background(tarsier_rgba, themed_bg)
            print(f"[VisualEngine] [{account_key}] Composite done!")
        
        # ====== CHANNEL COLOR FILTERS ======
        
        # 1. Special effects (cartoon, letterbox, etc.)
        if style["special"] == "cartoon":
            img = _apply_cartoon_filter(img)
        elif style["special"] == "funny_crop":
            img = _apply_funny_crop(img)
        
        # 2. Saturation
        if style["saturation"] != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(style["saturation"])
        
        # 3. Contrast
        if style["contrast"] != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(style["contrast"])
        
        # 4. Brightness
        if style["brightness"] != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(style["brightness"])
        
        # 5. Sharpness
        if style["sharpness"] != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(style["sharpness"])
        
        # 6. Color tint
        tint = style.get("color_tint", (0, 0, 0))
        if any(t != 0 for t in tint):
            img = _apply_color_tint(img, tint)
        
        # 7. Film grain
        if style["grain"] > 0:
            img = _apply_grain(img, style["grain"])
        
        # 8. Vignette
        if style["vignette"] > 0:
            img = _apply_vignette(img, style["vignette"])
        
        # 9. Letterbox (drama channel)
        if style["special"] == "letterbox":
            img = _apply_letterbox(img)
        
        img.save(output_path, "PNG", quality=95)
        return output_path
        
    except Exception as e:
        print(f"[VisualEngine] Error applying style: {e}")
        try:
            import shutil
            shutil.copy2(image_path, output_path)
        except Exception:
            pass
        return output_path


def generate_scene_variations(image_path: str, account_key: str, 
                               output_dir: str, num_scenes: int = 8) -> List[str]:
    """Generate 8 scene variations from one styled image.
    Blueprint: tiap gambar jadi 5-10 scene.
    Variations: full, mirror, zoom_in, zoom_out, crop_left, crop_right, close_up_eye, blur.
    Target: 6 images × 8 variations = 48 scenes → ~4 minutes video.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        scenes = []
        basename = os.path.splitext(os.path.basename(image_path))[0]
        
        SCENE_TWEAKS = [
            "full",          # Original full frame
            "mirror",        # Horizontal flip
            "zoom_in",       # Center 60% crop (zoom in)
            "zoom_out",      # Image on padded background (zoom out effect)
            "crop_left",     # Left 65% crop
            "crop_right",    # Right 65% crop
            "close_up_eye",  # Upper center crop (tarsier eyes area)
            "blur_bg",       # Foreground sharp, background blurred
        ]
        
        for i, name in enumerate(SCENE_TWEAKS[:num_scenes]):
            scene_path = os.path.join(output_dir, f"{basename}_scene_{i}_{name}.png")
            
            try:
                if name == "full":
                    scene_img = img.copy()
                
                elif name == "mirror":
                    scene_img = img.transpose(Image.FLIP_LEFT_RIGHT)
                
                elif name == "zoom_in":
                    # Center 60% crop → feels like zoom in
                    margin_x, margin_y = int(w * 0.20), int(h * 0.20)
                    scene_img = img.crop((margin_x, margin_y, w - margin_x, h - margin_y))
                
                elif name == "zoom_out":
                    # Place image on blurred+darkened padded canvas
                    canvas = img.copy().filter(ImageFilter.GaussianBlur(radius=20))
                    enhancer = ImageEnhance.Brightness(canvas)
                    canvas = enhancer.enhance(0.4)
                    small = img.resize((int(w * 0.7), int(h * 0.7)), Image.LANCZOS)
                    offset_x = (w - small.width) // 2
                    offset_y = (h - small.height) // 2
                    canvas.paste(small, (offset_x, offset_y))
                    scene_img = canvas
                
                elif name == "crop_left":
                    scene_img = img.crop((0, 0, int(w * 0.65), h))
                
                elif name == "crop_right":
                    scene_img = img.crop((int(w * 0.35), 0, w, h))
                
                elif name == "close_up_eye":
                    # Upper center crop (where tarsier eyes typically are)
                    cx, cy = w // 2, int(h * 0.35)
                    crop_w, crop_h = int(w * 0.45), int(h * 0.35)
                    x1 = max(0, cx - crop_w // 2)
                    y1 = max(0, cy - crop_h // 2)
                    scene_img = img.crop((x1, y1, min(x1 + crop_w, w), min(y1 + crop_h, h)))
                
                elif name == "blur_bg":
                    # Blur the whole image lightly, keep center sharp (faux depth of field)
                    blurred = img.filter(ImageFilter.GaussianBlur(radius=8))
                    mask = Image.new("L", (w, h), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    # Sharp ellipse in center
                    mx, my = int(w * 0.2), int(h * 0.15)
                    draw_mask.ellipse([mx, my, w - mx, h - my], fill=255)
                    mask = mask.filter(ImageFilter.GaussianBlur(radius=40))
                    scene_img = Image.composite(img, blurred, mask)
                
                else:
                    scene_img = img.copy()
                
                # Resize to standard vertical resolution
                scene_img = scene_img.resize((1080, 1920), Image.LANCZOS)
                scene_img.save(scene_path, "PNG")
                scenes.append(scene_path)
                
            except Exception as e:
                print(f"[VisualEngine] Scene '{name}' failed: {e}")
                continue
        
        print(f"[VisualEngine] {account_key}: {len(scenes)} scene variations from {os.path.basename(image_path)}")
        return scenes
        
    except Exception as e:
        print(f"[VisualEngine] Scene generation error: {e}")
        return []


# ========================================
# INTERNAL FILTER FUNCTIONS
# ========================================

def _apply_cartoon_filter(img: Image.Image) -> Image.Image:
    """VERY STRONG cartoon/illustration effect.
    Must look OBVIOUSLY like a cartoon, not a filtered photo.
    Technique: Extreme smoothing + 6 colors + bold edges + posterize.
    """
    # Step 1: EXTREME smoothing (6 passes — destroy ALL photo detail)
    smooth = img.copy()
    for _ in range(6):
        smooth = smooth.filter(ImageFilter.SMOOTH_MORE)
    # Extra bilateral-like smooth
    smooth = smooth.filter(ImageFilter.ModeFilter(size=7))
    
    # Step 2: EXTREME color quantize (6 colors = very flat cartoon)
    quantized = smooth.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    quantized = quantized.convert("RGB")
    
    # Step 3: Posterize for even flatter color bands
    quantized = ImageOps.posterize(quantized, 3)
    
    # Step 4: VERY BOLD edge detection (thick black outlines)
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = edges.filter(ImageFilter.MaxFilter(5))  # VERY thick edges
    edges = edges.point(lambda x: 0 if x > 20 else 255)  # Lower threshold = more edges
    edges = edges.convert("RGB")
    
    # Step 5: Multiply bold edges onto flat cartoon colors
    result = np.array(quantized).astype(np.float32)
    edge_arr = np.array(edges).astype(np.float32) / 255.0
    result = (result * edge_arr).astype(np.uint8)
    
    # Step 6: Strong brightness boost
    cart_img = Image.fromarray(result)
    enhancer = ImageEnhance.Brightness(cart_img)
    cart_img = enhancer.enhance(1.35)
    
    # Step 7: VERY vivid saturated colors
    enhancer = ImageEnhance.Color(cart_img)
    cart_img = enhancer.enhance(1.8)
    
    return cart_img


def _apply_funny_crop(img: Image.Image) -> Image.Image:
    """Random slight rotation + brightness for meme feel."""
    angle = random.choice([-3, -2, -1, 0, 1, 2, 3])
    if angle != 0:
        img = img.rotate(angle, fillcolor=(255, 255, 255), expand=False)
    return img


def _apply_color_tint(img: Image.Image, tint: Tuple[int, int, int]) -> Image.Image:
    """Apply RGB color tint to image."""
    arr = np.array(img).astype(np.int16)
    arr[:, :, 0] = np.clip(arr[:, :, 0] + tint[0], 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + tint[1], 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] + tint[2], 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _apply_grain(img: Image.Image, intensity: int) -> Image.Image:
    """Add film grain noise."""
    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, intensity, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _apply_vignette(img: Image.Image, strength: float) -> Image.Image:
    """Apply vignette (darkened edges)."""
    w, h = img.size
    arr = np.array(img).astype(np.float32)
    
    # Create radial gradient
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    dist_norm = dist / max_dist
    
    # Apply vignette
    vignette_mask = 1.0 - (dist_norm * strength)
    vignette_mask = np.clip(vignette_mask, 0.3, 1.0)  # Don't go too dark
    
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * vignette_mask
    
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _apply_letterbox(img: Image.Image) -> Image.Image:
    """Add cinematic 2.35:1 letterbox bars."""
    w, h = img.size
    target_h = int(w / 2.35)
    bar_h = (h - target_h) // 2
    
    if bar_h > 0:
        arr = np.array(img)
        arr[:bar_h] = 0       # Top bar
        arr[-bar_h:] = 0      # Bottom bar
        return Image.fromarray(arr)
    return img


# ========================================
# BATCH STYLING — Style all images for one channel
# ========================================

def style_batch_for_channel(raw_images: List[str], account_key: str, 
                            output_dir: str) -> List[str]:
    """Apply channel style to all raw images and generate scene variations.
    
    Blueprint: 5-10 gambar → tiap gambar jadi 5-10 scene → total 48+ scenes.
    Each channel gets SHUFFLED scene order so videos look different.
    
    Args:
        raw_images: List of raw image paths (shared pool)
        account_key: Channel identifier
        output_dir: Where to save styled images
        
    Returns:
        List of all scene variation paths (styled + cropped), SHUFFLED per channel
    """
    os.makedirs(output_dir, exist_ok=True)
    all_scenes = []
    
    for i, raw_path in enumerate(raw_images):
        if not os.path.exists(raw_path):
            continue
            
        # Step 1: Apply channel visual style (V3: rembg + themed BG + color filter)
        styled_path = os.path.join(output_dir, f"{account_key}_styled_{i}.png")
        apply_channel_style(raw_path, account_key, styled_path, image_index=i)
        
        # Step 2: Generate 8 scene variations from styled image
        scenes = generate_scene_variations(styled_path, account_key, output_dir, num_scenes=8)
        all_scenes.extend(scenes)
    
    # Step 3: SHUFFLE scene order per channel (deterministic but unique)
    # Same images but different sequence = videos feel different
    random.seed(hash(account_key) + 42)
    random.shuffle(all_scenes)
    random.seed()  # Reset to true random
    
    print(f"[VisualEngine] {account_key}: {len(all_scenes)} total scenes from {len(raw_images)} raw images (SHUFFLED)")
    return all_scenes
