import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, 
    QTableWidget, QTableWidgetItem, QMessageBox, QProgressBar, QHBoxLayout,QHeaderView
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Backend.backuphandler import create_backup, restore_backup

METADATA_FILE = "backup_metadata.json"

class BackupThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, source, destination, password=None):
        super().__init__()
        self.source = source
        self.destination = destination
        self.password = password

    def run(self):
        self.log_signal.emit(f"🔄 Starting backup: {self.source} ➝ {self.destination}")
        create_backup(self.source, self.destination, self.password)
        self.log_signal.emit(f"✅ Backup completed: {self.destination}")

class BackupUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backup Engine")
        self.setGeometry(300, 200, 750, 550)
        self.setStyleSheet(self.get_dark_mode_style())  

        layout = QVBoxLayout()

        # Buttons Layout
        btn_layout = QHBoxLayout()
        self.source_btn = QPushButton("Select Source")
        self.source_btn.setIcon(QIcon("icons/folder.png"))
        self.source_btn.clicked.connect(self.select_source)  

        self.dest_btn = QPushButton("Select Destination")
        self.dest_btn.setIcon(QIcon("icons/folder.png"))
        self.dest_btn.clicked.connect(self.select_destination)  

        btn_layout.addWidget(self.source_btn)
        btn_layout.addWidget(self.dest_btn)
        layout.addLayout(btn_layout)

        # Start Backup Button
        self.start_backup_btn = QPushButton("Start Backup")
        self.start_backup_btn.setIcon(QIcon("icons/backup.png"))
        self.start_backup_btn.clicked.connect(self.start_backup)  # ✅ FIXED FUNCTION
        layout.addWidget(self.start_backup_btn)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        # Log Display
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Backup List Table
        self.backup_table = QTableWidget(self)
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Backup Name", "Size (KB)", "Date", "Actions"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.backup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.backup_table.setStyleSheet("background-color: #212121; color: #E0E0E0;")
        self.backup_table.setColumnWidth(3, 100)  
        layout.addWidget(self.backup_table)

        # Refresh Button
        self.refresh_btn = QPushButton("Refresh Backup List")
        self.refresh_btn.setIcon(QIcon("icons/refresh.png"))
        self.refresh_btn.clicked.connect(self.load_backup_list)
        layout.addWidget(self.refresh_btn)

        self.source = ""
        self.destination = ""

        self.load_backup_list()
        self.setLayout(layout)

    def select_source(self):
        """Select source directory."""
        self.source = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if self.source:
            self.log_display.append(f"🟢 Selected Source: {self.source}")

    def select_destination(self):
        """Select backup destination directory."""
        self.destination = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
        if self.destination:
            self.log_display.append(f"🟢 Selected Destination: {self.destination}")

    def start_backup(self):
        """Start the backup process."""
        if not self.source or not self.destination:
            QMessageBox.warning(self, "Warning", "Please select both source and destination.")
            return

        self.log_display.append(f"🟢 Starting backup for {self.source} ➝ {self.destination}")
        self.backup_thread = BackupThread(self.source, self.destination)
        self.backup_thread.log_signal.connect(self.update_log)
        self.backup_thread.start()
        self.load_backup_list()

    def update_log(self, message):
        """Update log display."""
        self.log_display.append(message)

    def load_backup_list(self):
        """Load backup details into the table."""
        self.backup_table.setRowCount(0)
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "r") as f:
                metadata = json.load(f)

            for row, (source, details) in enumerate(metadata.items()):
                self.backup_table.insertRow(row)
                self.backup_table.setItem(row, 0, QTableWidgetItem(os.path.basename(details["last_backup"])))
                self.backup_table.setItem(row, 1, QTableWidgetItem(str(details["size"] // 1024)))
                self.backup_table.setItem(row, 2, QTableWidgetItem(details["last_modified"]))

                restore_btn = QPushButton("Restore")
                restore_btn.setIcon(QIcon("icons/restore.png"))
                restore_btn.setStyleSheet("padding: 2px; height: 24px;")  
                restore_btn.clicked.connect(lambda _, d=details["last_backup"]: self.restore_backup(d))
                self.backup_table.setCellWidget(row, 3, restore_btn)

                self.backup_table.setRowHeight(row, 30)  

    def restore_backup(self, backup_path):
        """Restore a backup to a selected destination."""
        destination = QFileDialog.getExistingDirectory(self, "Select Restore Destination")
        if destination:
            restore_backup(backup_path, destination)
            QMessageBox.information(self, "Restore", f"Backup restored to {destination}")

    def get_dark_mode_style(self):
        """Dark mode styling."""
        return """
            QWidget {
                background-color: #121212;
                color: #E0E0E0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #333;
            }
            QTableWidget {
                background-color: #212121;
                color: #D4D4D4;
                gridline-color: #333;
                border: 1px solid #444;
            }
            QTableWidget::item {
                border-bottom: 1px solid #333;
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #333;
                padding: 5px;
                border: 1px solid #444;
            }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BackupUI()
    window.show()
    sys.exit(app.exec())
