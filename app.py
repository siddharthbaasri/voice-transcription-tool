import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem, QPushButton
from PyQt6.QtWidgets import QLabel, QListWidget, QSizePolicy, QMenu, QMessageBox, QInputDialog, QStyle
from PyQt6.QtCore import Qt, QSize
from record import Recorder
from pathlib import Path
from datetime import datetime

class RecordingItemWidget(QWidget):
    def __init__(self, text, menu_callback):
        super().__init__()

        self.text = text
        self.menu_callback = menu_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)

        self.label = QLabel(text)
        self.label.setStyleSheet("""
            background-color: #FFFFFF;  /* white background */
            color: #1C1C1E;             /* dark text */
            padding-left: 4px;
        """)

        self.menu_button = QPushButton("⋯")
        # Slightly larger clickable area and clear hover state for visibility
        self.menu_button.setFixedSize(28, 28)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setToolTip("More options")
        self.menu_button.setAccessibleName("Recording options")
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1C1C1E;
                font-size: 16px;
                font-weight: 700;
                border: none;
                padding: 0px;
                margin: 0px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.06);
            }
            QPushButton:pressed {
                background-color: rgba(0,0,0,0.10);
            }
        """)

        self.menu_button.clicked.connect(self._show_menu)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.menu_button)

    def _show_menu(self):
        self.menu_callback(self)

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
            self.transcription_file = self.root_dir / f"rec_{timestamp}.txt"
        
        self.paused = False
        #Set button visibilities.
        self.resume_button.setHidden(True)
        self.pause_button.setHidden(False)
        self.stop_button.setHidden(False)
        self.side_record_button.setHidden(True)

        threading.Thread(target=lambda: self.recorder.record(self.update_text), daemon=True).start()

    def on_stop_button_click(self):
        self.recorder.stop_recording()
        self.paused = False

        #Set button visibilities.
        self.resume_button.setHidden(True)
        self.stop_button.setHidden(True)
        self.pause_button.setHidden(True)
        self.side_record_button.setHidden(False)

        #Save to documents folder here
        # Write current transcription text to the known transcription file
        text = self.main_label.text()
        self.transcription_file.write_text(text or "", encoding="utf-8")
        #Refresh sidebar to show updated file list
        self._refresh_sidebar()

        self.main_label.setText("")

    
    def on_pause_button_click(self):
        self.recorder.stop_recording()
        self.paused = True
        self.resume_button.setHidden(False)
        self.pause_button.setHidden(True)

    def update_text(self, text):
        current_text = self.main_label.text()
        if current_text:
            current_text += text
        else:
            current_text = text
        self.main_label.setText(current_text)
    
    def load_recording(self, item):
        """
        Load the contents of the clicked recording into the main label.
        """
        # Build the full path
        if self.paused:
            return

        file_path = self.root_dir / item.text()
        
        if file_path.exists() and file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            self.main_label.setText(text)
        else:
            self.main_label.setText("Error: File not found")
    
    def _show_menu_for_name(self, file_name, widget):
        menu = QMenu(self.window)

        delete_action = menu.addAction("Delete Recording")
        rename_action = menu.addAction("Rename Recording")

        # Style the menu to have a visible border and match the light theme
        menu.setStyleSheet("""
            QMenu { border: 1px solid #D1D1D6; background-color: #FFFFFF; padding: 4px; }
            QMenu::item { color: #1C1C1E; padding: 6px 18px; }
            QMenu::item:selected { background-color: #E8F0FF; color: #0A62D8; }
        """)

        button_pos = widget.menu_button.mapToGlobal(
            widget.menu_button.rect().bottomRight()
        )

        action = menu.exec(button_pos)

        fake_item = QListWidgetItem(file_name)

        if action == delete_action:
            self._delete_recording(fake_item)
        elif action == rename_action:
            self._rename_recording(fake_item)
    
    def _delete_recording(self, item):
        file_path = self.root_dir / item.text()
        if file_path.exists():
            # Build a custom QMessageBox so we can use a white question-mark icon
            msg = QMessageBox(self.window)
            msg.setWindowTitle("Confirm Delete")
            msg.setText(f"Are you sure you want to delete '{item.text()}'?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            # Do not show an icon in the confirmation dialog (cleaner on dark theme)
            msg.setIcon(QMessageBox.Icon.NoIcon)
            result = msg.exec()

            if result == QMessageBox.StandardButton.Yes:
                if self.main_label.text() == file_path.read_text(encoding="utf-8"):
                    self.main_label.setText("")
                file_path.unlink()  # Delete file
                self._refresh_sidebar()
                # Optionally clear main label if the deleted file was loaded
    
    def _rename_recording(self, item):
        old_file = self.root_dir / item.text()
        if not old_file.exists():
            return

        new_name, ok = QInputDialog.getText(
            self.window,
            "Rename Recording",
            "Enter new file name (without extension):",
            text=old_file.stem
        )
        if ok and new_name.strip():
            new_file = self.root_dir / f"{new_name.strip()}.txt"
            if new_file.exists():
                QMessageBox.warning(self.window, "Error", "File with this name already exists!")
                return
            old_file.rename(new_file)
            self._refresh_sidebar()
    
    def create_layout(self):
        self.window = QWidget()
        self.window.setWindowTitle("AI-powered voice recorder")
        # Use a default mac-like app window size and allow resizing
        self.window.resize(900, 600)
        self.window.setMinimumSize(700, 400)

        # Main horizontal layout: side panel + center panel
        self.main_layout = QHBoxLayout()

        # --- Side panel (similar width to mac Voice Memos list) ---
        self.side_panel = QVBoxLayout()
        side_header = QLabel("Recordings")
        side_header.setStyleSheet("font-weight: 600; padding: 6px 8px; color: #1C1C1E;")
        self.side_list = QListWidget()
        self.side_list.setFixedWidth(260)
        self._refresh_sidebar()
        self.side_list.itemClicked.connect(self.load_recording)
        self.side_list.setMinimumHeight(400)
        self.side_list.setMaximumHeight(700)
        self.side_panel.addWidget(side_header)
        self.side_panel.addWidget(self.side_list)
        
        # Add spacer and a bottom-aligned "Record" button in the side panel
        self.side_panel.addStretch()
        self.side_record_button = QPushButton("Record")
        self.side_record_button.setObjectName("side_record_button")
        # Make the button visually slightly inset compared to the list width
        self.side_record_button.setMaximumWidth(220)
        self.side_panel.addWidget(self.side_record_button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self.side_record_button.clicked.connect(self.on_start_button_click)

        self._create_record_panel()

        # Add side panel and center panel to main layout
        self.main_layout.addLayout(self.side_panel)
        self.main_layout.addLayout(self.center_panel)

        # Apply a light mac-like color scheme
        self.window.setStyleSheet("""
        /* Light theme inspired by macOS Light Mode */
        QWidget { background-color: #F2F2F5; color: #1C1C1E; }
        QLabel#main_label { background-color: #FFFFFF; border-radius: 8px; padding: 12px; color: #1C1C1E; }
        QLabel { color: #1C1C1E; }
        QListWidget { 
            background-color: #FFFFFF;  /* white background for list itself */
            border-radius: 8px; 
            padding: 0px;  /* remove extra padding if any */
        }
        QListWidget::item { 
            background-color: #FFFFFF;  /* white background for items */
            border: none;
        }
        QListWidget::item:selected { 
            background-color: #E8F0FF; 
            color: #0A62D8; 
        }
        QPushButton { background-color: #0A84FF; color: white; border: none; padding: 6px 12px; border-radius: 8px; }
        QPushButton#stop_button { background-color: #FF3B30; }
        QPushButton#pause_button { background-color: #FF9F0A; color: #1C1C1E; }
        QPushButton:disabled { background-color: #D1D1D6; color: #8E8E93; }
        QPushButton#side_record_button { background-color: #30D158; color: #FFFFFF; border: none; padding: 6px 12px; border-radius: 10px; }
        """)


        # Set the layout for the window
        self.window.setLayout(self.main_layout)
    
    def _create_record_panel(self):
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
        #Create buttons for pause, resume and stop which are hidden at first
        self.resume_button = QPushButton("Resume Recording")
        self.pause_button = QPushButton("Pause Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.pause_button.setHidden(True)
        self.resume_button.setHidden(True)
        self.stop_button.setHidden(True)

        # Set the size of the buttons
        self.resume_button.setMaximumSize(150, 30)
        self.stop_button.setMaximumSize(150, 30)
        self.pause_button.setMaximumSize(150, 30)

        # Set object names for styling
        self.resume_button.setObjectName("start_button")
        self.stop_button.setObjectName("stop_button")
        self.pause_button.setObjectName("pause_button")

        # Connect signals
        self.resume_button.clicked.connect(self.on_start_button_click)
        self.stop_button.clicked.connect(self.on_stop_button_click)
        self.pause_button.clicked.connect(self.on_pause_button_click)

        # Add buttons to bottom container
        self.bottom_container.addWidget(self.resume_button)
        self.bottom_container.addWidget(self.pause_button)
        self.bottom_container.addWidget(self.stop_button)

        # Add bottom container to center panel
        self.center_panel.addLayout(self.bottom_container)
        return self.center_panel
    
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
        self.side_list.clear()

        for file_name in self._get_recording_files():
            item = QListWidgetItem(file_name)
            item.setSizeHint(QSize(240, 36))

            widget = RecordingItemWidget(
                file_name,
                lambda w, name=file_name: self._show_menu_for_name(name, w)
            )

            self.side_list.addItem(item)
            self.side_list.setItemWidget(item, widget)

# Main window
if __name__ == "__main__":
    app = App.create()
    app.run()

