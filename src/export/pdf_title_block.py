"""
Tittelfelt-tegning for PDF-eksport.
Profesjonelt stående tittelfelt med logo, prosjektdata og tegningsinformasjon.
"""
from datetime import datetime

from reportlab.lib.colors import Color, black
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from ..models.door import DoorParams
from .pdf_constants import (
    COLOR_TITLE_BG, COMPANY_ADDRESS, DRAWING_STATUS, LOGO_PATH
)
from ..utils.constants import DOOR_TYPES


def draw_title_block(c: canvas.Canvas, x: float, y: float,
                     width: float, height: float,
                     door: DoorParams,
                     drawing_title: str, sheet_id: str,
                     scale: float,
                     show_scale: bool = True) -> None:
    """
    Tegner profesjonelt stående tittelfelt med prosjektdata.

    Args:
        c: Canvas å tegne på
        x, y: Nedre venstre hjørne av tittelfeltet
        width, height: Dimensjoner på tittelfeltet
        door: DoorParams for prosjektdata
        drawing_title: Tittel på tegningen
        sheet_id: Ark-ID (f.eks. "D.01")
        scale: Målestokk (f.eks. 10 for 1:10)
        show_scale: Om målestokk skal vises
    """
    pad = 5

    # Bakgrunn og ramme
    c.setFillColor(COLOR_TITLE_BG)
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(x, y, width, height, fill=1, stroke=1)

    # --- LAYOUT-BEREGNINGER (fra topp til bunn) ---
    info_row_h = 12 * mm
    upper_section_top = y + height
    upper_section_h = info_row_h * 3
    upper_section_bottom = upper_section_top - upper_section_h

    four_box_h = info_row_h
    four_box_top = upper_section_bottom
    four_box_bottom = four_box_top - four_box_h

    contact_box_h = 6 * mm
    contact_box_bottom = y
    contact_box_top = y + contact_box_h

    logo_section_h = 35 * mm
    logo_section_bottom = contact_box_top

    # Y-posisjoner for info-radene
    row_y = []
    current_y = upper_section_top
    for _ in range(3):
        row_y.append(current_y - info_row_h)
        current_y -= info_row_h

    # Horisontale skillelinjer
    for ry in row_y:
        c.line(x, ry, x + width, ry)
    c.line(x, four_box_top, x + width, four_box_top)
    c.line(x, four_box_bottom, x + width, four_box_bottom)

    half_w = width / 2

    # RAD 1: PROSJEKT | ID
    c.line(x + half_w, row_y[0], x + half_w, upper_section_top)
    door_type_name = DOOR_TYPES.get(door.door_type, door.door_type)
    _draw_label_value_row(c, x, row_y[0], half_w, info_row_h,
                          "Produkt:", door_type_name,
                          pad, value_size=12)
    _draw_label_value_row(c, x + half_w, row_y[0], half_w, info_row_h,
                          "ID:", sheet_id or "-",
                          pad, value_size=12)

    # RAD 2: STATUS | TEGNING
    c.line(x + half_w, row_y[1], x + half_w, row_y[0])
    _draw_label_value_row(c, x, row_y[1], half_w, info_row_h,
                          "Status:", DRAWING_STATUS,
                          pad, value_size=12)
    _draw_label_value_row(c, x + half_w, row_y[1], half_w, info_row_h,
                          "Tegning:", drawing_title,
                          pad, value_size=12)

    # RAD 3: KUNDE | PROSJEKT-ID
    c.line(x + half_w, row_y[2], x + half_w, row_y[1])
    _draw_label_value_row(c, x, row_y[2], half_w, info_row_h,
                          "Kunde:", door.customer or "-",
                          pad, value_size=11)
    _draw_label_value_row(c, x + half_w, row_y[2], half_w, info_row_h,
                          "Prosjekt-ID:", door.project_id or "-",
                          pad, value_size=11)

    # 4-RUTERS RAD
    box_w = width / 4
    box_h = four_box_h

    for i in range(1, 4):
        c.line(x + i * box_w, four_box_bottom, x + i * box_w, four_box_top)

    _draw_bottom_box(c, x, four_box_bottom, box_w, box_h,
                     "Tegn. dato:",
                     datetime.now().strftime("%d.%m.%y"), pad)

    # Bygg transportmål-tekst med 90° og 180° bredde
    bt_90 = door.transport_width_90()
    bt_180 = door.transport_width_180()
    ht = door.transport_height_by_threshold()

    bt_90_str = str(bt_90) if bt_90 is not None else "—"
    bt_180_str = str(bt_180) if bt_180 is not None else "—"
    ht_str = str(ht) if ht is not None else "—"

    # Format: BM: 1010×2110 / BT90°: 890 / BT180°: 920 / H: 2060
    dim_text = f"BM:{door.width}×{door.height} BT90°:{bt_90_str} BT180°:{bt_180_str} H:{ht_str}"
    _draw_bottom_box(c, x + box_w, four_box_bottom, box_w, box_h,
                     "Mål:",
                     dim_text, pad)

    scale_text = f"1 : {int(scale)}" if show_scale else "-"
    _draw_bottom_box(c, x + 2 * box_w, four_box_bottom, box_w, box_h,
                     "Målestokk:",
                     scale_text, pad)

    _draw_bottom_box(c, x + 3 * box_w, four_box_bottom, box_w, box_h,
                     "Arkformat:",
                     "A3", pad)

    # LOGO-SEKSJON
    c.line(x, contact_box_top, x + width, contact_box_top)

    logo_area_h = logo_section_bottom + logo_section_h - logo_section_bottom

    if LOGO_PATH.exists():
        try:
            drawing = svg2rlg(str(LOGO_PATH))
            if drawing:
                logo_max_w = width - 2 * pad
                logo_max_h = logo_area_h * 0.75
                scale_x = logo_max_w / drawing.width
                scale_y = logo_max_h / drawing.height
                scale = min(scale_x, scale_y)
                scaled_w = drawing.width * scale
                scaled_h = drawing.height * scale
                drawing.width = scaled_w
                drawing.height = scaled_h
                drawing.scale(scale, scale)
                logo_img_x = x + pad + (logo_max_w - scaled_w) / 2
                logo_img_y = logo_section_bottom + (logo_area_h - scaled_h) / 2
                renderPDF.draw(drawing, c, logo_img_x, logo_img_y)
        except Exception:
            pass

    # Kontaktinfo
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    contact_y = contact_box_bottom + (contact_box_h / 2) - 3
    c.drawCentredString(x + width / 2, contact_y, COMPANY_ADDRESS)


