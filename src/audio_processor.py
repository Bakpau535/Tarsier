"""
Audio Processor — Normalize, volume control, and ducking for voiceover + music.
Per-channel volume specs ensure music never drowns out narration.
Uses pydub for audio processing.
"""
import os
from typing import Optional


# Per-channel volume settings
# Formula: final_dBFS = -20 + 20*log10(music_vol)
# VO channels: music ~10dB below VO | No-VO channels: music = main audio
# NOTE: assemble.py NO LONGER applies a second volume scale — these values are the FINAL volume
VOLUME_SPEC = {
    "yt_documenter": {"music_normal": 0.50, "music_ducked": 0.25, "duck_threshold": -30},  # normal=-26dB, ducked=-32dB, VO=-16dB
    "yt_funny":      {"music_normal": 1.25, "music_ducked": 1.25, "duck_threshold": -30},  # No VO → music=-18dB (main audio)
    "yt_anthro":     {"music_normal": 0.50, "music_ducked": 0.25, "duck_threshold": -28},  # normal=-26dB, ducked=-32dB, VO=-16dB
    "yt_pov":        {"music_normal": 1.25, "music_ducked": 1.25, "duck_threshold": -32},  # No VO → music=-18dB (main audio)
    "yt_drama":      {"music_normal": 0.63, "music_ducked": 0.30, "duck_threshold": -28},  # normal=-24dB, ducked=-30dB, VO=-16dB
    "fb_fanspage":   {"music_normal": 0.55, "music_ducked": 0.28, "duck_threshold": -30},  # normal=-25dB, ducked=-31dB, VO=-14dB
}


