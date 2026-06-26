from PyQt6.QtCore import Qt, QPoint, QTimer, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QApplication

from config import ConfigManager
from sun import Sun
from ruler_painter import RulerPainter


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configuration
        self.config = ConfigManager()
        self.sun = Sun(self.config.city, self.config.country)
        self.ruler = RulerPainter(
            self.config.start_hour,
            self.config.end_hour,
            self.sun,
        )

        # Window setup – frameless, always on top
        self.setWindowTitle("Daily Pomodoro")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = self.screen().availableGeometry()
        self.setGeometry(0, self.config.y_position, screen.width(), 120)   # height reduced to 120

        # Button areas (top‑right corner)
        self.btn_width = 30
        self.btn_height = 25
        self.btn_margin = 5
        self.close_btn_rect = QRect(
            self.width() - self.btn_width - self.btn_margin,
            self.btn_margin,
            self.btn_width,
            self.btn_height,
        )
        self.min_btn_rect = QRect(
            self.width() - 2 * (self.btn_width + self.btn_margin),
            self.btn_margin,
            self.btn_width,
            self.btn_height,
        )

        # Drag state (whole window is draggable)
        self.drag_start = QPoint()
        self.dragging = False

        # Refresh every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    # ── Resize: update button positions ──────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.close_btn_rect.moveRight(self.width() - self.btn_margin)
        self.min_btn_rect.moveRight(self.width() - self.btn_width - 2 * self.btn_margin)

    # ── Mouse events (drag + button clicks) ──────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if self.close_btn_rect.contains(pos):
                QApplication.instance().quit()          # close
            elif self.min_btn_rect.contains(pos):
                self.showMinimized()                    # minimize
            else:
                self.dragging = True
                self.drag_start = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return
        delta = event.globalPosition().toPoint() - self.drag_start
        self.move(0, self.y() + delta.y())
        self.drag_start = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.config.save(self.y())

    # ── Painting ─────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Dark semi‑transparent background (only inside the bar area)
        bg_color = QColor(20, 20, 20, 200)     # dark grey, alpha 200
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        # 2. Draw the ruler, dome, sun, etc.
        self.ruler.paint(painter, self.width(), self.height())

        # 3. Custom window buttons (minimize / close)
        self.draw_buttons(painter)

    def draw_buttons(self, painter):
        """Draw minimize and close buttons with simple symbols."""
        # Close button
        if self.close_btn_rect.isValid():
            painter.setPen(Qt.PenStyle.NoPen)
            if self.close_btn_rect.contains(self.mapFromGlobal(self.cursor().pos())):
                painter.setBrush(QColor(255, 80, 80))   # red when hovered
            else:
                painter.setBrush(QColor(180, 80, 80))   # muted red
            painter.drawRoundedRect(self.close_btn_rect, 4, 4)

            # "X" symbol
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(self.close_btn_rect, Qt.AlignmentFlag.AlignCenter, "✕")

        # Minimize button
        if self.min_btn_rect.isValid():
            painter.setPen(Qt.PenStyle.NoPen)
            if self.min_btn_rect.contains(self.mapFromGlobal(self.cursor().pos())):
                painter.setBrush(QColor(100, 100, 100))
            else:
                painter.setBrush(QColor(70, 70, 70))
            painter.drawRoundedRect(self.min_btn_rect, 4, 4)

            # "–" symbol
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            painter.drawText(self.min_btn_rect, Qt.AlignmentFlag.AlignCenter, "–")