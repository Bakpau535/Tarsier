import os
import random
from typing import List, Optional, Tuple
from PIL import Image
import numpy as np

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TMP_DIR, CLIP_DURATION_SEC, VIDEO_PROFILES
from src.loop_engine import apply_color_grade, generate_clip_variations
from src.text_overlay import render_text_on_frame


class VideoAssembler:
    """
    Per-channel video assembly engine.
    Reads VIDEO_PROFILES to build fundamentally different videos per channel:
    - Different cut durations (1-3s for funny, 6-12s for POV)
    - Different transitions (hard cut for funny, dissolve for documentary)
    - Different aspect ratios (16:9 for YT, 1:1 for FB)
    - Letterbox for drama channel (2.35:1 cinematic)
    - Loop engine integration for stock clip expansion
    """
    def __init__(self):
        self.fps = 24

    def _get_dimensions(self, account_key: str) -> Tuple[int, int]:
        """Per-channel resolution based on aspect_ratio profile.
        V3: ALL channels are VERTICAL 9:16 (1080x1920)."""
        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        ratio = profile.get("aspect_ratio", "9:16")
        if ratio == "1:1":
            return 1080, 1080  # Square for Facebook
        else:
            return 1080, 1920  # VERTICAL 9:16 (shorts format)

    def _apply_letterbox(self, frame: np.ndarray, account_key: str) -> np.ndarray:
        """Apply cinematic letterbox (2.35:1) for drama channel."""
        profile = VIDEO_PROFILES.get(account_key, {})
        if not profile.get("letterbox", False):
            return frame
        h, w = frame.shape[:2]
        # 2.35:1 letterbox — add black bars top and bottom
        target_h = int(w / 2.35)
        bar_h = (h - target_h) // 2
        if bar_h > 0:
            frame[:bar_h] = 0       # top bar
            frame[-bar_h:] = 0      # bottom bar
        return frame

    def _apply_color_grade(self, frame: np.ndarray, account_key: str) -> np.ndarray:
        """Per-channel color grading + letterbox."""
        graded = apply_color_grade(frame, account_key)
        return self._apply_letterbox(graded, account_key)

    def _ken_burns_frames(self, img_array: np.ndarray, duration: float,
                          width: int, height: int,
                          effect: str = None, account_key: str = None) -> List[np.ndarray]:
        """Creates Ken Burns (zoom/pan) frames from a single image.
        Per-channel behavior:
          yt_documenter: slow steady pans (NatGeo feel)
          yt_funny:      fast zoom + quick pans (attention grab)
          yt_pov:        slow creepy zoom-in (horror immersion)
          yt_drama:      cinematic slow push-in
          yt_anthro:     medium speed varied
          fb_fanspage:   standard smooth zoom
        """
        h, w = img_array.shape[:2]
        
        # Channel-specific effect + speed selection
        CHANNEL_KB = {
            "yt_documenter": {"effects": ["pan_left", "pan_right", "zoom_in"], "zoom_range": 0.12, "pan_range": 0.08},
            "yt_funny":      {"effects": ["zoom_in", "zoom_out", "zoom_in"], "zoom_range": 0.30, "pan_range": 0.15},
            "yt_anthro":     {"effects": ["zoom_in", "zoom_out", "pan_left", "pan_right"], "zoom_range": 0.18, "pan_range": 0.10},
            "yt_pov":        {"effects": ["zoom_in", "zoom_in", "zoom_in", "pan_left"], "zoom_range": 0.15, "pan_range": 0.06},
            "yt_drama":      {"effects": ["zoom_in", "pan_left", "pan_right"], "zoom_range": 0.15, "pan_range": 0.08},
            "fb_fanspage":   {"effects": ["zoom_in", "zoom_out", "pan_left", "pan_right"], "zoom_range": 0.20, "pan_range": 0.10},
        }
        
        kb_config = CHANNEL_KB.get(account_key, CHANNEL_KB["fb_fanspage"])
        if effect is None:
            effect = random.choice(kb_config["effects"])
        
        zoom_range = kb_config["zoom_range"]
        pan_range = kb_config["pan_range"]
        total_frames = int(duration * self.fps)
        frames = []

        for i in range(total_frames):
            progress = i / max(total_frames - 1, 1)

            if effect == "zoom_in":
                scale = 1.0 - zoom_range * progress
            elif effect == "zoom_out":
                scale = (1.0 - zoom_range) + zoom_range * progress
            elif effect in ("pan_left", "pan_right"):
                scale = 1.0 - (zoom_range * 0.5)  # Slight zoom during pan
                cx_offset = pan_range * progress * (-1 if effect == "pan_left" else 1)
                cx = int(w * (0.5 + cx_offset))
                cy = h // 2
                cw, ch = int(w * scale), int(h * scale)
                x1, y1 = max(0, cx - cw // 2), max(0, cy - ch // 2)
                x2, y2 = min(w, x1 + cw), min(h, y1 + ch)
                cropped = img_array[y1:y2, x1:x2]
                if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                    frames.append(np.array(Image.fromarray(cropped).resize((width, height), Image.LANCZOS)))
                continue
            else:
                scale = 1.0

            cw, ch = int(w * scale), int(h * scale)
            x1, y1 = (w - cw) // 2, (h - ch) // 2
            x2, y2 = x1 + cw, y1 + ch
            cropped = img_array[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
            if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                frames.append(np.array(Image.fromarray(cropped).resize((width, height), Image.LANCZOS)))

        return frames

    def _get_clip_duration(self, account_key: str) -> float:
        """Get random clip duration within channel's range."""
        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        dur_range = profile.get("cut_duration", (4, 7))
        return random.uniform(dur_range[0], dur_range[1])

    def _get_transition(self, account_key: str) -> str:
        """Get transition type for this channel."""
        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        return profile.get("transition", "dissolve")

    def assemble_final_video(self, account_key: str, topic: str,
                             media_items: list, voiceover_file: str,
                             music_file: str, script_segments: list = None,
                             ambience_path: str = None) -> Optional[str]:
        """
        Per-channel video assembly using VIDEO_PROFILES.
        Each channel gets fundamentally different:
        - Cut durations
        - Transitions (hard_cut vs dissolve)
        - Aspect ratio (16:9 vs 1:1)
        - Letterbox (drama channel 2.35:1)
        - Loop variations for stock clips
        """
        if not media_items:
            print(f"[{account_key}] No media provided.")
            return None

        profile = VIDEO_PROFILES.get(account_key, VIDEO_PROFILES["fb_fanspage"])
        width, height = self._get_dimensions(account_key)
        transition_type = self._get_transition(account_key)
        loop_style = profile.get("loop_style", "standard")

        # Handle both old format (list of paths) and new format (list of tuples)
        if isinstance(media_items[0], str):
            media_items = [
                ("video" if p.endswith(".mp4") else "image", p)
                for p in media_items
            ]

        # === SCENE LIMITER ===
        # Prevents assembling 300s+ of video only to trim/cap later (wasting RAM + CPU)
        MAX_NO_VO_DURATION = 60.0
        has_vo = profile.get("has_voiceover", True)
        dur_range = profile.get("cut_duration", (4, 7))
        avg_dur = sum(dur_range) / len(dur_range) if isinstance(dur_range, (tuple, list)) else dur_range

        if not has_vo:
            # No-VO: cap to 60s
            target_dur = MAX_NO_VO_DURATION
        else:
            # VO channels: estimate target from VO file duration + buffer
            target_dur = 70.0  # default ~70s if we can't read VO
            if processed_voice and os.path.exists(processed_voice):
                try:
                    from moviepy import AudioFileClip
                    _tmp_vo = AudioFileClip(processed_voice)
                    target_dur = _tmp_vo.duration + 5.0  # +5s buffer
                    _tmp_vo.close()
                    del _tmp_vo
                except Exception:
                    target_dur = 70.0

        max_scenes = max(6, int(target_dur / avg_dur) + 2)  # +2 buffer, minimum 6
        if len(media_items) > max_scenes:
            original_count = len(media_items)
            random.shuffle(media_items)
            media_items = media_items[:max_scenes]
            label = "no-VO" if not has_vo else "VO-matched"
            print(f"[{account_key}] Scene limiter ({label}): {original_count} → {max_scenes} scenes "
                  f"(target {target_dur:.0f}s, avg {avg_dur:.0f}s/scene)")

        video_count = sum(1 for t, _ in media_items if t == "video")
        image_count = sum(1 for t, _ in media_items if t == "image")
        print(f"[{account_key}] Assembly profile: cut={profile['cut_duration']}s, "
              f"transition={transition_type}, ratio={profile['aspect_ratio']}, "
              f"letterbox={profile['letterbox']}, loop={loop_style}")
        print(f"[{account_key}] Assembling: {video_count} stock clips + {image_count} AI images...")

        try:
            from moviepy import (VideoFileClip, ImageSequenceClip, AudioFileClip,
                                 CompositeAudioClip, concatenate_videoclips)

            clips = []
            last_variation = None  # Track to prevent consecutive same variations

            # === SPREAD text overlays across scenes — VO-synced pacing ===
            # V2: Phrases appear sequentially (scene 1, 2, 3...) matching VO pacing.
            # Scene 0 is text-free (let visual breathe), then phrases flow consecutively.
            # After all phrases shown, remaining scenes are text-free (visual outro).
            overlay_map = {}
            if script_segments and len(media_items) > 0:
                n_segments = len(script_segments)
                n_scenes = len(media_items)
                
                # Start text from scene 1 (scene 0 = visual intro, no text)
                start_scene = min(1, n_scenes - 1)
                
                if n_segments >= n_scenes - start_scene:
                    # More phrases than available scenes → assign 1 per scene from start
                    for i in range(n_scenes - start_scene):
                        overlay_map[start_scene + i] = script_segments[i]
                else:
                    # Fewer phrases than scenes → assign consecutively from start
                    # This creates natural pacing: text flows, then visual outro
                    for seg_idx in range(n_segments):
                        scene_idx = start_scene + seg_idx
                        if scene_idx < n_scenes:
                            overlay_map[scene_idx] = script_segments[seg_idx]
                
                text_scenes = len(overlay_map)
                free_scenes = n_scenes - text_scenes
                print(f"[{account_key}] Text overlay: {n_segments} phrases → "
                      f"{text_scenes} scenes with text, {free_scenes} scenes text-free")

            for i, (media_type, media_path) in enumerate(media_items):
                if not os.path.exists(media_path):
                    continue

                # Per-channel clip duration
                clip_dur = self._get_clip_duration(account_key)

                try:
                    if media_type == "video":
                        # --- STOCK VIDEO CLIP ---
                        vc = VideoFileClip(media_path)

                        # Generate loop variations from this clip via loop_engine
                        if loop_style in ("standard", "replay", "drift", "emotional", "reaction"):
                            variations = generate_clip_variations(
                                media_path, account_key, loop_style, TMP_DIR, i
                            )
                            # Use the first variation that differs from last
                            used_var = False
                            for var_path in variations:
                                if var_path != last_variation and os.path.exists(var_path):
                                    try:
                                        var_clip = VideoFileClip(var_path)
                                        if var_clip.duration > clip_dur:
                                            max_s = max(0, var_clip.duration - clip_dur)
                                            s = random.uniform(0, max_s)
                                            var_clip = var_clip.subclipped(s, s + clip_dur)
                                        var_clip = var_clip.resized((width, height))
                                        var_clip = var_clip.image_transform(
                                            lambda f, ak=account_key: self._apply_color_grade(f, ak)
                                        )
                                        clips.append(var_clip)
                                        last_variation = var_path
                                        used_var = True
                                        print(f"[{account_key}] Added variation {i+1}: {os.path.basename(var_path)} ({var_clip.duration:.1f}s)")
                                        break
                                    except Exception as e:
                                        print(f"[{account_key}] Variation error: {e}")
                                        continue

                            if used_var:
                                vc.close()
                                continue

                        # Fallback: use original clip directly
                        if vc.duration > clip_dur:
                            max_start = max(0, vc.duration - clip_dur)
                            start = random.uniform(0, max_start)
                            vc = vc.subclipped(start, start + clip_dur)
                        vc = vc.resized((width, height))
                        vc = vc.image_transform(
                            lambda f, ak=account_key: self._apply_color_grade(f, ak)
                        )
                        clips.append(vc)
                        print(f"[{account_key}] Added stock clip {i+1} ({vc.duration:.1f}s)")

                    elif media_type == "image":
                        # --- AI ENVIRONMENT IMAGE → Ken Burns effect (LAZY) ---
                        img = Image.open(media_path).convert("RGB")
                        # Ensure image is large enough for Ken Burns
                        if img.width < width or img.height < height:
                            ratio = max(width / img.width, height / img.height) * 1.3
                            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                        img_arr = np.array(img)
                        del img  # Free PIL image immediately
                        
                        # LAZY Ken Burns — generate 1 frame at a time (saves ~17GB RAM)
                        # Channel-specific effect + speed
                        CHANNEL_KB = {
                            "yt_documenter": {"effects": ["pan_left", "pan_right", "zoom_in"], "zoom_range": 0.12, "pan_range": 0.08},
                            "yt_funny":      {"effects": ["zoom_in", "zoom_out", "zoom_in"], "zoom_range": 0.30, "pan_range": 0.15},
                            "yt_anthro":     {"effects": ["zoom_in", "zoom_out", "pan_left", "pan_right"], "zoom_range": 0.18, "pan_range": 0.10},
                            "yt_pov":        {"effects": ["zoom_in", "zoom_in", "zoom_in", "pan_left"], "zoom_range": 0.15, "pan_range": 0.06},
                            "yt_drama":      {"effects": ["zoom_in", "pan_left", "pan_right"], "zoom_range": 0.15, "pan_range": 0.08},
                            "fb_fanspage":   {"effects": ["zoom_in", "zoom_out", "pan_left", "pan_right"], "zoom_range": 0.20, "pan_range": 0.10},
                        }
                        kb_cfg = CHANNEL_KB.get(account_key, CHANNEL_KB["fb_fanspage"])
                        kb_effect = random.choice(kb_cfg["effects"])
                        kb_zoom = kb_cfg["zoom_range"]
                        kb_pan = kb_cfg["pan_range"]
                        overlay = overlay_map.get(i)  # Spread across scenes via map
                        
                        def make_frame(t, _img=img_arr, _dur=clip_dur, _w=width, _h=height,
                                       _effect=kb_effect, _ak=account_key, _overlay=overlay,
                                       _zr=kb_zoom, _pr=kb_pan):
                            """Generate a single Ken Burns frame at time t (lazy, 1 at a time)."""
                            progress = t / max(_dur - 1/24, 0.001)
                            ih, iw = _img.shape[:2]
                            
                            if _effect == "zoom_in":
                                scale = 1.0 - _zr * progress
                            elif _effect == "zoom_out":
                                scale = (1.0 - _zr) + _zr * progress
                            elif _effect in ("pan_left", "pan_right"):
                                scale = 1.0 - (_zr * 0.5)
                                cx_off = _pr * progress * (-1 if _effect == "pan_left" else 1)
                                cx = int(iw * (0.5 + cx_off))
                                cy = ih // 2
                                cw, ch = int(iw * scale), int(ih * scale)
                                x1, y1 = max(0, cx - cw // 2), max(0, cy - ch // 2)
                                x2, y2 = min(iw, x1 + cw), min(ih, y1 + ch)
                                cropped = _img[y1:y2, x1:x2]
                                frame = np.array(Image.fromarray(cropped).resize((_w, _h), Image.LANCZOS))
                                frame = self._apply_color_grade(frame, _ak)
                                if _overlay:
                                    frame = render_text_on_frame(frame, _overlay, _ak)
                                return frame
                            else:
                                scale = 1.0
                            
                            cw, ch = int(iw * scale), int(ih * scale)
                            x1, y1 = (iw - cw) // 2, (ih - ch) // 2
                            cropped = _img[max(0,y1):min(ih,y1+ch), max(0,x1):min(iw,x1+cw)]
                            frame = np.array(Image.fromarray(cropped).resize((_w, _h), Image.LANCZOS))
                            frame = self._apply_color_grade(frame, _ak)
                            if _overlay:
                                frame = render_text_on_frame(frame, _overlay, _ak)
                            return frame
                        
                        from moviepy import VideoClip
                        ic = VideoClip(make_frame, duration=clip_dur).with_fps(self.fps)
                        clips.append(ic)
                        print(f"[{account_key}] Added environment image {i+1} (Ken Burns {clip_dur:.1f}s)")

                except Exception as e:
                    print(f"[{account_key}] Error processing media {i+1}: {e}")
                    continue

            if not clips:
                print(f"[{account_key}] No valid clips assembled.")
                return None

            # Concatenate clips with per-channel transition
            if transition_type == "dissolve" and len(clips) > 1:
                # Cross-dissolve transition (0.5s overlap)
                transition_dur = 0.5
                final_video = concatenate_videoclips(clips, method="compose",
                                                     padding=-transition_dur)
            else:
                # Hard cut — no transition (used by yt_funny)
                final_video = concatenate_videoclips(clips, method="compose")

            print(f"[{account_key}] Video assembled: {final_video.duration:.1f}s total "
                  f"(transition={transition_type})")

            # Add Audio (Voiceover + Music) — with per-channel processing
            from src.audio_processor import process_audio
            processed_voice, processed_music = process_audio(
                voiceover_file, music_file, account_key, TMP_DIR
            )
            audio_clips = []

            if processed_voice and os.path.exists(processed_voice):
                try:
                    voice = AudioFileClip(processed_voice)
                    print(f"[{account_key}] VO duration: {voice.duration:.1f}s | Video duration: {final_video.duration:.1f}s")
                    
                    if voice.duration > final_video.duration + 0.5:
                        # VO longer than video → EXTEND video
                        # RULE: VO is NEVER trimmed — it must always play completely
                        # RULE: NO identical clip repetition — filler uses reversed/different segments
                        target_dur = voice.duration + 1.0  # +1s buffer
                        print(f"[{account_key}] Extending video from {final_video.duration:.1f}s to {target_dur:.1f}s to match VO...")
                        if clips:
                            filler_clips = []
                            filler_dur = 0
                            gap = target_dur - final_video.duration
                            clip_idx = 0
                            while filler_dur < gap:
                                src_clip = clips[clip_idx % len(clips)]
                                remaining = gap - filler_dur
                                use_dur = min(src_clip.duration, remaining)
                                
                                # ANTI-REPEAT: alternate between normal and time-reversed
                                # So clip 0 plays normal, clip 0 (2nd time) plays reversed
                                cycle = clip_idx // len(clips)  # How many times we've looped
                                if cycle > 0 and cycle % 2 == 1:
                                    # Reverse the clip (plays backwards = looks different)
                                    try:
                                        filler = src_clip.time_transform(
                                            lambda t, d=src_clip.duration: d - t - 1/24,
                                            apply_to=['mask', 'audio']
                                        ).subclipped(0, use_dur)
                                    except Exception:
                                        # Fallback: use different start point
                                        offset = min(src_clip.duration * 0.3, src_clip.duration - use_dur)
                                        filler = src_clip.subclipped(offset, offset + use_dur)
                                else:
                                    filler = src_clip.subclipped(0, use_dur)
                                
                                filler_clips.append(filler)
                                filler_dur += use_dur
                                clip_idx += 1
                            if filler_clips:
                                extended = concatenate_videoclips([final_video] + filler_clips, method="compose")
                                final_video = extended
                                cycles_used = clip_idx // max(len(clips), 1)
                                print(f"[{account_key}] Video extended to {final_video.duration:.1f}s ({len(filler_clips)} filler clips, {cycles_used} cycles)")
                    
                    elif voice.duration < final_video.duration - 2.0:
                        # VO shorter than video → trim video to match VO + 1.5s buffer
                        target_dur = voice.duration + 1.5
                        final_video = final_video.subclipped(0, min(target_dur, final_video.duration))
                        print(f"[{account_key}] Trimmed video to match VO ({target_dur:.1f}s)")
                    
                    audio_clips.append(voice)
                except Exception as e:
                    print(f"[{account_key}] Voiceover load failed (skipping): {e}")
            else:
                # NO VOICEOVER — cap video to max 60s for shorts format
                MAX_NO_VO_DURATION = 60.0
                if final_video.duration > MAX_NO_VO_DURATION:
                    final_video = final_video.subclipped(0, MAX_NO_VO_DURATION)
                    print(f"[{account_key}] No VO: capped video to {MAX_NO_VO_DURATION:.0f}s")

            if processed_music and os.path.exists(processed_music):
                try:
                    music = AudioFileClip(processed_music)
                    # NOTE: Music volume is ALREADY set by audio_processor.py (per-channel + ducking)
                    # Do NOT scale again here — previous double-scaling made music inaudible
                    # (e.g., audio_processor 20% × assembler 45% = 9% effective)
                    print(f"[{account_key}] Music loaded (volume pre-set by audio_processor)")
                    if music.duration < final_video.duration:
                        from moviepy import concatenate_audioclips
                        loops = int(final_video.duration / music.duration) + 1
                        music = concatenate_audioclips([music] * loops)
                    music = music.subclipped(0, final_video.duration)
                    audio_clips.append(music)
                except Exception as e:
                    print(f"[{account_key}] Music load failed (skipping): {e}")

            if audio_clips:
                # Mix ambience layer ON TOP of music (per-channel volume)
                if ambience_path and os.path.exists(ambience_path):
                    try:
                        ambience = AudioFileClip(ambience_path)
                        # Per-channel ambience volume
                        AMB_VOL = {
                            "yt_documenter": 0.15, "yt_funny": 0.25, "yt_anthro": 0.12,
                            "yt_pov": 0.35, "yt_drama": 0.20, "fb_fanspage": 0.10,
                        }
                        amb_vol = AMB_VOL.get(account_key, 0.15)
                        ambience = ambience.with_volume_scaled(amb_vol)
                        # Loop if shorter than video
                        if ambience.duration < final_video.duration:
                            from moviepy import concatenate_audioclips
                            loops = int(final_video.duration / ambience.duration) + 1
                            ambience = concatenate_audioclips([ambience] * loops)
                        ambience = ambience.subclipped(0, final_video.duration)
                        audio_clips.append(ambience)
                        print(f"[{account_key}] Ambience layer added (vol: {amb_vol:.0%})")
                    except Exception as e:
                        print(f"[{account_key}] Ambience load failed (skipping): {e}")
                
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

            # Cleanup clips — release ALL MoviePy memory
            for c in clips:
                try:
                    c.close()
                except:
                    pass
            try:
                final_video.close()
            except:
                pass
            for ac in audio_clips:
                try:
                    ac.close()
                except:
                    pass
            del clips, final_video, audio_clips
            import gc
            gc.collect()

            print(f"[{account_key}] Final video: {output}")
            return output

        except Exception as e:
            print(f"[{account_key}] Assembly error: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    pass
