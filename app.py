import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt 
from record import Recorder

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.recorder = Recorder.create()
        self.paused = False
    
    @staticmethod
    def create():
        app = App()
        app.create_layout()
        return app

    def on_start_button_click(self):
        if not self.paused:
            self.main_label.setText("")
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
        self.window.setFixedSize(500, 300)

        # Main vertical layout (top + bottom)
        self.main_layout = QVBoxLayout()

        # Top container (main content)
        self.top_container = QVBoxLayout()
        self.main_label = QLabel("")
        self.main_label.setWordWrap(True)
        self.main_label.setFixedWidth(450)
        self.top_container.addWidget(self.main_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

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

        # Connect signals
        self.start_button.clicked.connect(self.on_start_button_click)
        self.stop_button.clicked.connect(self.on_stop_button_click)
        self.pause_button.clicked.connect(self.on_pause_button_click)

        # Add buttons to bottom container
        self.bottom_container.addWidget(self.start_button)
        self.bottom_container.addWidget(self.pause_button)
        self.bottom_container.addWidget(self.stop_button)

        # Add top and bottom containers to the main layout
        self.main_layout.addLayout(self.top_container)
        self.main_layout.addLayout(self.bottom_container)

        # Set the layout for the window
        self.window.setLayout(self.main_layout)
    
    def run(self):
        # Show the window
        self.window.show()
        # Run the event loop
        sys.exit(self.app.exec())

# Main window
if __name__ == "__main__":
    app = App.create()
    app.run()

