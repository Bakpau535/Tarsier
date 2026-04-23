import os
from moviepy import VideoFileClip
from typing import Dict, Any

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import MINIMUM_QC_SCORE, VIDEO_PROFILES

class QualityControl:
    def __init__(self):
        # Weight per criteria (total = 100)
        self.criteria = {
            "resolution": 25,
            "text_cutoff": 25,  # Mocked pass (would need OCR)
            "av_sync": 20,      # Mocked pass (would need complex analysis)
            "metadata": 20,
            "duration": 10
        }

    def check_resolution(self, video_path: str, account_key: str = "") -> int:
        """
        Checks if video resolution matches the channel's expected format.
        - YouTube channels (16:9): min 1920x1080
        - FB fanspage (1:1): min 1080x1080
        """
        try:
            clip = VideoFileClip(video_path)
            w, h = clip.size
            clip.close()
            
            profile = VIDEO_PROFILES.get(account_key, {})
            aspect = profile.get("aspect_ratio", "16:9")
            
            if aspect == "1:1":
                # FB square format — 1080x1080 is valid
                if w >= 1080 and h >= 1080:
                    print(f"QC Resolution: {w}x{h} (1:1 square) — PASS")
                    return self.criteria["resolution"]
            elif aspect == "9:16":
                # VERTICAL shorts format — 1080x1920 minimum
                if w >= 1080 and h >= 1920:
                    print(f"QC Resolution: {w}x{h} (9:16 vertical) — PASS")
                    return self.criteria["resolution"]
                # Accept close matches (e.g. 1080x1906 from letterbox)
                if w >= 1080 and h >= 1800:
                    print(f"QC Resolution: {w}x{h} (9:16 near-vertical) — PASS")
                    return self.criteria["resolution"]
            else:
                # Standard 16:9 format — 1920x1080 minimum
                if w >= 1920 and h >= 1080:
                    print(f"QC Resolution: {w}x{h} (16:9) — PASS")
                    return self.criteria["resolution"]
            
            expected = "1080x1080" if aspect == "1:1" else ("1080x1920" if aspect == "9:16" else "1920x1080")
            print(f"QC Resolution: {w}x{h} — FAIL (expected {expected})")
            return 0
        except Exception as e:
            print(f"QC Resolution check error: {e}")
            return 0

    def check_metadata(self, metadata: Dict[str, Any]) -> int:
        """Checks if all metadata fields are present and valid."""
        required_keys = ["title", "description", "hashtags", "tags", "category", "language"]
        if all(key in metadata and metadata[key] for key in required_keys):
            print(f"QC Metadata: all fields present — PASS")
            return self.criteria["metadata"]
        missing = [k for k in required_keys if k not in metadata or not metadata[k]]
        print(f"QC Metadata: missing {missing} — FAIL")
        return 0

    def check_duration(self, video_path: str, account_key: str = "",
                       target_duration: int = 72, tolerance: int = 40) -> int:
        """
        Checks if video duration is within acceptable range.
        RULE: ALL videos must be at least 60s (shorts replaced long-form).
        Tolerance is generous (±40s) because loop engine variations 
        can create natural length variations.
        """
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()
            
            # MINIMUM 60s — shorts now replace long videos, must be at least 1 minute
            ABSOLUTE_MIN_DURATION = 60
            min_dur = max(target_duration - tolerance, ABSOLUTE_MIN_DURATION)
            max_dur = target_duration + tolerance
            
            if min_dur <= duration <= max_dur:
                print(f"QC Duration: {duration:.1f}s (target: {target_duration}s, range: {min_dur}-{max_dur}s) — PASS")
                return self.criteria["duration"]
            
            if duration < ABSOLUTE_MIN_DURATION:
                print(f"QC Duration: {duration:.1f}s — FAIL (below absolute minimum {ABSOLUTE_MIN_DURATION}s)")
            else:
                print(f"QC Duration: {duration:.1f}s — FAIL (need {min_dur}-{max_dur}s)")
            return 0
        except Exception as e:
            print(f"QC Duration check error: {e}")
            return 0

    def evaluate(self, video_path: str, metadata: Dict[str, Any],
                 target_duration: int = 60, account_key: str = "") -> bool:
        """
        Runs the full QC pipeline. Returns True if score >= MINIMUM_QC_SCORE.
        Channel-aware: uses VIDEO_PROFILES for resolution and duration targets.
        """
        if not os.path.exists(video_path):
            print("QC Failed: Video file not found.")
            return False
            
        print(f"Running Quality Control for [{account_key}] {video_path}...")
        
        score = 0
        
        # Channel-aware checks
        score += self.check_resolution(video_path, account_key)
        score += self.check_metadata(metadata)
        score += self.check_duration(video_path, account_key, target_duration)
        
        # Mocking the difficult visual/audio checks for this version
        score += self.criteria["text_cutoff"]  # Assume passed
        score += self.criteria["av_sync"]      # Assume passed
        
        print(f"QC Score: {score}/100 (threshold: {MINIMUM_QC_SCORE})")
        
        if score >= MINIMUM_QC_SCORE:
            print(f"[{account_key}] QC Passed!")
            return True
        else:
            print(f"[{account_key}] QC Failed: {score}/100 (below {MINIMUM_QC_SCORE})")
            return False

if __name__ == "__main__":
    pass
