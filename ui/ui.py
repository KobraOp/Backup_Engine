import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QHBoxLayout, QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHeaderView
from qt_material import apply_stylesheet

# Import backup functions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Backend.backuphandler import create_backup, restore_backup

METADATA_FILE = "backup_metadata.json"
MONITORING_FILE = "monitoring_list.json"

class BackupUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Backup Engine")
        self.setGeometry(300, 200, 1000, 600)

        layout = QVBoxLayout()

        # Log Display
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")
        layout.addWidget(self.log_display)

        # Path Selection Layout
        path_layout = QHBoxLayout()
        self.source_btn = QPushButton("📁 Select Source")
        self.source_btn.clicked.connect(self.select_source)
        path_layout.addWidget(self.source_btn)

        self.destination_btn = QPushButton("💾 Select Destination")
        self.destination_btn.clicked.connect(self.select_destination)
        path_layout.addWidget(self.destination_btn)

        layout.addLayout(path_layout)

        # Password Input Layout
        password_layout = QHBoxLayout()
        self.password_label = QLabel("🔒 Password:")
        password_layout.addWidget(self.password_label)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("background-color: #3B3B3B; color: white; padding: 5px;")
        password_layout.addWidget(self.password_input)

        self.toggle_password_btn = QPushButton("👁️")
        self.toggle_password_btn.setFixedWidth(40)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.toggle_password_btn)

        layout.addLayout(password_layout)

        # Start Backup Button
        self.start_backup_btn = QPushButton("🚀 Start Backup")
        self.start_backup_btn.clicked.connect(self.start_backup)
        layout.addWidget(self.start_backup_btn)

        # Backup Table
        self.backup_table = QTableWidget(self)
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Backup Name", "Size (KB)", "Date", "Actions"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backup_table.verticalHeader().setDefaultSectionSize(50)
        self.backup_table.setStyleSheet("""
            QTableWidget {
                background-color: #232323;
                color: white;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
            }
        """)
        layout.addWidget(self.backup_table)

        # Refresh Button
        self.refresh_btn = QPushButton("🔄 Refresh Backup List")
        self.refresh_btn.clicked.connect(self.load_backup_list)
        layout.addWidget(self.refresh_btn)

        # **Monitoring Panel**
        self.monitoring_table = QTableWidget(self)
        self.monitoring_table.setColumnCount(2)
        self.monitoring_table.setHorizontalHeaderLabels(["Monitored Directory", "Actions"])
        self.monitoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monitoring_table.verticalHeader().setDefaultSectionSize(50)
        self.monitoring_table.setStyleSheet("""
            QTableWidget {
                background-color: #232323;
                color: white;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
            }
        """)
        layout.addWidget(QLabel("📡 Active Monitored Directories:"))
        layout.addWidget(self.monitoring_table)

        # Load Data
        self.load_backup_list()
        self.load_monitoring_list()

        self.setLayout(layout)

        # Variables
        self.source_path = ""
        self.destination_path = ""

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

        password = self.password_input.text() or None
        self.log_display.append(f"🔒 Password Protection: {'Enabled' if password else 'Disabled'}")
        QMessageBox.information(self, "Backup", "Backup started successfully!")
        self.load_backup_list()

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
                restore_btn.setFixedSize(80, 30)
                restore_btn.setStyleSheet("background-color: #444; color: white; border-radius: 5px;")
                restore_btn.clicked.connect(lambda _, d=details["last_backup"]: self.restore_backup(d))

                self.backup_table.setCellWidget(row, 3, restore_btn)

                row += 1

    def load_monitoring_list(self):
        """Load active monitoring directories into the table."""
        self.monitoring_table.setRowCount(0)
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

            row = 0
            for directory in monitoring_list:
                self.monitoring_table.insertRow(row)
                self.monitoring_table.setItem(row, 0, QTableWidgetItem(directory))

                # Stop Button
                stop_btn = QPushButton("⛔ Stop")
                stop_btn.setFixedSize(80, 30)
                stop_btn.setStyleSheet("background-color: #AA0000; color: white; border-radius: 5px;")
                stop_btn.clicked.connect(lambda _, d=directory: self.remove_from_monitoring(d))

                self.monitoring_table.setCellWidget(row, 1, stop_btn)

                row += 1

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("🙈")  # Change icon to indicate visibility
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("👁️")

    def add_to_monitoring(self, directory):
        """Add directory to monitoring list."""
        monitoring_list = []
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

        if directory not in monitoring_list:
            monitoring_list.append(directory)
            with open(MONITORING_FILE, "w") as f:
                json.dump(monitoring_list, f)

        self.load_monitoring_list()

    def remove_from_monitoring(self, directory):
        """Remove directory from monitoring list."""
        if os.path.exists(MONITORING_FILE):
            with open(MONITORING_FILE, "r") as f:
                monitoring_list = json.load(f)

            if directory in monitoring_list:
                monitoring_list.remove(directory)
                with open(MONITORING_FILE, "w") as f:
                    json.dump(monitoring_list, f)

        self.load_monitoring_list()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="dark_teal.xml")
    window = BackupUI()
    window.show()
    sys.exit(app.exec())
