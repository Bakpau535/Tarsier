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
from src.config import ACCOUNTS, TMP_DIR


# ========================================
# THEMED BACKGROUND PROMPTS PER CHANNEL
# CF Workers AI generates these as backgrounds
# ========================================

THEMED_BG_PROMPTS = {
    "yt_funny": [
        "bright colorful abstract pop art background, vibrant neon colors, comic book style, fun playful",
        "pastel rainbow gradient background, cute kawaii style, sparkles, cheerful mood",
        "yellow and orange explosion background, meme style, bold comic burst, internet humor",
    ],
    "yt_anthro": [
        "cartoon illustration of a cozy office interior, warm colors, studio ghibli style, desk and window",
        "cartoon city street at night, warm streetlights, illustrated, digital painting, anime style",
        "cartoon living room interior, warm colors, children book illustration, cozy home",
    ],
    "yt_pov": [
        "dark misty tropical forest at night, moonlight through trees, horror atmosphere, fog, eerie",
        "dark jungle path at midnight, bioluminescent mushrooms, creepy fog, horror movie lighting",
        "abandoned dark rainforest, twisted trees, heavy fog, blue moonlight, terrifying atmosphere",
    ],
    "yt_drama": [
        "dramatic sunset over tropical forest, golden hour, cinematic lighting, volumetric rays",
        "stormy sky over dense jungle, dramatic lightning, cinematic wide shot, epic atmosphere",
        "misty mountain forest at dawn, dramatic clouds, warm golden light breaking through, emotional",
    ],
    "fb_fanspage": [
        "vibrant tropical forest background, lush green leaves, bright sunlight, professional nature photography",
        "beautiful tropical rainforest canopy, vivid colors, sharp detail, national geographic style",
        "stunning green jungle background, rays of light, emerald leaves, ultra high quality",
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
        "special": "letterbox",
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


def _generate_themed_background(account_key: str, width: int, height: int, index: int = 0) -> Image.Image:
    """Generate a themed background using CF Workers AI.
    Falls back to solid color gradient if CF unavailable."""
    prompts = THEMED_BG_PROMPTS.get(account_key, [])
    if not prompts:
        return _gradient_fallback(account_key, width, height)
    
    prompt = prompts[index % len(prompts)]
    
    # Get CF credentials for this channel
    cf_config = ACCOUNTS.get(account_key, {})
    account_id = cf_config.get("account_id", "")
    api_token = cf_config.get("api_token", "")
    
    if not account_id or not api_token:
        print(f"[VisualEngine] No CF credentials for {account_key}, using gradient fallback")
        return _gradient_fallback(account_key, width, height)
    
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {"prompt": prompt, "width": min(width, 1024), "height": min(height, 1024)}
        
        print(f"[VisualEngine] Generating {account_key} themed BG: {prompt[:60]}...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            bg = Image.open(io.BytesIO(resp.content)).convert("RGB")
            bg = bg.resize((width, height), Image.LANCZOS)
            print(f"[VisualEngine] CF themed BG generated for {account_key}")
            return bg
        else:
            print(f"[VisualEngine] CF BG failed ({resp.status_code}), using gradient")
            return _gradient_fallback(account_key, width, height)
    except Exception as e:
        print(f"[VisualEngine] CF BG error: {e}")
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
                               output_dir: str, num_scenes: int = 5) -> List[str]:
    """Generate CHANNEL-SPECIFIC scene variations from one styled image.
    Same image → different framing per channel (bahan sama, rasa beda).
    
    Blueprint visual per channel:
      yt_documenter: wide shots, steady pans (NatGeo style)
      yt_funny:      absurd zooms, extreme close-up, tilts
      yt_anthro:     medium shots, varied framing (cartoon already applied)
      yt_pov:        EXTREME close-up mata, dark tight crops
      yt_drama:      cinematic wide + medium (letterbox already applied)
      fb_fanspage:   clean center crops, professional framing
    """
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        scenes = []
        basename = os.path.splitext(os.path.basename(image_path))[0]
        
        # ========================================
        # FULL FRAME SCENE VARIATIONS (NO CROP)
        # All scenes are FULL 1920x1080. Differentiation comes from:
        # - Channel visual STYLES (cartoon, horror, meme, etc.)
        # - Minor framing tweaks (mirror, slight rotate) for variety
        # ========================================
        SCENE_TWEAKS = [
            ("full", None),              # Original full frame
            ("mirror", None),            # Horizontal flip
            ("slight_rotate", 2),        # Very slight CW rotate (fills frame)
        ]
        
        for i, (name, param) in enumerate(SCENE_TWEAKS[:num_scenes]):
            scene_path = os.path.join(output_dir, f"{basename}_scene_{i}_{name}.png")
            
            try:
                if name == "full":
                    scene_img = img.copy()
                elif name == "mirror":
                    scene_img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif name == "slight_rotate":
                    angle = param if param else 2
                    # Rotate and crop to fill frame (no black borders)
                    rotated = img.rotate(angle, resample=Image.BICUBIC, expand=True)
                    # Center crop back to original size to remove borders
                    rw, rh = rotated.size
                    left = (rw - w) // 2
                    top = (rh - h) // 2
                    scene_img = rotated.crop((left, top, left + w, top + h))
                else:
                    scene_img = img.copy()
                
                # Resize to standard 1080p resolution (FULL SCREEN always)
                scene_img = scene_img.resize((1080, 1920), Image.LANCZOS)
                scene_img.save(scene_path, "PNG")
                scenes.append(scene_path)
                
            except Exception as e:
                print(f"[VisualEngine] Scene '{name}' failed: {e}")
                continue
        
        print(f"[VisualEngine] Generated {len(scenes)} scene variations for {account_key}")
        return scenes
        
    except Exception as e:
        print(f"[VisualEngine] Scene generation error: {e}")
        return []


# ========================================
# INTERNAL FILTER FUNCTIONS
# ========================================

def _apply_cartoon_filter(img: Image.Image) -> Image.Image:
    """STRONG cartoon/illustration effect.
    Technique: Heavy smoothing + extreme color reduction + bold edge overlay.
    Result should look OBVIOUSLY different from a photo.
    """
    # Step 1: HEAVY smoothing (destroy photo detail → flat cartoon)
    smooth = img.copy()
    for _ in range(4):  # 4 passes = very smooth
        smooth = smooth.filter(ImageFilter.SMOOTH_MORE)
    
    # Step 2: AGGRESSIVE color quantize (10 colors = obvious flat cartoon)
    quantized = smooth.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    quantized = quantized.convert("RGB")
    
    # Step 3: BOLD edge detection (thick black outlines)
    gray = img.convert("L")
    # Double edge detection for thicker lines
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = edges.filter(ImageFilter.MaxFilter(3))  # Thicken edges
    # Lower threshold = more edges = more cartoon-like
    edges = edges.point(lambda x: 0 if x > 25 else 255)
    edges = edges.convert("RGB")
    
    # Step 4: Multiply bold edges onto flat cartoon colors
    result = np.array(quantized).astype(np.float32)
    edge_arr = np.array(edges).astype(np.float32) / 255.0
    result = (result * edge_arr).astype(np.uint8)
    
    # Step 5: Strong brightness boost (cartoons are bright and cheerful)
    cart_img = Image.fromarray(result)
    enhancer = ImageEnhance.Brightness(cart_img)
    cart_img = enhancer.enhance(1.25)
    
    # Step 6: VERY vivid colors (cartoon = saturated)
    enhancer = ImageEnhance.Color(cart_img)
    cart_img = enhancer.enhance(1.6)
    
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
    
    Args:
        raw_images: List of raw image paths (shared pool)
        account_key: Channel identifier
        output_dir: Where to save styled images
        
    Returns:
        List of all scene variation paths (styled + cropped)
    """
    os.makedirs(output_dir, exist_ok=True)
    all_scenes = []
    
    for i, raw_path in enumerate(raw_images):
        if not os.path.exists(raw_path):
            continue
            
        # Step 1: Apply channel visual style (V3: with background replacement)
        styled_path = os.path.join(output_dir, f"{account_key}_styled_{i}.png")
        apply_channel_style(raw_path, account_key, styled_path, image_index=i)
        
        # Step 2: Generate scene variations from styled image
        scenes = generate_scene_variations(styled_path, account_key, output_dir, num_scenes=3)
        all_scenes.extend(scenes)
    
    print(f"[VisualEngine] {account_key}: {len(all_scenes)} total scenes from {len(raw_images)} raw images")
    return all_scenes