def _draw_label_value_row(c: canvas.Canvas, x: float, y: float,
                          width: float, height: float,
                          label: str, value: str,
                          pad: float, value_size: int = 12) -> None:
    """Tegner en rad med label og verdi med auto-skalering."""
    c.setFillColor(Color(0.4, 0.4, 0.4))
    c.setFont("Helvetica", 7)
    c.drawString(x + pad, y + height - 10, label)

    c.setFillColor(black)
    available_width = width - 2 * pad
    font_size = value_size
    min_font_size = 6

    while font_size >= min_font_size:
        c.setFont("Helvetica-Bold", font_size)
        text_width = c.stringWidth(value, "Helvetica-Bold", font_size)
        if text_width <= available_width:
            break
        font_size -= 0.5

    c.drawString(x + pad, y + height - 10 - font_size - 2, value)


def _draw_bottom_box(c: canvas.Canvas, x: float, y: float,
                     width: float, height: float,
                     label: str, value: str, pad: float) -> None:
    """Tegner en boks i 4-ruters raden med label og verdi."""
    c.setFillColor(Color(0.4, 0.4, 0.4))
    c.setFont("Helvetica", 6)
    c.drawString(x + pad, y + height - 9, label)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + pad, y + height / 2 - 6, value)


def draw_drawing_frame(c: canvas.Canvas, page_width: float, page_height: float,
                       margin: float, title_block_x: float,
                       gap: float = 5 * mm) -> None:
    """Tegner ramme rundt tegneområdet (venstre del av arket)."""
    frame_x = margin / 2
    frame_y = margin / 2
    frame_width = title_block_x - gap - frame_x
    frame_height = page_height - margin

    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(frame_x, frame_y, frame_width, frame_height, fill=0, stroke=1)
