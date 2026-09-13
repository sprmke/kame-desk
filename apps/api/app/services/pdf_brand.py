from __future__ import annotations

DEFAULT_CLINIC_BRAND_COLOR = "#465fff"


def brand_rgb(hex_color: str | None) -> tuple[float, float, float]:
    color = (hex_color or DEFAULT_CLINIC_BRAND_COLOR).lstrip("#")
    if len(color) != 6:
        color = DEFAULT_CLINIC_BRAND_COLOR.lstrip("#")
    r = int(color[0:2], 16) / 255.0
    g = int(color[2:4], 16) / 255.0
    b = int(color[4:6], 16) / 255.0
    return r, g, b


def draw_letterhead_accent(canvas, x: float, y: float, width: float, hex_color: str | None) -> None:
    r, g, b = brand_rgb(hex_color)
    canvas.setStrokeColorRGB(r, g, b)
    canvas.setLineWidth(2)
    canvas.line(x, y, x + width, y)
