"""
PDF-eksport for KIAS Dørkonfigurator.
Genererer profesjonell produksjonstegning med frontvisning,
horisontalsnitt og tittelfelt.
"""
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, Color
from reportlab.pdfgen import canvas

from ..models.door import DoorParams
from ..utils.constants import DOOR_TYPES
from .pdf_constants import (
    A3_WIDTH, A3_HEIGHT, A3_MARGIN,
    COLOR_DOOR_FILL, COLOR_DOOR_STROKE, COLOR_FRAME_FILL,
    COLOR_DIMENSION, COLOR_HANDLE, COLOR_HINGE,
    COLOR_WALL_FILL, COLOR_WALL_HATCH, COLOR_SECTION_CUT,
    COLOR_SWING_ARC, COLOR_SECTION_LINE,
    KARM_SECTION_PROFILES,
)
from .pdf_utils import (
    ral_to_color, mm_to_scaled, calculate_scale,
    draw_hatch_pattern, draw_arrow,
    draw_dimension_line_h, draw_dimension_line_v,
)
from .pdf_title_block import (
    draw_title_block, draw_drawing_frame,
    TITLE_BLOCK_WIDTH, TITLE_BLOCK_HEIGHT,
)


# Mellomrom mellom stakkede mållinjer
DIM_SPACING = 8 * mm
# Avstand fra tegning til første mållinje
DIM_OFFSET = 10 * mm


def export_door_pdf(door: DoorParams, filepath: Path,
                    company_name: str = "KVANNE INDUSTRIER AS") -> None:
    """
    Eksporterer komplett PDF-produksjonstegning av dør.

    Args:
        door: DoorParams med dørkonfigurasjon
        filepath: Utfilsti (.pdf)
        company_name: Firmanavn for tittelfelt
    """
    filepath = Path(filepath)
    if not str(filepath).endswith('.pdf'):
        filepath = Path(str(filepath) + '.pdf')

    c = canvas.Canvas(str(filepath), pagesize=(A3_WIDTH, A3_HEIGHT))

    _draw_production_page(c, door)

    c.save()


def _draw_production_page(c: canvas.Canvas, door: DoorParams) -> None:
    """Tegner produksjonstegning med frontvisning, snitt og tittelfelt.

    Layout:
    ┌───────────────────────────┬────────────┐
    │                           │            │
    │     FRONTVISNING          │            │
    │     (maks høyde)          │ TITTELFELT │
    │                           │ (nedre del)│
    ├───────────────────────────┤            │
    │     SNITT A—A (kompakt)   │            │
    └───────────────────────────┴────────────┘
    """
    page_w = A3_WIDTH
    page_h = A3_HEIGHT
    margin = A3_MARGIN
    m2 = margin / 2
    gap = 3 * mm

    # --- Ytre ramme ---
    draw_drawing_frame(c, page_w, page_h, margin)

    # --- Høyre kolonne (tittelfelt) ---
    title_w = TITLE_BLOCK_WIDTH
    title_h = TITLE_BLOCK_HEIGHT
    col_x = page_w - m2 - title_w
    title_x = col_x
    title_y = m2

    # Vertikal skillelinje: venstre | høyre
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.line(col_x - gap / 2, m2, col_x - gap / 2, page_h - m2)

    # --- Venstre tegneområde ---
    draw_x = m2
    draw_y = m2
    draw_w = col_x - gap - m2
    draw_h = page_h - margin

    # Kompakt snittsone (65mm) nederst i venstre kolonne
    section_h = 65 * mm
    section_y = draw_y
    section_x = draw_x

    # Frontvisning: resten over snittet
    front_y = section_y + section_h + gap
    front_h = draw_h - section_h - gap
    front_x = draw_x
    front_w = draw_w

    # Horisontal skillelinje mellom front og snitt
    c.setStrokeColor(Color(0.6, 0.6, 0.6))
    c.setLineWidth(0.3)
    c.line(draw_x, front_y - gap / 2, draw_x + draw_w, front_y - gap / 2)

    # --- Beregn skalering ---
    wall_ext_mm = 60
    kw = door.karm_width()
    kh = door.karm_height()

    total_w_mm = max(kw, door.width) + 2 * wall_ext_mm
    total_h_mm = max(kh, door.height) + wall_ext_mm

    avail_w = front_w - 2 * DIM_OFFSET - 4 * DIM_SPACING
    avail_h = front_h - 2 * DIM_OFFSET - 4 * DIM_SPACING

    scale = calculate_scale(avail_w, avail_h, total_w_mm, total_h_mm)

    # --- Tegn ---
    _draw_front_view(c, door, front_x, front_y, front_w, front_h, scale)
    _draw_horizontal_section(c, door, section_x, section_y, draw_w, section_h, scale)

    draw_title_block(
        c, title_x, title_y, title_w, title_h,
        door,
        drawing_title="Produksjonstegning",
        sheet_id="D.01",
        scale=scale,
    )


