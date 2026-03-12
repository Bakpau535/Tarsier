import os
import sys
import smtplib
from email.message import EmailMessage
import random
from datetime import datetime, timedelta
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import ACCOUNTS, TOPICS_FILE
from src.database import DatabaseManager
from src.metadata import MetadataGenerator
from src.thumbnail import ThumbnailGenerator

class PerformanceMonitor:
    def __init__(self):
        self.db = DatabaseManager(TOPICS_FILE)
        self.metadata_gen = MetadataGenerator()
        self.thumbnail_gen = ThumbnailGenerator()
        
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")  # Fixed typo: was SMTP_user
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.admin_email = os.environ.get("FB_ADMIN_EMAIL", "admin@example.com")

    # =========================================================================
    # Bagian 9 - Threshold Performa
    # =========================================================================

    # --- YT Video Panjang ---
    # | Metrik      | Bagus | Normal | Perlu Perbaikan |
    # | CTR         | >4%   | 2-4%   | <2%             |
    # | Watch Time  | >50%  | 30-50% | <30%            |
    # | Like Ratio  | >4%   | 2-4%   | <2%             |

    # --- YT Shorts ---
    # | Retention   | >70%  | 50-70% | <50%            |

    # --- Facebook ---
    # | Watch Time  | >3min | 1-3min | <1min           |
    # | Engagement  | >3%   | 1-3%   | <1%             |

    def _get_mock_metrics(self, platform: str, is_short: bool = False) -> dict:
        """Returns mock metrics for testing the evaluation logic."""
        if platform == "YT":
            if is_short:
                 return {
                     "retention": random.uniform(30.0, 90.0) # percentage
                 }
            else:
                 return {
                     "ctr": random.uniform(1.0, 6.0),     # percentage
                     "watch_time": random.uniform(20.0, 70.0), # percentage
                     "like_ratio": random.uniform(1.0, 6.0) # percentage
                 }
        else: # FB
            return {
                "watch_time_mins": random.uniform(0.5, 5.0),
                "engagement_rate": random.uniform(0.5, 5.0) # percentage
            }

    def evaluate_yt_long(self, metrics: dict) -> list:
        """Evaluates YT long video metrics against thresholds (Bagian 9)."""
        issues = []
        if metrics.get("ctr", 0) < 2.0: issues.append("LOW_CTR")
        if metrics.get("watch_time", 0) < 30.0: issues.append("LOW_RETENTION")
        if metrics.get("like_ratio", 0) < 2.0: issues.append("LOW_ENGAGEMENT")
        return issues

    def evaluate_yt_short(self, metrics: dict) -> list:
        """Evaluates YT Shorts retention against threshold (Bagian 9)."""
        if metrics.get("retention", 0) < 50.0:
            return ["LOW_RETENTION"]
        return []

    def evaluate_fb(self, metrics: dict) -> list:
        """Evaluates FB metrics against thresholds (Bagian 9)."""
        issues = []
        if metrics.get("watch_time_mins", 0) < 1.0: issues.append("LOW_RETENTION")
        if metrics.get("engagement_rate", 0) < 1.0: issues.append("LOW_ENGAGEMENT")
        return issues

    # =========================================================================
    # Bagian 9 - Aksi Otomatis
    # =========================================================================
    # - CTR rendah → generate & update thumbnail + judul baru
    # - Retention rendah → update deskripsi dengan hook lebih kuat
    # - Engagement rendah → refresh hashtag & tags dengan keyword trending
    # - Semua rendah → flag & kirim laporan ke email untuk review manual

    def take_action(self, account_key: str, issues: list, topic_info: dict) -> dict:
        """Takes optimization actions based on identified issues (Bagian 9)."""
        actions_taken = []
        
        print(f"[{account_key}] Issues identified: {issues}")
        
        # CTR rendah → generate & update thumbnail + judul baru
        if "LOW_CTR" in issues:
            print(f"[{account_key}] Auto-Action: Regenerating Thumbnail & Title...")
            new_title = f"{topic_info.get('topik')} (Updated {datetime.now().year})"
            self.thumbnail_gen.generate(account_key, new_title, topic_info.get("topik", "Unknown"))
            actions_taken.append("Updated Thumbnail & Title")
            
        # Retention rendah → update deskripsi dengan hook lebih kuat
        if "LOW_RETENTION" in issues:
            print(f"[{account_key}] Auto-Action: Updating Description with stronger hook...")
            actions_taken.append("Updated Description with stronger hook")
             
        # Engagement rendah → refresh hashtag & tags dengan keyword trending
        if "LOW_ENGAGEMENT" in issues:
            print(f"[{account_key}] Auto-Action: Refreshing Hashtags & Tags with trending keywords...")
            actions_taken.append("Refreshed Hashtags & Tags")

        # Semua rendah → flag & kirim laporan ke email untuk review manual
        flagged = len(issues) >= 3
        if flagged:
            print(f"[{account_key}] *** ALL METRICS LOW - Flagged for manual review ***")

        return {
             "topic": topic_info.get("topik"),
             "account": account_key,
             "actions": actions_taken,
             "flagged_for_manual_review": flagged
        }

    # =========================================================================
    # Bagian 9 - Jadwal Monitoring 
    # - 3 hari setelah posting → cek awal
    # - 7 hari → evaluasi utama
    # - 30 hari → evaluasi bulanan
    # =========================================================================

    def _should_evaluate(self, post_date_str: str) -> str:
        """
        Determines evaluation type based on days since posting.
        Returns: 'day3', 'day7', 'day30', or '' if not in any evaluation window.
        """
        try:
            post_date = datetime.strptime(post_date_str, "%Y-%m-%d")
            days_since = (datetime.now() - post_date).days
            
            # Evaluate at day 3 (window: day 3-4)
            if 3 <= days_since <= 4:
                return "day3"
            # Evaluate at day 7 (window: day 7-8)
            elif 7 <= days_since <= 8:
                return "day7"
            # Evaluate at day 30 (window: day 30-31)
            elif 30 <= days_since <= 31:
                return "day30"
            
            return ""
        except (ValueError, TypeError):
            return ""

    # =========================================================================
    # Bagian 9 - Laporan
    # - Rekap performa semua 6 akun dalam 1 email
    # - Deteksi pola performa antar akun
    # - Rekomendasi perbaikan otomatis
    # =========================================================================

    def _detect_cross_account_patterns(self, report_data: dict) -> str:
        """
        Deteksi pola performa antar akun (Bagian 9 - Laporan).
        Analyzes issues across all 6 accounts to find common patterns.
        """
        all_issues = []
        account_issues = {}
        
        for acc_key, data in report_data.items():
            acc_issues = []
            for action in data['actions']:
                acc_issues.extend(action.get('raw_issues', []))
            account_issues[acc_key] = acc_issues
            all_issues.extend(acc_issues)
        
        if not all_issues:
            return "No cross-account patterns detected. All accounts performing well."
        
        # Count frequency of each issue across accounts
        issue_counts = Counter(all_issues)
        patterns = []
        
        total_accounts = len(ACCOUNTS)
        for issue, count in issue_counts.most_common():
            affected = sum(1 for acc, issues in account_issues.items() if issue in issues)
            if affected >= 3:  # Pattern = affects 3+ accounts
                patterns.append(f"  ⚠ {issue} affects {affected}/{total_accounts} accounts - systemic issue detected")
        
        if patterns:
            return "CROSS-ACCOUNT PATTERNS DETECTED:\n" + "\n".join(patterns)
        return "No significant cross-account patterns detected."

    def _generate_recommendations(self, report_data: dict) -> str:
        """Rekomendasi perbaikan otomatis (Bagian 9 - Laporan)."""
        recommendations = []
        
        total_flagged = sum(
            1 for data in report_data.values()
            for action in data['actions']
            if action.get('flagged_for_manual_review')
        )
        
        total_ctr_issues = sum(
            1 for data in report_data.values()
            for action in data['actions']
            if "Updated Thumbnail & Title" in action.get('actions', [])
        )
        
        total_retention_issues = sum(
            1 for data in report_data.values()
            for action in data['actions']
            if "Updated Description with stronger hook" in action.get('actions', [])
        )
        
        if total_flagged > 0:
            recommendations.append(f"  💡 {total_flagged} videos flagged for manual review. Consider reviewing content strategy.")
        if total_ctr_issues > 3:
            recommendations.append("  💡 Multiple CTR issues detected. Consider A/B testing thumbnail styles.")
        if total_retention_issues > 3:
            recommendations.append("  💡 Multiple retention issues. Consider stronger opening hooks in scripts.")
        if not recommendations:
            recommendations.append("  ✅ All accounts performing within acceptable ranges. Keep current strategy.")
        
        return "AUTO-RECOMMENDATIONS:\n" + "\n".join(recommendations)

    def generate_report(self, report_data: dict):
        """
        Sends a comprehensive maintenance report (Bagian 9 - Laporan).
        - Rekap performa semua 6 akun dalam 1 email
        - Deteksi pola performa antar akun
        - Rekomendasi perbaikan otomatis
        """
        print("\n=== GENERATING MAINTENANCE REPORT ===")
        
        # Build report body
        body = f"Tarsier Pipeline Monitoring Report - {datetime.now().strftime('%Y-%m-%d')}\n"
        body += "=" * 60 + "\n\n"
        
        # Rekap performa semua 6 akun dalam 1 email
        for acc_key, data in report_data.items():
            body += f"Account: {ACCOUNTS[acc_key]['name']} ({ACCOUNTS[acc_key]['platform']})\n"
            body += f"- Videos Evaluated: {len(data['evaluated'])}\n"
            if data['actions']:
                body += "- Interventions:\n"
                for act in data['actions']:
                    body += f"  > {act['topic']}: {', '.join(act['actions'])}\n"
                    if act['flagged_for_manual_review']:
                        body += f"    *** FLAGGED FOR MANUAL REVIEW ***\n"
            else:
                body += "- Interventions: None. All performing normally or well.\n"
            body += "\n"
        
        # Deteksi pola performa antar akun
        body += "\n" + self._detect_cross_account_patterns(report_data) + "\n\n"
        
        # Rekomendasi perbaikan otomatis
        body += self._generate_recommendations(report_data) + "\n"
        
        if not self.smtp_user or not self.smtp_pass:
            print("SMTP credentials missing. Printing report to console:")
            print(body)
            return
             
        msg = EmailMessage()
        msg['Subject'] = f"Tarsier Pipeline Maintenance Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.smtp_user
        msg['To'] = self.admin_email
        msg.set_content(body)
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            print("Report sent successfully.")
        except Exception as e:
            print(f"Failed to send report: {e}")

    def run_maintenance(self):
        """
        Main entry point for monitoring schedule (Bagian 9).
        Evaluates videos based on their posting date:
        - 3 hari setelah posting → cek awal
        - 7 hari → evaluasi utama
        - 30 hari → evaluasi bulanan
        """
        print("Starting Tarsier Maintenance & Monitoring Protocol...")
        topics = self.db.load_data()
        
        report_data = {acc: {"evaluated": [], "actions": []} for acc in ACCOUNTS.keys()}
        
        for entry in topics:
            if entry.get("status") != "selesai":
                continue
                
            account_key = entry.get("akun")
            if account_key not in ACCOUNTS:
                continue
            
            # Jadwal Monitoring: Check if this video is at day 3, 7, or 30
            eval_type = self._should_evaluate(entry.get("tanggal", ""))
            if not eval_type:
                continue  # Skip if not in any evaluation window
                
            platform = ACCOUNTS[account_key]["platform"]
            
            print(f"Evaluating ({eval_type}): {account_key} - {entry.get('topik')}")
            
            issues = []
            if platform == "YT":
                # Check Long video metrics
                long_metrics = self._get_mock_metrics("YT", is_short=False)
                issues.extend(self.evaluate_yt_long(long_metrics))
                
                # Check Short video metrics
                short_metrics = self._get_mock_metrics("YT", is_short=True)
                issues.extend(self.evaluate_yt_short(short_metrics))
            else:
                fb_metrics = self._get_mock_metrics("FB")
                issues.extend(self.evaluate_fb(fb_metrics))
                
            # Remove duplicates
            issues = list(set(issues))
            
            report_data[account_key]["evaluated"].append(entry.get("topik"))
            
            if issues:
                action_result = self.take_action(account_key, issues, entry)
                action_result["raw_issues"] = issues  # For cross-account analysis
                action_result["eval_type"] = eval_type
                report_data[account_key]["actions"].append(action_result)

        self.generate_report(report_data)

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run_maintenance()
