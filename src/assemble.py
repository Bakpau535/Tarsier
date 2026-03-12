import os
import random
from typing import List, Optional, Tuple
from PIL import Image
import numpy as np

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TMP_DIR, CLIP_DURATION_SEC
from src.loop_engine import apply_color_grade

class VideoAssembler:
    def __init__(self):
        self.fps = 24
        self.width = 1920
        self.height = 1080

    def _unify_frame(self, frame: np.ndarray, account_key: str = "fb_fanspage") -> np.ndarray:
        """
        Per-channel color grading — each channel gets its own visual style.
        Uses loop_engine.apply_color_grade for channel-specific processing.
        """
        return apply_color_grade(frame, account_key)

    def _ken_burns_frames(self, img_array: np.ndarray, duration: float) -> List[np.ndarray]:
        """Creates Ken Burns (zoom/pan) frames from a single image."""
        h, w = img_array.shape[:2]
        effect = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
        total_frames = int(duration * self.fps)
        frames = []
        
        for i in range(total_frames):
            progress = i / total_frames
            
            if effect == "zoom_in":
                scale = 1.0 - 0.2 * progress
            elif effect == "zoom_out":
                scale = 0.8 + 0.2 * progress
            elif effect == "pan_left":
                scale = 0.85
                cx = int(w * (0.55 - 0.1 * progress))
                cy = h // 2
                cw, ch = int(w * scale), int(h * scale)
                x1, y1 = max(0, cx - cw//2), max(0, cy - ch//2)
                cropped = img_array[y1:y1+ch, x1:x1+cw]
                frames.append(np.array(Image.fromarray(cropped).resize((self.width, self.height), Image.LANCZOS)))
                continue
            elif effect == "pan_right":
                scale = 0.85
                cx = int(w * (0.45 + 0.1 * progress))
                cy = h // 2
                cw, ch = int(w * scale), int(h * scale)
                x1, y1 = max(0, cx - cw//2), max(0, cy - ch//2)
                cropped = img_array[y1:y1+ch, x1:x1+cw]
                frames.append(np.array(Image.fromarray(cropped).resize((self.width, self.height), Image.LANCZOS)))
                continue
            else:
                scale = 1.0
            
            cw, ch = int(w * scale), int(h * scale)
            x1, y1 = (w - cw) // 2, (h - ch) // 2
            cropped = img_array[y1:y1+ch, x1:x1+cw]
            frames.append(np.array(Image.fromarray(cropped).resize((self.width, self.height), Image.LANCZOS)))
        
        return frames

    def assemble_final_video(self, account_key: str, topic: str,
                             media_items: list, voiceover_file: str,
                             music_file: str) -> Optional[str]:
        """
        Creates final video from mixed media (video clips + images).
        media_items: list of (type, path) tuples where type is "video" or "image"
        Bagian 4 Step 7.
        """
        if not media_items:
            print(f"[{account_key}] No media provided.")
            return None

        # Handle both old format (list of paths) and new format (list of tuples)
        if isinstance(media_items[0], str):
            # Old format: list of file paths — detect type by extension
            media_items = [
                ("video" if p.endswith(".mp4") else "image", p) 
                for p in media_items
            ]

        video_count = sum(1 for t, _ in media_items if t == "video")
        image_count = sum(1 for t, _ in media_items if t == "image")
        print(f"[{account_key}] Assembling: {video_count} video clips + {image_count} AI images...")

        try:
            from moviepy import (VideoFileClip, ImageSequenceClip, AudioFileClip,
                                 CompositeAudioClip, concatenate_videoclips)

            clips = []
            clip_dur = CLIP_DURATION_SEC  # 6 seconds per scene

            for i, (media_type, media_path) in enumerate(media_items):
                if not os.path.exists(media_path):
                    continue

                try:
                    if media_type == "video":
                        # Real stock video clip
                        vc = VideoFileClip(media_path)
                        if vc.duration > clip_dur:
                            max_start = max(0, vc.duration - clip_dur)
                            start = random.uniform(0, max_start)
                            vc = vc.subclipped(start, start + clip_dur)
                        vc = vc.resized((self.width, self.height))
                        # Same post-processing for ALL clips
                        vc = vc.image_transform(lambda f: self._unify_frame(f, account_key))
                        clips.append(vc)
                        print(f"[{account_key}] Added stock clip {i+1} ({vc.duration:.1f}s)")

                    elif media_type == "image":
                        # AI tarsier image → Ken Burns effect
                        img = Image.open(media_path).convert("RGB")
                        if img.width < self.width or img.height < self.height:
                            ratio = max(self.width / img.width, self.height / img.height) * 1.3
                            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                        frames = self._ken_burns_frames(np.array(img), clip_dur)
                        # Apply same post-processing to every AI frame
                        frames = [self._unify_frame(f, account_key) for f in frames]
                        ic = ImageSequenceClip(frames, fps=self.fps)
                        clips.append(ic)
                        print(f"[{account_key}] Added AI tarsier {i+1} (Ken Burns {clip_dur}s)")

                except Exception as e:
                    print(f"[{account_key}] Error processing media {i+1}: {e}")
                    continue

            if not clips:
                print(f"[{account_key}] No valid clips assembled.")
                return None

            # Concatenate all clips
            final_video = concatenate_videoclips(clips, method="compose")
            print(f"[{account_key}] Video assembled: {final_video.duration:.1f}s total")

            # Add Audio (Voiceover + Music) — with per-channel processing
            from src.audio_processor import process_audio
            processed_voice, processed_music = process_audio(
                voiceover_file, music_file, account_key, TMP_DIR
            )
            audio_clips = []

            if processed_voice and os.path.exists(processed_voice):
                try:
                    voice = AudioFileClip(processed_voice)
                    if voice.duration > final_video.duration:
                        voice = voice.subclipped(0, final_video.duration)
                    audio_clips.append(voice)
                except Exception as e:
                    print(f"[{account_key}] Voiceover load failed (skipping): {e}")

            if processed_music and os.path.exists(processed_music):
                try:
                    music = AudioFileClip(processed_music)
                    music = music.with_volume_scaled(0.5)  # Base level, already processed
                    if music.duration < final_video.duration:
                        from moviepy import concatenate_audioclips
                        loops = int(final_video.duration / music.duration) + 1
                        music = concatenate_audioclips([music] * loops)
                    music = music.subclipped(0, final_video.duration)
                    audio_clips.append(music)
                except Exception as e:
                    print(f"[{account_key}] Music load failed (skipping): {e}")

            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                final_video = final_video.with_audio(final_audio)

            # Export
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]
            output = os.path.join(TMP_DIR, f"{account_key}_{safe_topic}_final.mp4")

            final_video.write_videofile(
                output,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                preset="ultrafast",
                logger=None
            )

            # Cleanup clips
            for c in clips:
                try:
                    c.close()
                except:
                    pass

            print(f"[{account_key}] Final video: {output}")
            return output

        except Exception as e:
            print(f"[{account_key}] Assembly error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    pass