# ============================================================================
# FRONTVISNING
# ============================================================================

def _draw_front_view(c: canvas.Canvas, door: DoorParams,
                     area_x: float, area_y: float,
                     area_w: float, area_h: float,
                     scale: float) -> None:
    """Tegner frontvisning med vegg, karm, blad, hengsler, håndtak, slagbue og mål."""

    # Beregnede mål
    bm = door.width
    hm = door.height
    kw = door.karm_width()
    kh = door.karm_height()
    sw = door.sidestolpe_width()  # Visuell sidestolpe-bredde
    bw = door.blade_width()
    bh = door.blade_height()
    bt90 = door.transport_width_90()
    bt180 = door.transport_width_180()
    ht = door.transport_height_by_threshold()

    wall_ext_mm = 60  # mm vegg utover utsparingen

    # Skalerte verdier (PDF-punkter)
    s_bm = mm_to_scaled(bm, scale)
    s_hm = mm_to_scaled(hm, scale)
    s_kw = mm_to_scaled(kw, scale)
    s_kh = mm_to_scaled(kh, scale)
    s_sw = mm_to_scaled(sw, scale)
    s_bw = mm_to_scaled(bw, scale)
    s_bh = mm_to_scaled(bh, scale)
    s_wall_ext = mm_to_scaled(wall_ext_mm, scale)

    # Sentrer utsparingen i tegneområdet (med offset for mål)
    dim_space_bottom = DIM_OFFSET + 5 * DIM_SPACING
    dim_space_right = DIM_OFFSET + 4 * DIM_SPACING

    center_x = area_x + (area_w - dim_space_right) / 2
    center_y = area_y + dim_space_bottom + (area_h - dim_space_bottom) / 2

    # Utsparing (opening) posisjon
    open_x = center_x - s_bm / 2
    open_y = center_y - s_hm / 2

    # Karm posisjon (sentrert på utsparing horisontalt, bunn-justert)
    karm_x = open_x - (s_kw - s_bm) / 2
    karm_y = open_y  # Bunn-justert med utsparing

    # For SD3/ID: karm er INNENFOR utsparing
    if door.karm_type == 'SD3/ID':
        karm_x = open_x + (s_bm - s_kw) / 2

    # Blad posisjon (sentrert i utsparing horisontalt, bunn ved utsparing)
    blade_x = center_x - s_bw / 2
    blade_y = open_y

    # --- 1. VEGG ---
    _draw_wall(c, open_x, open_y, s_bm, s_hm, s_wall_ext, scale)

    # --- 2. KARM ---
    karm_color = ral_to_color(door.karm_color)
    _draw_karm_frame(c, door, karm_x, karm_y, s_kw, s_kh, s_sw, karm_color, scale)

    # --- 3. DØRBLAD ---
    door_color = ral_to_color(door.color)
    _draw_blades(c, door, blade_x, blade_y, s_bw, s_bh, door_color, scale)

    # --- 4. HENGSLER ---
    _draw_hinges(c, door, blade_x, blade_y, s_bw, s_bh, scale)

    # --- 5. HÅNDTAK ---
    _draw_handle(c, door, blade_x, blade_y, s_bw, s_bh, scale)

    # --- 6. SLAGBUE ---
    _draw_swing_arc(c, door, blade_x, blade_y, s_bw, s_bh, scale)

    # --- 7. SNITTLINJE A-A ---
    _draw_section_line_marker(c, open_x, open_y, s_bm, s_hm, s_wall_ext, scale)

    # --- 8. MÅLLINJER ---
    _draw_front_dimensions(
        c, door, open_x, open_y, s_bm, s_hm,
        karm_x, karm_y, s_kw, s_kh,
        blade_x, blade_y, s_bw, s_bh,
        scale
    )


