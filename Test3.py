import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QListWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from pass60 import ClipboardGeminiTool  # <- adjust if file renamed


class GeminiWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, tool: ClipboardGeminiTool):
        super().__init__()
        self.tool = tool

    def run(self):
        response = self.tool.send_to_gemini()
        self.finished.emit(response if response else "❌ Failed to get response from Gemini.")


class GeminiGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI ClipBoard 60")
        self.setGeometry(300, 100, 380, 700)
        self.setStyleSheet("background-color: #2e2e2e; color: #FFD43B; font-family: Altone-Trial;")

        self.tool = ClipboardGeminiTool()

        # Set up hotkeys for the tool (this was missing!)
        self.tool.setup_hotkeys()

        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: #2e2e2e;")

        # Create main widget for scroll area
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # Add spacing between sections

        # Title
        title = QLabel("AI ClipBoard 60")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("margin: 10px 0px;")
        main_layout.addWidget(title)

        # Status indicator
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #90EE90; margin: 5px 0px;")
        main_layout.addWidget(self.status_label)

        # Clipboard frame (buffer + buttons)
        buffer_frame = QFrame()
        buffer_frame.setStyleSheet(
            "background-color: #1e1e1e; border: 2px solid #FFD43B; "
            "border-radius: 12px; padding: 15px; margin: 5px;"
        )
        buffer_layout = QVBoxLayout()

        buffer_title = QLabel("Clipboard Buffer")
        buffer_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        buffer_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buffer_layout.addWidget(buffer_title)

        self.buffer_list = QListWidget()
        self.buffer_list.setStyleSheet(
            "background-color: #1e1e1e; color: white; border: none; "
            "min-height: 120px; max-height: 120px;"
        )
        buffer_layout.addWidget(self.buffer_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Clipboard")
        add_btn.setStyleSheet(
            "background-color: #FFD43B; color: black; padding: 8px 12px; "
            "border-radius: 8px; font-weight: bold;"
        )
        add_btn.clicked.connect(self.add_to_buffer)
        btn_row.addWidget(add_btn)

        clear_btn = QPushButton("Clear Buffer")
        clear_btn.setStyleSheet(
            "background-color: #FF6B6B; color: white; padding: 8px 12px; "
            "border-radius: 8px; font-weight: bold;"
        )
        clear_btn.clicked.connect(self.clear_buffer)
        btn_row.addWidget(clear_btn)

        buffer_layout.addLayout(btn_row)
        buffer_frame.setLayout(buffer_layout)
        main_layout.addWidget(buffer_frame)

        # Shortcuts Panel - Fixed with actual shortcuts displayed
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet(
            "background-color: #3e3e3e; border-radius: 10px; padding: 15px; margin: 5px;"
        )
        sc_layout = QVBoxLayout()

        sc_title = QLabel("Keyboard Shortcuts")
        sc_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sc_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sc_layout.addWidget(sc_title)

        # Create shortcuts grid with actual shortcuts
        shortcuts = [
            ("Start Collecting", "Ctrl+Shift+S"),
            ("Input Mode", "Ctrl+Shift+Q"),
            ("Add to Buffer", "Ctrl+Shift+A"),
            ("Get Response", "Ctrl+Enter"),
            ("Stop & Add Input", "Ctrl+Shift+W"),
            ("Clear Buffer", "Ctrl+Shift+X"),
            ("Paste Response", "Ctrl+L"),
            ("Type Response", "Ctrl+Shift+L"),
            ("Pause Typing", "Ctrl+P"),
            ("Stop Typing", "Ctrl+Shift+Z"),
            ("Speed Up", "Shift+F"),
            ("Speed Down", "Shift+S"),
            ("Reset Speed", "Shift+R"),
            ("Show Status", "Ctrl+Shift+H"),
            ("Exit", "Esc"),
        ]

        # Create shortcuts in a more compact way
        for i in range(0, len(shortcuts), 1):
            shortcut_row = QHBoxLayout()
            shortcut_row.setSpacing(5)

            action_label = QLabel(shortcuts[i][0])
            action_label.setStyleSheet("color: #FFD43B; font-size: 11px;")
            action_label.setMinimumWidth(120)
            shortcut_row.addWidget(action_label)

            key_label = QLabel(shortcuts[i][1])
            key_label.setStyleSheet(
                "background-color: #555; color: white; padding: 2px 6px; "
                "border-radius: 4px; font-size: 10px; font-family: monospace;"
            )
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            shortcut_row.addWidget(key_label)

            sc_layout.addLayout(shortcut_row)

        shortcuts_frame.setLayout(sc_layout)
        main_layout.addWidget(shortcuts_frame)

        # Response box
        response_frame = QFrame()
        response_frame.setStyleSheet(
            "background-color: #1e1e1e; border: 2px solid #FFD43B; "
            "border-radius: 12px; padding: 15px; margin: 5px;"
        )
        response_layout = QVBoxLayout()

        response_title = QLabel("AI Response")
        response_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        response_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        response_layout.addWidget(response_title)

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet(
            "background-color: #1e1e1e; color: white; border: none; "
            "min-height: 150px; max-height: 200px;"
        )
        self.response_box.setPlainText("No response yet. Add items to buffer and click 'Get Response'.")
        response_layout.addWidget(self.response_box)

        # Response action buttons
        resp_btn_row = QHBoxLayout()
        get_resp_btn = QPushButton("Get Response")
        get_resp_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px 12px; "
            "border-radius: 8px; font-weight: bold;"
        )
        get_resp_btn.clicked.connect(self.get_response)
        resp_btn_row.addWidget(get_resp_btn)

        paste_btn = QPushButton("Paste Response")
        paste_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 8px 12px; "
            "border-radius: 8px; font-weight: bold;"
        )
        paste_btn.clicked.connect(self.paste_response)
        resp_btn_row.addWidget(paste_btn)

        type_btn = QPushButton("Type Response")
        type_btn.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 8px 12px; "
            "border-radius: 8px; font-weight: bold;"
        )
        type_btn.clicked.connect(self.type_response)
        resp_btn_row.addWidget(type_btn)

        response_layout.addLayout(resp_btn_row)
        response_frame.setLayout(response_layout)
        main_layout.addWidget(response_frame)

        # Bottom control buttons - Fixed positioning
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("margin: 10px 5px;")
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        start_btn = QPushButton("🚀 Start Collecting")
        start_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        start_btn.setStyleSheet(
            "background-color: #FFD43B; color: black; padding: 15px 20px; "
            "border-radius: 18px; min-height: 25px;"
        )
        start_btn.clicked.connect(self.start_collecting)
        bottom_layout.addWidget(start_btn)

        stop_btn = QPushButton("🛑 Stop & Exit")
        stop_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stop_btn.setStyleSheet(
            "background-color: #F44336; color: white; padding: 15px 20px; "
            "border-radius: 18px; min-height: 25px;"
        )
        stop_btn.clicked.connect(self.stop_tool)
        bottom_layout.addWidget(stop_btn)

        bottom_frame.setLayout(bottom_layout)
        main_layout.addWidget(bottom_frame)

        # Set up the scroll area
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)

        # Set the scroll area as the main layout
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(scroll_area)
        self.setLayout(window_layout)

        # Set up timer to refresh UI periodically
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_ui)
        self.refresh_timer.start(1000)  # Refresh every second

    def start_collecting(self):
        """Start the collecting mode"""
        self.tool.start_collecting()
        self.status_label.setText("Status: Collecting (Auto-copy mode active)")
        self.status_label.setStyleSheet("color: #90EE90; margin: 5px 0px;")
        self.refresh_ui()

    def add_to_buffer(self):
        """Add current clipboard content to buffer"""
        self.tool.add_to_buffer()
        self.refresh_ui()

    def clear_buffer(self):
        """Clear the buffer"""
        self.tool.clear_buffer()
        self.status_label.setText("Status: Buffer cleared")
        self.refresh_ui()

    def get_response(self):
        """Get response from Gemini"""
        if not self.tool.clipboard_buffer:
            self.response_box.setPlainText("❌ No items in buffer. Add some items first!")
            return

        self.response_box.setPlainText("🤖 Getting response from Gemini...")
        self.status_label.setText("Status: Processing with AI...")
        self.status_label.setStyleSheet("color: #FFA500; margin: 5px 0px;")

        # Run Gemini request in separate thread
        self.worker = GeminiWorker(self.tool)
        self.worker.finished.connect(self.show_response)
        self.worker.start()

    def show_response(self, response):
        """Display the response from Gemini"""
        self.tool.current_response = response
        self.response_box.setPlainText(response)
        self.status_label.setText("Status: Response ready")
        self.status_label.setStyleSheet("color: #90EE90; margin: 5px 0px;")

    def paste_response(self):
        """Paste the response using the tool's paste function"""
        if not self.tool.current_response:
            self.response_box.setPlainText("❌ No response available to paste!")
            return
        self.tool.paste_response()

    def type_response(self):
        """Type the response using the tool's type function"""
        if not self.tool.current_response:
            self.response_box.setPlainText("❌ No response available to type!")
            return
        self.tool.type_response()

    def stop_tool(self):
        """Stop the tool and close the application"""
        self.refresh_timer.stop()
        self.tool.exit_program()
        self.close()

    def refresh_ui(self):
        """Refresh the UI with current buffer contents"""
        self.buffer_list.clear()
        if self.tool.clipboard_buffer:
            for i, item in enumerate(self.tool.clipboard_buffer, 1):
                preview = item[:60] + "..." if len(item) > 60 else item
                self.buffer_list.addItem(f"{i}. {preview}")
        else:
            self.buffer_list.addItem("No items in buffer")

        # Update status based on tool state
        if self.tool.collecting:
            if not self.status_label.text().startswith("Status: Processing"):
                self.status_label.setText("Status: Collecting (Auto-copy mode active)")
                self.status_label.setStyleSheet("color: #90EE90; margin: 5px 0px;")
        elif self.tool.typing_in_progress:
            progress = (self.tool.current_char_index / len(
                self.tool.current_response)) * 100 if self.tool.current_response else 0
            self.status_label.setText(f"Status: Typing response ({progress:.1f}%)")
            self.status_label.setStyleSheet("color: #FFA500; margin: 5px 0px;")

    def closeEvent(self, event):
        """Handle window close event"""
        self.refresh_timer.stop()
        self.tool.exit_program()
        event.accept()


def main():
    app = QApplication(sys.argv)
    gui = GeminiGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()