"""
PDF-eksport av kappeliste.

Genererer A4 portrett-PDF med KIAS-logo, kappeliste-tabeller
og diverse-tabell. Bruker reportlab platypus for automatiske sideskift.
"""
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

from .pdf_constants import (
    COMPANY_NAME, COMPANY_ADDRESS, LOGO_PATH,
    COLOR_COMPANY_BLUE, COLOR_KIAS_YELLOW,
    A4_PORT_MARGIN,
)
from ..models.production_list import ProductionList


# Farger
_YELLOW = COLOR_KIAS_YELLOW
_GREY_HEADER = HexColor('#E0E0E0')
_GREY_ALT = HexColor('#F5F5F5')


def export_kappeliste_pdf(
    prod_list: ProductionList,
    filepath: str,
    merknader: Optional[dict] = None,
    diverse_merknader: Optional[dict] = None,
) -> None:
    """Eksporterer kappeliste til PDF.

    Args:
        prod_list: ProductionList med dørene
        filepath: Filsti for PDF-filen
        merknader: Dict med merknader for hovedtabellen
                   {(section_title, profilnavn, mm): tekst}
        diverse_merknader: Dict med merknader for diverse-tabellen
                           {(forklaring, b_mm, h_mm): tekst}
    """
    merknader = merknader or {}
    diverse_merknader = diverse_merknader or {}

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=A4_PORT_MARGIN,
        rightMargin=A4_PORT_MARGIN,
        topMargin=A4_PORT_MARGIN,
        bottomMargin=A4_PORT_MARGIN + 10 * mm,
    )

    elements = []

    # Header
    elements.extend(_build_header(prod_list))
    elements.append(Spacer(1, 6 * mm))

    # Kappeliste-seksjoner
    sections = prod_list.get_kappeliste_sections()
    for section in sections:
        table = _build_section_table(section, merknader)
        elements.append(KeepTogether([table, Spacer(1, 4 * mm)]))

    # Diverse-tabell
    diverse_rows = prod_list.get_diverse_rows()
    if diverse_rows:
        table = _build_diverse_table(diverse_rows, diverse_merknader)
        elements.append(KeepTogether([table]))

    doc.build(elements, onFirstPage=_draw_footer, onLaterPages=_draw_footer)


def _build_header(prod_list: ProductionList) -> list:
    """Bygger header med logo, tittel og metadata."""
    elements = []
    styles = getSampleStyleSheet()

    # Logo
    if LOGO_PATH.exists():
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF as _rpdf
            drawing = svg2rlg(str(LOGO_PATH))
            if drawing:
                max_w = 60 * mm
                max_h = 18 * mm
                scale_x = max_w / drawing.width
                scale_y = max_h / drawing.height
                s = min(scale_x, scale_y)
                drawing.width = drawing.width * s
                drawing.height = drawing.height * s
                drawing.scale(s, s)

                from reportlab.graphics import renderPM
                # Bruk renderSVG -> platypus-kompatibelt via en wrapper
                # Enkleste: lag en tabell med drawing som flowable
                from reportlab.platypus.flowables import Drawing
                elements.append(drawing)
                elements.append(Spacer(1, 2 * mm))
        except Exception:
            pass

    # Tittel
    title_style = ParagraphStyle(
        'KappelisteTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=2 * mm,
        textColor=COLOR_COMPANY_BLUE,
    )
    elements.append(Paragraph("KAPPELISTE", title_style))

    # Metadata-rad: firma, dato, antall
    dato = datetime.now().strftime("%d.%m.%Y")
    door_count = prod_list.door_count
    meta_style = ParagraphStyle(
        'KappelisteMeta',
        parent=styles['Normal'],
        fontSize=9,
        textColor=black,
        spaceAfter=1 * mm,
    )
    elements.append(Paragraph(
        f"{COMPANY_NAME} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Dato: {dato} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Antall d\u00f8rer: {door_count}",
        meta_style
    ))

    return elements


