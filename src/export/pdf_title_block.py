"""
Tittelfelt-tegning for PDF-eksport.
Kompakt tittelfelt i nedre høyre hjørne med all produksjonsrelevant data.
"""
from datetime import datetime

from reportlab.lib.colors import Color, black, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from ..models.door import DoorParams
from .pdf_constants import COLOR_TITLE_BG, COMPANY_ADDRESS, LOGO_PATH
from ..utils.constants import (
    DOOR_TYPES, SWING_DIRECTIONS, HINGE_TYPES, THRESHOLD_TYPES,
)

# Tittelfelt-dimensjoner (brukes av pdf_exporter for layout)
TITLE_BLOCK_WIDTH = 80 * mm

# Beregnet innholdshøyde
_ROW_H = 10 * mm
_NUM_ROWS = 6
_DIM_SECTION_H = 32 * mm
_BOTTOM_ROW_H = 8 * mm
_LOGO_H = 14 * mm
_CONTACT_H = 4 * mm

TITLE_BLOCK_HEIGHT = (
    _NUM_ROWS * _ROW_H +
    _DIM_SECTION_H +
    _BOTTOM_ROW_H +
    _LOGO_H +
    _CONTACT_H
)


def draw_title_block(c: canvas.Canvas, x: float, y: float,
                     width: float, height: float,
                     door: DoorParams,
                     drawing_title: str, sheet_id: str,
                     scale: float,
                     show_scale: bool = True) -> None:
    """Tegner kompakt tittelfelt med produksjonsdata."""
    pad = 4

    # Bakgrunn og ramme
    c.setFillColor(COLOR_TITLE_BG)
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(x, y, width, height, fill=1, stroke=1)

    half_w = width / 2

    # ================================================================
    # LAYOUT: fra bunn og oppover
    # ================================================================

    # --- BUNN: Kontaktinfo ---
    c.setFillColor(black)
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(x + width / 2, y + 1, COMPANY_ADDRESS)
    contact_top = y + _CONTACT_H
    c.line(x, contact_top, x + width, contact_top)

    # --- LOGO (kompakt) ---
    logo_y = contact_top
    logo_top = logo_y + _LOGO_H
    _draw_logo(c, x, logo_y, width, _LOGO_H, pad)
    c.line(x, logo_top, x + width, logo_top)

    # --- 3-RUTERS RAD: Dato | Målestokk | Format ---
    br_y = logo_top
    br_top = br_y + _BOTTOM_ROW_H
    c.line(x, br_top, x + width, br_top)

    third_w = width / 3
    for i in range(1, 3):
        c.line(x + i * third_w, br_y, x + i * third_w, br_top)

    _draw_cell(c, x, br_y, third_w, _BOTTOM_ROW_H,
               "Dato:", datetime.now().strftime("%d.%m.%y"), pad, val_size=8)
    scale_text = f"1:{int(scale)}" if show_scale else "-"
    _draw_cell(c, x + third_w, br_y, third_w, _BOTTOM_ROW_H,
               "Målestokk:", scale_text, pad, val_size=8)
    _draw_cell(c, x + 2 * third_w, br_y, third_w, _BOTTOM_ROW_H,
               "Format:", "A3", pad, val_size=8)

    # --- MÅL-SEKSJON ---
    dim_y = br_top
    dim_top = dim_y + _DIM_SECTION_H
    c.line(x, dim_top, x + width, dim_top)
    _draw_dimension_section(c, door, x, dim_y, width, _DIM_SECTION_H, pad)

    # --- INFO-RADER (fra toppen nedover) ---
    door_type_name = DOOR_TYPES.get(door.door_type, door.door_type)
    swing_text = SWING_DIRECTIONS.get(door.swing_direction, door.swing_direction)
    hinge_info = HINGE_TYPES.get(door.hinge_type, {})
    hinge_name = hinge_info.get('navn', door.hinge_type) if isinstance(hinge_info, dict) else door.hinge_type
    hinge_short = hinge_name.replace('Hengsler ', '').replace('i SF stål', 'SF')
    hinge_text = f"{hinge_short} ({door.hinge_count})"
    threshold_text = THRESHOLD_TYPES.get(door.threshold_type, door.threshold_type)

    rows = [
        ("Produkt:", door_type_name, "Tegning:", sheet_id or "D.01"),
        ("Karmtype:", door.karm_type, "Fløyer:", f"{door.floyer}-fløyet"),
        ("Slagretning:", swing_text, "Vegg:", f"{door.thickness} mm"),
        ("Farge blad:", door.color, "Farge karm:", door.karm_color),
        ("Hengsler:", hinge_text, "Terskel:", threshold_text),
        ("Ordre Ref.:", door.customer or "-", "Prosjekt:", door.project_id or "-"),
    ]

    current_top = y + height
    for i, (ll, vl, lr, vr) in enumerate(rows):
        row_bottom = current_top - (i + 1) * _ROW_H
        if row_bottom < dim_top:
            break
        c.line(x, row_bottom, x + width, row_bottom)
        c.line(x + half_w, row_bottom, x + half_w, row_bottom + _ROW_H)

        _draw_cell(c, x, row_bottom, half_w, _ROW_H,
                   ll, vl, pad, val_size=9)
        _draw_cell(c, x + half_w, row_bottom, half_w, _ROW_H,
                   lr, vr, pad, val_size=9)


