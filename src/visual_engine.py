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
        "saturation": 0.80,       # desaturate 20%
        "contrast": 1.10,
        "brightness": 1.0,
        "sharpness": 1.3,         # slight sharpen
        "color_tint": (0, 10, 20),  # slight teal/blue
        "grain": 3,
        "vignette": 0.15,
        "special": None,
    },
    "yt_funny": {
        "name": "meme_bright",
        "saturation": 1.35,       # oversaturate +35%
        "contrast": 1.15,
        "brightness": 1.15,       # brighter
        "sharpness": 1.1,
        "color_tint": (8, 5, -5),  # warm orange
        "grain": 0,
        "vignette": 0.0,
        "special": "funny_crop",   # random absurd crops/angles
    },
    "yt_anthro": {
        "name": "cartoon",
        "saturation": 1.10,
        "contrast": 1.05,
        "brightness": 1.05,
        "sharpness": 0.8,         # slightly softer for cartoon
        "color_tint": (8, 4, -3),  # warm
        "grain": 0,
        "vignette": 0.10,
        "special": "cartoon",      # cartoon filter pipeline
    },
    "yt_pov": {
        "name": "dark_horror",
        "saturation": 0.70,       # desaturate
        "contrast": 1.15,
        "brightness": 0.55,       # MUCH darker
        "sharpness": 1.0,
        "color_tint": (-10, -5, 25),  # strong blue tint
        "grain": 12,              # heavy grain
        "vignette": 0.35,         # strong vignette
        "special": None,
    },
    "yt_drama": {
        "name": "cinematic",
        "saturation": 0.90,
        "contrast": 1.20,         # high contrast
        "brightness": 0.90,       # slightly dark
        "sharpness": 1.15,
        "color_tint": (-3, 8, -5),  # teal-green (safe scenes)
        "grain": 5,
        "vignette": 0.25,
        "special": "letterbox",    # cinematic letterbox
    },
    "fb_fanspage": {
        "name": "bold_vivid",
        "saturation": 1.30,       # vivid
        "contrast": 1.20,         # high contrast
        "brightness": 1.08,
        "sharpness": 1.4,         # extra sharp
        "color_tint": (5, 5, 0),
        "grain": 0,
        "vignette": 0.05,
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
    """Generate multiple scene variations from one styled image.
    Each variation is a different crop/zoom/pan that will become a Ken Burns scene.
    
    Returns:
        List of paths to scene variation images
    """
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        scenes = []
        basename = os.path.splitext(os.path.basename(image_path))[0]
        
        # Define variation techniques
        variations = [
            ("full", None),           # Full frame (Ken Burns zoom in)
            ("center_zoom", 0.65),    # Center crop 65%
            ("eyes_close", 0.40),     # Extreme close-up (center top)
            ("left_pan", "left"),      # Left third crop
            ("right_pan", "right"),    # Right third crop
        ]
        
        # Add extra variations for channels that need more scenes
        style = VISUAL_STYLES.get(account_key, {})
        if style.get("special") == "funny_crop":
            variations.append(("tilt_left", "tilt_l"))
            variations.append(("extreme_zoom", 0.30))
        
        for i, (name, param) in enumerate(variations[:num_scenes]):
            scene_path = os.path.join(output_dir, f"{basename}_scene_{name}.png")
            
            try:
                if name == "full":
                    # Full frame — no crop, Ken Burns will handle animation
                    scene_img = img.copy()
                    
                elif name == "center_zoom":
                    # Center crop at given scale
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
                    y1 = int(h * 0.15)  # Upper area
                    scene_img = img.crop((x1, y1, x1 + cw, min(y1 + ch, h)))
                    
                elif name == "left_pan":
                    # Left third
                    cw = int(w * 0.55)
                    scene_img = img.crop((0, 0, cw, h))
                    
                elif name == "right_pan":
                    # Right third
                    cw = int(w * 0.55)
                    x1 = w - cw
                    scene_img = img.crop((x1, 0, w, h))
                    
                elif name == "tilt_left":
                    # Slight rotation for funny channel
                    scene_img = img.rotate(random.randint(5, 15), 
                                          fillcolor=(0, 0, 0), expand=False)
                    
                elif name == "extreme_zoom":
                    # Extreme close-up
                    scale = param
                    cw, ch = int(w * scale), int(h * scale)
                    cx = random.randint(cw // 2, w - cw // 2)
                    cy = random.randint(ch // 2, h - ch // 2)
                    scene_img = img.crop((cx - cw // 2, cy - ch // 2, 
                                         cx + cw // 2, cy + ch // 2))
                else:
                    scene_img = img.copy()
                
                # Resize to standard resolution
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
    """Cartoon/illustration effect using PIL.
    Technique: Edge detection + color quantize + smooth + overlay edges.
    """
    # Step 1: Smooth the image (reduce detail for cartoon look)
    smooth = img.filter(ImageFilter.SMOOTH_MORE)
    smooth = smooth.filter(ImageFilter.SMOOTH_MORE)
    
    # Step 2: Quantize colors (reduce color palette for flat cartoon look)
    quantized = smooth.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    quantized = quantized.convert("RGB")
    
    # Step 3: Find edges (for cartoon outlines)
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    # Threshold edges to make crisp black lines
    edges = edges.point(lambda x: 0 if x > 40 else 255)
    edges = edges.convert("RGB")
    
    # Step 4: Multiply edges onto cartoon (darken where edges are)
    result = np.array(quantized).astype(np.float32)
    edge_arr = np.array(edges).astype(np.float32) / 255.0
    result = (result * edge_arr).astype(np.uint8)
    
    # Step 5: Slight brightness boost (cartoons are usually bright)
    cart_img = Image.fromarray(result)
    enhancer = ImageEnhance.Brightness(cart_img)
    cart_img = enhancer.enhance(1.15)
    
    # Step 6: Boost saturation (cartoons have vivid colors)
    enhancer = ImageEnhance.Color(cart_img)
    cart_img = enhancer.enhance(1.3)
    
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
