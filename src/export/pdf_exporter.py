"""
PDF-eksport for KIAS Dørkonfigurator.
Genererer teknisk tegning av dør med mål og tittelfelt.
"""
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.lib.colors import black, Color
from reportlab.pdfgen import canvas

from ..models.door import DoorParams
from ..utils.constants import DOOR_TYPES
from .pdf_constants import (
    A3_WIDTH, A3_HEIGHT, A3_MARGIN,
    COLOR_DOOR_FILL, COLOR_DOOR_STROKE, COLOR_FRAME_FILL,
    COLOR_GLASS, COLOR_DIMENSION, COLOR_HANDLE, COLOR_HINGE
)
from .pdf_utils import ral_to_color, mm_to_scaled, calculate_scale
from .pdf_title_block import draw_title_block, draw_drawing_frame


def export_door_pdf(door: DoorParams, filepath: Path,
                    company_name: str = "KVANNE INDUSTRIER AS") -> None:
    """
    Eksporterer komplett PDF-tegning av dør.

    Args:
        door: DoorParams med dørkonfigurasjon
        filepath: Utfilsti (.pdf)
        company_name: Firmanavn for tittelfelt
    """
    filepath = Path(filepath)
    if not str(filepath).endswith('.pdf'):
        filepath = Path(str(filepath) + '.pdf')

    c = canvas.Canvas(str(filepath), pagesize=(A3_WIDTH, A3_HEIGHT))

    # Side 1: Frontvisning
    _draw_front_view_page(c, door)

    c.save()


def _draw_front_view_page(c: canvas.Canvas, door: DoorParams) -> None:
    """Tegner frontvisning av dør med mål og tittelfelt."""
    page_w = A3_WIDTH
    page_h = A3_HEIGHT
    margin = A3_MARGIN

    # Tittelfelt-dimensjoner (høyre side)
    title_block_width = 60 * mm
    title_block_height = page_h - margin - margin / 2
    title_block_x = page_w - margin / 2 - title_block_width
    title_block_y = margin / 2

    # Tegn tittelfelt
    draw_title_block(
        c, title_block_x, title_block_y,
        title_block_width, title_block_height,
        door,
        drawing_title="Frontvisning",
        sheet_id="D.01",
        scale=10
    )

    # Tegn ramme rundt tegneområdet
    draw_drawing_frame(c, page_w, page_h, margin, title_block_x)

    # --- Tegneområde ---
    draw_x = margin / 2
    draw_y = margin / 2
    draw_w = title_block_x - 5 * mm - draw_x
    draw_h = page_h - margin

    # Beregn skalering
    door_w_mm = door.width
    door_h_mm = door.height

    # La det være plass til målpiler (30mm på hver side)
    avail_w = draw_w - 60 * mm
    avail_h = draw_h - 60 * mm

    scale = calculate_scale(avail_w, avail_h, door_w_mm, door_h_mm)

    # Skalerte dør-dimensjoner i PDF-punkter
    scaled_w = mm_to_scaled(door_w_mm, scale)
    scaled_h = mm_to_scaled(door_h_mm, scale)

    # Sentrer døren i tegneområdet
    center_x = draw_x + draw_w / 2
    center_y = draw_y + draw_h / 2
    door_x = center_x - scaled_w / 2
    door_y = center_y - scaled_h / 2

    # Tegn dør
    _draw_door(c, door, door_x, door_y, scaled_w, scaled_h, scale)

    # Tegn mål
    _draw_dimensions(c, door, door_x, door_y, scaled_w, scaled_h)


