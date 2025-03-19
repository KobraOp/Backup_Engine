import sys
import os
import json
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QLabel
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QHeaderView
from qt_material import apply_stylesheet
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import backup functions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Backend.backuphandler import create_backup, restore_backup

METADATA_FILE = "backup_metadata.json"
MONITORING_FILE = "monitoring_list.json"

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_any_event(self, event):
        self.callback(event.src_path)

class MonitoringThread(QThread):
    change_detected = pyqtSignal(str)

    def __init__(self, directories):
        super().__init__()
        self.directories = directories
        self.running = True
        self.observer = Observer()
        self.last_change_time = {}

    def run(self):
        event_handler = FileChangeHandler(self.on_change_detected)
        for directory in self.directories:
            self.observer.schedule(event_handler, directory, recursive=True)
        self.observer.start()

        while self.running:
            time.sleep(1)

    def stop(self):
        self.running = False
        self.observer.stop()
        self.observer.join()

    def on_change_detected(self, path):
        directory = os.path.dirname(path)
        self.last_change_time[directory] = time.time()

        time.sleep(300)  # Wait for 5 minutes before triggering backup
        if time.time() - self.last_change_time[directory] >= 300:
            self.change_detected.emit(directory)

class BackupUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("D:\\BackupEngine\\Backup_Engine\\ui\\assets\\BackupEngine.png"))
        self.setWindowTitle("Backup Engine")
        self.setGeometry(300, 200, 1000, 600)

        layout = QVBoxLayout()

        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        path_layout = QHBoxLayout()
        self.source_btn = QPushButton("📁 Select Source")
        self.source_btn.clicked.connect(self.select_source)
        path_layout.addWidget(self.source_btn)

        self.destination_btn = QPushButton("💾 Select Destination")
        self.destination_btn.clicked.connect(self.select_destination)
        path_layout.addWidget(self.destination_btn)

        layout.addLayout(path_layout)

        self.start_backup_btn = QPushButton("🚀 Start Backup")
        self.start_backup_btn.clicked.connect(self.start_backup)
        layout.addWidget(self.start_backup_btn)

        self.backup_table = QTableWidget(self)
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Backup Name", "Size (KB)", "Date", "Actions"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backup_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.backup_table)

        self.refresh_btn = QPushButton("🔄 Refresh Backup List")
        self.refresh_btn.clicked.connect(self.load_backup_list)
        layout.addWidget(self.refresh_btn)

        self.monitoring_table = QTableWidget(self)
        self.monitoring_table.setColumnCount(2)
        self.monitoring_table.setHorizontalHeaderLabels(["Monitored Directory", "Actions"])
        self.monitoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monitoring_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(QLabel("📡 Active Monitored Directories:"))
        layout.addWidget(self.monitoring_table)

        self.load_backup_list()
        self.load_monitoring_list()  # FIX: Ensure the function is called

        self.setLayout(layout)

        self.source_path = ""
        self.destination_path = ""

        self.monitoring_thread = None
        self.start_monitoring()

    def select_source(self):
        self.source_path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if self.source_path:
            self.log_display.append(f"🟢 Selected Source: {self.source_path}")
            self.add_to_monitoring(self.source_path)

    def select_destination(self):
        self.destination_path = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
        if self.destination_path:
            self.log_display.append(f"🟢 Selected Destination: {self.destination_path}")

    def start_backup(self):
        if not self.source_path or not self.destination_path:
            QMessageBox.warning(self, "Warning", "Please select both Source and Destination folders!")
            return

        self.log_display.append("🔄 Backup started...")
        create_backup(self.source_path, self.destination_path)

        self.add_to_monitoring(self.source_path)

        self.load_backup_list()
        QMessageBox.information(self, "Backup", "Backup completed successfully!")

    def load_backup_list(self):
        self.backup_table.setRowCount(0)
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "r") as f:
                metadata = json.load(f)

            row = 0
            for source, details in metadata.items():
                self.backup_table.insertRow(row)
                self.backup_table.setItem(row, 0, QTableWidgetItem(os.path.basename(details["last_backup"])))
                self.backup_table.setItem(row, 1, QTableWidgetItem(str(details["size"] // 1024)))
                self.backup_table.setItem(row, 2, QTableWidgetItem(details["last_modified"]))

                restore_btn = QPushButton("🔄 Restore")
                restore_btn.clicked.connect(lambda _, d=details["last_backup"]: restore_backup(d))
                self.backup_table.setCellWidget(row, 3, restore_btn)

                row += 1

        self.auto_add_backed_up_dirs_to_monitoring()

    def auto_add_backed_up_dirs_to_monitoring(self):
        """Ensures previously backed-up directories are added to monitoring automatically."""
        if not os.path.exists(METADATA_FILE):
            return

        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)

        for directory in metadata.keys():
            self.add_to_monitoring(directory)

    def start_monitoring(self):
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                directories = json.load(f)

            if directories:
                self.monitoring_thread = MonitoringThread(directories)
                self.monitoring_thread.change_detected.connect(self.start_backup)
                self.monitoring_thread.start()

    def add_to_monitoring(self, directory):
        monitoring_list = []
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

        if directory not in monitoring_list:
            monitoring_list.append(directory)
            with open(MONITORING_FILE, "w") as f:
                json.dump(monitoring_list, f)

        self.start_monitoring()
        self.load_monitoring_list()  # FIX: Function added

    def load_monitoring_list(self):
        """Loads and displays monitored directories."""
        self.monitoring_table.setRowCount(0)
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

            row = 0
            for directory in monitoring_list:
                self.monitoring_table.insertRow(row)
                self.monitoring_table.setItem(row, 0, QTableWidgetItem(directory))

                remove_btn = QPushButton("❌ Remove")
                remove_btn.clicked.connect(lambda _, d=directory: self.remove_from_monitoring(d))
                self.monitoring_table.setCellWidget(row, 1, remove_btn)

                row += 1

    def remove_from_monitoring(self, directory):
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

            monitoring_list = [d for d in monitoring_list if d != directory]

            with open(MONITORING_FILE, "w") as f:
                json.dump(monitoring_list, f)

        self.load_monitoring_list()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="dark_teal.xml")
    window = BackupUI()
    window.show()
    sys.exit(app.exec())
