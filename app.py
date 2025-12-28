import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QSizePolicy
from PyQt6.QtCore import Qt
from record import Recorder
from pathlib import Path
from datetime import datetime

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.recorder = Recorder.create()
        self.paused = False

        # Create a dedicated folder for all transcriptions
        self.root_dir = Path.home() / "Documents" / "Recordings"
        self.root_dir.mkdir(parents=True, exist_ok=True)  # creates folder if it doesn't exist

        self.current_file = None
    
    @staticmethod
    def create():
        app = App()
        app.create_layout()
        return app

    def on_start_button_click(self):
        #Logic for when user starts a new recording.
        if not self.paused:
            self.main_label.setText("")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.transcription_file = self.root_dir / f"transcription_{timestamp}.txt"
        
        self.paused = False
        self.start_button.setHidden(True)
        self.pause_button.setHidden(False)
        self.stop_button.setEnabled(True)

        threading.Thread(target=lambda: self.recorder.record(self.update_text), daemon=True).start()

    def on_stop_button_click(self):
        self.recorder.stop_recording()
        self.paused = False
        self.start_button.setText("Start Recording")
        self.stop_button.setEnabled(False)
        self.start_button.setHidden(False)
        self.pause_button.setHidden(True)

        #Save to documents folder here
        # Write current transcription text to the known transcription file
        text = self.main_label.text()
        self.transcription_file.write_text(text or "", encoding="utf-8")
        self._refresh_sidebar()

    
    def on_pause_button_click(self):
        self.recorder.stop_recording()
        self.paused = True
        self.start_button.setText("Resume Recording")
        self.stop_button.setEnabled(True)
        self.start_button.setHidden(False)
        self.pause_button.setHidden(True)

    def update_text(self, text):
        current_text = self.main_label.text()
        if current_text:
            current_text += text
        else:
            current_text = text
        self.main_label.setText(current_text)
    
    def create_layout(self):
        self.window = QWidget()
        self.window.setWindowTitle("Top/Bottom Layout Example")
        # Use a default mac-like app window size and allow resizing
        self.window.resize(900, 600)
        self.window.setMinimumSize(700, 400)

        # Main horizontal layout: side panel + center panel
        self.main_layout = QHBoxLayout()

        # --- Side panel (similar width to mac Voice Memos list) ---
        self.side_panel = QVBoxLayout()
        side_header = QLabel("Recordings")
        side_header.setStyleSheet("font-weight: 600; padding: 6px 8px; color: #E6E6E6;")
        self.side_list = QListWidget()
        self.side_list.setFixedWidth(260)
        # Placeholder items (will be populated in real use)
        self.side_list.addItems(self._get_recording_files())
        self.side_panel.addWidget(side_header)
        self.side_panel.addWidget(self.side_list)

        # --- Center panel (current main content + buttons) ---
        self.center_panel = QVBoxLayout()
        self.main_label = QLabel("")
        self.main_label.setObjectName("main_label")
        self.main_label.setWordWrap(True)
        # Ensure text is aligned to the top-left and the label expands to fill space
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.main_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_label.setMinimumSize(400, 300)
        self.center_panel.addWidget(self.main_label)

        # Bottom container (buttons side by side)
        self.bottom_container = QHBoxLayout()
        self.start_button = QPushButton("Start Recording")
        self.pause_button = QPushButton("Pause Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setHidden(True)

        # Optional: make buttons smaller
        self.start_button.setMaximumSize(150, 30)
        self.stop_button.setMaximumSize(150, 30)
        self.pause_button.setMaximumSize(150, 30)

        # Set object names for styling
        self.start_button.setObjectName("start_button")
        self.stop_button.setObjectName("stop_button")
        self.pause_button.setObjectName("pause_button")

        # Connect signals
        self.start_button.clicked.connect(self.on_start_button_click)
        self.stop_button.clicked.connect(self.on_stop_button_click)
        self.pause_button.clicked.connect(self.on_pause_button_click)

        # Add buttons to bottom container
        self.bottom_container.addWidget(self.start_button)
        self.bottom_container.addWidget(self.pause_button)
        self.bottom_container.addWidget(self.stop_button)

        # Add bottom container to center panel
        self.center_panel.addLayout(self.bottom_container)

        # Add side panel and center panel to main layout
        self.main_layout.addLayout(self.side_panel)
        self.main_layout.addLayout(self.center_panel)

        # Apply a simple, mac-like color scheme
        self.window.setStyleSheet("""
        /* Dark theme inspired by macOS Dark Mode */
        QWidget { background-color: #0B0B0C; color: #E6E6E6; }
        QLabel#main_label { background-color: #141416; border-radius: 8px; padding: 12px; color: #E6E6E6; }
        QLabel { color: #E6E6E6; }
        QListWidget { background-color: #1C1C1E; border-radius: 8px; padding: 6px; color: #E6E6E6; }
        QListWidget::item:selected { background-color: #2C2C2F; color: #FFFFFF; }
        QPushButton { background-color: #0A84FF; color: white; border: none; padding: 6px 12px; border-radius: 8px; }
        QPushButton#stop_button { background-color: #FF453A; }
        QPushButton#pause_button { background-color: #FF9F0A; color: #1C1C1E; }
        QPushButton:disabled { background-color: #2C2C2E; color: #6E6E73; }
        """)

        # Set the layout for the window
        self.window.setLayout(self.main_layout)
    
    def run(self):
        # Show the window
        self.window.show()
        # Run the event loop
        sys.exit(self.app.exec())
    
    def _get_recording_files(self):
        """
        Returns a list of file names (strings) in the recordings folder, sorted by creation time descending.
        """

        # Only include .txt files
        files = [f for f in self.root_dir.iterdir() if f.is_file() and f.suffix == ".txt"]

        # Sort by creation/modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Return just the file names
        return [f.name for f in files]
    
    def _refresh_sidebar(self):
        """
        Updates the QListWidget to show all recordings in the folder.
        """
        self.side_list.clear()
        file_names = self._get_recording_files()
        self.side_list.addItems(file_names)

# Main window
if __name__ == "__main__":
    app = App.create()
    app.run()

