import threading
import time
import json
import os
import sys

# Ensure the Backend folder is in the import path
sys.path.append(os.path.join(os.path.dirname(__file__), "Backend"))

from Backend.filemonitor import start_monitoring
from Backend.restorehandler import restore_backup
from Backend.backuphandler import create_backup

CONFIG_FILE = "backup_config.json"

def configure_directories():
    """Ask the user for source and destination directories and store them in a config file."""
    directories = []
    
    while True:
        source = input("Enter the source directory (or type 'done' to finish): ").strip()
        if source.lower() == "done":
            break
        if not os.path.exists(source):
            print("Invalid path! Please enter a valid directory.")
            continue

        destination = input("Enter the destination directory: ").strip()
        if not os.path.exists(destination):
            print("Invalid path! Please enter a valid directory.")
            continue
        
        directories.append({"source": source, "destination": destination})

    with open(CONFIG_FILE, "w") as f:
        json.dump({"directories": directories}, f, indent=4)
    
    print("Directories configured successfully.")

def manual_backup():
    """Allow user to trigger a backup manually."""
    if not os.path.exists(CONFIG_FILE):
        print("No configuration found. Please configure directories first.")
        return
    
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    for entry in config["directories"]:
        source = entry["source"]
        destination = entry["destination"]

        password = input(f"Do you want to set a password for backup of {source}? (y/n): ").strip().lower()
        password = input("Enter password: ").strip() if password == "y" else None

        create_backup(source, destination, password)

def start_backup_monitoring():
    """Start the file monitoring system in a separate thread."""
    print("Starting monitoring... Press Ctrl+C to stop.")
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    while True:
        time.sleep(1)  # Keep main thread alive

def main_menu():
    """Display the main menu and handle user choices."""
    while True:
        print("\n--- Local Backup System ---")
        print("1. Configure Directories")
        print("2. Manual Backup")
        print("3. Start Monitoring & Automatic Backup")
        print("4. Restore Backup")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            configure_directories()
        elif choice == "2":
            manual_backup()
        elif choice == "3":
            start_backup_monitoring()
        elif choice == "4":
            restore_backup()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice! Please select a valid option.")

if __name__ == "__main__":
    main_menu()