def _draw_wall(c: canvas.Canvas,
               open_x: float, open_y: float,
               s_bm: float, s_hm: float,
               s_wall_ext: float, scale: float) -> None:
    """Tegner vegg med utsparing og skravering."""
    # Vegg-rektangel (strekker seg utover utsparingen)
    wall_x = open_x - s_wall_ext
    wall_y = open_y
    wall_w = s_bm + 2 * s_wall_ext
    wall_h = s_hm + s_wall_ext  # Vegg over utsparing, ikke under (dør-åpning)

    # Venstre vegg-del
    c.setFillColor(COLOR_WALL_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.5)
    c.rect(wall_x, wall_y, s_wall_ext, wall_h, fill=1, stroke=1)
    draw_hatch_pattern(c, wall_x, wall_y, s_wall_ext, wall_h,
                       spacing=mm_to_scaled(30, scale))

    # Høyre vegg-del
    c.setFillColor(COLOR_WALL_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.5)
    right_x = open_x + s_bm
    c.rect(right_x, wall_y, s_wall_ext, wall_h, fill=1, stroke=1)
    draw_hatch_pattern(c, right_x, wall_y, s_wall_ext, wall_h,
                       spacing=mm_to_scaled(30, scale))

    # Topp vegg-del (over utsparing)
    c.setFillColor(COLOR_WALL_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.5)
    top_y = open_y + s_hm
    c.rect(wall_x, top_y, wall_w, s_wall_ext, fill=1, stroke=1)
    draw_hatch_pattern(c, wall_x, top_y, wall_w, s_wall_ext,
                       spacing=mm_to_scaled(30, scale))


def _draw_karm_frame(c: canvas.Canvas, door: DoorParams,
                     karm_x: float, karm_y: float,
                     s_kw: float, s_kh: float,
                     s_sw: float, color: Color,
                     scale: float) -> None:
    """Tegner karmramme (U-form: to sidestolper + toppstykke)."""
    c.setFillColor(color)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.6)

    # Toppstykke-høyde = sidestolpe-bredde (uniform ramme)
    top_h = s_sw

    # Venstre sidestolpe
    c.rect(karm_x, karm_y, s_sw, s_kh, fill=1, stroke=1)

    # Høyre sidestolpe
    c.rect(karm_x + s_kw - s_sw, karm_y, s_sw, s_kh, fill=1, stroke=1)

    # Toppstykke
    c.rect(karm_x, karm_y + s_kh - top_h, s_kw, top_h, fill=1, stroke=1)


def _draw_blades(c: canvas.Canvas, door: DoorParams,
                 blade_x: float, blade_y: float,
                 s_bw: float, s_bh: float,
                 color: Color, scale: float) -> None:
    """Tegner dørblad (1- eller 2-fløyet)."""
    c.setFillColor(color)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.8)

    if door.floyer == 1:
        c.rect(blade_x, blade_y, s_bw, s_bh, fill=1, stroke=1)
    else:
        # 2-fløyet: fordel etter floyer_split med 4mm gap
        gap = mm_to_scaled(4, scale)
        split_frac = door.floyer_split / 100.0
        blade1_w = (s_bw - gap) * split_frac
        blade2_w = (s_bw - gap) * (1.0 - split_frac)

        c.rect(blade_x, blade_y, blade1_w, s_bh, fill=1, stroke=1)
        c.rect(blade_x + blade1_w + gap, blade_y, blade2_w, s_bh, fill=1, stroke=1)


def _draw_hinges(c: canvas.Canvas, door: DoorParams,
                 blade_x: float, blade_y: float,
                 s_bw: float, s_bh: float,
                 scale: float) -> None:
    """Tegner hengsler på korrekt side."""
    count = door.hinge_count
    if count <= 0:
        return

    hinge_w = mm_to_scaled(15, scale)
    hinge_h = mm_to_scaled(60, scale)

    # Hengselposisjoner (fra bunn)
    if count == 1:
        positions = [0.5]
    elif count == 2:
        positions = [0.12, 0.88]
    elif count == 3:
        positions = [0.12, 0.5, 0.88]
    else:
        step = 0.76 / (count - 1) if count > 1 else 0
        positions = [0.12 + i * step for i in range(count)]

    c.setFillColor(COLOR_HINGE)
    c.setStrokeColor(black)
    c.setLineWidth(0.4)

    if door.floyer == 1:
        # 1-fløyet: hengsler på swing_direction-siden
        if door.swing_direction == 'left':
            hx = blade_x - hinge_w
        else:
            hx = blade_x + s_bw

        for pos in positions:
            hy = blade_y + s_bh * pos - hinge_h / 2
            c.rect(hx, hy, hinge_w, hinge_h, fill=1, stroke=1)
    else:
        # 2-fløyet: hengsler på ytre kanter av begge blad
        gap = mm_to_scaled(4, scale)
        split_frac = door.floyer_split / 100.0
        blade1_w = (s_bw - gap) * split_frac

        # Venstre blad — hengsler på venstre side
        hx_left = blade_x - hinge_w
        # Høyre blad — hengsler på høyre side
        hx_right = blade_x + s_bw

        for pos in positions:
            hy = blade_y + s_bh * pos - hinge_h / 2
            c.rect(hx_left, hy, hinge_w, hinge_h, fill=1, stroke=1)
            c.rect(hx_right, hy, hinge_w, hinge_h, fill=1, stroke=1)


