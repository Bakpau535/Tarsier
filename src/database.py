import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self, topics_file: str):
        self.topics_file = topics_file
        self.ensure_file()

    def ensure_file(self):
        """Creates the JSON file if it doesn't exist."""
        if not os.path.exists(self.topics_file):
            with open(self.topics_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)

    def load_data(self) -> List[Dict]:
        """Loads data from the JSON file."""
        try:
            with open(self.topics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
            # Auto-reset corrupted files (e.g. UTF-16 BOM from PowerShell)
            self.save_data([])
            return []

    def save_data(self, data: List[Dict]):
        """Saves data back to the JSON file."""
        with open(self.topics_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def is_topic_completed(self, topic: str, account: str) -> bool:
        """Checks if a topic has already been successfully processed for a given account."""
        data = self.load_data()
        for entry in data:
            if (entry.get("topik", "").lower() == topic.lower() and 
                entry.get("akun", "") == account and 
                entry.get("status", "") == "selesai"):
                return True
        return False

    def get_pending_topics(self) -> List[Dict]:
        """Gets all topics that might have failed and need to be retried."""
        data = self.load_data()
        return [entry for entry in data if entry.get("status", "") != "selesai"]
        
    def add_topic_record(self, topic: str, account: str, status: str = "dalam_proses"):
        """Adds a new record or updates an existing one."""
        data = self.load_data()
        
        # Check if it already exists
        for entry in data:
            if entry.get("topik") == topic and entry.get("akun") == account:
                entry["status"] = status
                entry["tanggal"] = datetime.now().strftime("%Y-%m-%d")
                self.save_data(data)
                return
                
        # If new, append
        data.append({
            "topik": topic,
            "tanggal": datetime.now().strftime("%Y-%m-%d"),
            "akun": account,
            "status": status
        })
        self.save_data(data)

    def mark_completed(self, topic: str, account: str):
        """Marks a topic as successfully completed."""
        self.add_topic_record(topic, account, "selesai")

    def mark_failed(self, topic: str, account: str):
        """Marks a topic as failed."""
        self.add_topic_record(topic, account, "gagal")

    # === Script Hash Dedup System ===
    # Ensures NO script is ever reused — within same channel or across channels
    
    def _get_scripts_file(self) -> str:
        """Path to used_scripts.json in same directory as topics.json."""
        return os.path.join(os.path.dirname(self.topics_file), "used_scripts.json")
    
    def _load_script_hashes(self) -> dict:
        """Load script hash database. Format: {hash: {account, topic, date}}"""
        scripts_file = self._get_scripts_file()
        if not os.path.exists(scripts_file):
            return {}
        try:
            with open(scripts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_script_hashes(self, data: dict):
        scripts_file = self._get_scripts_file()
        with open(scripts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def is_script_duplicate(self, script: str) -> bool:
        """
        Check if this exact script (by hash) has EVER been used on ANY channel.
        Returns True if duplicate.
        """
        import hashlib
        script_hash = hashlib.sha256(script.strip().encode()).hexdigest()[:16]
        hashes = self._load_script_hashes()
        if script_hash in hashes:
            prev = hashes[script_hash]
            print(f"[DEDUP] Script hash {script_hash} already used by {prev.get('account','')} on {prev.get('date','')}")
            return True
        return False
    
    def record_script_hash(self, script: str, account: str, topic: str):
        """Record a script hash so it can never be reused."""
        import hashlib
        script_hash = hashlib.sha256(script.strip().encode()).hexdigest()[:16]
        hashes = self._load_script_hashes()
        hashes[script_hash] = {
            "account": account,
            "topic": topic,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._save_script_hashes(hashes)
        print(f"[DEDUP] Script hash {script_hash} recorded for {account}")

    # === Video ID Tracking ===
    # Stores YouTube video IDs so monitoring can query real metrics
    
    def _get_video_ids_file(self) -> str:
        return os.path.join(os.path.dirname(self.topics_file), "video_ids.json")
    
    def _load_video_ids(self) -> dict:
        vid_file = self._get_video_ids_file()
        if not os.path.exists(vid_file):
            return {}
        try:
            with open(vid_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_video_ids(self, data: dict):
        vid_file = self._get_video_ids_file()
        with open(vid_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def save_video_id(self, account: str, topic: str, video_id: str, short_id: str = ""):
        """Save YouTube video ID after successful upload for monitoring."""
        data = self._load_video_ids()
        key = f"{account}_{topic}"
        data[key] = {
            "account": account,
            "topic": topic,
            "video_id": video_id,
            "short_id": short_id,
            "upload_date": datetime.now().strftime("%Y-%m-%d"),
        }
        self._save_video_ids(data)
        print(f"[DB] Video ID {video_id} saved for {account}/{topic}")
    
    def get_video_ids(self, account: str = "") -> list:
        """Get all stored video IDs, optionally filtered by account."""
        data = self._load_video_ids()
        results = list(data.values())
        if account:
            results = [r for r in results if r.get("account") == account]
        return results
