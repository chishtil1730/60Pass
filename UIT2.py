import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QListWidget, QScrollArea, QGraphicsBlurEffect,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor

from pass60 import ClipboardGeminiTool  # <- adjust if file renamed


class NotificationPopup(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.setStyleSheet("""
            QLabel {
                background: rgba(139, 92, 246, 0.95);
                color: white;
                padding: 20px 30px;
                border-radius: 15px;
                border: 2px solid rgba(167, 139, 250, 0.8);
            }
        """)
        self.hide()

        # Timer for auto-hide
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_notification)

    def show_notification(self, message, duration=2500):
        self.setText(message)
        self.adjustSize()

        # Center in parent
        if self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
            x = (parent_width - self.width()) // 2
            y = (parent_height - self.height()) // 2 - 50
            self.move(x, y)

        self.raise_()
        self.show()
        self.timer.start(duration)

    def hide_notification(self):
        self.timer.stop()
        self.hide()


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

        # Glassmorphism main window style with beautiful gradient
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(15, 23, 42, 240),
                    stop:0.5 rgba(30, 41, 59, 240),
                    stop:1 rgba(51, 65, 85, 240));
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial;
            }
        """)

        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

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
        scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 92, 246, 0.6);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(139, 92, 246, 0.8);
            }
        """)

        # Create widget to hold content
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Title with glass effect
        title = QLabel("AI ClipBoard 60")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid rgba(167, 139, 250, 0.3);
            border-radius: 15px;
            padding: 15px;
            color: #A78BFA;
            backdrop-filter: blur(10px);
        """)
        content_layout.addWidget(title)

        # Clipboard frame (buffer + buttons) - glassmorphism style
        buffer_frame = QFrame()
        buffer_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 15px;
                padding: 15px;
                backdrop-filter: blur(10px);
            }
        """)
        buffer_layout = QVBoxLayout()

        self.buffer_list = QListWidget()
        self.buffer_list.setStyleSheet("""
            QListWidget {
                background: rgba(0, 0, 0, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background: rgba(139, 92, 246, 0.2);
            }
        """)
        self.buffer_list.setMaximumHeight(80)
        buffer_layout.addWidget(self.buffer_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(139, 92, 246, 0.3);
                color: white;
                padding: 10px;
                border: 1px solid rgba(167, 139, 250, 0.5);
                border-radius: 12px;
                font-weight: bold;
                backdrop-filter: blur(10px);
            }
            QPushButton:hover {
                background: rgba(139, 92, 246, 0.5);
            }
            QPushButton:pressed {
                background: rgba(139, 92, 246, 0.7);
            }
        """)
        add_btn.clicked.connect(self.add_to_buffer)
        btn_row.addWidget(add_btn)

        resp_btn = QPushButton("Get Response")
        resp_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                font-weight: bold;
                backdrop-filter: blur(10px);
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.35);
            }
        """)
        resp_btn.clicked.connect(self.get_response)
        btn_row.addWidget(resp_btn)
        buffer_layout.addLayout(btn_row)

        buffer_frame.setLayout(buffer_layout)

        # Store button references for state changes
        self.add_btn = add_btn
        self.resp_btn = resp_btn
        content_layout.addWidget(buffer_frame)

        # Start/Stop buttons - glassmorphism style
        start_stop_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: rgba(139, 92, 246, 0.4);
                color: white;
                padding: 14px;
                border: 2px solid rgba(167, 139, 250, 0.6);
                border-radius: 18px;
                backdrop-filter: blur(10px);
            }
            QPushButton:hover {
                background: rgba(139, 92, 246, 0.6);
                border: 2px solid rgba(167, 139, 250, 0.8);
            }
        """)
        self.start_btn.clicked.connect(self.start_collecting)
        start_stop_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: rgba(244, 63, 94, 0.3);
                color: white;
                padding: 14px;
                border: 2px solid rgba(251, 113, 133, 0.5);
                border-radius: 18px;
                backdrop-filter: blur(10px);
            }
            QPushButton:hover {
                background: rgba(244, 63, 94, 0.5);
                border: 2px solid rgba(251, 113, 133, 0.7);
            }
        """)
        self.stop_btn.clicked.connect(self.stop_tool)
        start_stop_row.addWidget(self.stop_btn)
        content_layout.addLayout(start_stop_row)

        # Shortcuts Panel - glassmorphism style
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 15px;
                backdrop-filter: blur(10px);
            }
        """)
        sc_layout = QVBoxLayout()

        sc_title = QLabel("Shortcuts")
        sc_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        sc_title.setStyleSheet("color: #C4B5FD; background: transparent; border: none;")
        sc_layout.addWidget(sc_title)

        # Shortcuts in original 2x2 grid format with actual shortcuts shown
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

        # Create 2x2 grid layout like original
        for i in range(0, len(shortcuts), 2):
            row = QHBoxLayout()
            for j in range(2):
                if i + j < len(shortcuts):
                    btn_container = QVBoxLayout()
                    btn_container.setSpacing(2)

                    btn = QPushButton(shortcuts[i + j][0])
                    btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(255, 255, 255, 0.08);
                            color: #DDD6FE;
                            padding: 8px 12px;
                            border: 1px solid rgba(167, 139, 250, 0.3);
                            border-radius: 10px;
                            backdrop-filter: blur(5px);
                        }
                    """)
                    btn.setEnabled(False)  # display-only

                    shortcut_label = QLabel(shortcuts[i + j][1])
                    shortcut_label.setStyleSheet("""
                        color: rgba(255, 255, 255, 0.6);
                        font-size: 9px;
                        background: transparent;
                        border: none;
                    """)
                    shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    btn_container.addWidget(btn)
                    btn_container.addWidget(shortcut_label)
                    row.addLayout(btn_container)
            sc_layout.addLayout(row)

        shortcuts_frame.setLayout(sc_layout)
        content_layout.addWidget(shortcuts_frame)

        # Response box - glassmorphism style
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 10px;
                backdrop-filter: blur(10px);
            }
        """)
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
        self.refresh_timer.start(1000)  # Refresh every second

        # Create notification popup
        self.notification = NotificationPopup(self)

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

        # Show notification for sending to AI
        self.notification.show_notification("📤 Response sent to AI...", 2500)

        self.response_box.setPlainText("Getting response from Gemini...")
        self.resp_btn.setStyleSheet("""
            QPushButton {
                background: rgba(251, 146, 60, 0.4);
                color: white;
                padding: 10px;
                border: 1px solid rgba(253, 186, 116, 0.6);
                border-radius: 12px;
                font-weight: bold;
                backdrop-filter: blur(10px);
            }
        """)
        self.worker = GeminiWorker(self.tool)
        self.worker.finished.connect(self.show_response)
        self.worker.start()

    def show_response(self, response):
        self.tool.current_response = response
        self.response_box.setPlainText(response)
        self.update_button_states()

        # Show notification for response ready
        self.notification.show_notification("✅ Response ready to paste!", 3000)

    def stop_tool(self):
        self.refresh_timer.stop()
        self.tool.exit_program()
        self.close()

    def update_button_states(self):
        """Update button colors based on current tool state"""
        # Update Start button
        if self.tool.collecting:
            self.start_btn.setText("🟢 Active")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(34, 197, 94, 0.4);
                    color: white;
                    padding: 14px;
                    border: 2px solid rgba(74, 222, 128, 0.6);
                    border-radius: 18px;
                    backdrop-filter: blur(10px);
                }
            """)
        else:
            self.start_btn.setText("Start")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(139, 92, 246, 0.4);
                    color: white;
                    padding: 14px;
                    border: 2px solid rgba(167, 139, 250, 0.6);
                    border-radius: 18px;
                    backdrop-filter: blur(10px);
                }
                QPushButton:hover {
                    background: rgba(139, 92, 246, 0.6);
                    border: 2px solid rgba(167, 139, 250, 0.8);
                }
            """)

        # Update Get Response button
        if self.tool.current_response:
            self.resp_btn.setText("Response Ready")
            self.resp_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(34, 197, 94, 0.4);
                    color: white;
                    padding: 10px;
                    border: 1px solid rgba(74, 222, 128, 0.6);
                    border-radius: 12px;
                    font-weight: bold;
                    backdrop-filter: blur(10px);
                }
            """)
        else:
            self.resp_btn.setText("Get Response")
            self.resp_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.15);
                    color: white;
                    padding: 10px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 12px;
                    font-weight: bold;
                    backdrop-filter: blur(10px);
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.25);
                }
            """)

        # Update Add button based on collecting state
        if self.tool.collecting:
            self.add_btn.setText("Auto-Adding")
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(59, 130, 246, 0.4);
                    color: white;
                    padding: 10px;
                    border: 1px solid rgba(96, 165, 250, 0.6);
                    border-radius: 12px;
                    font-weight: bold;
                    backdrop-filter: blur(10px);
                }
            """)
        else:
            self.add_btn.setText("Add")
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(139, 92, 246, 0.3);
                    color: white;
                    padding: 10px;
                    border: 1px solid rgba(167, 139, 250, 0.5);
                    border-radius: 12px;
                    font-weight: bold;
                    backdrop-filter: blur(10px);
                }
                QPushButton:hover {
                    background: rgba(139, 92, 246, 0.5);
                }
            """)

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