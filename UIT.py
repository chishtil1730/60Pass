import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QListWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from pass60 import ClipboardGeminiTool


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
        self.setGeometry(300, 100, 360, 620)
        self.setStyleSheet("background-color: #2e2e2e; color: #FFD43B; font-family: Arial;")

        self.tool = ClipboardGeminiTool()

        # Set up hotkeys for the tool
        self.tool.setup_hotkeys()

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Create widget to hold content
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Title
        title = QLabel("AI ClipBoard 60")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        # Clipboard frame (buffer + buttons)
        buffer_frame = QFrame()
        buffer_frame.setStyleSheet(
            "background-color: #1e1e1e; border: 2px solid #FFD43B; "
            "border-radius: 12px; padding: 10px;"
        )
        buffer_layout = QVBoxLayout()

        self.buffer_list = QListWidget()
        self.buffer_list.setStyleSheet("background-color: #1e1e1e; color: white; border: none;")
        self.buffer_list.setMaximumHeight(80)
        buffer_layout.addWidget(self.buffer_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet("background-color: #FFD43B; color: black; padding: 8px; border-radius: 12px;")
        add_btn.clicked.connect(self.add_to_buffer)
        btn_row.addWidget(add_btn)

        resp_btn = QPushButton("Get Response")
        resp_btn.setStyleSheet("background-color: #555; color: white; padding: 8px; border-radius: 12px;")
        resp_btn.clicked.connect(self.get_response)
        btn_row.addWidget(resp_btn)
        buffer_layout.addLayout(btn_row)

        buffer_frame.setLayout(buffer_layout)

        # Store button references
        self.add_btn = add_btn
        self.resp_btn = resp_btn
        content_layout.addWidget(buffer_frame)

        # Start/Stop buttons
        start_stop_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("background-color: #FFD43B; color: black; padding: 14px; border-radius: 18px;")
        self.start_btn.clicked.connect(self.start_collecting)
        start_stop_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("background-color: #FFD43B; color: black; padding: 14px; border-radius: 18px;")
        self.stop_btn.clicked.connect(self.stop_tool)
        start_stop_row.addWidget(self.stop_btn)
        content_layout.addLayout(start_stop_row)

        # Shortcuts Panel
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet("background-color: #3e3e3e; border-radius: 10px; padding: 10px;")
        sc_layout = QVBoxLayout()

        sc_title = QLabel("Shortcuts")
        sc_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        sc_layout.addWidget(sc_title)

        shortcuts = [
            ("Start", "Ctrl+Shift+S"),
            ("Stop Type", "Ctrl+Shift+Z"),
            ("Typing Input", "Ctrl+Shift+Q"),
            ("Stop Typing", "Ctrl+Shift+E"),
            ("Add Item", "Ctrl+Shift+A"),
            ("Get Response", "Ctrl+Enter"),
            ("Clear", "Ctrl+Shift+X"),
            ("Paste", "Ctrl+L"),
            ("Paste by Typing", "Ctrl+Shift+L"),
            ("Pause", "Ctrl+Shift+P"),
            ("Type Fast", "Ctrl+Shift+F")
        ]

        for i in range(0, len(shortcuts), 2):
            row = QHBoxLayout()
            for j in range(2):
                if i + j < len(shortcuts):
                    btn_container = QVBoxLayout()
                    btn_container.setSpacing(2)

                    btn = QPushButton(shortcuts[i + j][0])
                    btn.setStyleSheet(
                        "background-color: #555; color: #FFD43B; "
                        "padding: 6px 12px; border-radius: 12px;"
                    )
                    btn.setEnabled(False)
                    shortcut_label = QLabel(shortcuts[i + j][1])
                    shortcut_label.setStyleSheet("color: #AAA; font-size: 9px;")
                    shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    btn_container.addWidget(btn)
                    btn_container.addWidget(shortcut_label)
                    row.addLayout(btn_container)
            sc_layout.addLayout(row)

        shortcuts_frame.setLayout(sc_layout)
        content_layout.addWidget(shortcuts_frame)

        # Response box
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet("background-color: #1e1e1e; color: white; border-radius: 8px;")
        self.response_box.setMaximumHeight(120)
        content_layout.addWidget(self.response_box)

        # Set content widget layout and add to scroll area
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

        # Set up timer to refresh UI periodically
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_ui)
        self.refresh_timer.start(1000)

        # Flag to track if we've already pasted for current response
        self.response_pasted = False

    def start_collecting(self):
        self.tool.start_collecting()
        self.update_button_states()
        self.refresh_ui()

    def add_to_buffer(self):
        self.tool.add_to_buffer()
        self.update_button_states()
        self.refresh_ui()

    def get_response(self):
        if not self.tool.clipboard_buffer:
            self.response_box.setPlainText("No items in buffer. Add some items first!")
            return

        self.response_box.setPlainText("Getting response from Gemini...")
        self.resp_btn.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 8px; border-radius: 12px;")

        self.worker = GeminiWorker(self.tool)
        self.worker.finished.connect(self.show_response)
        self.worker.start()

    def show_response(self, response):
        """Handle response from Gemini and auto-paste notification"""
        self.tool.current_response = response
        self.response_box.setPlainText(response)
        self.update_button_states()

        # Trigger auto-paste only once, right here when response arrives
        QTimer.singleShot(500, self.rsp_ready)

    def rsp_ready(self):
        """Auto-paste 'response ready' notification"""
        import pyautogui, pyperclip
        try:
            print("Auto-pasting 'response ready'...")
            prev_clip = pyperclip.paste()  # Save current clipboard
            pyperclip.copy("response ready")  # Copy our message
            pyautogui.hotkey("ctrl", "v")  # Simulate paste (Ctrl+V)
            pyperclip.copy(prev_clip)  # Restore original clipboard
            print("Paste complete!")
        except Exception as e:
            print("Auto-paste failed:", e)

    def stop_tool(self):
        self.refresh_timer.stop()
        self.tool.exit_program()
        self.close()

    def update_button_states(self):
        """Update button colors based on current tool state"""
        # Update Start button
        if self.tool.collecting:
            self.start_btn.setText("🟢 Active")
            self.start_btn.setStyleSheet(
                "background-color: #4CAF50; color: white; padding: 14px; border-radius: 18px;")
        else:
            self.start_btn.setText("Start")
            self.start_btn.setStyleSheet(
                "background-color: #FFD43B; color: black; padding: 14px; border-radius: 18px;")

        # Update Get Response button and trigger auto-paste ONLY ONCE
        if self.tool.current_response:
            self.resp_btn.setText("Response Ready")

            # Only paste once per response
            if not self.response_pasted:
                self.response_pasted = True
                QTimer.singleShot(500, self.rsp_ready)

            self.resp_btn.setStyleSheet(
                "background-color: #4CAF50; color: white; padding: 8px; border-radius: 12px;")
        else:
            self.resp_btn.setText("Get Response")
            self.resp_btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 12px;")

        # Update Add button based on collecting state
        if self.tool.collecting:
            self.add_btn.setText("Auto-Adding")
            self.add_btn.setStyleSheet(
                "background-color: #2196F3; color: white; padding: 8px; border-radius: 12px;")
        else:
            self.add_btn.setText("Add")
            self.add_btn.setStyleSheet(
                "background-color: #FFD43B; color: black; padding: 8px; border-radius: 12px;")

    def refresh_ui(self):
        self.buffer_list.clear()
        for i, item in enumerate(self.tool.clipboard_buffer, 1):
            preview = item[:80] + "..." if len(item) > 80 else item
            self.buffer_list.addItem(f"{i}. {preview}")

        # Update button states whenever UI refreshes
        self.update_button_states()

    def closeEvent(self, event):
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