def _build_section_table(section: dict, merknader: dict) -> Table:
    """Bygger en platypus-tabell for en kappeliste-seksjon."""
    title = section['title']
    rows = section['rows']

    col_headers = ['PROFILNAVN', 'STK', 'MM', 'SLAGRETNING', 'FARGE', 'MERKNAD']
    col_widths = [85, 30, 50, 65, 65, None]  # None = resten

    # Beregn tilgjengelig bredde
    page_w = A4[0]
    avail = page_w - 2 * A4_PORT_MARGIN
    fixed = sum(w for w in col_widths if w is not None)
    col_widths = [w if w is not None else avail - fixed for w in col_widths]

    # Bygg data
    data = []
    # Rad 0: Seksjons-header (spanner hele bredden)
    data.append([title, '', '', '', '', ''])
    # Rad 1: Kolonneoverskrifter
    data.append(col_headers)

    prev_profil = ''
    for row in rows:
        show_name = row['profilnavn'] != prev_profil
        prev_profil = row['profilnavn']

        merknad_key = (title, row['profilnavn'], row['mm'])
        merknad = merknader.get(merknad_key, '')

        data.append([
            row['profilnavn'] if show_name else '',
            str(row['stk']),
            row['mm'],
            row['slagretning'],
            row['farge'],
            merknad,
        ])

    table = Table(data, colWidths=col_widths, repeatRows=2)

    # Styling
    style_cmds = [
        # Seksjons-header: gul bakgrunn, fet skrift, span alle kolonner
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), _YELLOW),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),

        # Kolonneoverskrifter: grå bakgrunn
        ('BACKGROUND', (0, 1), (-1, 1), _GREY_HEADER),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('TOPPADDING', (0, 1), (-1, 1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 3),

        # Data-rader
        ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, -1), 8),
        ('TOPPADDING', (0, 2), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 2),

        # Sentrering for STK, MM, SLAGRETNING
        ('ALIGN', (1, 1), (3, -1), 'CENTER'),

        # Ramme
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.8, black),

        # Vertikal midtstilling
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Annenhver rad lys grå bakgrunn (fra rad 2)
    for i in range(2, len(data)):
        if (i - 2) % 2 == 1:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), _GREY_ALT))

    table.setStyle(TableStyle(style_cmds))
    return table


def _build_diverse_table(diverse_rows: list, diverse_merknader: dict) -> Table:
    """Bygger en platypus-tabell for diverse-seksjonen."""
    col_headers = ['FORKLARING', 'STK', 'B MM', 'H MM', 'FARGE', 'MERKNAD']
    col_widths = [85, 30, 50, 50, 65, None]

    page_w = A4[0]
    avail = page_w - 2 * A4_PORT_MARGIN
    fixed = sum(w for w in col_widths if w is not None)
    col_widths = [w if w is not None else avail - fixed for w in col_widths]

    data = []
    # Rad 0: Seksjons-header
    data.append(['Diverse', '', '', '', '', ''])
    # Rad 1: Kolonneoverskrifter
    data.append(col_headers)

    prev_forkl = ''
    for row in diverse_rows:
        show_name = row['forklaring'] != prev_forkl
        prev_forkl = row['forklaring']

        merknad_key = (row['forklaring'], row['b_mm'], row['h_mm'])
        merknad = diverse_merknader.get(merknad_key, '')

        data.append([
            row['forklaring'] if show_name else '',
            str(row['stk']),
            row['b_mm'],
            row['h_mm'],
            row['farge'],
            merknad,
        ])

    table = Table(data, colWidths=col_widths, repeatRows=2)

    style_cmds = [
        # Seksjons-header
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), _YELLOW),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),

        # Kolonneoverskrifter
        ('BACKGROUND', (0, 1), (-1, 1), _GREY_HEADER),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('TOPPADDING', (0, 1), (-1, 1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 3),

        # Data-rader
        ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, -1), 8),
        ('TOPPADDING', (0, 2), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 2),

        # Sentrering for STK, B MM, H MM
        ('ALIGN', (1, 1), (3, -1), 'CENTER'),

        # Ramme
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.8, black),

        # Vertikal midtstilling
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    for i in range(2, len(data)):
        if (i - 2) % 2 == 1:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), _GREY_ALT))

    table.setStyle(TableStyle(style_cmds))
    return table


def _draw_footer(canvas_obj: canvas.Canvas, doc) -> None:
    """Tegner bunntekst med firmanavn og sidetall."""
    canvas_obj.saveState()
    page_w, page_h = A4
    margin = A4_PORT_MARGIN

    y = margin - 5 * mm

    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawString(margin, y, COMPANY_NAME)
    canvas_obj.drawRightString(
        page_w - margin, y,
        f"Side {canvas_obj.getPageNumber()}"
    )
    canvas_obj.restoreState()
