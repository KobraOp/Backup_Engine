import os
import zipfile
import pyzipper

def list_backups(backup_dir):
    backups = [f for f in os.listdir(backup_dir) if f.endswith(".zip")]
    if not backups:
        print("No backups found.")
        return []
    
    print("\nAvailable Backups:")
    for idx, backup in enumerate(backups, 1):
        print(f"{idx}. {backup}")
    
    return backups

def restore_backup():
    backup_dir = input("Enter the backup directory path: ").strip()
    if not os.path.exists(backup_dir):
        print("Invalid backup directory.")
        return

    backups = list_backups(backup_dir)
    if not backups:
        return

    try:
        choice = int(input("Select a backup to restore (Enter the number): ")) - 1
        if choice < 0 or choice >= len(backups):
            print("Invalid selection.")
            return

        zip_path = os.path.join(backup_dir, backups[choice])
        destination = input("Enter the restore location (or press Enter to restore to original location): ").strip()

        extract_backup(zip_path, destination)
    
    except ValueError:
        print("Please enter a valid number.")

def extract_backup(zip_path, destination):
    try:
        with pyzipper.AESZipFile(zip_path, "r") as zipf:
            if zipf.testzip() is not None:
                print("ZIP file is corrupted.")
                return
            
            try:
                zipf.extractall(destination)
                print(f"Backup restored to: {destination if destination else 'original location'}")
            except RuntimeError:
                password = input("This backup is password-protected. Enter password: ").strip()
                try:
                    zipf.setpassword(password.encode())
                    zipf.extractall(destination)
                    print(f"Backup restored successfully to: {destination if destination else 'original location'}")
                except RuntimeError:
                    print("Incorrect password. Restoration failed.")
    
    except FileNotFoundError:
        print("Backup file not found.")
