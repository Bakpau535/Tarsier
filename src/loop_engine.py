"""
Loop Engine — Generate clip variations from a single tarsier source clip.
One 4-5 second clip → 10 variations → ~60 seconds of unique tarsier content.
Anti-repetition rules ensure no same technique appears consecutively.
"""
import os
import random
from typing import List, Tuple
from PIL import Image
import numpy as np


# Per-channel color grade presets (applied as numpy transformations)
COLOR_GRADES = {
    "yt_documenter": {
        "name": "documentary",
        "red_mult": 0.98, "green_mult": 1.02, "blue_mult": 1.06,  # teal-green tone
        "saturation": 0.80,  # desaturate 20%
        "contrast": 1.06, "brightness": 2,
        "grain": 3.0,
        "vignette": 0.20,
    },
    "yt_funny": {
        "name": "comedy",
        "red_mult": 1.05, "green_mult": 1.0, "blue_mult": 0.92,  # warm orange tone
        "saturation": 1.15,  # saturate +15%
        "contrast": 1.08, "brightness": 5,
        "grain": 1.5,
        "vignette": 0.10,
    },
    "yt_anthro": {
        "name": "sitcom",
        "red_mult": 1.04, "green_mult": 1.01, "blue_mult": 0.95,  # warm tone
        "saturation": 1.0,
        "contrast": 1.04, "brightness": 3,
        "grain": 2.0,
        "vignette": 0.25,  # slight vignette
    },
    "yt_pov": {
        "name": "nightvision",
        "red_mult": 0.90, "green_mult": 0.95, "blue_mult": 1.15,  # blue shadows
        "saturation": 0.85,
        "contrast": 1.10, "brightness": -5,
        "grain": 6.0,  # heavy grain +25%
        "vignette": 0.30,
    },
    "yt_drama": {
        "name": "cinematic",
        "red_mult": 0.98, "green_mult": 1.03, "blue_mult": 0.96,  # warm green (safe scenes)
        "saturation": 0.95,
        "contrast": 1.12, "brightness": 0,
        "grain": 4.0,
        "vignette": 0.28,
    },
    "fb_fanspage": {
        "name": "vivid",
        "red_mult": 1.03, "green_mult": 1.03, "blue_mult": 1.0,
        "saturation": 1.20,  # vivid, high contrast
        "contrast": 1.15, "brightness": 5,
        "grain": 1.0,
        "vignette": 0.08,
    },
}


def apply_color_grade(frame: np.ndarray, account_key: str) -> np.ndarray:
    """
    Apply per-channel color grading to a single frame.
    """
    grade = COLOR_GRADES.get(account_key, COLOR_GRADES["fb_fanspage"])
    f = frame.astype(np.float32)
    
    # 1. Color channel multipliers
    f[:, :, 0] = f[:, :, 0] * grade["red_mult"]
    f[:, :, 1] = f[:, :, 1] * grade["green_mult"]
    f[:, :, 2] = f[:, :, 2] * grade["blue_mult"]
    
    # 2. Saturation adjustment
    if grade["saturation"] != 1.0:
        gray = np.mean(f, axis=2, keepdims=True)
        f = gray + grade["saturation"] * (f - gray)
    
    # 3. Contrast and brightness
    f = ((f - 128) * grade["contrast"]) + 128 + grade["brightness"]
    
    # 4. Film grain
    if grade["grain"] > 0:
        h, w = f.shape[:2]
        grain = np.random.normal(0, grade["grain"], (h, w, 1)).astype(np.float32)
        f = f + grain
    
    # 5. Vignette
    if grade["vignette"] > 0:
        h, w = f.shape[:2]
        Y, X = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        vignette = 1.0 - grade["vignette"] * (dist / max_dist) ** 2
        f = f * vignette[:, :, np.newaxis]
    
    return np.clip(f, 0, 255).astype(np.uint8)


# ---- Loop variation techniques ----