def _draw_handle(c: canvas.Canvas, door: DoorParams,
                 blade_x: float, blade_y: float,
                 s_bw: float, s_bh: float,
                 scale: float) -> None:
    """Tegner håndtak på motsatt side av hengsler, ved 1020mm høyde."""
    handle_w = mm_to_scaled(12, scale)
    handle_h = mm_to_scaled(50, scale)
    handle_y_offset = mm_to_scaled(1020, scale)  # Standard håndtakhøyde

    # Begrens til bladhøyde
    if handle_y_offset > s_bh:
        handle_y_offset = s_bh * 0.47

    c.setFillColor(COLOR_HANDLE)
    c.setStrokeColor(black)
    c.setLineWidth(0.4)

    if door.floyer == 1:
        # Håndtak på motsatt side av hengsler
        if door.swing_direction == 'left':
            hx = blade_x + s_bw - handle_w - mm_to_scaled(15, scale)
        else:
            hx = blade_x + mm_to_scaled(15, scale)

        hy = blade_y + handle_y_offset - handle_h / 2
        c.rect(hx, hy, handle_w, handle_h, fill=1, stroke=1)
    else:
        # 2-fløyet: håndtak ved midten på begge blad
        gap = mm_to_scaled(4, scale)
        split_frac = door.floyer_split / 100.0
        blade1_w = (s_bw - gap) * split_frac
        blade2_w = (s_bw - gap) * (1.0 - split_frac)

        hy = blade_y + handle_y_offset - handle_h / 2

        # Venstre blad — håndtak på høyre side (mot midten)
        hx1 = blade_x + blade1_w - handle_w - mm_to_scaled(15, scale)
        c.rect(hx1, hy, handle_w, handle_h, fill=1, stroke=1)

        # Høyre blad — håndtak på venstre side (mot midten)
        hx2 = blade_x + blade1_w + gap + mm_to_scaled(15, scale)
        c.rect(hx2, hy, handle_w, handle_h, fill=1, stroke=1)


def _draw_swing_arc(c: canvas.Canvas, door: DoorParams,
                    blade_x: float, blade_y: float,
                    s_bw: float, s_bh: float,
                    scale: float) -> None:
    """Tegner stiplet slagbue (90° kvartbue) ved bladets nedre kant."""
    c.saveState()
    c.setStrokeColor(COLOR_SWING_ARC)
    c.setLineWidth(0.4)
    c.setDash(4, 3)

    if door.floyer == 1:
        radius = s_bw
        if door.swing_direction == 'left':
            # Hengsler venstre, dør svinger mot høyre
            cx = blade_x
            cy = blade_y
            # Bue fra 0° (høyre/lukket) til 90° (opp/åpen)
            # I reportlab: 0° = høyre (3 o'clock), 90° = opp
            c.arc(cx - radius, cy - radius, cx + radius, cy + radius,
                  startAng=0, extent=90)
        else:
            # Hengsler høyre, dør svinger mot venstre
            cx = blade_x + s_bw
            cy = blade_y
            c.arc(cx - radius, cy - radius, cx + radius, cy + radius,
                  startAng=90, extent=90)
    else:
        # 2-fløyet: bue for begge blad
        gap = mm_to_scaled(4, scale)
        split_frac = door.floyer_split / 100.0
        blade1_w = (s_bw - gap) * split_frac
        blade2_w = (s_bw - gap) * (1.0 - split_frac)

        # Venstre blad — hengsler venstre, svinger høyre
        r1 = blade1_w
        cx1 = blade_x
        cy1 = blade_y
        c.arc(cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1,
              startAng=0, extent=90)

        # Høyre blad — hengsler høyre, svinger venstre
        r2 = blade2_w
        cx2 = blade_x + s_bw
        cy2 = blade_y
        c.arc(cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2,
              startAng=90, extent=90)

    c.restoreState()


