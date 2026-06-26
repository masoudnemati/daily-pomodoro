from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPainterPath
from clock import Clock


class RulerPainter:
    def __init__(self, start_hour, end_hour, sun):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.sun = sun
        self.peak_height = 60          # height of the dome above the ruler

    # ─────────────────────────── PAINT ───────────────────────────
    def paint(self, painter: QPainter, width: int, height: int):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        left_margin = 20
        right_margin = 20
        line_y = 80

        hours = self.end_hour - self.start_hour + 1
        spacing = (width - left_margin - right_margin) / (hours - 1)

        # Pens & font
        outline_pen = QPen(QColor(0, 0, 0), 5)
        white_pen = QPen(QColor(255, 255, 255), 2)
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)

        # ---- Ruler line ----
        painter.setPen(outline_pen)
        painter.drawLine(left_margin, line_y, width - right_margin, line_y)
        painter.setPen(white_pen)
        painter.drawLine(left_margin, line_y, width - right_margin, line_y)

        # ---- Hour ticks & labels ----
        for i in range(hours):
            x = left_margin + spacing * i

            # Tick
            painter.setPen(outline_pen)
            painter.drawLine(int(x), line_y, int(x), line_y - 8)
            painter.setPen(white_pen)
            painter.drawLine(int(x), line_y, int(x), line_y - 8)

            # Text (outline + white)
            text = str(self.start_hour + i)
            painter.setPen(QColor(0, 0, 0))
            for dx, dy in [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1),
            ]:
                painter.drawText(int(x - 8 + dx), line_y + 20 + dy, text)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(x - 8), line_y + 20, text)

        # ---- Daylight dome + sun + noon marker ----
        self.draw_daylight(painter, left_margin, right_margin, line_y, width)

        # ---- Current time indicator (vertical line) ----
        now = Clock.now()
        current_hour = now.hour
        current_minute = now.minute

        if self.start_hour <= current_hour <= self.end_hour:
            total_hours = self.end_hour - self.start_hour
            x = (left_margin
                 + ((current_hour - self.start_hour) + current_minute / 60)
                 * (width - left_margin - right_margin) / total_hours)
            outline_pen.setWidth(7)
            painter.setPen(outline_pen)
            painter.drawLine(int(x), line_y - 35, int(x), line_y + 8)
            white_pen.setWidth(3)
            painter.setPen(white_pen)
            painter.drawLine(int(x), line_y - 35, int(x), line_y + 8)

    # ───────────────────── DAYLIGHT (dome, sun, noon) ─────────────────────
    def draw_daylight(self, painter, left_margin, right_margin, line_y, width):
        """Draw the dome arc, the solar‑noon marker, and the moving sun."""
        if self.sun.sunrise is None or self.sun.sunset is None or self.sun.solar_noon is None:
            return

        # Decimal hours
        sunrise_h = self.sun.sunrise.hour + self.sun.sunrise.minute / 60
        sunset_h  = self.sun.sunset.hour + self.sun.sunset.minute / 60
        noon_h    = self.sun.solar_noon.hour + self.sun.solar_noon.minute / 60

        total_hours = self.end_hour - self.start_hour
        ruler_start_x = left_margin
        ruler_end_x   = width - right_margin

        def hour_to_x(h):
            return left_margin + (h - self.start_hour) * (ruler_end_x - left_margin) / total_hours

        sx = hour_to_x(sunrise_h)   # sunrise x
        ex = hour_to_x(sunset_h)    # sunset x
        nx = hour_to_x(noon_h)      # solar noon x

        sy = line_y                 # y on the ruler
        peak_y = line_y - self.peak_height

        # Normalised position of noon (0..1)
        t0 = (nx - sx) / (ex - sx) if ex != sx else 0.5

        # Coefficients for the cubic Bézier with vertical tangents
        A = 3 * (1 - t0) ** 2 * t0
        B = 3 * (1 - t0) * t0 ** 2
        C = self.peak_height
        D = (1 - t0) * (1 - 3 * t0)
        E = t0 * (2 - 3 * t0)

        if abs(E) > 1e-9:
            h1 = C / (A - B * D / E)
            h2 = -D / E * h1
        else:
            h1 = C / A if A != 0 else 0
            h2 = 0

        # Build the dome path
        dome_path = QPainterPath()
        dome_path.moveTo(sx, sy)
        dome_path.cubicTo(sx, sy - h1, ex, sy - h2, ex, sy)

        # ---- Draw the dome (black outline + golden dotted) ----
        painter.save()
        clip_rect = QRectF(ruler_start_x, line_y - self.peak_height - 20,
                           ruler_end_x - ruler_start_x, self.peak_height + 30)
        painter.setClipRect(clip_rect)

        outline_pen = QPen(QColor(0, 0, 0), 3.5, Qt.PenStyle.SolidLine)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(dome_path)

        golden_pen = QPen(QColor(255, 215, 0), 1.5, Qt.PenStyle.DotLine)
        painter.setPen(golden_pen)
        painter.drawPath(dome_path)

        # ---- Solar noon marker (yellow diamond at the peak) ----
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QColor(255, 255, 0))
        diamond_size = 6
        diamond_points = [
            QPointF(nx, peak_y - diamond_size),
            QPointF(nx + diamond_size, peak_y),
            QPointF(nx, peak_y + diamond_size),
            QPointF(nx - diamond_size, peak_y),
        ]
        painter.drawPolygon(*diamond_points)

        # ---- Moving sun ----
        now = Clock.now()
        now_h = now.hour + now.minute / 60 + now.second / 3600

        if sunrise_h <= now_h <= sunset_h:
            # Parameter t along the x‑axis (linear with time)
            t = (now_h - sunrise_h) / (sunset_h - sunrise_h)

            # Position on the cubic Bézier
            x = sx + t * (ex - sx)           # because x is linear
            # y coordinate from cubic formula:
            y = ((1 - t) ** 3 * sy +
                 3 * (1 - t) ** 2 * t * (sy - h1) +
                 3 * (1 - t) * t ** 2 * (sy - h2) +
                 t ** 3 * sy)

            # Determine color
            if t <= t0:
                # white → yellow
                u = t / t0 if t0 != 0 else 1
                r = int(255 + (255 - 255) * u)  # stays 255
                g = int(255 + (215 - 255) * u)  # 255 -> 215
                b = int(255 + (0 - 255) * u)    # 255 -> 0
            else:
                u = (t - t0) / (1 - t0) if (1 - t0) != 0 else 1
                # yellow → orange → red
                if u < 0.5:
                    v = u / 0.5
                    r = 255
                    g = int(215 + (165 - 215) * v)  # 215 -> 165
                    b = 0
                else:
                    v = (u - 0.5) / 0.5
                    r = int(255 + (255 - 255) * (1 - v))  # stays 255
                    g = int(165 + (0 - 165) * v)          # 165 -> 0
                    b = 0

            sun_color = QColor(r, g, b)

            # Draw the sun (small circle with outline)
            sun_radius = 7
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(sun_color)
            painter.drawEllipse(QPointF(x, y), sun_radius, sun_radius)

        painter.restore()