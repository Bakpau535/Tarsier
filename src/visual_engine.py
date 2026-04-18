"""
Visual Engine — Per-Channel Image Styling System
Transforms raw tarsier images into channel-specific art styles using PIL/OpenCV.
All processing is LOCAL — zero API cost, unlimited usage.

Styles:
  yt_documenter: Clean NatGeo — slight desaturation, teal grade, sharpening
  yt_funny:      Meme bright  — oversaturated, bright, high contrast
  yt_anthro:     Cartoon       — edge detection + bilateral filter + color quantize
  yt_pov:        Dark horror  — darkness, blue tint, heavy grain, vignette
  yt_drama:      Cinematic    — contrast, teal-orange split tone, letterbox
  fb_fanspage:   Bold vivid   — high saturation, sharpening, crisp
"""
import os
import random
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from typing import List, Tuple, Optional


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


def apply_channel_style(image_path: str, account_key: str, output_path: str) -> str:
    """Apply per-channel visual style to an image.
    
    Args:
        image_path: Path to raw source image
        account_key: Channel identifier (e.g. 'yt_documenter')
        output_path: Where to save the styled image
        
    Returns:
        Path to styled image, or original if styling fails
    """
    try:
        img = Image.open(image_path).convert("RGB")
        style = VISUAL_STYLES.get(account_key, VISUAL_STYLES["fb_fanspage"])
        
        print(f"[VisualEngine] Applying '{style['name']}' style to {os.path.basename(image_path)}")
        
        # 1. Special effects first (cartoon, letterbox, etc.)
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
        # Fallback: copy original
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
        # CHANNEL-SPECIFIC CROP/FRAMING SETS
        # ========================================
        CHANNEL_VARIATIONS = {
            "yt_documenter": [
                ("full", None),              # Wide full frame (documentary establishing shot)
                ("left_pan", "left"),         # Slow left pan crop
                ("right_pan", "right"),       # Slow right pan crop
                ("center_zoom", 0.70),       # Medium zoom (subject detail)
                ("bottom_half", "bottom"),   # Lower portion (habitat view)
            ],
            "yt_funny": [
                ("extreme_zoom", 0.25),      # ABSURD close-up (zoom muka)
                ("center_zoom", 0.40),       # Tight zoom on subject
                ("tilt_left", "tilt_l"),      # Tilted angle (meme style)
                ("tilt_right", "tilt_r"),     # Opposite tilt
                ("random_crop", 0.35),       # Random area extreme zoom
            ],
            "yt_anthro": [
                ("center_zoom", 0.60),       # Medium close-up
                ("full", None),              # Full frame with cartoon effect
                ("left_pan", "left"),         # Left portion
                ("eyes_close", 0.45),        # Face area
                ("right_pan", "right"),       # Right portion
            ],
            "yt_pov": [
                ("eyes_close", 0.30),        # EXTREME close-up mata (horror POV)
                ("center_zoom", 0.35),       # Very tight crop (claustrophobic)
                ("dark_corner", "corner"),    # Corner crop (peeking feel)
                ("extreme_zoom", 0.25),      # Maximum zoom (immersive)
                ("top_half", "top"),          # Upper area (looking up)
            ],
            "yt_drama": [
                ("full", None),              # Establishing wide shot
                ("center_zoom", 0.60),       # Medium dramatic shot
                ("left_pan", "left"),         # Cinematic pan left
                ("eyes_close", 0.45),        # Emotional close-up
                ("right_pan", "right"),       # Cinematic pan right
            ],
            "fb_fanspage": [
                ("center_zoom", 0.65),       # Clean center crop
                ("full", None),              # Full frame vivid
                ("center_zoom", 0.50),       # Tighter center (detail shot)
                ("left_pan", "left"),         # Left variation
                ("right_pan", "right"),       # Right variation
            ],
        }
        
        variations = CHANNEL_VARIATIONS.get(account_key, CHANNEL_VARIATIONS["fb_fanspage"])
        
        for i, (name, param) in enumerate(variations[:num_scenes]):
            scene_path = os.path.join(output_dir, f"{basename}_scene_{i}_{name}.png")
            
            try:
                if name == "full":
                    scene_img = img.copy()
                    
                elif name == "center_zoom":
                    scale = param
                    cw, ch = int(w * scale), int(h * scale)
                    x1 = (w - cw) // 2
                    y1 = (h - ch) // 2
                    scene_img = img.crop((x1, y1, x1 + cw, y1 + ch))
                    
                elif name == "eyes_close":
                    # Close-up of upper center (where eyes typically are)
                    scale = param
                    cw, ch = int(w * scale), int(h * scale)
                    x1 = (w - cw) // 2
                    y1 = int(h * 0.10)  # Upper area (eyes)
                    scene_img = img.crop((x1, y1, x1 + cw, min(y1 + ch, h)))
                    
                elif name == "left_pan":
                    cw = int(w * 0.55)
                    scene_img = img.crop((0, 0, cw, h))
                    
                elif name == "right_pan":
                    cw = int(w * 0.55)
                    x1 = w - cw
                    scene_img = img.crop((x1, 0, w, h))
                    
                elif name == "top_half":
                    ch = int(h * 0.55)
                    scene_img = img.crop((0, 0, w, ch))
                    
                elif name == "bottom_half":
                    ch = int(h * 0.55)
                    y1 = h - ch
                    scene_img = img.crop((0, y1, w, h))
                    
                elif name == "tilt_left":
                    angle = random.randint(5, 12)
                    scene_img = img.rotate(angle, fillcolor=(0, 0, 0), expand=False)
                    
                elif name == "tilt_right":
                    angle = random.randint(-12, -5)
                    scene_img = img.rotate(angle, fillcolor=(0, 0, 0), expand=False)
                    
                elif name == "extreme_zoom":
                    scale = param
                    cw, ch = int(w * scale), int(h * scale)
                    # Random position for variety
                    cx = random.randint(cw // 2, max(cw // 2 + 1, w - cw // 2))
                    cy = random.randint(ch // 2, max(ch // 2 + 1, h - ch // 2))
                    scene_img = img.crop((cx - cw // 2, cy - ch // 2, 
                                         cx + cw // 2, cy + ch // 2))
                    
                elif name == "random_crop":
                    scale = param
                    cw, ch = int(w * scale), int(h * scale)
                    cx = random.randint(cw // 2, max(cw // 2 + 1, w - cw // 2))
                    cy = random.randint(ch // 2, max(ch // 2 + 1, h - ch // 2))
                    scene_img = img.crop((cx - cw // 2, cy - ch // 2, 
                                         cx + cw // 2, cy + ch // 2))
                    
                elif name == "dark_corner":
                    # Crop from corner (peeking/stalker POV feel)
                    cw, ch = int(w * 0.45), int(h * 0.45)
                    corner = random.choice(["tl", "tr", "bl", "br"])
                    if corner == "tl":
                        scene_img = img.crop((0, 0, cw, ch))
                    elif corner == "tr":
                        scene_img = img.crop((w - cw, 0, w, ch))
                    elif corner == "bl":
                        scene_img = img.crop((0, h - ch, cw, h))
                    else:
                        scene_img = img.crop((w - cw, h - ch, w, h))
                else:
                    scene_img = img.copy()
                
                # QUALITY GUARD: skip extreme crops on small source images
                # If source < 1280px wide, aggressive crops would all fallback to center crop (identical)
                if w < 1280 and name in ("extreme_zoom", "eyes_close", "dark_corner", "random_crop"):
                    # Use full frame instead — preserves quality on small images
                    scene_img = img.copy()
                    print(f"[VisualEngine] Skip '{name}' (source {w}px too small) — using full frame")
                elif scene_img.width < MIN_SRC_WIDTH:
                    # Larger source but crop still too small — use generous center crop
                    safe_scale = max(0.75, MIN_SRC_WIDTH / w)
                    cw, ch = int(w * safe_scale), int(h * safe_scale)
                    x1, y1 = (w - cw) // 2, (h - ch) // 2
                    scene_img = img.crop((x1, y1, x1 + cw, y1 + ch))
                    print(f"[VisualEngine] Quality guard: '{name}' too small, using {safe_scale:.0%} center crop")
                
                # Resize to standard 1080p resolution
                scene_img = scene_img.resize((1920, 1080), Image.LANCZOS)
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
            
        # Step 1: Apply channel visual style
        styled_path = os.path.join(output_dir, f"{account_key}_styled_{i}.png")
        apply_channel_style(raw_path, account_key, styled_path)
        
        # Step 2: Generate scene variations from styled image
        scenes = generate_scene_variations(styled_path, account_key, output_dir, num_scenes=3)
        all_scenes.extend(scenes)
    
    print(f"[VisualEngine] {account_key}: {len(all_scenes)} total scenes from {len(raw_images)} raw images")
    return all_scenes
