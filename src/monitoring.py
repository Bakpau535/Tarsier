"""
Performance Monitoring & Auto-Repair System (Bagian 9)
Uses REAL YouTube Data API to get video metrics and auto-fix underperforming videos.

Schedule: Daily at 14:00 WIB
- Day 3: Initial check
- Day 7: Main evaluation + auto-fix
- Day 30: Monthly review

Actions:
- LOW_CTR → regenerate thumbnail + update title
- LOW_ENGAGEMENT → refresh tags/hashtags
- LOW_RETENTION → update description with stronger hook
"""

import os
import sys
import json
import smtplib
import time
from email.message import EmailMessage
from datetime import datetime, timedelta
from collections import Counter

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (ACCOUNTS, TOPICS_FILE, GEMINI_MONITORING_KEY, 
                         GROQ_MONITORING_KEY)
from src.database import DatabaseManager
from src.metadata import MetadataGenerator
from src.thumbnail import ThumbnailGenerator

SCOPES = ["https://www.googleapis.com/auth/youtube"]
TOKEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tokens")


class PerformanceMonitor:
    def __init__(self):
        self.db = DatabaseManager(TOPICS_FILE)
        # Lazy init — only created when auto-fix needs them (avoids crash if no Gemini keys)
        self._metadata_gen = None
        self._thumbnail_gen = None
        
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587").strip())
        self.smtp_user = os.environ.get("SMTP_USER", "").strip()
        self.smtp_pass = os.environ.get("SMTP_PASS", "").strip()
        self.admin_email = os.environ.get("FB_ADMIN_EMAIL", "admin@example.com").strip()

    # =========================================================================
    # YouTube API Service
    # =========================================================================

    def _get_youtube_service(self, account_key: str):
        """Load OAuth2 token and return YouTube API service for this channel."""
        token_file = os.path.join(TOKEN_DIR, f"{account_key}_token.json")
        
        if not os.path.exists(token_file):
            print(f"[{account_key}] Token file not found: {token_file}")
            return None
        
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            print(f"[{account_key}] Token file invalid: {e}")
            return None
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "w") as f:
                    f.write(creds.to_json())
                print(f"[{account_key}] Token refreshed.")
            except Exception as e:
                print(f"[{account_key}] Token refresh failed: {e}")
                return None
        
        if not creds.valid:
            print(f"[{account_key}] Token invalid.")
            return None
        
        return build("youtube", "v3", credentials=creds)

    # =========================================================================
    # Bagian 9 - Real Video Metrics
    # =========================================================================

    def get_video_metrics(self, service, video_id: str) -> dict:
        """Get REAL video statistics from YouTube Data API."""
        try:
            response = service.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()
            
            if not response.get("items"):
                print(f"  Video {video_id} not found on YouTube")
                return {}
            
            item = response["items"][0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            # Calculate engagement rate
            engagement = ((likes + comments) / views * 100) if views > 0 else 0
            
            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": round(engagement, 2),
                "published_at": snippet.get("publishedAt", ""),
            }
        except HttpError as e:
            print(f"  YouTube API error for {video_id}: {e}")
            return {}
        except Exception as e:
            print(f"  Error getting metrics for {video_id}: {e}")
            return {}

    # =========================================================================
    # Bagian 9 - Threshold Performa
    # =========================================================================
    # | Metrik          | Bagus    | Normal   | Perlu Perbaikan |
    # | Views (7 days)  | >100     | 20-100   | <20             |
    # | Engagement      | >4%      | 2-4%     | <2%             |
    # | Like Ratio      | >4%      | 2-4%     | <2%             |

    def evaluate_video(self, metrics: dict, days_since_upload: int) -> list:
        """Evaluate video performance against thresholds."""
        issues = []
        
        if not metrics:
            return ["NO_DATA"]
        
        views = metrics.get("views", 0)
        engagement = metrics.get("engagement_rate", 0)
        likes = metrics.get("likes", 0)
        
        # Scale expected views by age
        if days_since_upload <= 3:
            min_views = 5
        elif days_since_upload <= 7:
            min_views = 20
        else:
            min_views = 50
        
        if views < min_views:
            issues.append("LOW_VIEWS")
        
        if views > 10 and engagement < 2.0:
            issues.append("LOW_ENGAGEMENT")
        
        # Like ratio check (only meaningful with enough views)
        if views > 20:
            like_ratio = (likes / views * 100) if views > 0 else 0
            if like_ratio < 2.0:
                issues.append("LOW_LIKE_RATIO")
        
        return issues

    # =========================================================================
    # Bagian 9 - Auto-Repair Actions (REAL YouTube API Updates)
    # =========================================================================

    def take_action(self, service, account_key: str, video_id: str,
                    issues: list, metrics: dict, topic: str) -> dict:
        """Takes REAL optimization actions via YouTube API."""
        actions_taken = []
        
        print(f"[{account_key}] Issues for {video_id}: {issues}")
        
        # LOW_VIEWS / LOW_ENGAGEMENT → Update title + description for better discoverability
        if "LOW_VIEWS" in issues or "LOW_ENGAGEMENT" in issues:
            try:
                # Get current video data
                response = service.videos().list(
                    part="snippet", id=video_id
                ).execute()
                
                if response.get("items"):
                    snippet = response["items"][0]["snippet"]
                    old_title = snippet.get("title", "")
                    
                    # Generate fresh metadata via Gemini primary + Groq secondary
                    if not self._metadata_gen:
                        try:
                            mon_keys = [k for k in [GEMINI_MONITORING_KEY] if k]
                            self._metadata_gen = MetadataGenerator(
                                dedicated_keys=mon_keys,
                                groq_key_override=GROQ_MONITORING_KEY
                            )
                        except Exception:
                            self._metadata_gen = None
                            actions_taken.append("Monitoring API keys unavailable")
                    
                    if self._metadata_gen:
                        fresh_meta = self._metadata_gen.generate(
                            f"Topic: {topic}. Original title: {old_title}. "
                            f"This video needs better SEO — it only has {metrics.get('views', 0)} views.",
                            account_key
                        )
                    else:
                        fresh_meta = None
                    
                    if fresh_meta and fresh_meta.get("title"):
                        new_title = fresh_meta["title"]
                        new_desc = fresh_meta.get("description", snippet.get("description", ""))
                        new_tags = fresh_meta.get("tags", snippet.get("tags", []))
                        
                        # Update video metadata on YouTube
                        snippet["title"] = new_title
                        snippet["description"] = new_desc
                        snippet["tags"] = new_tags if isinstance(new_tags, list) else snippet.get("tags", [])
                        
                        service.videos().update(
                            part="snippet",
                            body={
                                "id": video_id,
                                "snippet": snippet
                            }
                        ).execute()
                        
                        actions_taken.append(f"Updated title: '{old_title}' → '{new_title}'")
                        print(f"[{account_key}] Title updated: {new_title}")
                        time.sleep(5)  # Rate limit protection
                    else:
                        actions_taken.append("Gemini unavailable — skipped title update")
                        
            except HttpError as e:
                print(f"[{account_key}] YouTube update error: {e}")
                actions_taken.append(f"Update failed: {e}")
            except Exception as e:
                print(f"[{account_key}] Update error: {e}")
                actions_taken.append(f"Update failed: {e}")
        
        # LOW_LIKE_RATIO → Regenerate and upload new thumbnail
        if "LOW_LIKE_RATIO" in issues:
            try:
                if not self._thumbnail_gen:
                    try:
                        self._thumbnail_gen = ThumbnailGenerator()
                    except Exception:
                        self._thumbnail_gen = None
                        actions_taken.append("ThumbnailGen unavailable")
                
                if self._thumbnail_gen:
                    thumb_path = self._thumbnail_gen.generate(
                        account_key,
                        metrics.get("title", topic),
                        topic
                    )
                else:
                    thumb_path = None
                if thumb_path and os.path.exists(thumb_path):
                    service.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumb_path, mimetype="image/png")
                    ).execute()
                    actions_taken.append("Uploaded new thumbnail")
                    print(f"[{account_key}] New thumbnail uploaded for {video_id}")
                    time.sleep(5)
            except HttpError as e:
                # Custom thumbnails require channel verification
                print(f"[{account_key}] Thumbnail upload failed (channel may need verification): {e}")
                actions_taken.append(f"Thumbnail failed: {e}")
            except Exception as e:
                print(f"[{account_key}] Thumbnail error: {e}")
        
        flagged = len(issues) >= 3
        if flagged:
            print(f"[{account_key}] *** FLAGGED FOR MANUAL REVIEW ***")
        
        return {
            "topic": topic,
            "video_id": video_id,
            "account": account_key,
            "metrics": metrics,
            "issues": issues,
            "actions": actions_taken,
            "flagged_for_manual_review": flagged
        }

    # =========================================================================
    # Bagian 9 - Evaluation Schedule
    # =========================================================================

    def _days_since(self, date_str: str) -> int:
        """Calculate days since a date string."""
        try:
            post_date = datetime.strptime(date_str, "%Y-%m-%d")
            return (datetime.now() - post_date).days
        except (ValueError, TypeError):
            return -1

    def _should_evaluate(self, date_str: str) -> str:
        """Determine evaluation type: day3, day7, day30, or empty."""
        days = self._days_since(date_str)
        if 3 <= days <= 4:
            return "day3"
        elif 7 <= days <= 8:
            return "day7"
        elif 30 <= days <= 31:
            return "day30"
        return ""

    # =========================================================================
    # Bagian 9 - Report Generation
    # =========================================================================

    def _detect_cross_account_patterns(self, report_data: dict) -> str:
        """Detect systemic issues across all channels."""
        all_issues = []
        account_issues = {}
        
        for acc_key, data in report_data.items():
            acc_issues = []
            for action in data.get('actions', []):
                acc_issues.extend(action.get('issues', []))
            account_issues[acc_key] = acc_issues
            all_issues.extend(acc_issues)
        
        if not all_issues:
            return "No cross-account patterns detected. All accounts performing well."
        
        issue_counts = Counter(all_issues)
        patterns = []
        total_accounts = len(ACCOUNTS)
        
        for issue, count in issue_counts.most_common():
            affected = sum(1 for acc, issues in account_issues.items() if issue in issues)
            if affected >= 3:
                patterns.append(f"  ⚠ {issue} affects {affected}/{total_accounts} accounts — systemic issue")
        
        if patterns:
            return "CROSS-ACCOUNT PATTERNS:\n" + "\n".join(patterns)
        return "No significant cross-account patterns."

    def generate_report(self, report_data: dict):
        """Send comprehensive maintenance report via email."""
        print("\n=== GENERATING MAINTENANCE REPORT ===")
        
        body = f"Tarsier Pipeline Monitoring Report — {datetime.now().strftime('%Y-%m-%d')}\n"
        body += "=" * 60 + "\n\n"
        
        total_evaluated = 0
        total_fixed = 0
        
        for acc_key, data in report_data.items():
            if acc_key not in ACCOUNTS:
                continue
            evaluated = data.get('evaluated', [])
            actions = data.get('actions', [])
            total_evaluated += len(evaluated)
            total_fixed += len(actions)
            
            body += f"Channel: {ACCOUNTS[acc_key]['name']} ({ACCOUNTS[acc_key]['platform']})\n"
            body += f"  Videos Evaluated: {len(evaluated)}\n"
            
            for act in actions:
                vid = act.get('video_id', 'N/A')
                metrics = act.get('metrics', {})
                body += f"  📊 {vid}: {metrics.get('views', 0)} views, {metrics.get('engagement_rate', 0)}% engagement\n"
                body += f"     Issues: {', '.join(act.get('issues', []))}\n"
                for a in act.get('actions', []):
                    body += f"     ✅ {a}\n"
                if act.get('flagged_for_manual_review'):
                    body += f"     ⚠ FLAGGED FOR MANUAL REVIEW\n"
            
            if not actions:
                body += "  ✅ All videos performing normally.\n"
            body += "\n"
        
        body += f"\nSummary: {total_evaluated} videos evaluated, {total_fixed} auto-fixed.\n\n"
        body += self._detect_cross_account_patterns(report_data) + "\n"
        
        # Print to console always
        print(body)
        
        # CHANNEL 1: GitHub Actions Step Summary (visible in Actions UI — no auth needed)
        github_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
        if github_summary:
            try:
                with open(github_summary, 'a', encoding='utf-8') as f:
                    f.write(f"## 📊 Tarsier Monitoring Report\n\n")
                    f.write(f"```\n{body}\n```\n")
                print("Report written to GitHub Actions Summary.")
            except Exception as e:
                print(f"Failed to write GitHub Summary: {e}")
        
        # CHANNEL 2: Email report (requires SMTP App Password)
        if self.smtp_user and self.smtp_pass:
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Tarsier Monitoring Report — {datetime.now().strftime('%Y-%m-%d')}"
                msg['From'] = self.smtp_user
                msg['To'] = self.admin_email
                msg.set_content(body)
                
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
                print("Report email sent successfully.")
            except Exception as e:
                print(f"Email report failed: {e}")
        
        # CHANNEL 3: Save report to file (committed to repo for history)
        try:
            report_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "monitoring_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(body)
            print(f"Report saved to {report_file}")
        except Exception as e:
            print(f"Failed to save report file: {e}")

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    def run_maintenance(self):
        """
        Main monitoring protocol (Bagian 9).
        1. Load all uploaded video IDs from database
        2. Check each video's age (day 3, 7, or 30)
        3. Get REAL metrics from YouTube API
        4. Auto-fix underperforming videos
        5. Send report
        """
        print("Starting Tarsier Maintenance & Monitoring Protocol...")
        print(f"Token directory: {TOKEN_DIR}")
        
        report_data = {acc: {"evaluated": [], "actions": []} for acc in ACCOUNTS.keys()}
        
        # Get all stored video IDs
        all_videos = self.db.get_video_ids()
        print(f"Found {len(all_videos)} videos in database to check.\n")
        
        if not all_videos:
            print("No videos in database yet. Skipping monitoring.")
            self.generate_report(report_data)
            return
        
        # Cache YouTube services per account (avoid repeated auth)
        yt_services = {}
        
        for video_entry in all_videos:
            account_key = video_entry.get("account", "")
            video_id = video_entry.get("video_id", "")
            topic = video_entry.get("topic", "")
            upload_date = video_entry.get("upload_date", "")
            
            if not video_id or account_key not in ACCOUNTS:
                continue
            
            # Skip non-YouTube video IDs (e.g. placeholder IDs)
            if not video_id or len(video_id) < 5 or video_id.startswith("PREVIEW_"):
                continue
            
            # Only YT channels (skip fb_fanspage)
            if ACCOUNTS[account_key]["platform"] != "YT":
                continue
            
            # Check if this video is due for evaluation
            eval_type = self._should_evaluate(upload_date)
            if not eval_type:
                continue
            
            days = self._days_since(upload_date)
            print(f"[{account_key}] Evaluating ({eval_type}, {days}d old): {video_id} — {topic}")
            
            # Get or create YouTube service for this account
            if account_key not in yt_services:
                service = self._get_youtube_service(account_key)
                yt_services[account_key] = service
            else:
                service = yt_services[account_key]
            
            if not service:
                print(f"[{account_key}] No YouTube API access — skipping")
                continue
            
            # Get REAL metrics
            metrics = self.get_video_metrics(service, video_id)
            report_data[account_key]["evaluated"].append(topic)
            
            if not metrics:
                continue
            
            print(f"  📊 {metrics.get('views', 0)} views, {metrics.get('engagement_rate', 0)}% engagement")
            
            # Evaluate against thresholds
            issues = self.evaluate_video(metrics, days)
            
            if issues:
                # Take auto-repair actions (day 7+ only)
                if eval_type in ("day7", "day30"):
                    action_result = self.take_action(
                        service, account_key, video_id, issues, metrics, topic
                    )
                    report_data[account_key]["actions"].append(action_result)
                else:
                    # Day 3: just log, don't fix yet
                    report_data[account_key]["actions"].append({
                        "topic": topic,
                        "video_id": video_id,
                        "metrics": metrics,
                        "issues": issues,
                        "actions": [f"Day 3 observation only — will auto-fix at day 7 if still low"],
                        "flagged_for_manual_review": False
                    })
            
            time.sleep(1)  # Rate limit between API calls
        
        self.generate_report(report_data)


if __name__ == "__main__":
    print(f"[Monitoring] Gemini-13 key: {'SET' if GEMINI_MONITORING_KEY else 'NOT SET'}")
    print(f"[Monitoring] Groq-2 key: {'SET' if GROQ_MONITORING_KEY else 'NOT SET'}")
    monitor = PerformanceMonitor()
    monitor.run_maintenance()
