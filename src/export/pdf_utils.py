"""
Hjelpefunksjoner for PDF-eksport.
Fargekonvertering, skalering og sideramme.
"""
from reportlab.lib.colors import Color, black
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from ..utils.constants import RAL_COLORS


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
