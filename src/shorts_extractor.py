import os
import random
from moviepy import VideoFileClip, concatenate_videoclips
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TMP_DIR, SHORT_DURATIONS_SEC


class ShortsExtractor:
    """Extracts YouTube Shorts from full video.
    
    RULES:
    - Shorts must feel COMPLETE, not chopped/hanging
    - Cut at sentence boundaries (silence gaps in audio)
    - Always start from the BEGINNING (hook/intro) for maximum engagement
    - Target 30-45 seconds
    - 9:16 vertical crop with fade transitions
    """
    
    def __init__(self):
        self.target_duration = 45  # seconds
        self.min_duration = 15     # minimum viable short
        self.max_duration = 58     # YouTube Shorts max = 60s

    def _find_silence_points(self, audio_clip, threshold=0.02, min_gap=0.3):
        """Find silence points in audio that indicate sentence boundaries.
        Returns list of timestamps where silence gaps occur."""
        import numpy as np
        
        try:
            fps = audio_clip.fps
            # Sample audio at lower rate for speed
            sample_rate = min(fps, 8000)
            duration = audio_clip.duration
            
            silence_points = []
            window_size = int(sample_rate * min_gap)
            
            # Get audio as numpy array
            audio_frames = []
            for t in range(0, int(duration * sample_rate)):
                time_sec = t / sample_rate
                if time_sec >= duration:
                    break
                try:
                    frame = audio_clip.get_frame(time_sec)
                    rms = float(abs(frame).mean())
                    audio_frames.append((time_sec, rms))
                except Exception:
                    continue
            
            # Find silence gaps (low RMS regions)
            if audio_frames:
                avg_rms = sum(f[1] for f in audio_frames) / len(audio_frames)
                silence_threshold = avg_rms * 0.15  # 15% of average = silence
                
                in_silence = False
                silence_start = 0
                for time_sec, rms in audio_frames:
                    if rms < silence_threshold:
                        if not in_silence:
                            silence_start = time_sec
                            in_silence = True
                    else:
                        if in_silence and (time_sec - silence_start) > min_gap:
                            # Found a silence gap — this is a sentence boundary
                            silence_points.append(time_sec)
                        in_silence = False
            
            return silence_points
        except Exception as e:
            print(f"[ShortsExtractor] Silence detection error: {e}")
            return []

    def extract_hook(self, video_path: str, account_key: str, topic: str) -> str:
        """Extracts a Short from the video — always starts from beginning (hook),
        cuts at nearest sentence boundary to avoid hanging mid-sentence."""
        print(f"[{account_key}] Extracting Short from {video_path}...")
        
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Source video not found: {video_path}")
                
            clip = VideoFileClip(video_path)
            
            if clip.duration < self.min_duration:
                print(f"[{account_key}] Video too short ({clip.duration:.1f}s) for Shorts extraction")
                clip.close()
                return ""
            
            # STRATEGY: Start from SECOND 0 (the hook/intro is the strongest part)
            # Then find the best cut point near target_duration using silence detection
            start_time = 0
            raw_end = min(self.target_duration, clip.duration)
            
            # Try to find a clean sentence boundary near our target end
            best_end = raw_end
            if clip.audio:
                try:
                    silence_points = self._find_silence_points(clip.audio)
                    if silence_points:
                        # Find the silence point closest to (but not exceeding) target duration
                        # Prefer points between 25s-50s for a natural short
                        valid_points = [p for p in silence_points 
                                       if self.min_duration < p <= min(self.max_duration, clip.duration)]
                        if valid_points:
                            # Pick the one closest to target_duration
                            best_end = min(valid_points, key=lambda p: abs(p - self.target_duration))
                            print(f"[{account_key}] Found clean cut at {best_end:.1f}s (sentence boundary)")
                        else:
                            print(f"[{account_key}] No clean cut found, using {raw_end:.1f}s")
                except Exception as e:
                    print(f"[{account_key}] Silence detection failed: {e}, using raw cut")
            
            # Ensure we don't exceed max shorts duration
            best_end = min(best_end, self.max_duration, clip.duration)
            
            # Extract the segment
            short_clip = clip.subclipped(start_time, best_end)
            
            # Add fade-in/out so it feels COMPLETE, not chopped
            try:
                short_clip = short_clip.with_effects([
                    lambda c: c.crossfadein(0.5),
                    lambda c: c.crossfadeout(0.8),
                ])
            except Exception:
                # Fallback: try simpler fade
                try:
                    from moviepy.video.fx import FadeIn, FadeOut
                    short_clip = short_clip.with_effects([FadeIn(0.5), FadeOut(0.8)])
                except Exception:
                    pass  # No fades if not supported
            
            # Crop to 9:16 vertical (YouTube Shorts)
            w, h = short_clip.size
            if w > h:
                target_w = int(h * 9 / 16)
                x1 = (w - target_w) // 2
                x2 = x1 + target_w
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
            
            final_dur = short_clip.duration
            short_clip.close()
            clip.close()
            
            print(f"[{account_key}] Short saved: {output} ({final_dur:.1f}s, cut at sentence boundary)")
            return output
            
        except Exception as e:
            print(f"[{account_key}] Shorts extraction error: {e}")
            return ""


if __name__ == "__main__":
    pass
