import os
import json
import hashlib
import zipfile
import pyzipper
from datetime import datetime

METADATA_FILE = "backup_metadata.json"

def restore_backup(backup_path, restore_dir, password=None):
    if not os.path.exists(backup_path):
        print(f"Backup file not found: {backup_path}")
        return

    try:
        with pyzipper.AESZipFile(backup_path, "r") as zipf:
            if password:
                zipf.setpassword(password.encode())

            zipf.extractall(restore_dir)
            print(f"Backup restored successfully to {restore_dir}")

    except Exception as e:
        print(f"Error restoring backup: {e}")

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_backup(source_dir, destination_dir, password=None):
    metadata = load_metadata()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = os.path.join(destination_dir, backup_name)

    if source_dir not in metadata:
        print(f"Performing full backup for {source_dir}...")
        file_hashes = full_backup(source_dir, backup_path, password)
    else:
        print(f"Performing incremental backup for {source_dir}...")
        file_hashes = incremental_backup(source_dir, backup_path, metadata[source_dir]["file_hashes"], password)

    metadata[source_dir] = {
        "last_backup": backup_path,
        "file_hashes": file_hashes,
        "size": os.path.getsize(backup_path),
        "last_modified": timestamp
    }
    save_metadata(metadata)

    print(f"Backup completed: {backup_path}")

def full_backup(source_dir, backup_path, password=None):
    file_hashes = {}
    
    with pyzipper.AESZipFile(backup_path, 'w', compression=pyzipper.ZIP_DEFLATED) as zipf:
        if password:
            zipf.setencryption(pyzipper.WZ_AES)
            zipf.setpassword(password.encode())

        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, relative_path)
                file_hashes[relative_path] = get_file_hash(file_path)

    return file_hashes

def incremental_backup(source_dir, backup_path, old_file_hashes, password=None):
    file_hashes = {}

    with pyzipper.AESZipFile(backup_path, "w", compression=pyzipper.ZIP_DEFLATED) as zipf:
        if password:
            zipf.setencryption(pyzipper.WZ_AES)
            zipf.setpassword(password.encode())

        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, source_dir)
                new_hash = get_file_hash(file_path)
                
                if relative_path not in old_file_hashes or old_file_hashes[relative_path] != new_hash:
                    zipf.write(file_path, relative_path)
                    file_hashes[relative_path] = new_hash
                else:
                    file_hashes[relative_path] = old_file_hashes[relative_path]  # Keep unchanged files

    return file_hashes
