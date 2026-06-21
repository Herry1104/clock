import sys
import time

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QEvent, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


PAUSE_TEXT = "\u6682\u505c"
RESUME_TEXT = "\u7ee7\u7eed"
TRANSPARENT_TEXT = "\u900f\u660e\u7a97\u53e3"
OPAQUE_TEXT = "\u5173\u95ed\u900f\u660e"
COLOR_TEXT = "\u53d8\u6362\u989c\u8272"
CLOCK_TEXT = "\u65f6\u949f"
COUNTDOWN_TEXT = "\u5012\u8ba1\u65f6"
START_TEXT = "\u5f00\u59cb"
RESET_TEXT = "\u91cd\u7f6e"

MIN_WIDTH = 440
MIN_HEIGHT = 220
WINDOW_MARGIN = 10
WINDOW_RADIUS = 28


class ClockApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clock")
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(380, 210)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.is_paused = False
        self.is_transparent = False
        self.color_index = 0
        self.mode = "clock"
        self.countdown_running = False
        self.countdown_remaining = 5 * 60
        self.drag_offset = QPoint()

        self.themes = [
            {
                "bg": "#f8fafc",
                "panel": "#e2e8f0",
                "text": "#172033",
                "muted": "#64748b",
                "button": "#ffffff",
                "active": "#dbeafe",
                "border": "#d7dee8",
                "pattern": "#8fa2bc",
            },
            {
                "bg": "#111827",
                "panel": "#374151",
                "text": "#f9fafb",
                "muted": "#9ca3af",
                "button": "#1f2937",
                "active": "#2563eb",
                "border": "#4b5563",
                "pattern": "#6b7280",
            },
            {
                "bg": "#fef3c7",
                "panel": "#fbbf24",
                "text": "#78350f",
                "muted": "#92400e",
                "button": "#fffbeb",
                "active": "#fde68a",
                "border": "#f59e0b",
                "pattern": "#b45309",
            },
            {
                "bg": "#ecfdf5",
                "panel": "#34d399",
                "text": "#064e3b",
                "muted": "#047857",
                "button": "#ffffff",
                "active": "#a7f3d0",
                "border": "#10b981",
                "pattern": "#059669",
            },
        ]

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.apply_style()
        self.update_clock_display()
        self.update_controls()

    def build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            WINDOW_MARGIN + 18,
            WINDOW_MARGIN + 14,
            WINDOW_MARGIN + 18,
            WINDOW_MARGIN + 14,
        )
        self.main_layout.setSpacing(8)

        self.title_bar = QWidget(self)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)

        self.title_label = QLabel("Desktop Clock", self.title_bar)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.minimize_button = QPushButton("-", self.title_bar)
        self.minimize_button.setFixedSize(28, 24)
        self.minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("x", self.title_bar)
        self.close_button.setFixedSize(28, 24)
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        self.main_layout.addWidget(self.title_bar)
        self.title_bar.installEventFilter(self)
        self.title_label.installEventFilter(self)

        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.time_label, stretch=1)

        self.countdown_panel = QWidget(self)
        countdown_layout = QHBoxLayout(self.countdown_panel)
        countdown_layout.setContentsMargins(0, 0, 0, 0)
        countdown_layout.setSpacing(8)

        self.minute_spin = QSpinBox(self.countdown_panel)
        self.minute_spin.setRange(0, 999)
        self.minute_spin.setValue(5)
        self.minute_spin.setSuffix(" \u5206")
        self.minute_spin.valueChanged.connect(self.sync_countdown_from_inputs)
        countdown_layout.addWidget(self.minute_spin, stretch=1)

        self.second_spin = QSpinBox(self.countdown_panel)
        self.second_spin.setRange(0, 59)
        self.second_spin.setValue(0)
        self.second_spin.setSuffix(" \u79d2")
        self.second_spin.valueChanged.connect(self.sync_countdown_from_inputs)
        countdown_layout.addWidget(self.second_spin, stretch=1)

        self.reset_button = QPushButton(RESET_TEXT, self.countdown_panel)
        self.reset_button.clicked.connect(self.reset_countdown)
        countdown_layout.addWidget(self.reset_button, stretch=1)

        self.main_layout.addWidget(self.countdown_panel)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.mode_button = QPushButton(COUNTDOWN_TEXT, self)
        self.mode_button.clicked.connect(self.toggle_mode)
        controls_layout.addWidget(self.mode_button, stretch=1)

        self.pause_button = QPushButton(PAUSE_TEXT, self)
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button, stretch=1)

        self.transparent_button = QPushButton(TRANSPARENT_TEXT, self)
        self.transparent_button.clicked.connect(self.toggle_transparency)
        controls_layout.addWidget(self.transparent_button, stretch=1)

        self.color_button = QPushButton(COLOR_TEXT, self)
        self.color_button.clicked.connect(self.change_color)
        controls_layout.addWidget(self.color_button, stretch=1)

        self.resize_grip = QSizeGrip(self)
        self.resize_grip.setFixedSize(18, 18)
        controls_layout.addWidget(
            self.resize_grip,
            alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
        )

        self.main_layout.addLayout(controls_layout)
        self.countdown_panel.hide()

    def tick(self):
        if self.mode == "countdown":
            self.tick_countdown()
        elif not self.is_paused:
            self.update_clock_display()

    def update_clock_display(self):
        self.time_label.setText(time.strftime("%H:%M:%S"))

    def tick_countdown(self):
        if not self.countdown_running:
            return

        self.countdown_remaining = max(0, self.countdown_remaining - 1)
        self.update_countdown_display()

        if self.countdown_remaining == 0:
            self.countdown_running = False
            self.update_controls()

    def update_countdown_display(self):
        total_seconds = max(0, self.countdown_remaining)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            self.time_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")
        else:
            self.time_label.setText(f"{minutes:02}:{seconds:02}")

    def toggle_pause(self):
        if self.mode == "countdown":
            self.toggle_countdown()
            return

        self.is_paused = not self.is_paused
        self.update_controls()

    def toggle_countdown(self):
        if self.countdown_running:
            self.countdown_running = False
            self.update_controls()
            return

        if self.countdown_remaining <= 0:
            self.sync_countdown_from_inputs()

        if self.countdown_remaining <= 0:
            return

        self.countdown_running = True
        self.update_controls()

    def toggle_mode(self):
        if self.mode == "clock":
            self.mode = "countdown"
            self.countdown_running = False
            self.sync_countdown_from_inputs()
            self.countdown_panel.show()
            self.update_countdown_display()
        else:
            self.mode = "clock"
            self.countdown_running = False
            self.countdown_panel.hide()
            self.update_clock_display()

        self.update_controls()
        self.resizeEvent(None)

    def sync_countdown_from_inputs(self):
        if self.countdown_running:
            return

        self.countdown_remaining = self.minute_spin.value() * 60 + self.second_spin.value()
        if self.mode == "countdown":
            self.update_countdown_display()
            self.update_controls()

    def reset_countdown(self):
        self.countdown_running = False
        self.sync_countdown_from_inputs()
        self.update_controls()

    def update_controls(self):
        self.mode_button.setText(CLOCK_TEXT if self.mode == "countdown" else COUNTDOWN_TEXT)
        show_countdown_settings = self.mode == "countdown" and not self.countdown_running
        self.countdown_panel.setVisible(show_countdown_settings)

        if self.mode == "countdown":
            if self.countdown_running:
                self.pause_button.setText(PAUSE_TEXT)
            elif self.countdown_remaining <= 0:
                self.pause_button.setText(START_TEXT)
            elif self.countdown_remaining != self.configured_countdown_seconds():
                self.pause_button.setText(RESUME_TEXT)
            else:
                self.pause_button.setText(START_TEXT)
        else:
            self.pause_button.setText(RESUME_TEXT if self.is_paused else PAUSE_TEXT)

        self.minute_spin.setEnabled(show_countdown_settings)
        self.second_spin.setEnabled(show_countdown_settings)
        self.reset_button.setEnabled(show_countdown_settings)
        self.resizeEvent(None)

    def configured_countdown_seconds(self):
        return self.minute_spin.value() * 60 + self.second_spin.value()

    def toggle_transparency(self):
        self.is_transparent = not self.is_transparent
        self.setWindowOpacity(0.76 if self.is_transparent else 1.0)
        self.transparent_button.setText(
            OPAQUE_TEXT if self.is_transparent else TRANSPARENT_TEXT
        )
        self.apply_style()

    def change_color(self):
        self.color_index = (self.color_index + 1) % len(self.themes)
        self.apply_style()

    def resizeEvent(self, event):
        if event is not None:
            super().resizeEvent(event)
        reserved_height = 150 if self.countdown_panel.isVisible() else 108
        font_size = max(34, min(92, self.width() // 7, self.height() - reserved_height))
        self.time_label.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))

    def eventFilter(self, watched, event):
        if not hasattr(self, "title_label"):
            return super().eventFilter(watched, event)

        if watched not in (self.title_bar, self.title_label):
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True

        if event.type() == QEvent.Type.MouseMove:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_offset)
                return True

        return super().eventFilter(watched, event)

    def apply_style(self):
        theme = self.themes[self.color_index]
        button_style = self.button_style(theme["button"], theme["panel"], theme["text"])
        active_button_style = self.button_style(
            theme["active"],
            theme["panel"],
            theme["text"],
        )

        self.title_label.setStyleSheet(
            f"color: {theme['muted']}; font-family: Segoe UI; font-size: 10pt;"
        )
        self.time_label.setStyleSheet(f"color: {theme['text']};")
        self.countdown_panel.setStyleSheet("background: transparent;")
        self.mode_button.setStyleSheet(button_style)
        self.pause_button.setStyleSheet(button_style)
        self.transparent_button.setStyleSheet(
            active_button_style if self.is_transparent else button_style
        )
        self.color_button.setStyleSheet(button_style)
        self.reset_button.setStyleSheet(button_style)
        self.minute_spin.setStyleSheet(self.input_style(theme))
        self.second_spin.setStyleSheet(self.input_style(theme))

        chrome_style = (
            "QPushButton {"
            "background: transparent;"
            f"color: {theme['muted']};"
            "border: none;"
            "border-radius: 8px;"
            "font-family: Segoe UI;"
            "font-size: 10pt;"
            "}"
            "QPushButton:hover {"
            f"background: {theme['panel']};"
            f"color: {theme['text']};"
            "}"
        )
        self.minimize_button.setStyleSheet(chrome_style)
        self.close_button.setStyleSheet(chrome_style)
        self.repaint()

    def button_style(self, background, hover, text):
        return (
            "QPushButton {"
            f"background: {background};"
            f"color: {text};"
            "border: none;"
            "border-radius: 8px;"
            "padding: 8px 12px;"
            "font-family: Microsoft YaHei UI;"
            "font-size: 10pt;"
            "}"
            "QPushButton:hover {"
            f"background: {hover};"
            "}"
            "QPushButton:pressed {"
            f"background: {hover};"
            "}"
        )

    def input_style(self, theme):
        return (
            "QSpinBox {"
            f"background: {theme['button']};"
            f"color: {theme['text']};"
            "border: none;"
            "border-radius: 8px;"
            "padding: 7px 10px;"
            "font-family: Segoe UI;"
            "font-size: 10pt;"
            "}"
            "QSpinBox:disabled {"
            f"color: {theme['muted']};"
            f"background: {theme['panel']};"
            "}"
        )

    def transparent_color(self, value, alpha):
        color = QColor(value)
        color.setAlpha(alpha)
        return color

    def draw_notre_dame_pattern(self, painter, rect, theme):
        pattern = self.transparent_color(theme["pattern"], 68)
        faint_pattern = self.transparent_color(theme["pattern"], 38)
        center = QPointF(rect.center().x(), rect.top() + rect.height() * 0.42)
        rose_radius = min(rect.width(), rect.height()) * 0.26

        painter.setPen(QPen(faint_pattern, 1.15))
        self.draw_pointed_arches(painter, rect, rose_radius)

        painter.setPen(QPen(pattern, 1.45))
        painter.drawEllipse(center, rose_radius, rose_radius)
        painter.drawEllipse(center, rose_radius * 0.66, rose_radius * 0.66)
        painter.drawEllipse(center, rose_radius * 0.28, rose_radius * 0.28)

        for index in range(24):
            angle = index * 15
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.drawLine(
                QPointF(0, -rose_radius * 0.28),
                QPointF(0, -rose_radius * 0.96),
            )
            painter.drawEllipse(
                QPointF(0, -rose_radius * 0.74),
                rose_radius * 0.055,
                rose_radius * 0.14,
            )
            painter.restore()

        painter.setPen(QPen(faint_pattern, 1.1))
        stone_y = int(rect.bottom() - 40)
        for x in range(int(rect.left()) + 28, int(rect.right()) - 20, 46):
            painter.drawLine(x, stone_y, x + 26, stone_y)
            painter.drawLine(x + 13, stone_y, x + 13, stone_y + 14)

    def draw_pointed_arches(self, painter, rect, rose_radius):
        arch_top = rect.top() + 42
        arch_bottom = rect.bottom() - 30
        arch_width = max(42, rect.width() * 0.16)
        centers = (
            rect.left() + arch_width * 0.82,
            rect.right() - arch_width * 0.82,
        )

        for center_x in centers:
            self.draw_arch(painter, center_x, arch_top, arch_bottom, arch_width)
            self.draw_arch(painter, center_x, arch_top + 18, arch_bottom - 10, arch_width * 0.58)

        side_step = max(28, int(rect.width() / 9))
        for x in range(int(rect.left()) + side_step, int(rect.right()) - side_step, side_step):
            if abs(x - rect.center().x()) < rose_radius * 1.2:
                continue
            painter.drawLine(x, int(arch_top + 28), x, int(arch_bottom - 8))

    def draw_arch(self, painter, center_x, top, bottom, width):
        half_width = width / 2
        path = QPainterPath()
        path.moveTo(center_x - half_width, bottom)
        path.lineTo(center_x - half_width, top + width * 0.55)
        path.quadTo(center_x - half_width, top + width * 0.12, center_x, top)
        path.quadTo(center_x + half_width, top + width * 0.12, center_x + half_width, top + width * 0.55)
        path.lineTo(center_x + half_width, bottom)
        painter.drawPath(path)

    def background_gradient(self, rect, theme):
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(theme["bg"]))
        gradient.setColorAt(0.48, QColor(theme["bg"]))
        gradient.setColorAt(1, self.transparent_color(theme["panel"], 255))
        return gradient

    def paintEvent(self, event):
        super().paintEvent(event)
        theme = self.themes[self.color_index]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(
            WINDOW_MARGIN + 0.5,
            WINDOW_MARGIN + 0.5,
            self.width() - WINDOW_MARGIN * 2 - 1,
            self.height() - WINDOW_MARGIN * 2 - 1,
        )
        background_path = QPainterPath()
        background_path.addRoundedRect(rect, WINDOW_RADIUS, WINDOW_RADIUS)

        painter.fillPath(background_path, self.background_gradient(rect, theme))
        painter.save()
        painter.setClipPath(background_path)
        self.draw_notre_dame_pattern(painter, rect, theme)
        painter.restore()

        painter.setPen(QPen(QColor(theme["border"]), 1))
        painter.drawPath(background_path)


def main():
    app = QApplication(sys.argv)
    clock = ClockApp()
    clock.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
