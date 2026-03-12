import os
from PIL import Image, ImageDraw, ImageFont
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TEMPLATES_DIR, TMP_DIR, ACCOUNTS

class ThumbnailGenerator:
    def __init__(self):
        # In a real scenario, you'd want a .ttf file in the assets folder
        # We will fallback to default PIL font if not found.
        self.font_path = "arial.ttf" # Example
        
    def _get_font(self, size: int):
        try:
            return ImageFont.truetype(self.font_path, size)
        except IOError:
            return ImageFont.load_default()

    def generate(self, account_key: str, title: str, topic: str) -> str:
        """
        Generates a thumbnail image based on the account's template style.
        """
        print(f"[{account_key}] Generating thumbnail for: {title}")
        
        # Determine base template path (mocking templates existence)
        template_filename = f"{account_key}_template.png"
        template_path = os.path.join(TEMPLATES_DIR, template_filename)
        
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        output_filename = os.path.join(TMP_DIR, f"{account_key}_{safe_topic}_thumbnail.jpg")

        # Try to open the actual template, fallback to creating a blank canvas if missing
        try:
            if os.path.exists(template_path):
                img = Image.open(template_path)
            else:
                # Create a blank 1920x1080 canvas with a distinct background color based on account
                colors = {
                    "yt_documenter": (20, 40, 60), # Dark Blue
                    "yt_funny": (255, 200, 50),    # Bright Yellow
                    "yt_anthro": (255, 100, 100),  # Warm Red
                    "yt_pov": (50, 100, 50),       # Dark Green
                    "yt_drama": (30, 0, 0),        # Dark Red
                    "fb_fanspage": (50, 150, 200)  # Facebook Blue
                }
                bg_color = colors.get(account_key, (0, 0, 0))
                img = Image.new('RGB', (1920, 1080), color=bg_color)
                
            draw = ImageDraw.Draw(img)
            
            # Simple text rendering logic (would need word wrapping in production)
            # Limit title to ~4 words as per checklist
            words = title.split()
            short_title = " ".join(words[:min(4, len(words))])
            
            # Draw text shadow/outline
            font = self._get_font(120)
            x, y = 100, 100
            shadow_color = 'black'
            text_color = 'white' if account_key != "yt_funny" else "black"
            
            # Draw shadow
            draw.text((x+5, y+5), short_title, font=font, fill=shadow_color)
            # Draw actual text
            draw.text((x, y), short_title, font=font, fill=text_color)
            
            # Add watermark text or logo
            logo_font = self._get_font(60)
            channel_name = ACCOUNTS[account_key]["name"]
            draw.text((100, 950), channel_name, font=logo_font, fill='white')
            
            # Save the result
            img.save(output_filename, format="JPEG", quality=90)
            return output_filename
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return ""

if __name__ == "__main__":
    # Test stub
    pass
