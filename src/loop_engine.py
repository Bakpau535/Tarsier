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


def generate_clip_variations(clip_path: str, account_key: str,
                             loop_style: str, tmp_dir: str,
                             clip_index: int = 0) -> List[str]:
    """
    Generate video clip variations using FFmpeg from a single stock clip.
    Returns list of variation file paths.
    
    Per-channel loop_style (from VIDEO_PROFILES):
    - standard: normal, slow-mo 0.5x, ken burns zoom, flip
    - replay:   normal, slow-mo 0.4x, zoom punch (yt_funny)
    - drift:    very slow float pan (yt_pov)
    - emotional: very slow ken burns 2% zoom (yt_drama)
    - reaction: silent stare loops with crop variation (yt_anthro)
    """
    import subprocess
    
    if not os.path.exists(clip_path):
        return []
    
    variations = []
    base_name = os.path.splitext(os.path.basename(clip_path))[0]
    
    # Define variations per loop_style
    if loop_style == "standard":
        # Correction plan: normal, slow-mo 0.5x, ken burns zoom in, zoom out, flip, crop-eyes
        var_specs = [
            ("slowmo", f'-vf "setpts=2.0*PTS" -an'),  # 0.5x speed
            ("zoomin", f'-vf "zoompan=z=\'min(zoom+0.002,1.2)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d=1:s=1920x1080:fps=24" -an'),
            ("flip", f'-vf "hflip" -an'),
        ]
    elif loop_style == "replay":
        # yt_funny: normal → slow-mo 0.4x → zoom punch 1.3x
        var_specs = [
            ("slowmo", f'-vf "setpts=2.5*PTS" -an'),  # 0.4x speed
            ("zoom_punch", f'-vf "zoompan=z=\'min(zoom+0.005,1.3)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d=1:s=1920x1080:fps=24" -an'),
        ]
    elif loop_style == "drift":
        # yt_pov: very slow drift float (1-2% pan over 8s)
        var_specs = [
            ("drift", f'-vf "zoompan=z=\'min(zoom+0.001,1.05)\':x=\'iw/2-(iw/zoom/2)+10*on/25\':y=\'ih/2-(ih/zoom/2)\':d=1:s=1920x1080:fps=24" -an'),
            ("slowmo", f'-vf "setpts=1.5*PTS" -an'),  # gentle slow-mo
        ]
    elif loop_style == "emotional":
        # yt_drama: very slow ken burns 2% zoom over 10s
        var_specs = [
            ("slow_zoom", f'-vf "zoompan=z=\'min(zoom+0.0005,1.02)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d=1:s=1920x1080:fps=24" -an'),
            ("slowmo", f'-vf "setpts=2.0*PTS" -an'),
        ]
    elif loop_style == "reaction":
        # yt_anthro: silent stare loops with different crop regions
        var_specs = [
            ("crop_center", f'-vf "crop=iw*0.6:ih*0.6:iw*0.2:ih*0.1,scale=1920:1080" -an'),
            ("flip", f'-vf "hflip" -an'),
        ]
    else:
        var_specs = [
            ("slowmo", f'-vf "setpts=2.0*PTS" -an'),
        ]
    
    for var_name, ffmpeg_filter in var_specs:
        output_path = os.path.join(tmp_dir, f"{base_name}_{var_name}_{clip_index}.mp4")
        
        # Skip if already generated
        if os.path.exists(output_path):
            variations.append(output_path)
            continue
        
        try:
            cmd = f'ffmpeg -y -i "{clip_path}" {ffmpeg_filter} -c:v libx264 -preset ultrafast -crf 23 "{output_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                variations.append(output_path)
                print(f"[{account_key}] Loop variation: {var_name} from clip {clip_index}")
            else:
                # If FFmpeg fails, still include original
                if result.stderr:
                    print(f"[{account_key}] FFmpeg {var_name} error: {result.stderr.decode()[:100]}")
        except Exception as e:
            print(f"[{account_key}] Variation '{var_name}' failed: {e}")
    
    # Always include original clip as first option
    variations.insert(0, clip_path)
    return variations