def _draw_dimension_section(c: canvas.Canvas, door: DoorParams,
                            x: float, y: float,
                            width: float, height: float,
                            pad: float) -> None:
    """Tegner mål-seksjonen med alle produksjonsmål."""
    c.setFillColor(Color(0.3, 0.3, 0.3))
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x + pad, y + height - 9, "MÅL (mm)")

    bm_w, bm_h = door.width, door.height
    kw, kh = door.karm_width(), door.karm_height()
    bw, bh = door.blade_width(), door.blade_height()
    bt90 = door.transport_width_90()
    bt180 = door.transport_width_180()
    ht = door.transport_height_by_threshold()

    lines = [
        f"BM  {bm_w} × {bm_h}",
        f"KB  {kw} × {kh}",
        f"BB  {bw} × {bh}",
    ]

    bt_parts = []
    if bt90 is not None:
        bt_parts.append(f"BT90° {bt90}")
    if bt180 is not None:
        bt_parts.append(f"BT180° {bt180}")
    if ht is not None:
        bt_parts.append(f"HT {ht}")
    if bt_parts:
        lines.append("  ".join(bt_parts))

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7.5)
    line_h = 8
    start_y = y + height - 18
    for i, line in enumerate(lines):
        ly = start_y - i * line_h
        if ly < y + 1:
            break
        c.drawString(x + pad + 1, ly, line)


def _draw_cell(c: canvas.Canvas, x: float, y: float,
               width: float, height: float,
               label: str, value: str,
               pad: float, val_size: float = 9) -> None:
    """Tegner en celle med label øverst og verdi under."""
    c.setFillColor(Color(0.45, 0.45, 0.45))
    c.setFont("Helvetica", 5.5)
    c.drawString(x + pad, y + height - 7, label)

    c.setFillColor(black)
    available = width - 2 * pad
    fs = val_size
    while fs >= 5:
        c.setFont("Helvetica-Bold", fs)
        if c.stringWidth(value, "Helvetica-Bold", fs) <= available:
            break
        fs -= 0.5

    c.drawString(x + pad, y + height - 7 - fs - 1, value)


def _draw_logo(c: canvas.Canvas, x: float, y: float,
               width: float, height: float, pad: float) -> None:
    """Tegner KIAS-logoen kompakt."""
    if not LOGO_PATH.exists():
        return
    try:
        drawing = svg2rlg(str(LOGO_PATH))
        if not drawing:
            return
        logo_max_w = width - 2 * pad
        logo_max_h = height - 2
        sx = logo_max_w / drawing.width
        sy = logo_max_h / drawing.height
        s = min(sx, sy)
        sw = drawing.width * s
        sh = drawing.height * s
        drawing.width = sw
        drawing.height = sh
        drawing.scale(s, s)
        renderPDF.draw(drawing, c, x + pad + (logo_max_w - sw) / 2,
                       y + (height - sh) / 2)
    except Exception:
        pass


def draw_drawing_frame(c: canvas.Canvas, page_width: float, page_height: float,
                       margin: float) -> None:
    """Tegner ytre ramme rundt hele siden."""
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(margin / 2, margin / 2,
           page_width - margin, page_height - margin,
           fill=0, stroke=1)