def _draw_door(c: canvas.Canvas, door: DoorParams,
               x: float, y: float, w: float, h: float,
               scale: float) -> None:
    """Tegner selve døren (rektangel med karm, håndtak, hengsler)."""
    # Karm (5mm tykkere rundt døren)
    karm_offset = mm_to_scaled(50, scale)  # 50mm karm
    c.setFillColor(COLOR_FRAME_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(1.0)
    c.rect(x - karm_offset, y, w + 2 * karm_offset, h + karm_offset,
           fill=1, stroke=1)

    # Dørblad med farge
    door_color = ral_to_color(door.color)
    c.setFillColor(door_color)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.8)
    c.rect(x, y, w, h, fill=1, stroke=1)

    # Glass (hvis aktuelt)
    if door.glass:
        glass_w = w * 0.3
        glass_h = h * 0.3
        glass_x = x + (w - glass_w) / 2
        glass_y = y + h * 0.5
        c.setFillColor(COLOR_GLASS)
        c.setStrokeColor(COLOR_DOOR_STROKE)
        c.setLineWidth(0.5)
        c.rect(glass_x, glass_y, glass_w, glass_h, fill=1, stroke=1)
        # Kryss i glass (markering)
        c.setStrokeColor(Color(0.6, 0.75, 0.9))
        c.setLineWidth(0.3)
        c.line(glass_x, glass_y, glass_x + glass_w, glass_y + glass_h)
        c.line(glass_x + glass_w, glass_y, glass_x, glass_y + glass_h)

    # Håndtak
    handle_w = w * 0.04
    handle_h = h * 0.04
    if door.swing_direction == 'left':
        handle_x = x + w - w * 0.12
    else:
        handle_x = x + w * 0.08
    handle_y = y + h * 0.47
    c.setFillColor(COLOR_HANDLE)
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(handle_x, handle_y, handle_w, handle_h, fill=1, stroke=1)

    # Hengsler (3 stk)
    hinge_w = w * 0.02
    hinge_h = h * 0.02
    hinge_positions = [0.15, 0.5, 0.85]

    if door.swing_direction == 'left':
        hinge_x = x - hinge_w / 2
    else:
        hinge_x = x + w - hinge_w / 2

    c.setFillColor(COLOR_HINGE)
    for pos in hinge_positions:
        hinge_y = y + h * pos - hinge_h / 2
        c.rect(hinge_x, hinge_y, hinge_w, hinge_h, fill=1, stroke=1)


def _draw_dimensions(c: canvas.Canvas, door: DoorParams,
                     door_x: float, door_y: float,
                     door_w: float, door_h: float) -> None:
    """Tegner mål-linjer og tekst rundt døren."""
    c.setStrokeColor(COLOR_DIMENSION)
    c.setFillColor(COLOR_DIMENSION)
    c.setLineWidth(0.5)

    offset = 15 * mm  # Avstand fra dør til mållinje
    ext = 3 * mm      # Forlengelseslinjer
    arrow = 2 * mm    # Pilstørrelse

    # --- BREDDE (under døren) ---
    dim_y = door_y - offset

    # Forlengelseslinjer
    c.line(door_x, door_y - 2 * mm, door_x, dim_y - ext)
    c.line(door_x + door_w, door_y - 2 * mm, door_x + door_w, dim_y - ext)

    # Mållinje
    c.line(door_x, dim_y, door_x + door_w, dim_y)

    # Piler
    _draw_arrow(c, door_x, dim_y, 'right', arrow)
    _draw_arrow(c, door_x + door_w, dim_y, 'left', arrow)

    # Tekst
    c.setFont("Helvetica-Bold", 10)
    text = f"{door.width}"
    text_w = c.stringWidth(text, "Helvetica-Bold", 10)
    c.drawString(door_x + door_w / 2 - text_w / 2, dim_y - 12, text)

    # --- HØYDE (til høyre for døren) ---
    dim_x = door_x + door_w + offset

    # Forlengelseslinjer
    c.line(door_x + door_w + 2 * mm, door_y, dim_x + ext, door_y)
    c.line(door_x + door_w + 2 * mm, door_y + door_h, dim_x + ext, door_y + door_h)

    # Mållinje
    c.line(dim_x, door_y, dim_x, door_y + door_h)

    # Piler
    _draw_arrow(c, dim_x, door_y, 'up', arrow)
    _draw_arrow(c, dim_x, door_y + door_h, 'down', arrow)

    # Tekst (rotert 90 grader)
    c.saveState()
    c.translate(dim_x + 12, door_y + door_h / 2)
    c.rotate(90)
    text = f"{door.height}"
    text_w = c.stringWidth(text, "Helvetica-Bold", 10)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(-text_w / 2, 0, text)
    c.restoreState()


def _draw_arrow(c: canvas.Canvas, x: float, y: float,
                direction: str, size: float) -> None:
    """Tegner en pil i angitt retning."""
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
