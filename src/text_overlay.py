"""
Text Overlay Engine — Per-Channel Text Rendering on Video Frames
Each channel has its own typography style, color, position, and font treatment.
All rendering uses PIL — zero API cost.
"""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple
import numpy as np


# ========================================
# PER-CHANNEL TEXT STYLE DEFINITIONS
# ========================================

TEXT_STYLES = {
    "yt_documenter": {
        "name": "data_overlay",
        "font_size": 42,
        "font_bold": True,
        "color": (255, 255, 255),          # White
        "stroke_color": (0, 0, 0),         # Black stroke
        "stroke_width": 3,
        "bg_color": (0, 0, 0, 140),        # Semi-transparent black bg
        "position": "bottom_center",
        "max_chars_per_line": 40,
        "margin_bottom": 120,
    },
    "yt_funny": {
        "name": "meme_caption",
        "font_size": 58,                   # LARGE for meme impact
        "font_bold": True,
        "color": (255, 255, 255),          # White
        "stroke_color": (0, 0, 0),         # Black stroke
        "stroke_width": 5,                 # VERY thick outline
        "bg_color": None,
        "position": "bottom_center",       # Consistent bottom position
        "max_chars_per_line": 28,
        "margin_bottom": 100,
    },
    "yt_anthro": {
        "name": "subtitle",
        "font_size": 40,
        "font_bold": True,
        "color": (255, 255, 255),
        "stroke_color": None,
        "stroke_width": 0,
        "bg_color": (0, 0, 0, 180),        # Solid semi-transparent black bg
        "position": "bottom_center",
        "max_chars_per_line": 42,
        "margin_bottom": 100,
    },
    "yt_pov": {
        "name": "minimal",
        "font_size": 34,
        "font_bold": False,
        "color": (180, 180, 180),          # Faded grey
        "stroke_color": (0, 0, 0),
        "stroke_width": 2,
        "bg_color": None,
        "position": "bottom_center",       # FIXED: was top_left, now consistent
        "max_chars_per_line": 40,
        "margin_bottom": 100,
    },
    "yt_drama": {
        "name": "title_card",
        "font_size": 48,
        "font_bold": True,
        "color": (255, 255, 255),
        "stroke_color": (0, 0, 0),
        "stroke_width": 3,
        "bg_color": (0, 0, 0, 140),        # Semi-transparent overlay
        "position": "bottom_center",       # FIXED: was center, now consistent
        "max_chars_per_line": 35,
        "margin_bottom": 120,
    },
    "fb_fanspage": {
        "name": "bold_overlay",
        "font_size": 52,                   # Large, bold
        "font_bold": True,
        "color": (255, 255, 0),            # Yellow for attention
        "stroke_color": (0, 0, 0),
        "stroke_width": 4,
        "bg_color": None,
        "position": "bottom_center",       # FIXED: was center, now consistent
        "max_chars_per_line": 28,
        "margin_bottom": 100,
    },
}


