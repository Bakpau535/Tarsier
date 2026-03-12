import os
from moviepy import VideoFileClip
from typing import Dict, Any

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import MINIMUM_QC_SCORE

class QualityControl:
    def __init__(self):
        # We define weights according to the master checklist
        self.criteria = {
            "resolution": 25,
            "text_cutoff": 25, # Usually requires OCR, mocking pass for now
            "av_sync": 20,     # Requires complex analysis, mocking pass for now
            "metadata": 20,
            "duration": 10
        }

    def check_resolution(self, video_path: str) -> int:
        """Checks if video is at least 1080p."""
        try:
            clip = VideoFileClip(video_path)
            w, h = clip.size
            clip.close()
            if w >= 1920 and h >= 1080:
                return self.criteria["resolution"]
            return 0
        except Exception:
            return 0

    def check_metadata(self, metadata: Dict[str, Any]) -> int:
        """Checks if all metadata fields are present and valid (Bagian 6)."""
        # Bagian 6: Judul, Deskripsi, Hashtag, Tags, Kategori, Bahasa
        required_keys = ["title", "description", "hashtags", "tags", "category", "language"]
        if all(key in metadata and metadata[key] for key in required_keys):
            return self.criteria["metadata"]
        missing = [k for k in required_keys if k not in metadata or not metadata[k]]
        print(f"QC Warning: Missing metadata fields: {missing}")
        return 0

    def check_duration(self, video_path: str, target_duration: int = 72, tolerance: int = 30) -> int:
        """Checks if video is within the target duration +/- tolerance."""
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()
            
            if abs(duration - target_duration) <= tolerance:
                return self.criteria["duration"]
            return 0
        except Exception:
            return 0

    def evaluate(self, video_path: str, metadata: Dict[str, Any], target_duration: int = 60) -> bool:
        """
        Runs the full QC pipeline. Returns True if score >= MINIMUM_QC_SCORE.
        """
        if not os.path.exists(video_path):
            print("QC Failed: Video file not found.")
            return False
            
        print(f"Running Quality Control for {video_path}...")
        
        score = 0
        
        score += self.check_resolution(video_path)
        score += self.check_metadata(metadata)
        score += self.check_duration(video_path, target_duration)
        
        # Mocking the difficult visual/audio checks for this version
        score += self.criteria["text_cutoff"] # Assume passed
        score += self.criteria["av_sync"]     # Assume passed
        
        print(f"QC Score: {score}/100")
        
        if score >= MINIMUM_QC_SCORE:
            print("QC Passed!")
            return True
        else:
            print(f"QC Failed: Score below minimum threshold ({MINIMUM_QC_SCORE})")
            return False

if __name__ == "__main__":
    # Test stub
    pass
