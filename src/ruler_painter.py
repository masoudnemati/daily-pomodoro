from PyQt6.QtCore import Qt, QPointF, QRectF, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPainterPath, QRegion
from clock import Clock


class RulerPainter:
    def __init__(self, start_hour, end_hour, sun):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.sun = sun
        self.peak_height = 60

        self._left_margin = 20
        self._right_margin = 20
        self._line_y = 80
        self._click_band = 28
        self._sun_pos = None          # (x, y) of the moving sun (used if needed externally)

    def get_input_mask(self, width: int, widget_height: int) -> QRegion:
        y_top = max(0, self._line_y - self._click_band)
        y_bot = min(widget_height, self._line_y + self._click_band)
        return QRegion(QRect(0, y_top, width, y_bot - y_top))

    def paint(self, painter: QPainter, width: int, height: int):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        left_margin = self._left_margin
        right_margin = self._right_margin
        line_y = self._line_y

        hours = self.end_hour - self.start_hour + 1
        spacing = (width - left_margin - right_margin) / (hours - 1)

        # Pens & font
        ruler_pen = QPen(QColor(80, 80, 80), 2)            # dark grey, no outline
        tick_pen = QPen(QColor(0, 0, 0), 2)                # black outline for ticks
        tick_inner = QPen(QColor(255, 255, 255), 1)        # white tick centre
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)

        # ---- Ruler line (simple dark grey) ----
        painter.setPen(ruler_pen)
        painter.drawLine(left_margin, line_y, width - right_margin, line_y)

        # ---- Hour ticks & labels ----
        for i in range(hours):
            x = left_margin + spacing * i

            # Tick (black outline + white centre)
            painter.setPen(tick_pen)
            painter.drawLine(int(x), line_y, int(x), line_y - 8)
            painter.setPen(tick_inner)
            painter.drawLine(int(x), line_y, int(x), line_y - 8)

            # Text (black outline + white fill)
            text = str(self.start_hour + i)
            painter.setPen(QColor(0, 0, 0))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                           (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                painter.drawText(int(x - 8 + dx), line_y + 20 + dy, text)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(x - 8), line_y + 20, text)

        # ---- Daylight dome, sun, and all time indicators ----
        self._draw_daylight(painter, left_margin, right_margin, line_y, width)

    # ───────────────────────────────────────────────────────────────

    def _invert_smoothstep(self, u: float) -> float:
        if u <= 0.0:
            return 0.0
        if u >= 1.0:
            return 1.0
        t = u
        for _ in range(12):
            ft  = t * t * (3.0 - 2.0 * t)
            dft = 6.0 * t * (1.0 - t)
            if abs(dft) < 1e-12:
                break
            t -= (ft - u) / dft
            t = max(0.0, min(1.0, t))
        return t

    def _bezier_control_heights(self, sx, ex, nx, sy):
        t0 = (nx - sx) / (ex - sx) if ex != sx else 0.5
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
        return h1, h2

    def _eval_bezier(self, t, sx, ex, sy, h1, h2):
        mt = 1 - t
        x = (mt**3 * sx
             + 3 * mt**2 * t * sx
             + 3 * mt * t**2 * ex
             + t**3 * ex)
        y = (mt**3 * sy
             + 3 * mt**2 * t * (sy - h1)
             + 3 * mt * t**2 * (sy - h2)
             + t**3 * sy)
        return x, y

    def _draw_daylight(self, painter, left_margin, right_margin, line_y, width):
        """Draw the dome, noon marker, sun (with its vertical line), and purple night line."""
        self._sun_pos = None   # reset for this frame

        # If we have no sun data at all, just draw the night‑time indicator (purple) if the current time is visible
        if self.sun.sunrise is None or self.sun.sunset is None or self.sun.solar_noon is None:
            self._draw_night_indicator(painter, left_margin, right_margin, line_y, width)
            return

        sunrise_h = self.sun.sunrise.hour + self.sun.sunrise.minute / 60
        sunset_h  = self.sun.sunset.hour  + self.sun.sunset.minute  / 60
        noon_h    = self.sun.solar_noon.hour + self.sun.solar_noon.minute / 60

        total_hours = self.end_hour - self.start_hour
        ruler_end_x = width - right_margin

        def hour_to_x(h):
            return left_margin + (h - self.start_hour) * (ruler_end_x - left_margin) / total_hours

        sx = hour_to_x(sunrise_h)
        ex = hour_to_x(sunset_h)
        nx = hour_to_x(noon_h)
        sy = line_y
        peak_y = line_y - self.peak_height

        h1, h2 = self._bezier_control_heights(sx, ex, nx, sy)

        # ---- Dome arc ----
        dome_path = QPainterPath()
        dome_path.moveTo(sx, sy)
        dome_path.cubicTo(sx, sy - h1, ex, sy - h2, ex, sy)

        painter.save()
        painter.setClipRect(QRectF(left_margin, line_y - self.peak_height - 20,
                                   ruler_end_x - left_margin, self.peak_height + 30))

        arc_pen = QPen(QColor(255, 215, 0, 160), 1.2, Qt.PenStyle.DotLine)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(dome_path)

        # ---- Solar noon diamond ----
        t0 = (nx - sx) / (ex - sx) if ex != sx else 0.5
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.setBrush(QColor(255, 255, 0, 200))
        d = 5
        painter.drawPolygon(
            QPointF(nx, peak_y - d), QPointF(nx + d, peak_y),
            QPointF(nx, peak_y + d), QPointF(nx - d, peak_y),
        )

        # ---- Current time indicator ----
        now = Clock.now()
        now_h = now.hour + now.minute / 60 + now.second / 3600

        # Daylight → dotted line from sun to ruler, then sun on top
        if sunrise_h <= now_h <= sunset_h:
            u = (now_h - sunrise_h) / (sunset_h - sunrise_h)
            t = self._invert_smoothstep(u)
            sun_x, sun_y = self._eval_bezier(t, sx, ex, sy, h1, h2)
            self._sun_pos = (sun_x, sun_y)

            # Draw the dotted line FIRST (so sun covers its endpoint)
            dot_pen = QPen(QColor(255, 255, 255, 180), 1.5, Qt.PenStyle.DotLine)
            painter.setPen(dot_pen)
            painter.drawLine(int(sun_x), int(sun_y), int(sun_x), line_y)

            # Sun colour
            if u <= t0:
                v = u / t0 if t0 != 0 else 1.0
                r, g, b = 255, int(255 - 40 * v), int(255 * (1 - v))
            else:
                v = (u - t0) / (1 - t0) if (1 - t0) != 0 else 1.0
                if v < 0.5:
                    w = v / 0.5
                    r, g, b = 255, int(215 - 50 * w), 0
                else:
                    w = (v - 0.5) / 0.5
                    r, g, b = 255, int(165 - 165 * w), 0

            painter.setPen(QPen(QColor(0, 0, 0), 1.5))
            painter.setBrush(QColor(r, g, b))
            painter.drawEllipse(QPointF(sun_x, sun_y), 7, 7)

        # Night‑time (or outside sunrise→sunset) → purple indicator
        elif self.start_hour <= now.hour <= self.end_hour:
            self._draw_night_indicator(painter, left_margin, right_margin, line_y, width)

        painter.restore()

    def _draw_night_indicator(self, painter, left_margin, right_margin, line_y, width):
        """Thin purple vertical line for hours outside daylight, within the displayed range."""
        now = Clock.now()
        if not (self.start_hour <= now.hour <= self.end_hour):
            return

        total_hours = self.end_hour - self.start_hour
        x = (left_margin
             + ((now.hour - self.start_hour) + now.minute / 60)
             * (width - left_margin - right_margin) / total_hours)

        purple_pen = QPen(QColor(128, 0, 128), 2)   # thin, solid, no outline
        painter.setPen(purple_pen)
        painter.drawLine(int(x), line_y - 35, int(x), line_y + 8)