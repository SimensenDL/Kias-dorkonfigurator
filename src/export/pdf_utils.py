"""
Hjelpefunksjoner for PDF-eksport.
Fargekonvertering, skalering, skravering og mållinjer.
"""
from reportlab.lib.colors import Color, black
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from ..utils.constants import RAL_COLORS
from .pdf_constants import COLOR_DIMENSION, COLOR_WALL_HATCH


def ral_to_color(ral_code: str) -> Color:
    """Konverterer RAL-kode til reportlab Color."""
    if ral_code in RAL_COLORS:
        r, g, b = RAL_COLORS[ral_code]['rgb']
        return Color(r, g, b)
    # Fallback til grå
    return Color(0.5, 0.5, 0.5)


def mm_to_scaled(value_mm: float, scale: float) -> float:
    """Konverterer mm til skalert PDF-punkter."""
    return (value_mm / scale) * mm


def calculate_scale(available_width: float, available_height: float,
                    drawing_width: float, drawing_height: float) -> float:
    """
    Beregner optimal målestokk for å passe tegningen.

    Args:
        available_width: Tilgjengelig bredde i PDF-punkter
        available_height: Tilgjengelig høyde i PDF-punkter
        drawing_width: Tegningens bredde i mm
        drawing_height: Tegningens høyde i mm

    Returns:
        Målestokk (f.eks. 10 for 1:10)
    """
    scale_x = drawing_width / (available_width / mm)
    scale_y = drawing_height / (available_height / mm)

    required_scale = max(scale_x, scale_y)

    # Standard målestokker for dører (mindre enn bygninger)
    standard_scales = [1, 2, 5, 10, 15, 20, 25, 50]
    for s in standard_scales:
        if s >= required_scale:
            return s
    return 50


def draw_page_frame(c: canvas.Canvas, page_width: float, page_height: float,
                    margin: float) -> None:
    """Tegner ramme rundt siden."""
    c.setStrokeColor(black)
    c.setLineWidth(1.5)
    c.rect(margin / 2, margin / 2,
           page_width - margin, page_height - margin,
           fill=0, stroke=1)


def draw_hatch_pattern(c: canvas.Canvas, x: float, y: float,
                       w: float, h: float,
                       spacing: float = 3 * mm,
                       color: Color = None,
                       line_width: float = 0.3) -> None:
    """Tegner 45° skraveringsmønster innenfor et rektangel (klippet)."""
    if color is None:
        color = COLOR_WALL_HATCH
    c.saveState()
    p = c.beginPath()
    p.rect(x, y, w, h)
    c.clipPath(p, stroke=0)

    c.setStrokeColor(color)
    c.setLineWidth(line_width)

    # 45° linjer fra nedre-venstre til øvre-høyre
    total = w + h
    step = spacing
    d = 0.0
    while d <= total:
        x0 = x + d
        y0 = y
        x1 = x
        y1 = y + d
        # Klipp til rektangelets grenser
        if x0 > x + w:
            y0 = y + (x0 - (x + w))
            x0 = x + w
        if y1 > y + h:
            x1 = x + (y1 - (y + h))
            y1 = y + h
        if y0 <= y + h and x1 <= x + w:
            c.line(x1, y1, x0, y0)
        d += step

    c.restoreState()


def draw_arrow(c: canvas.Canvas, x: float, y: float,
               direction: str, size: float) -> None:
    """Tegner en fyllt pil i angitt retning (right/left/up/down)."""
    p = c.beginPath()
    if direction == 'right':
        p.moveTo(x, y)
        p.lineTo(x + size, y + size / 2)
        p.lineTo(x + size, y - size / 2)
    elif direction == 'left':
        p.moveTo(x, y)
        p.lineTo(x - size, y + size / 2)
        p.lineTo(x - size, y - size / 2)
    elif direction == 'up':
        p.moveTo(x, y)
        p.lineTo(x + size / 2, y + size)
        p.lineTo(x - size / 2, y + size)
    elif direction == 'down':
        p.moveTo(x, y)
        p.lineTo(x + size / 2, y - size)
        p.lineTo(x - size / 2, y - size)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def draw_dimension_line_h(c: canvas.Canvas,
                          x_left: float, x_right: float, y: float,
                          ref_y_top: float, ref_y_bottom: float,
                          label: str, value_mm,
                          font_size: float = 7,
                          ext: float = 2 * mm,
                          arrow_size: float = 1.5 * mm) -> None:
    """
    Tegner en horisontal mållinje med forlengelseslinjer, piler og tekst.

    Args:
        x_left, x_right: Venstre og høyre endepunkt for mållinjen
        y: Y-posisjon for selve mållinjen
        ref_y_top: Øvre referansepunkt for forlengelseslinje (der målet starter)
        ref_y_bottom: Ikke brukt direkte — forlengelseslinjer trekkes ned til y
        label: Tekst-label (f.eks. "BM")
        value_mm: Verdi i mm (vises som tekst)
    """
    if value_mm is None:
        return

    c.setStrokeColor(COLOR_DIMENSION)
    c.setFillColor(COLOR_DIMENSION)
    c.setLineWidth(0.4)

    # Forlengelseslinjer (fra referansepunkt ned til mållinje)
    gap = 1.5 * mm
    c.line(x_left, ref_y_top - gap, x_left, y - ext)
    c.line(x_right, ref_y_top - gap, x_right, y - ext)

    # Mållinje
    c.line(x_left, y, x_right, y)

    # Piler
    draw_arrow(c, x_left, y, 'right', arrow_size)
    draw_arrow(c, x_right, y, 'left', arrow_size)

    # Tekst
    text = f"{label} {value_mm}"
    c.setFont("Helvetica", font_size)
    text_w = c.stringWidth(text, "Helvetica", font_size)
    mid_x = (x_left + x_right) / 2
    c.drawString(mid_x - text_w / 2, y - font_size - 1.5, text)


def draw_dimension_line_v(c: canvas.Canvas,
                          y_bottom: float, y_top: float, x: float,
                          ref_x_left: float, ref_x_right: float,
                          label: str, value_mm,
                          font_size: float = 7,
                          ext: float = 2 * mm,
                          arrow_size: float = 1.5 * mm) -> None:
    """
    Tegner en vertikal mållinje med forlengelseslinjer, piler og tekst.

    Args:
        y_bottom, y_top: Nedre og øvre endepunkt for mållinjen
        x: X-posisjon for selve mållinjen
        ref_x_left, ref_x_right: Referansepunkt — forlengelseslinjer mot x
        label: Tekst-label
        value_mm: Verdi i mm
    """
    if value_mm is None:
        return

    c.setStrokeColor(COLOR_DIMENSION)
    c.setFillColor(COLOR_DIMENSION)
    c.setLineWidth(0.4)

    # Forlengelseslinjer (fra referansepunkt ut til mållinje)
    gap = 1.5 * mm
    c.line(ref_x_right + gap, y_bottom, x + ext, y_bottom)
    c.line(ref_x_right + gap, y_top, x + ext, y_top)

    # Mållinje
    c.line(x, y_bottom, x, y_top)

    # Piler
    draw_arrow(c, x, y_bottom, 'up', arrow_size)
    draw_arrow(c, x, y_top, 'down', arrow_size)

    # Tekst (rotert 90°)
    text = f"{label} {value_mm}"
    c.saveState()
    c.translate(x + font_size + 2, (y_bottom + y_top) / 2)
    c.rotate(90)
    c.setFont("Helvetica", font_size)
    text_w = c.stringWidth(text, "Helvetica", font_size)
    c.drawString(-text_w / 2, 0, text)
    c.restoreState()
