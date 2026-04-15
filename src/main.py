import os
import sys

# Fix Windows console encoding for Unicode characters (arrows, emojis, etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import time
import random
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import ACCOUNTS, MAX_RETRIES, TMP_DIR, TOPICS_FILE, CLIP_DURATION_SEC, VIDEO_PROFILES
from src.visual_engine import style_batch_for_channel
from src.database import DatabaseManager

# PREVIEW_MODE: skip YouTube upload, save videos to output/ for review
PREVIEW_MODE = os.environ.get("PREVIEW_MODE", "false").lower() == "true"
from src.research import ResearchEngine
from src.script_engine import ScriptEngine
from src.media_gen import MediaGenerator
from src.assemble import VideoAssembler
from src.shorts_extractor import ShortsExtractor
from src.qc import QualityControl
from src.thumbnail import ThumbnailGenerator
from src.metadata import MetadataGenerator
from src.upload import Uploader

class Pipeline:
    def __init__(self, test_mode: bool = False, target: str = None):
        self.test_mode = test_mode
        self.target = target  # Optional: run only for a specific account (e.g., "fb_fanspage")
        self.db = DatabaseManager(TOPICS_FILE)
        self.researcher = ResearchEngine()
        self.script_engine = ScriptEngine()
        self.media_gen = MediaGenerator()
        self.assembler = VideoAssembler()
        self.shorts_extractor = ShortsExtractor()
        self.qc = QualityControl()
        self.thumbnail_gen = ThumbnailGenerator()
        self.metadata_gen = MetadataGenerator()
        self.uploader = Uploader()
        
        # Bagian 15 - Log System: Semua aktivitas pipeline tercatat di JSON log
        self.log_file = os.path.join(os.path.dirname(TOPICS_FILE), "pipeline_log.json")
        self.activity_log = []
        # Track upload results for summary email
        self.upload_results = []

    def _log(self, level: str, account: str, message: str):
        """Logs an activity entry to JSON (Bagian 15 - Log System)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "account": account,
            "message": message
        }
        self.activity_log.append(entry)
        print(f"[{level}] [{account}] {message}")

    def _save_log(self):
        """Saves the activity log to JSON file (Bagian 15 - Log System)."""
        try:
            existing = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    existing = []  # Auto-reset corrupted log
            existing.extend(self.activity_log)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving log: {e}")

    def _send_failure_email(self, account_key: str, error_msg: str):
        """
        Bagian 15 - Error Handling:
        Notifikasi email otomatis kalau ada kegagalan kritis
        """
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        admin_email = os.environ.get("FB_ADMIN_EMAIL", "")
        
        if not all([smtp_user, smtp_pass, admin_email]):
            print("SMTP credentials missing. Cannot send failure notification email.")
            return
            
        msg = EmailMessage()
        msg['Subject'] = f"⚠️ TARSIER PIPELINE CRITICAL FAILURE - {account_key}"
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg.set_content(
            f"Critical Failure in Tarsier Pipeline\n\n"
            f"Account: {account_key}\n"
            f"Time: {datetime.now().isoformat()}\n"
            f"Error: {error_msg}\n\n"
            f"The pipeline has exhausted all {MAX_RETRIES} retry attempts.\n"
            f"Please review the pipeline logs and take manual action."
        )
        
        try:
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"Failure notification sent for {account_key}.")
        except Exception as e:
            print(f"Failed to send failure notification: {e}")

    def cleanup(self):
        """
        Bagian 4 Step 13: Cleanup → hapus file video setelah upload/kirim.
        """
        self._log("INFO", "SYSTEM", "Cleaning up temporary files...")
        if not self.test_mode:
            for filename in os.listdir(TMP_DIR):
                file_path = os.path.join(TMP_DIR, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    self._log("WARN", "SYSTEM", f"Error deleting {file_path}: {e}")

    def _split_script_to_segments(self, script: str) -> list:
        """
        Splits a narration script into segments for individual clip generation.
        Each sentence/phrase becomes a prompt for one scene.
        """
        import re
        sentences = re.split(r'(?<=[.!?])\s+', script.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _download_shared_images(self, topic_name: str, num_images: int = 6) -> list:
        """Download shared image batch — 1 image per channel distributed.
        Returns list of VALIDATED raw image paths to be styled per-channel."""
        self._log("INFO", "BATCH", f"Downloading {num_images} shared images for topic: {topic_name}")
        
        raw_images = []
        
        # Step 1: Try stock photos first (Pexels/Pixabay/Wikimedia)
        stock_photos = self.media_gen.download_tarsier_photos("shared_batch", num_photos=num_images + 5)
        for photo in stock_photos:
            if len(raw_images) >= num_images:
                break
            # Validate each stock photo is a real image
            if self.media_gen._validate_image_file(photo):
                raw_images.append(photo)
            else:
                self._log("WARN", "BATCH", f"Stock photo invalid, skipping: {photo}")
        
        stock_count = len(raw_images)
        self._log("INFO", "BATCH", f"Stock photos (validated): {stock_count}/{num_images}")
        
        # Step 2: Fill remaining with AI-generated images (CF → HF)
        remaining = num_images - len(raw_images)
        if remaining > 0:
            self._log("INFO", "BATCH", f"Generating {remaining} AI images to fill batch...")
            # Distribute AI generation across channel accounts for key isolation
            channels_for_ai = list(ACCOUNTS.keys())
            for i in range(remaining):
                ai_channel = channels_for_ai[i % len(channels_for_ai)]
                ai_img = self.media_gen.generate_tarsier_image(ai_channel, i, topic_name, force_tarsier=True)
                if ai_img:  # generate_tarsier_image now validates internally
                    raw_images.append(ai_img)
                else:
                    self._log("WARN", "BATCH", f"AI image {i} failed for {ai_channel}")
                time.sleep(1)
        
        self._log("INFO", "BATCH", f"Shared batch: {len(raw_images)} images (stock:{stock_count} AI:{len(raw_images)-stock_count})")
        return raw_images

    def process_account(self, account_key: str, topic_info: dict, 
                        shared_images: list = None) -> bool:
        """Runs the full pipeline for a single account.
        V2: Accepts shared_images from batch pool, applies channel-specific style."""
        topic_name = topic_info['topic_name']
        
        # Anti Duplikasi
        if self.db.is_topic_completed(topic_name, account_key):
            self._log("INFO", account_key, f"Topic '{topic_name}' already completed. Skipping.")
            return True
            
        self.db.add_topic_record(topic_name, account_key, "dalam_proses")
        self._log("INFO", account_key, f"Processing topic: {topic_name}")

        try:
            # 2. Script Generate → Gemini API transform 1 script jadi 5+ style per akun (Bagian 4 Step 2)
            script, template_id = self.script_engine.generate_script(topic_info['raw_facts'], account_key)
            if not script:
                raise ValueError("Script generation failed.")
            
            # DEDUP CHECK: Reject scripts that have EVER been used before (any channel)
            if template_id:
                # Fallback script: dedup by stable template_id (not text hash)
                # because topic injection changes the hash every time
                if self.db.is_script_duplicate(template_id):
                    # ENFORCE: Do NOT use this duplicate — generate a unique MASHUP instead
                    self._log("WARN", account_key, f"Fallback template {template_id} already used! Generating unique MASHUP...")
                    script, template_id = self.script_engine.generate_script(
                        topic_info['raw_facts'], account_key, force_mashup=True
                    )
                    if not script:
                        raise ValueError("Mashup script generation failed.")
                # Record the template_id so it can never be reused by any channel
                self.db.record_script_hash(template_id, account_key, topic_name)
            else:
                # Gemini script: dedup by content hash (text is unique each time)
                for dedup_attempt in range(3):
                    if not self.db.is_script_duplicate(script):
                        break
                    self._log("WARN", account_key, f"Script duplicate detected! Regenerating (attempt {dedup_attempt+2})...")
                    # Add variation hint to force different output
                    variation = f"\n\nIMPORTANT: Generate a COMPLETELY DIFFERENT script. Variation #{dedup_attempt+2}."
                    script, template_id = self.script_engine.generate_script(topic_info['raw_facts'] + variation, account_key)
                    if not script:
                        raise ValueError("Script regeneration failed.")
                    if template_id:
                        # Fell back to template — check THAT for duplicates too
                        if self.db.is_script_duplicate(template_id):
                            script, template_id = self.script_engine.generate_script(
                                topic_info['raw_facts'], account_key, force_mashup=True
                            )
                        break
                
                # Record script hash so it can never be reused by any channel
                self.db.record_script_hash(script if not template_id else template_id, account_key, topic_name)
            
            self._log("INFO", account_key, "Script generated successfully.")

            # RATE LIMIT PROTECTION: 5s cooldown between Gemini calls
            time.sleep(5)

            # 11. Metadata Generator → Gemini API auto-generate judul, deskripsi, hashtag, tags (Bagian 4 Step 11)
            metadata = self.metadata_gen.generate(script, account_key)
            self._log("INFO", account_key, f"Metadata generated: {metadata.get('title', 'N/A')}")

            if self.test_mode:
                self._log("INFO", account_key, "TEST MODE: Skipping media generation.")
                thumb = self.thumbnail_gen.generate(account_key, metadata.get('title', 'Tarsier Facts'), topic_name)
                self.db.mark_completed(topic_name, account_key)
                return True

            # 4. Generate Visual Media — V2: SHARED BATCH + PER-CHANNEL STYLING
            script_segments = self._split_script_to_segments(script)
            
            if shared_images:
                # V2 BATCH MODE: Apply channel-specific visual style to shared images
                self._log("INFO", account_key, f"Styling {len(shared_images)} shared images for {account_key}...")
                styled_dir = os.path.join(TMP_DIR, f"{account_key}_styled")
                styled_scenes = style_batch_for_channel(shared_images, account_key, styled_dir)
                media_items = [("image", scene) for scene in styled_scenes]
                self._log("INFO", account_key, f"Styled scenes: {len(media_items)}")
            else:
                # FALLBACK: Old per-channel image sourcing
                media_items = self.media_gen.generate_all_clips(script_segments, account_key, topic_name)
            
            # 5. Generate Narasi Suara — V2: VO with PAUSES (not continuous)
            profile = VIDEO_PROFILES.get(account_key, {})
            audio_path = None
            if profile.get("has_voiceover", True):
                audio_path = self.media_gen.generate_voiceover(script, account_key, topic_name)
            else:
                self._log("INFO", account_key, "SKIP voiceover (has_voiceover=False)")
            
            # 6. Generate Musik + SFX (non-fatal: video works without it)
            music_path = self.media_gen.generate_music(account_key, topic_name)

            if not media_items:
                raise ValueError("No visual media generated.")

            # 7. Assemble → video clips + images + narasi + musik + TEXT OVERLAY
            final_video = self.assembler.assemble_final_video(
                account_key, topic_name, media_items, audio_path, music_path,
                script_segments=script_segments
            )
            if not final_video:
                raise ValueError("Video assembly failed.")
            self._log("INFO", account_key, "Video assembled successfully.")

            # 8. QC Check → scoring system per bagian, minimal skor 80/100 (Bagian 4 Step 8, Bagian 5)
            # Duration target based on channel profile clip count
            cut_dur = profile.get("cut_duration", 6)
            if isinstance(cut_dur, (tuple, list)):
                cut_dur = sum(cut_dur) / len(cut_dur)  # average of range
            target_duration = len(script_segments) * int(cut_dur)
            if not self.qc.evaluate(final_video, metadata, target_duration, account_key):
                raise ValueError("Quality Control failed. Score below 80/100.")

            # 9. Extract Shorts → auto-detect hook terbaik (Bagian 4 Step 9)
            short_video = self.shorts_extractor.extract_hook(final_video, account_key, topic_name)
            self._log("INFO", account_key, "Shorts extracted.")

            # 10. Thumbnail → auto-generate sesuai template branding per akun (Bagian 4 Step 10)
            thumbnail_img = self.thumbnail_gen.generate(account_key, metadata.get('title', 'Title'), topic_name)
            self._log("INFO", account_key, "Thumbnail generated.")

            # 12. Upload/Kirim -> YT via API otomatis, FB dikemas rapi kirim ke email (Bagian 4 Step 12)
            if PREVIEW_MODE:
                # PREVIEW MODE: skip upload, copy files to output/ for artifact download
                import shutil
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", account_key)
                os.makedirs(output_dir, exist_ok=True)
                
                # Copy video
                if final_video and os.path.exists(final_video):
                    shutil.copy2(final_video, os.path.join(output_dir, f"{topic_name}_video.mp4"))
                # Copy short
                if short_video and os.path.exists(short_video):
                    shutil.copy2(short_video, os.path.join(output_dir, f"{topic_name}_short.mp4"))
                # Copy thumbnail
                if thumbnail_img and os.path.exists(thumbnail_img):
                    shutil.copy2(thumbnail_img, os.path.join(output_dir, f"{topic_name}_thumb.png"))
                # Save metadata JSON
                with open(os.path.join(output_dir, f"{topic_name}_metadata.json"), 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                # Save script
                with open(os.path.join(output_dir, f"{topic_name}_script.txt"), 'w', encoding='utf-8') as f:
                    f.write(script)
                
                self._log("INFO", account_key, f"PREVIEW MODE: Files saved to output/{account_key}/")
                self.db.mark_completed(topic_name, account_key)
                self.upload_results.append({
                    "account": account_key,
                    "channel": ACCOUNTS[account_key]["name"],
                    "title": metadata.get("title", "N/A"),
                    "topic": topic_name,
                    "video_url": f"output/{account_key}/{topic_name}_video.mp4",
                    "short_url": f"output/{account_key}/{topic_name}_short.mp4",
                    "status": "PREVIEW (not uploaded)",
                    "platform": ACCOUNTS[account_key]["platform"],
                })
                return True
            
            upload_result = self.uploader.publish(account_key, final_video, short_video, thumbnail_img, metadata)
            
            if upload_result["success"]:
                self.db.mark_completed(topic_name, account_key)
                # Save video IDs for monitoring system
                vid = upload_result.get("video_id", "")
                sid = upload_result.get("short_id", "")
                if vid:
                    self.db.save_video_id(account_key, topic_name, vid, sid or "")
                self._log("INFO", account_key, "Upload successful!")
                # Track for summary email
                self.upload_results.append({
                    "account": account_key,
                    "channel": ACCOUNTS[account_key]["name"],
                    "title": metadata.get("title", "N/A"),
                    "topic": topic_name,
                    "video_url": upload_result.get("video_url"),
                    "short_url": upload_result.get("short_url"),
                    "status": "SUCCESS",
                    "platform": ACCOUNTS[account_key]["platform"],
                })
                return True
            else:
                # Bagian 15 - Backup Plan: API YT error -> video tersimpan di queue, retry berikutnya
                raise ValueError("Upload failed. Video queued for next retry.")

        except Exception as e:
            self._log("ERROR", account_key, f"Pipeline Error: {e}")
            self.db.mark_failed(topic_name, account_key)
            self.upload_results.append({
                "account": account_key,
                "channel": ACCOUNTS[account_key]["name"],
                "title": "N/A",
                "topic": topic_name,
                "video_url": None,
                "short_url": None,
                "status": f"FAILED: {e}",
                "platform": ACCOUNTS[account_key]["platform"],
            })
            return False

    def run(self):
        """
        V2 BATCH PIPELINE:
        1 topic → 6 shared images → 6 visually distinct videos (1 per channel)
        Each channel applies its own visual style, VO tone, and audio mood.
        Same ingredients → different flavors (analogi: 1 mie → 6 rasa beda)
        """
        self._log("INFO", "SYSTEM", "Starting Tarsier Pipeline V2 (Batch Mode)...")
        
        # Determine which accounts to process
        accounts_to_process = list(ACCOUNTS.keys())
        if self.target:
            if self.target in ACCOUNTS:
                accounts_to_process = [self.target]
            else:
                self._log("ERROR", "SYSTEM", f"Target account '{self.target}' not found!")
                return
        
        MAX_TOPIC_RETRIES = 20
        all_success = True
        
        # ==========================================
        # STEP 1: Pick 1 topic for entire batch
        # ==========================================
        topic_info = None
        for topic_attempt in range(MAX_TOPIC_RETRIES):
            candidate = self.researcher.generate_random_topic()
            topic_name = candidate['topic_name']
            # Check that at least 1 channel hasn't completed this topic
            any_available = any(
                not self.db.is_topic_completed(topic_name, acc)
                for acc in accounts_to_process
            )
            if any_available:
                topic_info = candidate
                self._log("INFO", "BATCH", f"Selected batch topic: {topic_name}")
                break
        
        if topic_info is None:
            self._log("ERROR", "BATCH", f"No available topic found after {MAX_TOPIC_RETRIES} attempts!")
            self._save_log()
            return
        
        batch_topic = topic_info['topic_name']
        
        # ==========================================
        # STEP 2: Download shared image pool (6 images)
        # ==========================================
        num_images = len(accounts_to_process)
        shared_images = self._download_shared_images(batch_topic, num_images=num_images)
        
        if not shared_images:
            self._log("ERROR", "BATCH", "Failed to download any shared images!")
            self._save_log()
            return
        
        self._log("INFO", "BATCH", f"Shared pool: {len(shared_images)} images for {len(accounts_to_process)} channels")
        
        # ==========================================
        # STEP 3: Process each channel with shared images
        # Each channel gets the SAME images but styles them differently
        # ==========================================
        
        # ANTI-BOT: Shuffle channel processing order
        random.shuffle(accounts_to_process)
        self._log("INFO", "BATCH", f"Channel order (shuffled): {' → '.join(accounts_to_process)}")
        
        channel_count = 0
        for account_key in accounts_to_process:
            # ANTI-BOT: Random delay between channels (2-8 minutes)
            if channel_count > 0:
                delay_sec = random.randint(120, 480)
                self._log("INFO", "SYSTEM", f"Anti-bot delay: {delay_sec}s (~{delay_sec//60}min) before {account_key}...")
                time.sleep(delay_sec)
            channel_count += 1
            
            # Skip if this channel already completed this topic
            if self.db.is_topic_completed(batch_topic, account_key):
                self._log("INFO", account_key, f"Topic '{batch_topic}' already completed. Skipping.")
                continue
            
            # Process with shared images — each channel applies its own visual style
            success = False
            for attempt in range(MAX_RETRIES):
                if attempt > 0:
                    self._log("WARN", account_key, f"Retry {attempt+1}/{MAX_RETRIES}...")
                    time.sleep(5)
                
                if self.process_account(account_key, topic_info, shared_images=shared_images):
                    success = True
                    break
            
            if not success:
                all_success = False
                self._log("ERROR", account_key, f"Failed after {MAX_RETRIES} attempts.")
                self._send_failure_email(account_key, f"Pipeline failed for {account_key} after {MAX_RETRIES} retries.")

        # Cleanup
        if all_success:
            self.cleanup()
        else:
            self._log("WARN", "SYSTEM", "Pipeline finished with errors. Skipping cleanup for debugging.")
        
        self._save_log()
        self._send_summary_email(batch_topic)

    def _send_summary_email(self, topic_name: str):
        """
        Sends a comprehensive pipeline summary email with all upload results.
        Includes video URLs for easy checking.
        """
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        admin_email = os.environ.get("FB_ADMIN_EMAIL", "")
        
        if not all([smtp_user, smtp_pass, admin_email]):
            print("SMTP credentials missing. Cannot send summary email.")
            return
        
        # Count results
        total = len(self.upload_results)
        success = sum(1 for r in self.upload_results if r["status"] == "SUCCESS")
        failed = total - success
        
        # Build email body
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_icon = "ALL SUCCESS" if failed == 0 else f"{failed} FAILED"
        
        body = f"""TARSIER PIPELINE REPORT
{'='*50}
Waktu    : {now}
Topik    : {topic_name}
Hasil    : {success}/{total} berhasil | {status_icon}
{'='*50}

