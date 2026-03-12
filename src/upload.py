import os
import sys
import json
import smtplib
import http.client
import httplib2
import random
import time
from email.message import EmailMessage
from typing import Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import ACCOUNTS, YT_OAUTH_CREDENTIALS

# YouTube API settings
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
           "https://www.googleapis.com/auth/youtube"]

# YouTube category IDs
CATEGORY_MAP = {
    "Pets & Animals": "15",
    "Education": "27",
    "Entertainment": "24",
    "Science & Technology": "28",
    "People & Blogs": "22",
    "Film & Animation": "1",
    "Comedy": "23",
}

TOKEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tokens")

# Retry settings for resumable upload
MAX_UPLOAD_RETRIES = 5
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class Uploader:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.fb_target_email = os.environ.get("FB_ADMIN_EMAIL", "")

    def _get_youtube_service(self, account_key: str):
        """
        Loads OAuth2 token for the given account and returns a YouTube API service.
        Token is auto-refreshed if expired.
        """
        token_file = os.path.join(TOKEN_DIR, f"{account_key}_token.json")
        
        if not os.path.exists(token_file):
            print(f"[{account_key}] Token file not found: {token_file}")
            print(f"[{account_key}] Run: python yt_authorize.py --account {account_key}")
            return None
        
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            print(f"[{account_key}] Refreshing expired token...")
            try:
                creds.refresh(Request())
                with open(token_file, "w") as f:
                    f.write(creds.to_json())
                print(f"[{account_key}] Token refreshed.")
            except Exception as e:
                print(f"[{account_key}] Token refresh failed: {e}")
                return None
        
        if not creds.valid:
            print(f"[{account_key}] Token invalid. Re-run: python yt_authorize.py --account {account_key}")
            return None
        
        return build("youtube", "v3", credentials=creds)

    def _resumable_upload(self, service, body: dict, media: MediaFileUpload, account_key: str) -> Optional[str]:
        """
        Performs a resumable upload to YouTube with retry logic.
        Returns the video ID on success, None on failure.
        """
        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        retry = 0
        
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"[{account_key}] Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry += 1
                    if retry > MAX_UPLOAD_RETRIES:
                        print(f"[{account_key}] Upload failed after {MAX_UPLOAD_RETRIES} retries.")
                        return None
                    wait = random.random() * (2 ** retry)
                    print(f"[{account_key}] Retriable error {e.resp.status}. Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    print(f"[{account_key}] Upload error: {e}")
                    return None
            except (httplib2.HttpLib2Error, http.client.HTTPException, IOError) as e:
                retry += 1
                if retry > MAX_UPLOAD_RETRIES:
                    return None
                wait = random.random() * (2 ** retry)
                print(f"[{account_key}] Network error. Retrying in {wait:.1f}s...")
                time.sleep(wait)
        
        if response:
            video_id = response.get("id", "")
            print(f"[{account_key}] Upload complete! Video ID: {video_id}")
            print(f"[{account_key}] URL: https://youtube.com/watch?v={video_id}")
            return video_id
        return None

    def upload_to_youtube(self, account_key: str, video_path: str, thumbnail_path: str,
                          metadata: Dict[str, Any], is_short: bool = False) -> Optional[str]:
        """
        Uploads a video to YouTube using the Data API v3 with resumable upload.
        Returns video_id on success, None on failure.
        """
        print(f"[{account_key}] {'Shorts' if is_short else 'Video'} upload starting...")
        
        service = self._get_youtube_service(account_key)
        if not service:
            print(f"[{account_key}] Cannot upload - no valid YouTube service.")
            return None
        
        # Map category name to ID
        category = metadata.get("category", "Pets & Animals")
        category_id = CATEGORY_MAP.get(category, "15")
        
        # Build request body
        tags = metadata.get("tags", [])
        if is_short:
            tags = tags + ["#shorts", "#tarsier"]
        
        body = {
            "snippet": {
                "title": metadata.get("title", "Tarsier Facts"),
                "description": metadata.get("description", ""),
                "tags": tags,
                "categoryId": category_id,
                "defaultLanguage": metadata.get("language", "en"),
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        }
        
        # Check video file exists
        if not os.path.exists(video_path):
            print(f"[{account_key}] Video file not found: {video_path}")
            return None
        
        # Create media upload object (resumable)
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 10  # 10MB chunks
        )
        
        video_id = self._resumable_upload(service, body, media, account_key)
        
        if not video_id:
            return None
        
        # Upload thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/png")
                ).execute()
                print(f"[{account_key}] Thumbnail uploaded.")
            except Exception as e:
                print(f"[{account_key}] Thumbnail upload failed (non-critical): {e}")
        
        return video_id

    def send_to_facebook_admin(self, video_path: str, thumbnail_path: str,
                                metadata: Dict[str, Any]) -> bool:
        """
        Packages video + metadata and sends via email for manual Facebook upload.
        Bagian 4 Step 12: FB dikemas rapi kirim ke email.
        """
        print(f"[fb_fanspage] Preparing email to Facebook Admin...")
        
        if not all([self.smtp_user, self.smtp_pass, self.fb_target_email]):
            print("[fb_fanspage] SMTP credentials missing. Cannot send email.")
            return False

        msg = EmailMessage()
        msg['Subject'] = f"[TARSIER] Video Siap Upload: {metadata.get('title', 'New Video')}"
        msg['From'] = self.smtp_user
        msg['To'] = self.fb_target_email
        
        hashtags = " ".join(metadata.get("hashtags", []))
        body = f"""Video Tarsier baru siap upload ke Facebook Fanspage!

JUDUL: {metadata.get('title', '')}

CAPTION:
{metadata.get('description', '')}

HASHTAG: {hashtags}

TAGS: {', '.join(metadata.get('tags', []))}

File video dan thumbnail terlampir di email ini.
Silakan upload manual ke Facebook Fanspage.
"""
        msg.set_content(body)
        
        # Attach video file if exists and not too large
        if video_path and os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            if file_size < 25 * 1024 * 1024:  # < 25MB (Gmail limit)
                with open(video_path, "rb") as f:
                    msg.add_attachment(f.read(), maintype="video", subtype="mp4",
                                       filename=os.path.basename(video_path))
                print(f"[fb_fanspage] Video attached ({file_size // 1024}KB)")
            else:
                print(f"[fb_fanspage] Video too large for email ({file_size // 1024 // 1024}MB). Path included in body.")
        
        # Attach thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="png",
                                   filename=os.path.basename(thumbnail_path))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            print("[fb_fanspage] Email sent successfully!")
            return True
        except Exception as e:
            print(f"[fb_fanspage] Failed to send email: {e}")
            return False

    def publish(self, account_key: str, video_path: str, short_path: str,
                thumbnail_path: str, metadata: Dict[str, Any]) -> dict:
        """
        Routes publishing: YouTube accounts -> API upload, FB -> email.
        Bagian 4 Step 12.
        Returns dict with upload results including video URLs.
        """
        result = {"success": False, "video_id": None, "short_id": None, "video_url": None, "short_url": None}
        
        if account_key == "fb_fanspage":
            result["success"] = self.send_to_facebook_admin(video_path, thumbnail_path, metadata)
            return result
        
        # Upload long video
        video_id = self.upload_to_youtube(
            account_key, video_path, thumbnail_path, metadata, is_short=False
        )
        result["video_id"] = video_id
        result["video_url"] = f"https://youtube.com/watch?v={video_id}" if video_id else None
        
        # Upload shorts if exists
        if short_path and os.path.exists(str(short_path)):
            short_meta = metadata.copy()
            short_meta['title'] = short_meta['title'] + " #shorts"
            short_id = self.upload_to_youtube(
                account_key, short_path, thumbnail_path, short_meta, is_short=True
            )
            result["short_id"] = short_id
            result["short_url"] = f"https://youtube.com/watch?v={short_id}" if short_id else None
        
        result["success"] = video_id is not None
        return result


if __name__ == "__main__":
    pass