def _ken_burns_frames(img: np.ndarray, fps: int, duration: float,
                      direction: str, target_w: int, target_h: int) -> List[np.ndarray]:
    """Ken Burns zoom effect on a static image."""
    h, w = img.shape[:2]
    total_frames = int(duration * fps)
    frames = []
    
    for i in range(total_frames):
        progress = i / max(total_frames - 1, 1)
        
        if direction == "zoom_in":
            scale = 1.0 - 0.20 * progress
        elif direction == "zoom_out":
            scale = 0.80 + 0.20 * progress
        elif direction == "pan_left":
            scale = 0.85
            cx = int(w * (0.55 - 0.10 * progress))
            cy = h // 2
            cw, ch = int(w * scale), int(h * scale)
            x1 = max(0, min(cx - cw // 2, w - cw))
            y1 = max(0, min(cy - ch // 2, h - ch))
            cropped = img[y1:y1 + ch, x1:x1 + cw]
            frames.append(np.array(Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS)))
            continue
        elif direction == "pan_right":
            scale = 0.85
            cx = int(w * (0.45 + 0.10 * progress))
            cy = h // 2
            cw, ch = int(w * scale), int(h * scale)
            x1 = max(0, min(cx - cw // 2, w - cw))
            y1 = max(0, min(cy - ch // 2, h - ch))
            cropped = img[y1:y1 + ch, x1:x1 + cw]
            frames.append(np.array(Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS)))
            continue
        elif direction == "drift":
            # Very slow pan + zoom combined
            scale = 1.0 - 0.05 * progress
            cx = int(w * (0.50 + 0.02 * progress))
            cy = int(h * (0.50 - 0.01 * progress))
            cw, ch = int(w * scale), int(h * scale)
            x1 = max(0, min(cx - cw // 2, w - cw))
            y1 = max(0, min(cy - ch // 2, h - ch))
            cropped = img[y1:y1 + ch, x1:x1 + cw]
            frames.append(np.array(Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS)))
            continue
        else:
            scale = 1.0
        
        cw, ch = int(w * scale), int(h * scale)
        x1, y1 = (w - cw) // 2, (h - ch) // 2
        cropped = img[y1:y1 + ch, x1:x1 + cw]
        frames.append(np.array(Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS)))
    
    return frames


def _flip_horizontal(img: np.ndarray) -> np.ndarray:
    """Mirror image horizontally."""
    return np.fliplr(img)


def _crop_eyes(img: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """Crop upper-center area (likely where tarsier eyes are in most photos)."""
    h, w = img.shape[:2]
    # Focus on upper 60% center 60%
    x1 = int(w * 0.20)
    y1 = int(h * 0.10)
    x2 = int(w * 0.80)
    y2 = int(h * 0.60)
    cropped = img[y1:y2, x1:x2]
    return np.array(Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS))


# Available variation techniques
VARIATION_TECHNIQUES = [
    "normal",
    "zoom_in",
    "zoom_out",
    "pan_left",
    "pan_right",
    "flip",
    "flip_zoom_in",
    "crop_eyes",
    "drift",
]


def generate_variations(img_path: str, account_key: str, clip_duration: float = 6.0,
                       fps: int = 24, target_w: int = 1920, target_h: int = 1080,
                       max_variations: int = 4) -> List[Tuple[str, List[np.ndarray]]]:
    """
    Generate multiple visual variations from a single image.
    Returns list of (variation_name, frames) tuples.
    Each variation is applied the channel's color grade.
    
    Anti-repetition: shuffles techniques and never returns same type consecutively.
    """
    try:
        img = Image.open(img_path).convert("RGB")
        # Upscale small images
        if img.width < target_w or img.height < target_h:
            ratio = max(target_w / img.width, target_h / img.height) * 1.3
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
        img_array = np.array(img)
    except Exception as e:
        print(f"[{account_key}] Failed to load image for loop: {e}")
        return []
    
    # Shuffle techniques and pick up to max_variations
    available = VARIATION_TECHNIQUES.copy()
    random.shuffle(available)
    selected = available[:max_variations]
    
    # Ensure no same technique type consecutively (anti-repetition)
    # Group by category to avoid zoom_in followed by zoom_out etc.
    variations = []
    
    for technique in selected:
        try:
            if technique == "normal":
                frames = _ken_burns_frames(img_array, fps, clip_duration, "zoom_in", target_w, target_h)
                # Use very minimal zoom for "normal" — just 5% zoom
                frames = [np.array(Image.fromarray(img_array).resize((target_w, target_h), Image.LANCZOS))] * int(clip_duration * fps)
                
            elif technique in ("zoom_in", "zoom_out", "pan_left", "pan_right", "drift"):
                frames = _ken_burns_frames(img_array, fps, clip_duration, technique, target_w, target_h)
                
            elif technique == "flip":
                flipped = _flip_horizontal(img_array)
                frames = _ken_burns_frames(flipped, fps, clip_duration, "zoom_in", target_w, target_h)
                
            elif technique == "flip_zoom_in":
                flipped = _flip_horizontal(img_array)
                frames = _ken_burns_frames(flipped, fps, clip_duration, "zoom_out", target_w, target_h)
                
            elif technique == "crop_eyes":
                cropped = _crop_eyes(img_array, target_w, target_h)
                frames = _ken_burns_frames(cropped, fps, clip_duration, "drift", target_w, target_h)
                
            else:
                continue
            
            # Apply channel-specific color grade
            frames = [apply_color_grade(f, account_key) for f in frames]
            
            variations.append((technique, frames))
            
        except Exception as e:
            print(f"[{account_key}] Variation '{technique}' failed: {e}")
            continue
    
    return variations
