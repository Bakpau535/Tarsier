"""
Text Overlay Engine — Per-Channel Themed Typography V2
Each channel has UNIQUE typography: font, position, color, effects.
Uses Google Fonts (installed via GitHub Actions workflow) for premium feel.

Channel Themes:
  yt_documenter: Clean white Inter on dark bg — professional NatGeo data overlay
  yt_funny:      IMPACT-style Bebas Neue top+bottom — classic meme format
  yt_anthro:     Warm Quicksand with rounded bg — friendly subtitle storytelling
  yt_pov:        Creepster centered — horror text fades from darkness, wide spacing
  yt_drama:      Playfair italic centered — cinematic serif with golden glow
  fb_fanspage:   Bold Inter yellow — high contrast for Facebook feed
"""
import os
import math
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Tuple, List
import numpy as np


# ========================================
# GOOGLE FONTS — Per-channel font paths
# Fallback chain: Google Font → System → PIL default
# ========================================

FONT_PATHS = {
    "creepster": [
        "/usr/share/fonts/truetype/google/Creepster-Regular.ttf",
        "C:/Users/Compaq/AppData/Local/Microsoft/Windows/Fonts/Creepster-Regular.ttf",
    ],
    "playfair_italic": [
        "/usr/share/fonts/truetype/google/PlayfairDisplay-BoldItalic.ttf",
        "C:/Windows/Fonts/times.ttf",  # Times New Roman fallback
    ],
    "playfair_bold": [
        "/usr/share/fonts/truetype/google/PlayfairDisplay-Bold.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
    ],
    "bebas": [
        "/usr/share/fonts/truetype/google/BebasNeue-Regular.ttf",
        "C:/Windows/Fonts/impact.ttf",  # Impact fallback
    ],
    "inter": [
        "/usr/share/fonts/truetype/google/Inter.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
    "quicksand": [
        "/usr/share/fonts/truetype/google/Quicksand.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
}


# ========================================
# PER-CHANNEL TEXT STYLE DEFINITIONS V2
# ========================================

TEXT_STYLES = {
    "yt_documenter": {
        "name": "data_overlay",
        "font_family": "inter",
        "font_size": 42,
        "color": (255, 255, 255),           # White
        "stroke_color": (0, 0, 0),          # Black stroke
        "stroke_width": 3,
        "bg_color": (0, 0, 0, 160),         # Semi-transparent dark bg
        "position": "bottom_center",
        "max_chars_per_line": 38,
        "margin_bottom": 130,
        "letter_spacing": 0,
        "effect": None,                     # Clean professional
    },
    "yt_funny": {
        "name": "meme_impact",
        "font_family": "bebas",
        "font_size": 68,                    # VERY LARGE for meme impact
        "color": (255, 255, 255),           # White
        "stroke_color": (0, 0, 0),          # Black stroke
        "stroke_width": 6,                  # VERY thick outline
        "bg_color": None,
        "position": "top_and_bottom",       # Classic meme: top + bottom
        "max_chars_per_line": 22,           # Short lines = punchy
        "margin_bottom": 100,
        "letter_spacing": 2,               # Slight spacing
        "effect": "meme_tilt",             # Random slight rotation
    },
    "yt_anthro": {
        "name": "warm_subtitle",
        "font_family": "quicksand",
        "font_size": 40,
        "color": (255, 255, 240),           # Warm white (ivory)
        "stroke_color": None,
        "stroke_width": 0,
        "bg_color": (30, 20, 10, 190),      # Warm dark semi-transparent
        "position": "bottom_center",
        "max_chars_per_line": 40,
        "margin_bottom": 110,
        "letter_spacing": 1,
        "effect": "rounded_box",           # Rounded corners on bg box
    },
    "yt_pov": {
        "name": "horror_center",
        "font_family": "creepster",
        "font_size": 52,
        "color": (180, 140, 140),           # Faded blood red-grey
        "stroke_color": (20, 0, 0),         # Very dark red stroke
        "stroke_width": 2,
        "bg_color": None,
        "position": "center",              # TEXT APPEARS FROM CENTER
        "max_chars_per_line": 25,           # Short creepy lines
        "margin_bottom": 0,
        "letter_spacing": 8,               # W I D E spacing = eerie
        "effect": "horror_glow",           # Red glow behind text
    },
    "yt_drama": {
        "name": "cinematic_serif",
        "font_family": "playfair_italic",
        "font_size": 48,
        "color": (255, 235, 180),           # Warm gold
        "stroke_color": (40, 30, 10),       # Dark warm stroke
        "stroke_width": 2,
        "bg_color": None,
        "position": "center",              # Centered cinematic
        "max_chars_per_line": 30,
        "margin_bottom": 0,
        "letter_spacing": 3,               # Slight elegant spacing
        "effect": "golden_glow",           # Golden glow behind text
    },
    "fb_fanspage": {
        "name": "bold_feed",
        "font_family": "inter",
        "font_size": 52,
        "color": (255, 240, 50),            # Bright yellow
        "stroke_color": (0, 0, 0),          # Black stroke
        "stroke_width": 5,
        "bg_color": None,
        "position": "bottom_center",
        "max_chars_per_line": 26,
        "margin_bottom": 100,
        "letter_spacing": 1,
        "effect": None,                    # Clean bold
    },
}


def _get_font(family: str = "inter", size: int = 42) -> ImageFont.FreeTypeFont:
    """Get a font by family name. Tries Google Fonts first, then system fallbacks."""
    candidates = FONT_PATHS.get(family, FONT_PATHS["inter"])

    for font_path in candidates:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            continue

    # Ultimate fallback — system DejaVu or PIL default
    fallbacks = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fb in fallbacks:
        try:
            if os.path.exists(fb):
                return ImageFont.truetype(fb, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _draw_text_with_spacing(draw: ImageDraw.Draw, x: int, y: int, text: str,
                            font: ImageFont.FreeTypeFont, fill: tuple,
                            spacing: int = 0):
    """Draw text with custom letter spacing."""
    if spacing <= 0:
        draw.text((x, y), text, font=font, fill=fill)
        return

    current_x = x
    for char in text:
        draw.text((current_x, y), char, font=font, fill=fill)
        bbox = font.getbbox(char)
        char_width = bbox[2] - bbox[0]
        current_x += char_width + spacing


def _get_text_width_with_spacing(text: str, font: ImageFont.FreeTypeFont,
                                  spacing: int = 0) -> int:
    """Calculate total text width including letter spacing."""
    if spacing <= 0:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    total = 0
    for char in text:
        bbox = font.getbbox(char)
        total += (bbox[2] - bbox[0]) + spacing
    return total - spacing  # Remove trailing spacing


def _apply_horror_glow(overlay: Image.Image, text_bounds: list) -> Image.Image:
    """Apply a red glow effect behind text for horror channel."""
    glow_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for (x1, y1, x2, y2) in text_bounds:
        padding = 25
        glow_draw.rectangle(
            [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
            fill=(80, 0, 0, 60)
        )

    # Heavy blur for soft glow
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=20))

    # Composite glow BEHIND text
    result = Image.alpha_composite(
        Image.new("RGBA", overlay.size, (0, 0, 0, 0)),
        glow_layer
    )
    result = Image.alpha_composite(result, overlay)
    return result


def _apply_golden_glow(overlay: Image.Image, text_bounds: list) -> Image.Image:
    """Apply a warm golden glow effect behind text for drama channel."""
    glow_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for (x1, y1, x2, y2) in text_bounds:
        padding = 20
        glow_draw.rectangle(
            [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
            fill=(60, 45, 10, 50)
        )

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=18))

    result = Image.alpha_composite(
        Image.new("RGBA", overlay.size, (0, 0, 0, 0)),
        glow_layer
    )
    result = Image.alpha_composite(result, overlay)
    return result


def render_text_on_frame(frame: np.ndarray, text: str, account_key: str) -> np.ndarray:
    """Render per-channel themed text on a video frame.

    V2: Each channel has UNIQUE typography with custom Google Fonts,
    position, color, effects (glow, spacing, etc.)

    Args:
        frame: numpy array (H, W, 3) RGB
        text: Text to render
        account_key: Channel identifier

    Returns:
        Frame with themed text rendered
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

        font = _get_font(family=style["font_family"], size=style["font_size"])
        spacing = style.get("letter_spacing", 0)

        # Wrap text
        wrapped = textwrap.fill(text, width=style["max_chars_per_line"])
        lines = wrapped.split("\n")

        # Calculate text size
        line_height = style["font_size"] + 12
        total_text_height = line_height * len(lines)

        # Determine position
        position = style["position"]
        margin = style.get("margin_bottom", 60)

        if position == "top_and_bottom":
            # === MEME STYLE: top half + bottom half ===
            text_bounds = _render_meme_style(draw, lines, w, h, margin,
                                             line_height, font, style, spacing)
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            return np.array(img.convert("RGB"))

        elif position == "center":
            start_y = (h - total_text_height) // 2
            align = "center"
        elif position == "bottom_center":
            start_y = h - total_text_height - margin
            align = "center"
        else:
            start_y = h - total_text_height - margin
            align = "center"

        text_bounds = []

        # Draw background box if needed
        if style.get("bg_color"):
            bg = style["bg_color"]
            padding = 14
            effect = style.get("effect", "")

            for i, line in enumerate(lines):
                y = start_y + i * line_height
                tw = _get_text_width_with_spacing(line, font, spacing)

                if align == "center":
                    x = (w - tw) // 2
                else:
                    x = 40

                if effect == "rounded_box":
                    # Rounded rectangle for warm feel
                    draw.rounded_rectangle(
                        [x - padding, y - padding // 2,
                         x + tw + padding, y + line_height + 2],
                        radius=10, fill=bg
                    )
                else:
                    draw.rectangle(
                        [x - padding, y - padding // 2,
                         x + tw + padding, y + line_height],
                        fill=bg
                    )

        # Render text lines
        for i, line in enumerate(lines):
            y = start_y + i * line_height
            bounds = _render_line(draw, line, w, y, font, style,
                                  align=align, spacing=spacing)
            if bounds:
                text_bounds.append(bounds)

        # Apply effects
        effect = style.get("effect", "")
        if effect == "horror_glow" and text_bounds:
            overlay = _apply_horror_glow(overlay, text_bounds)
        elif effect == "golden_glow" and text_bounds:
            overlay = _apply_golden_glow(overlay, text_bounds)

        # Composite overlay onto image
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        return np.array(img.convert("RGB"))

    except Exception as e:
        print(f"[TextOverlay] Error rendering text: {e}")
        return frame


def _render_meme_style(draw: ImageDraw.Draw, lines: List[str],
                       w: int, h: int, margin: int, line_height: int,
                       font: ImageFont.FreeTypeFont, style: dict,
                       spacing: int) -> list:
    """Render meme-style text: top half at top, bottom half at bottom."""
    text_bounds = []
    mid = max(1, len(lines) // 2)
    top_lines = lines[:mid]
    bottom_lines = lines[mid:]

    # Top lines
    for i, line in enumerate(top_lines):
        y = 40 + i * line_height
        bounds = _render_line(draw, line, w, y, font, style,
                              align="center", spacing=spacing)
        if bounds:
            text_bounds.append(bounds)

    # Bottom lines
    for i, line in enumerate(bottom_lines):
        y = h - margin - (len(bottom_lines) - i) * line_height
        bounds = _render_line(draw, line, w, y, font, style,
                              align="center", spacing=spacing)
        if bounds:
            text_bounds.append(bounds)

    return text_bounds


def _render_line(draw: ImageDraw.Draw, text: str, img_width: int, y: int,
                 font: ImageFont.FreeTypeFont, style: dict,
                 align: str = "center", spacing: int = 0) -> Optional[tuple]:
    """Render a single line of text with per-channel style.
    Returns bounding box (x1, y1, x2, y2) for glow effects."""
    try:
        tw = _get_text_width_with_spacing(text, font, spacing)

        if align == "center":
            x = (img_width - tw) // 2
        elif align == "left":
            x = 40
        else:
            x = (img_width - tw) // 2

        color = style["color"]
        fill = color + (255,) if len(color) == 3 else color

        # Draw stroke/outline first
        if style.get("stroke_color") and style.get("stroke_width", 0) > 0:
            sw = style["stroke_width"]
            sc = style["stroke_color"]
            sc_fill = sc + (255,) if len(sc) == 3 else sc
            for dx in range(-sw, sw + 1):
                for dy in range(-sw, sw + 1):
                    if dx * dx + dy * dy <= sw * sw:
                        _draw_text_with_spacing(draw, x + dx, y + dy, text,
                                                font, sc_fill, spacing)

        # Draw main text
        _draw_text_with_spacing(draw, x, y, text, font, fill, spacing)

        # Return bounds for glow effects
        line_height = style["font_size"] + 12
        return (x, y, x + tw, y + line_height)

    except Exception as e:
        print(f"[TextOverlay] Line render error: {e}")
        return None


def generate_title_card(text: str, account_key: str,
                        width: int = 1080, height: int = 1920) -> np.ndarray:
    """Generate a full-screen title card with channel-appropriate styling."""
    style = TEXT_STYLES.get(account_key, TEXT_STYLES["fb_fanspage"])

    # Per-channel background color
    BG_COLORS = {
        "yt_pov":    (8, 5, 10),       # Near black with purple
        "yt_drama":  (12, 10, 8),      # Near black warm
        "yt_funny":  (255, 200, 50),   # Bright yellow
        "yt_anthro": (25, 20, 15),     # Warm dark
        "yt_documenter": (15, 20, 25), # Cool dark
        "fb_fanspage": (20, 20, 30),   # Dark default
    }
    bg_color = BG_COLORS.get(account_key, (20, 20, 30))

    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)

    # Use larger font for title cards — override style temporarily
    title_style = style.copy()
    title_style["font_size"] = style["font_size"] + 24
    title_style["position"] = "center"

    # Build a temporary override in TEXT_STYLES
    _orig = TEXT_STYLES.get(account_key)
    TEXT_STYLES[account_key] = title_style
    result = render_text_on_frame(frame, text, account_key)
    TEXT_STYLES[account_key] = _orig  # Restore

    return result