def process_audio(voice_path: Optional[str], music_path: Optional[str],
                  account_key: str, output_dir: str) -> tuple:
    """
    Process voiceover and music with per-channel specs:
    1. Normalize voiceover volume
    2. Apply channel-specific music volume
    3. Apply ducking (lower music when voice is active)
    
    Returns: (processed_voice_path, processed_music_path)
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        print(f"[{account_key}] pydub not available, skipping audio processing")
        return voice_path, music_path
    
    spec = VOLUME_SPEC.get(account_key, VOLUME_SPEC["fb_fanspage"])
    processed_voice = voice_path
    processed_music = music_path
    
    # Step 1: Process voiceover — normalize
    if voice_path and os.path.exists(voice_path):
        try:
            voice = AudioSegment.from_file(voice_path)
            
            # Normalize to -16 LUFS (approximate via dBFS targeting)
            target_dbfs = -16.0
            if account_key == "yt_pov":
                target_dbfs = -18.0  # Quieter for intimate channel
            elif account_key == "fb_fanspage":
                target_dbfs = -14.0  # Louder for Facebook autoplay
            
            change_in_dbfs = target_dbfs - voice.dBFS
            voice = voice.apply_gain(change_in_dbfs)
            
            # High-pass filter at 80Hz to remove rumble (approximation)
            # pydub doesn't have native EQ, so we do basic normalization only
            
            processed_voice = os.path.join(output_dir, f"{account_key}_voice_processed.mp3")
            voice.export(processed_voice, format="mp3", bitrate="128k")
            print(f"[{account_key}] Voice normalized to {target_dbfs:.0f} dBFS")
            
        except Exception as e:
            print(f"[{account_key}] Voice processing failed (using original): {e}")
            processed_voice = voice_path
    
    # Step 2: Process music — adjust volume per channel
    if music_path and os.path.exists(music_path):
        try:
            music = AudioSegment.from_file(music_path)
            
            # Trim leading silence + slow fade-ins — Freesound previews often
            # have silent intros or very slow fade-ins that sound "blank"
            def _detect_leading_silence(sound, silence_threshold=-35.0, chunk_size=50):
                """Returns ms of leading silence (more aggressive than default)."""
                trim_ms = 0
                while trim_ms < len(sound) and sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold:
                    trim_ms += chunk_size
                return trim_ms
            
            def _detect_slow_fadein(sound, loud_threshold=-30.0, chunk_size=100):
                """Returns ms before first 'actually audible' chunk.
                Catches slow fade-ins that pass silence detection but sound blank."""
                scan_ms = 0
                # Only scan first 10 seconds max
                max_scan = min(len(sound), 10000)
                while scan_ms < max_scan and sound[scan_ms:scan_ms+chunk_size].dBFS < loud_threshold:
                    scan_ms += chunk_size
                return scan_ms
            
            # Primary: trim true silence
            leading_ms = _detect_leading_silence(music)
            if leading_ms > 100:  # More than 100ms silence = trim it
                music = music[leading_ms:]
                print(f"[{account_key}] Trimmed {leading_ms}ms leading silence from music")
            
            # Secondary: trim slow fade-in (sounds blank even if not technically silent)
            fadein_ms = _detect_slow_fadein(music)
            if fadein_ms > 500:  # More than 500ms of inaudible fade-in
                # Keep 200ms before the loud point for natural feel
                trim_point = max(0, fadein_ms - 200)
                music = music[trim_point:]
                print(f"[{account_key}] Trimmed {trim_point}ms slow fade-in from music")
            
            # Add quick fade-in (50ms) to prevent click artifacts after trim
            music = music.fade_in(50)
            
            # Apply channel-specific music volume
            music_vol = spec["music_normal"]
            
            # Calculate volume reduction in dB from ratio
            # e.g., 0.08 = -22dB, 0.18 = -15dB
            import math
            if music_vol > 0:
                vol_db = 20 * math.log10(music_vol)
            else:
                vol_db = -60
            
            # Normalize music to -20 dBFS, then apply channel volume reduction
            change_in_dbfs = -20.0 - music.dBFS  # Normalize to -20 dBFS first
            music = music.apply_gain(change_in_dbfs + vol_db)  # Then apply channel volume
            final_dbfs = -20.0 + vol_db
            print(f"[{account_key}] Music final level: {final_dbfs:.1f} dBFS (vol_db: {vol_db:.1f})")
            
            # Step 3: Apply ducking if voiceover exists
            if processed_voice and os.path.exists(processed_voice) and spec["music_ducked"] < spec["music_normal"]:
                music = _apply_ducking(music, processed_voice, spec, account_key)
            
            processed_music = os.path.join(output_dir, f"{account_key}_music_processed.mp3")
            music.export(processed_music, format="mp3", bitrate="128k")
            print(f"[{account_key}] Music processed (vol: {music_vol*100:.0f}%)")
            
        except Exception as e:
            print(f"[{account_key}] Music processing failed (using original): {e}")
            processed_music = music_path
    
    return processed_voice, processed_music


def _apply_ducking(music, voice_path: str, spec: dict, account_key: str):
    """
    Lower music volume when voiceover is active.
    Uses chunk-based analysis to detect voice activity.
    """
    try:
        from pydub import AudioSegment
        import math
        
        voice = AudioSegment.from_file(voice_path)
        
        # Calculate duck amount in dB
        duck_ratio = spec["music_ducked"] / max(spec["music_normal"], 0.01)
        duck_db = 20 * math.log10(max(duck_ratio, 0.01))
        
        chunk_ms = 100  # Analyze in 100ms chunks
        threshold = spec["duck_threshold"]  # Voice activity threshold in dBFS
        
        # Create ducked version
        ducked_music = AudioSegment.empty()
        
        for i in range(0, len(music), chunk_ms):
            music_chunk = music[i:i + chunk_ms]
            
            # Check if voice is active in this chunk
            if i < len(voice):
                voice_chunk = voice[i:i + chunk_ms]
                voice_active = voice_chunk.dBFS > threshold
            else:
                voice_active = False
            
            if voice_active:
                # Duck the music
                ducked_music += music_chunk.apply_gain(duck_db)
            else:
                ducked_music += music_chunk
        
        print(f"[{account_key}] Ducking applied ({duck_db:.1f}dB when voice active)")
        return ducked_music
        
    except Exception as e:
        print(f"[{account_key}] Ducking failed (using original music): {e}")
        return music