def _draw_section_line_marker(c: canvas.Canvas,
                              open_x: float, open_y: float,
                              s_bm: float, s_hm: float,
                              s_wall_ext: float, scale: float) -> None:
    """Tegner snittlinje A-A markering gjennom utsparingen."""
    # Snittlinje ved ~1000mm høyde (eller midt på bladet)
    cut_y = open_y + mm_to_scaled(1000, scale)

    # Begrens til innenfor utsparingen
    if cut_y > open_y + s_hm * 0.7:
        cut_y = open_y + s_hm * 0.45

    line_left = open_x - s_wall_ext - 8 * mm
    line_right = open_x + s_bm + s_wall_ext + 8 * mm

    c.saveState()
    c.setStrokeColor(COLOR_SECTION_LINE)
    c.setLineWidth(0.6)
    c.setDash([8, 3, 2, 3])  # Lang-kort strek-mønster
    c.line(line_left + 8 * mm, cut_y, line_right - 8 * mm, cut_y)
    c.setDash()

    # A-markører (sirkler med "A")
    marker_r = 3.5 * mm
    for mx in [line_left + 4 * mm, line_right - 4 * mm]:
        c.setFillColor(white)
        c.setStrokeColor(COLOR_SECTION_LINE)
        c.setLineWidth(0.6)
        c.circle(mx, cut_y, marker_r, fill=1, stroke=1)
        c.setFillColor(COLOR_SECTION_LINE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(mx, cut_y - 3, "A")

    c.restoreState()


def _draw_front_dimensions(c: canvas.Canvas, door: DoorParams,
                           open_x: float, open_y: float,
                           s_bm: float, s_hm: float,
                           karm_x: float, karm_y: float,
                           s_kw: float, s_kh: float,
                           blade_x: float, blade_y: float,
                           s_bw: float, s_bh: float,
                           scale: float) -> None:
    """Tegner stakkede mållinjer under og til høyre for frontvisningen."""

    bm = door.width
    hm = door.height
    kw = door.karm_width()
    kh = door.karm_height()
    bw = door.blade_width()
    bh = door.blade_height()
    bt90 = door.transport_width_90()
    bt180 = door.transport_width_180()
    ht = door.transport_height_by_threshold()

    # --- HORISONTALE MÅLLINJER (under døren) ---
    ref_y = open_y  # Referansepunkt (bunn av utsparing)

    # Samle horisontale mål (innerst til ytterst)
    h_dims = []

    # BB (Bladbredde) — bare hvis ulik BT90°
    if bw != bt90:
        h_dims.append((blade_x, blade_x + s_bw, "BB", bw))

    # BM (Utsparingsbredde)
    h_dims.append((open_x, open_x + s_bm, "BM", bm))

    # KB (Karmbredde)
    if kw != bm:
        h_dims.append((karm_x, karm_x + s_kw, "KB", kw))

    # BT90° (Transportbredde 90°)
    if bt90 is not None:
        s_bt90 = mm_to_scaled(bt90, scale)
        bt90_x = (open_x + s_bm / 2) - s_bt90 / 2
        h_dims.append((bt90_x, bt90_x + s_bt90, "BT90°", bt90))

    # BT180° (Transportbredde 180°)
    if bt180 is not None:
        s_bt180 = mm_to_scaled(bt180, scale)
        bt180_x = (open_x + s_bm / 2) - s_bt180 / 2
        h_dims.append((bt180_x, bt180_x + s_bt180, "BT180°", bt180))

    for i, (x_l, x_r, label, val) in enumerate(h_dims):
        y_pos = ref_y - DIM_OFFSET - i * DIM_SPACING
        draw_dimension_line_h(c, x_l, x_r, y_pos, ref_y, ref_y, label, val)

    # --- VERTIKALE MÅLLINJER (til høyre for døren) ---
    # Referanse: høyre kant av det bredeste elementet
    ref_x = max(open_x + s_bm, karm_x + s_kw)

    v_dims = []

    # BH (Bladhøyde)
    v_dims.append((blade_y, blade_y + s_bh, "BH", bh))

    # HM (Utsparingshøyde)
    if hm != bh:
        v_dims.append((open_y, open_y + s_hm, "HM", hm))

    # KH (Karmhøyde)
    if kh != hm:
        v_dims.append((karm_y, karm_y + s_kh, "KH", kh))

    # HT (Transporthøyde)
    if ht is not None and ht != bh:
        s_ht = mm_to_scaled(ht, scale)
        v_dims.append((open_y, open_y + s_ht, "HT", ht))

    for i, (y_b, y_t, label, val) in enumerate(v_dims):
        x_pos = ref_x + DIM_OFFSET + i * DIM_SPACING
        draw_dimension_line_v(c, y_b, y_t, x_pos, ref_x, ref_x, label, val)


# ============================================================================
# HORISONTALSNITT A-A
# ============================================================================

def _draw_horizontal_section(c: canvas.Canvas, door: DoorParams,
                             area_x: float, area_y: float,
                             area_w: float, area_h: float,
                             front_scale: float) -> None:
    """Tegner horisontalsnitt A-A (plansnitt gjennom døren sett ovenfra)."""

    # Tittel
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(area_x + 5 * mm, area_y + area_h - 5 * mm, "SNITT A — A")

    # Profilens data
    profile = KARM_SECTION_PROFILES.get(door.karm_type)
    if not profile:
        return

    wall_t = door.thickness
    bm = door.width

    # Dybde-skala (forstørret for å vise profilen tydelig)
    # Beregn tilgjengelig plass
    section_draw_h = area_h - 15 * mm  # Plass under tittelen
    section_draw_y = area_y + 5 * mm

    # Totale dybde som skal vises (mm)
    if profile.get('no_listverk'):
        total_depth_mm = profile['karm_depth'] + 20  # Litt luft
    else:
        listverk_t = profile.get('listverk_t', 7)
        if profile['both_sides']:
            total_depth_mm = wall_t + 2 * listverk_t + 20
        else:
            kobling_d = profile.get('kobling_depth_fixed', wall_t) or wall_t
            total_depth_mm = kobling_d + listverk_t + 20

    # Bruk bredde-skala fra frontvisning for X-aksen
    w_scale = front_scale

    # Beregn dybde-skala (Y-aksen i snittet)
    avail_depth = section_draw_h - 20 * mm  # Plass til mål
    d_scale_required = total_depth_mm / (avail_depth / mm)
    # Velg en pent skala-tall
    d_scales = [1, 2, 3, 5, 10, 15, 20]
    d_scale = d_scales[-1]
    for ds in d_scales:
        if ds >= d_scale_required:
            d_scale = ds
            break

    def s_w(val_mm):
        """Skaler bredde-verdi (mm → PDF-punkter)."""
        return mm_to_scaled(val_mm, w_scale)

    def s_d(val_mm):
        """Skaler dybde-verdi (mm → PDF-punkter)."""
        return mm_to_scaled(val_mm, d_scale)

    # Sentrer snittet horisontalt i tegneområdet
    s_bm = s_w(bm)
    wall_ext_w = s_w(80)  # Vegg som vises
    total_section_w = s_bm + 2 * wall_ext_w

    center_x = area_x + area_w / 2
    section_left = center_x - total_section_w / 2

    # Vertikal posisjon (front nederst, bak øverst)
    # Front-overflate Y-posisjon
    front_surface_y = section_draw_y + 10 * mm

    # --- VEGG (skravert stripe) ---
    s_wall_t = s_d(wall_t)

    # Venstre vegg
    c.setFillColor(COLOR_WALL_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.4)
    c.rect(section_left, front_surface_y, wall_ext_w, s_wall_t, fill=1, stroke=1)
    draw_hatch_pattern(c, section_left, front_surface_y,
                       wall_ext_w, s_wall_t, spacing=2.5 * mm)

    # Høyre vegg
    right_wall_x = section_left + wall_ext_w + s_bm
    c.setFillColor(COLOR_WALL_FILL)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.4)
    c.rect(right_wall_x, front_surface_y, wall_ext_w, s_wall_t, fill=1, stroke=1)
    draw_hatch_pattern(c, right_wall_x, front_surface_y,
                       wall_ext_w, s_wall_t, spacing=2.5 * mm)

    # Vegglinje over utsparing (bakside)
    # Topp-strek for veggens bakside
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.4)
    back_y = front_surface_y + s_wall_t
    c.line(section_left, back_y, section_left + wall_ext_w, back_y)
    c.line(right_wall_x, back_y, right_wall_x + wall_ext_w, back_y)

    # --- KARMPROFIL ---
    open_left = section_left + wall_ext_w  # Venstre kant av utsparing
    open_right = open_left + s_bm  # Høyre kant av utsparing

    _draw_section_profile(c, door, profile,
                          open_left, open_right,
                          front_surface_y, s_wall_t,
                          s_w, s_d, w_scale, d_scale)

    # --- DIMENSJONER I SNITTET ---
    # Veggtykkelse
    dim_x = section_left - 8 * mm
    c.setStrokeColor(COLOR_DIMENSION)
    c.setFillColor(COLOR_DIMENSION)
    c.setLineWidth(0.3)

    # Vertikale forlengelseslinjer for VT-mål
    gap = 1.5 * mm
    c.line(section_left - gap, front_surface_y, dim_x - 2 * mm, front_surface_y)
    c.line(section_left - gap, back_y, dim_x - 2 * mm, back_y)
    c.line(dim_x, front_surface_y, dim_x, back_y)
    draw_arrow(c, dim_x, front_surface_y, 'up', 1.2 * mm)
    draw_arrow(c, dim_x, back_y, 'down', 1.2 * mm)

    c.setFont("Helvetica", 6)
    vt_text = f"VT {wall_t}"
    c.saveState()
    c.translate(dim_x - 4, (front_surface_y + back_y) / 2)
    c.rotate(90)
    tw = c.stringWidth(vt_text, "Helvetica", 6)
    c.drawString(-tw / 2, 0, vt_text)
    c.restoreState()

    # Skala-indikator for snittet
    c.setFillColor(Color(0.4, 0.4, 0.4))
    c.setFont("Helvetica", 7)
    scale_text = f"Bredde 1:{int(w_scale)}, Dybde 1:{int(d_scale)}"
    c.drawString(area_x + area_w - c.stringWidth(scale_text, "Helvetica", 7) - 5 * mm,
                 area_y + area_h - 5 * mm, scale_text)


