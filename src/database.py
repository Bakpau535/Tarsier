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
