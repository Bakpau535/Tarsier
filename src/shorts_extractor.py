import os
from moviepy import VideoFileClip
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TMP_DIR, SHORT_DURATIONS_SEC

class ShortsExtractor:
    def __init__(self):
        self.target_duration = 45

    def extract_hook(self, video_path: str, account_key: str, topic: str) -> str:
        """Extracts a Short/Hook from the video (first ~45s, cropped 9:16)."""
        print(f"[{account_key}] Extracting Short from {video_path}...")
        
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Source video not found: {video_path}")
                
            clip = VideoFileClip(video_path)
            
            # Pick a segment
            start_time = min(15, clip.duration - 5) if clip.duration > 20 else 0
            end_time = min(start_time + self.target_duration, clip.duration)
            
            # moviepy v2 API: subclipped instead of subclip
            short_clip = clip.subclipped(start_time, end_time)
            
            # Crop to 9:16 vertical (YouTube Shorts)
            w, h = short_clip.size
            if w > h:
                target_w = int(h * 9 / 16)
                x1 = (w - target_w) // 2
                x2 = x1 + target_w
                # moviepy v2 API: cropped instead of crop
                short_clip = short_clip.cropped(x1=x1, y1=0, x2=x2, y2=h)
            
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]
            output = os.path.join(TMP_DIR, f"{account_key}_{safe_topic}_short.mp4")
            
            short_clip.write_videofile(
                output, 
                codec="libx264", 
                audio_codec="aac", 
                threads=2, 
                preset="ultrafast",
                logger=None
            )
            
            short_clip.close()
            clip.close()
            
            print(f"[{account_key}] Short saved: {output}")
            return output
            
        except Exception as e:
            print(f"[{account_key}] Shorts extraction error: {e}")
            return ""

if __name__ == "__main__":
    pass
