import time
import json
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backuphandler import create_backup

CONFIG_FILE = "backup_config.json"
WAIT_TIME = 300  # 5 minutes delay before triggering backup

class BackupHandler(FileSystemEventHandler):
    """Handles file system changes."""
    
    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.changes_detected = False

    def on_any_event(self, event):
        """Detect file changes and schedule backup."""
        if event.event_type in ["created", "modified", "deleted", "moved"]:
            print(f"Change detected in {self.source_dir}: {event.src_path}")
            self.changes_detected = True

def start_monitoring():
    """Load directories from config and start monitoring them."""
    if not os.path.exists(CONFIG_FILE):
        print("No directories configured. Please run config_manager.py first.")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    if not config.get("directories"):
        print("No directories to monitor.")
        return

    observers = []
    event_handlers = []

    for entry in config["directories"]:
        source_dir = entry["source"]
        event_handler = BackupHandler(source_dir)
        observer = Observer()
        observer.schedule(event_handler, source_dir, recursive=True)
        observer.start()

        observers.append(observer)
        event_handlers.append(event_handler)
        print(f"Monitoring started for: {source_dir}")

    try:
        while True:
            for handler in event_handlers:
                if handler.changes_detected:
                    print(f"Changes detected in {handler.source_dir}. Waiting {WAIT_TIME // 60} minutes before backup...")
                    time.sleep(WAIT_TIME)
                    create_backup(handler.source_dir)  # Trigger backup
                    handler.changes_detected = False  # Reset flag
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

if __name__ == "__main__":
    start_monitoring()