DETAIL PER AKUN:
"""
        for r in self.upload_results:
            body += f"\n--- {r['channel']} ({r['account']}) ---\n"
            body += f"  Platform : {r['platform']}\n"
            body += f"  Status   : {r['status']}\n"
            body += f"  Judul    : {r['title']}\n"
            
            if r.get("video_url"):
                body += f"  Video    : {r['video_url']}\n"
            if r.get("short_url"):
                body += f"  Shorts   : {r['short_url']}\n"
        
        body += f"\n{'='*50}\n"
        body += f"Total upload berhasil: {success}/{total}\n"
        if failed > 0:
            body += f"\nPerlu dicek manual: {failed} akun gagal. Cek GitHub Actions log.\n"
        body += f"\n--- Tarsier Bot ---\n"
        
        # Build email
        msg = EmailMessage()
        if failed == 0:
            msg['Subject'] = f"[TARSIER] Pipeline OK - {success}/{total} uploaded - {topic_name}"
        else:
            msg['Subject'] = f"[TARSIER] Pipeline WARNING - {failed}/{total} FAILED - {topic_name}"
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg.set_content(body)
        
        try:
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            self._log("INFO", "SYSTEM", f"Summary email sent: {success}/{total} success.")
        except Exception as e:
            self._log("ERROR", "SYSTEM", f"Failed to send summary email: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tarsier Content Pipeline")
    parser.add_argument("--test-mode", action="store_true", help="Run without generating heavy media (video/audio)")
    parser.add_argument("--target", type=str, default=None, help="Target specific account (e.g., fb_fanspage)")
    args = parser.parse_args()
    
    pipeline = Pipeline(test_mode=args.test_mode, target=args.target)
    pipeline.run()
