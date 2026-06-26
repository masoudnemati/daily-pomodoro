from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter

from config import ConfigManager
from sun import Sun
from ruler_painter import RulerPainter


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configuration
        self.config = ConfigManager()

        # Sun data (logs sunrise, solar noon, sunset automatically)
        self.sun = Sun(self.config.city, self.config.country)

        # The ruler painter
        self.ruler = RulerPainter(
            self.config.start_hour,
            self.config.end_hour,
            self.sun,
        )

        # Window setup
        self.setWindowTitle("Daily Pomodoro")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = self.screen().availableGeometry()
        self.setGeometry(0, self.config.y_position, screen.width(), 200)

        # Drag state
        self.drag_start = QPoint()
        self.dragging = False

        # Refresh every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    # ── Dragging ─────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return
        delta = event.globalPosition().toPoint() - self.drag_start
        self.move(0, self.y() + delta.y())
        self.drag_start = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.config.save(self.y())

    # ── Painting ─────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        self.ruler.paint(painter, self.width(), self.height())