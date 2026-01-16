import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QListWidget, QGraphicsDropShadowEffect
)

from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon


from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

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
        self.setGeometry(100, 200, 650, 380)

        # Initialize border colors
        self.hue = 0

        # Main container for border effect
        self.setStyleSheet("background: transparent;")

        main_container = QWidget()
        main_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29,
                    stop:0.5 #302b63,
                    stop:1 #24243e
                );
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-radius: 15px;
            }
        """)

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        main_container.setLayout(container_layout)

        self.tool = ClipboardGeminiTool()
        self.tool.setup_hotkeys()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        # Title with glow effect
        title = QLabel("AI ClipBoard 60")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea,
                stop:1 #764ba2
            );
            padding: 8px;
        """)

        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(20)
        title_shadow.setColor(QColor(102, 126, 234, 180))
        title_shadow.setOffset(0, 0)
        title.setGraphicsEffect(title_shadow)
        left_column.addWidget(title)

        # Glassmorphic clipboard frame
        buffer_frame = QFrame()
        buffer_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                padding: 12px;
            }
        """)

        frame_shadow = QGraphicsDropShadowEffect()
        frame_shadow.setBlurRadius(25)
        frame_shadow.setColor(QColor(0, 0, 0, 100))
        frame_shadow.setOffset(0, 4)
        buffer_frame.setGraphicsEffect(frame_shadow)

        buffer_layout = QVBoxLayout()

        buffer_label = QLabel("Clipboard Buffer")
        buffer_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        buffer_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); padding: 3px;")
        buffer_layout.addWidget(buffer_label)

        self.buffer_list = QListWidget()
        self.buffer_list.setStyleSheet("""
            QListWidget {
                background: rgba(0, 0, 0, 0.3);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px;
                font-size: 9px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: rgba(102, 126, 234, 0.3);
            }
        """)
        self.buffer_list.setMinimumHeight(90)
        self.buffer_list.setMaximumHeight(100)
        buffer_layout.addWidget(self.buffer_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        add_btn = QPushButton("Add")
        add_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
                color: white;
                padding: 8px 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2,
                    stop:1 #667eea
                );
            }
        """)
        add_btn.clicked.connect(self.add_to_buffer)

        add_shadow = QGraphicsDropShadowEffect()
        add_shadow.setBlurRadius(12)
        add_shadow.setColor(QColor(102, 126, 234, 150))
        add_shadow.setOffset(0, 2)
        add_btn.setGraphicsEffect(add_shadow)
        btn_row.addWidget(add_btn)

        resp_btn = QPushButton("Get Response")
        resp_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        resp_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 8px 16px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        resp_btn.clicked.connect(self.get_response)
        btn_row.addWidget(resp_btn)
        buffer_layout.addLayout(btn_row)

        buffer_frame.setLayout(buffer_layout)
        self.add_btn = add_btn
        self.resp_btn = resp_btn
        left_column.addWidget(buffer_frame)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #11998e,
                    stop:1 #38ef7d
                );
                color: white;
                padding: 12px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38ef7d,
                    stop:1 #11998e
                );
            }
        """)
        self.start_btn.clicked.connect(self.start_collecting)

        start_shadow = QGraphicsDropShadowEffect()
        start_shadow.setBlurRadius(15)
        start_shadow.setColor(QColor(56, 239, 125, 150))
        start_shadow.setOffset(0, 3)
        self.start_btn.setGraphicsEffect(start_shadow)
        bottom_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #eb3349,
                    stop:1 #f45c43
                );
                color: white;
                padding: 12px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f45c43,
                    stop:1 #eb3349
                );
            }
        """)
        self.stop_btn.clicked.connect(self.stop_tool)

        stop_shadow = QGraphicsDropShadowEffect()
        stop_shadow.setBlurRadius(15)
        stop_shadow.setColor(QColor(235, 51, 73, 150))
        stop_shadow.setOffset(0, 3)
        self.stop_btn.setGraphicsEffect(stop_shadow)
        bottom_row.addWidget(self.stop_btn)

        left_column.addLayout(bottom_row)
        main_layout.addLayout(left_column, 1)

        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(12)

        # Glassmorphic shortcuts panel
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                padding: 10px;
            }
        """)

        shortcuts_shadow = QGraphicsDropShadowEffect()
        shortcuts_shadow.setBlurRadius(25)
        shortcuts_shadow.setColor(QColor(0, 0, 0, 100))
        shortcuts_shadow.setOffset(0, 4)
        shortcuts_frame.setGraphicsEffect(shortcuts_shadow)

        sc_layout = QVBoxLayout()

        sc_title = QLabel("Shortcuts")
        sc_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        sc_title.setStyleSheet("""
            color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #f093fb,
                stop:1 #f5576c
            );
            padding: 3px;
        """)
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
        ]

        for i in range(0, len(shortcuts), 2):
            row = QHBoxLayout()
            row.setSpacing(6)
            for j in range(2):
                if i + j < len(shortcuts):
                    btn_container = QVBoxLayout()
                    btn_container.setSpacing(2)

                    btn = QPushButton(shortcuts[i + j][0])
                    btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(255, 255, 255, 0.08);
                            color: #e0e0e0;
                            padding: 6px 10px;
                            border-radius: 8px;
                            border: 1px solid rgba(255, 255, 255, 0.15);
                            font-size: 9px;
                        }
                    """)
                    btn.setEnabled(False)

                    shortcut_label = QLabel(shortcuts[i + j][1])
                    shortcut_label.setStyleSheet("""
                        color: rgba(255, 255, 255, 0.5);
                        font-size: 8px;
                    """)
                    shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    btn_container.addWidget(btn)
                    btn_container.addWidget(shortcut_label)
                    row.addLayout(btn_container)
            sc_layout.addLayout(row)

        shortcuts_frame.setLayout(sc_layout)
        right_column.addWidget(shortcuts_frame)

        # Glassmorphic response box
        response_container = QFrame()
        response_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                padding: 8px;
            }
        """)

        response_shadow = QGraphicsDropShadowEffect()
        response_shadow.setBlurRadius(25)
        response_shadow.setColor(QColor(0, 0, 0, 100))
        response_shadow.setOffset(0, 4)
        response_container.setGraphicsEffect(response_shadow)

        response_layout = QVBoxLayout()

        response_label = QLabel("AI Response")
        response_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        response_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); padding: 3px;")
        response_layout.addWidget(response_label)

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                font-size: 9px;
            }
        """)
        self.response_box.setMinimumHeight(70)
        self.response_box.setMaximumHeight(85)
        response_layout.addWidget(self.response_box)

        response_container.setLayout(response_layout)
        right_column.addWidget(response_container)

        main_layout.addLayout(right_column, 1)
        container_layout.addLayout(main_layout)

        # Outer layout with rainbow border
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.addWidget(main_container)
        self.setLayout(outer_layout)

        # Set up timers
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_ui)
        self.refresh_timer.start(1000)

        # Rainbow border animation
        self.border_timer = QTimer()
        self.border_timer.timeout.connect(self.animate_border)
        self.border_timer.start(50)



    def animate_border(self):
        """Animate rainbow border"""
        self.hue = (self.hue + 5) % 360
        color1 = QColor.fromHsv(self.hue, 255, 255)
        color2 = QColor.fromHsv((self.hue + 60) % 360, 255, 255)
        color3 = QColor.fromHsv((self.hue + 120) % 360, 255, 255)

        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color1.name()},
                    stop:0.5 {color2.name()},
                    stop:1 {color3.name()}
                );
                border-radius: 18px;
            }}
        """)

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

        # 🔔 Show popup when sending
        self.tray_icon.showMessage("Gemini", "✅ Sent to Gemini", QSystemTrayIcon.MessageIcon.Information)

        self.resp_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb,
                    stop:1 #f5576c
                );
                color: white;
                padding: 8px 16px;
                border-radius: 10px;
                border: none;
            }
        """)
        self.worker = GeminiWorker(self.tool)
        self.worker.finished.connect(self.show_response)
        self.worker.start()

    def show_response(self, response):
        self.tool.current_response = response
        self.response_box.setPlainText(response)

        # 🔔 Show popup when response is ready
        self.tray_icon.showMessage("Gemini", "✨ Response Ready", QSystemTrayIcon.MessageIcon.Information)

        self.update_button_states()

    def stop_tool(self):
        self.refresh_timer.stop()
        self.border_timer.stop()
        self.tool.exit_program()
        self.close()

    def update_button_states(self):
        """Update button colors based on current tool state"""
        if self.tool.collecting:
            self.start_btn.setText("🟢 Active")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #56ab2f,
                        stop:1 #a8e063
                    );
                    color: white;
                    padding: 12px;
                    border-radius: 12px;
                    border: none;
                }
            """)
        else:
            self.start_btn.setText("Start")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #11998e,
                        stop:1 #38ef7d
                    );
                    color: white;
                    padding: 12px;
                    border-radius: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #38ef7d,
                        stop:1 #11998e
                    );
                }
            """)

        if self.tool.current_response:
            self.resp_btn.setText("Response Ready")
            self.resp_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #56ab2f,
                        stop:1 #a8e063
                    );
                    color: white;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: none;
                }
            """)
        else:
            self.resp_btn.setText("Get Response")
            self.resp_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            """)

        if self.tool.collecting:
            self.add_btn.setText("Auto-Adding")
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4facfe,
                        stop:1 #00f2fe
                    );
                    color: white;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: none;
                }
            """)
        else:
            self.add_btn.setText("Add")
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea,
                        stop:1 #764ba2
                    );
                    color: white;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #764ba2,
                        stop:1 #667eea
                    );
                }
            """)

    def refresh_ui(self):
        self.buffer_list.clear()
        for i, item in enumerate(self.tool.clipboard_buffer, 1):
            preview = item[:60] + "..." if len(item) > 60 else item
            self.buffer_list.addItem(f"{i}. {preview}")
        self.update_button_states()

    def closeEvent(self, event):
        self.refresh_timer.stop()
        self.border_timer.stop()
        self.tool.exit_program()
        event.accept()


def main():
    app = QApplication(sys.argv)
    gui = GeminiGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()