def _draw_section_profile(c: canvas.Canvas, door: DoorParams, profile: dict,
                          open_left: float, open_right: float,
                          front_y: float, s_wall_t: float,
                          s_w, s_d,
                          w_scale: float, d_scale: float) -> None:
    """Tegner karmprofilen i horisontalsnitt per karmtype."""
    karm_color = ral_to_color(door.karm_color)
    door_color = ral_to_color(door.color)
    blade_t = door.blade_thickness
    wall_t = door.thickness

    c.setLineWidth(0.4)

    if profile.get('no_listverk'):
        # --- SD3/ID ---
        karm_depth = profile['karm_depth']  # 92mm
        body_w = profile['body_w']  # 24mm
        kobling_t = profile['kobling_t']  # 5mm
        anslag_w = profile['anslag_w']  # 20mm
        anslag_d = profile['anslag_d']  # 52mm

        # Karm er sentrert i veggen
        # Karm dybde-start (front-kant) i snittet
        karm_front_y = front_y + s_wall_t / 2 - s_d(karm_depth) / 2
        s_karm_d = s_d(karm_depth)

        # VENSTRE SIDESTOLPE
        # Kropp (24mm bred, full dybde)
        c.setFillColor(karm_color)
        c.setStrokeColor(COLOR_DOOR_STROKE)
        lx = open_left + s_w(10)  # Karm innenfor utsparing (BM - 20, 10mm på hver side)
        c.rect(lx, karm_front_y, s_w(body_w), s_karm_d, fill=1, stroke=1)

        # Kobling (5mm, innerkant av kroppen)
        c.rect(lx + s_w(body_w), karm_front_y, s_w(kobling_t), s_karm_d, fill=1, stroke=1)

        # Anslag (20mm bred, fra framkant)
        anslag_x = lx + s_w(body_w) + s_w(kobling_t)
        anslag_y = karm_front_y  # Fra karm framkant
        c.rect(anslag_x, anslag_y, s_w(anslag_w), s_d(anslag_d), fill=1, stroke=1)

        # HØYRE SIDESTOLPE (speilet)
        rx = open_right - s_w(10) - s_w(body_w)
        c.rect(rx, karm_front_y, s_w(body_w), s_karm_d, fill=1, stroke=1)
        c.rect(rx - s_w(kobling_t), karm_front_y, s_w(kobling_t), s_karm_d, fill=1, stroke=1)
        r_anslag_x = rx - s_w(kobling_t) - s_w(anslag_w)
        c.rect(r_anslag_x, anslag_y, s_w(anslag_w), s_d(anslag_d), fill=1, stroke=1)

        # DØRBLAD
        blade_y = karm_front_y + s_d(karm_depth / 2 - blade_t)
        _draw_section_blade(c, door, door_color,
                            anslag_x + s_w(anslag_w), r_anslag_x,
                            blade_y, s_d(blade_t), s_w)

    else:
        # --- SD1 / SD2 ---
        listverk_w = profile['listverk_w']  # 60mm
        listverk_t = profile['listverk_t']  # 7mm
        kobling_t = profile['kobling_t']     # 5mm
        anslag_w = profile['anslag_w']       # 20mm
        anslag_d = profile['anslag_d']       # 44mm
        both_sides = profile['both_sides']
        kobling_d_fixed = profile.get('kobling_depth_fixed')
        kobling_d = kobling_d_fixed if kobling_d_fixed else wall_t

        # Dybde-positioner
        s_listverk_t = s_d(listverk_t)
        s_kobling_d = s_d(kobling_d)
        s_anslag_d = s_d(anslag_d)

        # Front listverk Y = stikker ut foran veggen
        front_list_y = front_y - s_listverk_t

        # Kobling Y = fra front veggoverflate (eller fra front listverk)
        kobling_y = front_y
        if kobling_d_fixed:
            # SD2: fast dybde fra front veggoverflate
            kobling_y = front_y + s_wall_t / 2 - s_d(kobling_d_fixed) / 2
            # Justert: kobling starter på fremre veggflate, strekker seg bakover
            kobling_y = front_y

        # Dørblad-posisjon: flush med listverk framside
        blade_z_y = front_y - s_listverk_t + s_d(blade_t)  # hmm
        # Blade y = front surface + 7(list) - blade_t = front_y - 7 + blade_pos
        # Blade Z offset er 22mm fra front (hardkodet i 3D)
        # Men i profilen: blade_y = wall_t/2 + 7 - blade_t
        # I snittet: blade front face = front_y - listverk_t (= list framside)
        # blade back face = blade front face + blade_t
        # Altså: blade_y_start = front_y - s_listverk_t
        blade_sec_y = front_y - s_listverk_t
        s_blade_t = s_d(blade_t)

        # Anslag: bak bladet
        anslag_sec_y = blade_sec_y + s_blade_t

        # VENSTRE SIDESTOLPE

        # Front listverk (60mm bred ut fra utsparing, 7mm dypt ut fra vegg)
        c.setFillColor(karm_color)
        c.setStrokeColor(COLOR_DOOR_STROKE)
        c.rect(open_left - s_w(listverk_w), front_list_y,
               s_w(listverk_w), s_listverk_t, fill=1, stroke=1)

        # Kobling (5mm bred, ved innerkant = utsparing-kanten)
        c.rect(open_left - s_w(kobling_t), kobling_y,
               s_w(kobling_t), s_kobling_d, fill=1, stroke=1)

        # Anslag (20mm inn i utsparingen, bak bladet)
        c.rect(open_left, anslag_sec_y,
               s_w(anslag_w), s_anslag_d, fill=1, stroke=1)

        # Bakside listverk (kun SD1)
        if both_sides:
            back_list_y = front_y + s_wall_t
            c.rect(open_left - s_w(listverk_w), back_list_y,
                   s_w(listverk_w), s_listverk_t, fill=1, stroke=1)

        # HØYRE SIDESTOLPE (speilet)

        # Front listverk
        c.rect(open_right, front_list_y,
               s_w(listverk_w), s_listverk_t, fill=1, stroke=1)

        # Kobling
        c.rect(open_right, kobling_y,
               s_w(kobling_t), s_kobling_d, fill=1, stroke=1)

        # Anslag
        c.rect(open_right - s_w(anslag_w), anslag_sec_y,
               s_w(anslag_w), s_anslag_d, fill=1, stroke=1)

        # Bakside listverk (kun SD1)
        if both_sides:
            c.rect(open_right, back_list_y,
                   s_w(listverk_w), s_listverk_t, fill=1, stroke=1)

        # DØRBLAD
        blade_left = open_left + s_w(anslag_w)
        blade_right = open_right - s_w(anslag_w)
        _draw_section_blade(c, door, door_color,
                            blade_left, blade_right,
                            blade_sec_y, s_blade_t, s_w)


def _draw_section_blade(c: canvas.Canvas, door: DoorParams,
                        color: Color,
                        blade_left: float, blade_right: float,
                        blade_y: float, s_blade_t: float,
                        s_w) -> None:
    """Tegner dørblad i horisontalsnitt."""
    c.setFillColor(color)
    c.setStrokeColor(COLOR_DOOR_STROKE)
    c.setLineWidth(0.5)

    if door.floyer == 1:
        c.rect(blade_left, blade_y,
               blade_right - blade_left, s_blade_t,
               fill=1, stroke=1)
    else:
        # 2-fløyet: to blad med gap
        gap = s_w(4)
        total_w = blade_right - blade_left
        split_frac = door.floyer_split / 100.0
        b1_w = (total_w - gap) * split_frac
        b2_w = (total_w - gap) * (1.0 - split_frac)

        c.rect(blade_left, blade_y, b1_w, s_blade_t, fill=1, stroke=1)
        c.rect(blade_left + b1_w + gap, blade_y, b2_w, s_blade_t, fill=1, stroke=1)