def _get_font(bold: bool = True, size: int = 42) -> ImageFont.FreeTypeFont:
    """Get a font — tries system fonts, falls back to default."""
    font_candidates = [
        # Linux (GitHub Actions)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/impact.ttf",
    ]
    
    # Prefer bold fonts for bold style
    if bold:
        bold_candidates = [f for f in font_candidates if "Bold" in f or "bold" in f or "impact" in f.lower()]
        font_candidates = bold_candidates + font_candidates
    
    for font_path in font_candidates:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    
    # Fallback to PIL default
    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def render_text_on_frame(frame: np.ndarray, text: str, account_key: str) -> np.ndarray:
    """Render per-channel styled text on a video frame.
    
    Args:
        frame: numpy array (H, W, 3) RGB
        text: Text to render
        account_key: Channel identifier
        
    Returns:
        Frame with text rendered
    """
    if not text or not text.strip():
        return frame
    
    style = TEXT_STYLES.get(account_key, TEXT_STYLES["fb_fanspage"])
    
    try:
        h, w = frame.shape[:2]
        img = Image.fromarray(frame)
        
        # Create overlay for semi-transparent elements
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        font = _get_font(bold=style["font_bold"], size=style["font_size"])
        
        # Wrap text
        wrapped = textwrap.fill(text, width=style["max_chars_per_line"])
        lines = wrapped.split("\n")
        
        # Calculate text size
        line_height = style["font_size"] + 8
        total_text_height = line_height * len(lines)
        
        # Determine position
        position = style["position"]
        margin = style.get("margin_bottom", 60)
        
        if position == "bottom_center":
            start_y = h - total_text_height - margin
            align = "center"
        elif position == "top_left":
            start_y = 40
            align = "left"
        elif position == "center":
            start_y = (h - total_text_height) // 2
            align = "center"
        elif position == "top_and_bottom":
            # Meme style: split text, half on top, half on bottom
            mid = len(lines) // 2
            top_lines = lines[:max(1, mid)]
            bottom_lines = lines[max(1, mid):]
            
            # Render top
            for i, line in enumerate(top_lines):
                _render_line(draw, line, w, 30 + i * line_height, 
                           font, style, align="center")
            # Render bottom
            for i, line in enumerate(bottom_lines):
                y = h - margin - (len(bottom_lines) - i) * line_height
                _render_line(draw, line, w, y, font, style, align="center")
            
            # Composite and return
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            return np.array(img.convert("RGB"))
        else:
            start_y = h - total_text_height - margin
            align = "center"
        
        # Draw background box if needed
        if style.get("bg_color"):
            bg = style["bg_color"]
            padding = 12
            for i, line in enumerate(lines):
                y = start_y + i * line_height
                bbox = font.getbbox(line)
                tw = bbox[2] - bbox[0]
                
                if align == "center":
                    x = (w - tw) // 2
                elif align == "left":
                    x = 40
                else:
                    x = (w - tw) // 2
                    
                draw.rectangle(
                    [x - padding, y - padding // 2, 
                     x + tw + padding, y + line_height],
                    fill=bg
                )
        
        # Render text lines
        for i, line in enumerate(lines):
            y = start_y + i * line_height
            _render_line(draw, line, w, y, font, style, align=align)
        
        # Composite overlay onto image
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        return np.array(img.convert("RGB"))
        
    except Exception as e:
        print(f"[TextOverlay] Error rendering text: {e}")
        return frame


def _render_line(draw: ImageDraw.Draw, text: str, img_width: int, y: int,
                 font: ImageFont.FreeTypeFont, style: dict, align: str = "center"):
    """Render a single line of text with style."""
    try:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        
        if align == "center":
            x = (img_width - tw) // 2
        elif align == "left":
            x = 40
        else:
            x = (img_width - tw) // 2
        
        color = style["color"]
        
        # Draw stroke/outline first
        if style.get("stroke_color") and style.get("stroke_width", 0) > 0:
            sw = style["stroke_width"]
            sc = style["stroke_color"]
            for dx in range(-sw, sw + 1):
                for dy in range(-sw, sw + 1):
                    if dx * dx + dy * dy <= sw * sw:
                        draw.text((x + dx, y + dy), text, font=font, 
                                 fill=sc + (255,) if len(sc) == 3 else sc)
        
        # Draw main text
        fill = color + (255,) if len(color) == 3 else color
        draw.text((x, y), text, font=font, fill=fill)
        
    except Exception as e:
        print(f"[TextOverlay] Line render error: {e}")


def generate_title_card(text: str, account_key: str, 
                        width: int = 1080, height: int = 1920) -> np.ndarray:
    """Generate a full-screen title card (used for episode titles, scene cards etc.)"""
    style = TEXT_STYLES.get(account_key, TEXT_STYLES["fb_fanspage"])
    
    # Create dark background
    if account_key == "yt_pov":
        bg_color = (10, 10, 20)    # Near black with blue
    elif account_key == "yt_drama":
        bg_color = (15, 15, 15)    # Pure dark
    elif account_key == "yt_funny":
        bg_color = (255, 200, 50)  # Bright yellow
    else:
        bg_color = (20, 20, 30)    # Dark default
    
    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
    
    # Use larger font for title cards
    enlarged_style = style.copy()
    enlarged_style["font_size"] = style["font_size"] + 20
    enlarged_style["position"] = "center"
    
    return render_text_on_frame(frame, text, account_key)
