"""
Konstanter for PDF-eksport.
Farger, sidestørrelser, marginer og firmainformasjon.
"""
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, white


def get_base_path() -> Path:
    """Returnerer rot-stien for ressurser (fungerer både i dev og PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent.parent


# Tegnefarger
COLOR_DOOR_FILL = Color(0.78, 0.78, 0.78)       # Lys grå for dør
COLOR_DOOR_STROKE = Color(0.2, 0.2, 0.2)        # Mørk grå for dørkonturer
COLOR_FRAME_FILL = Color(0.55, 0.55, 0.55)      # Grå for karm
COLOR_DIMENSION = Color(0, 0, 0.7)              # Blå for dimensjoner
COLOR_TITLE_BG = white                            # Hvit bakgrunn for tittelfelt
COLOR_HINGE = Color(0.3, 0.3, 0.3)              # Mørk for hengsler
COLOR_HANDLE = Color(0.15, 0.15, 0.15)          # Mørk for håndtak

# Vegg- og snittfarger
COLOR_WALL_FILL = Color(0.88, 0.88, 0.88)       # Lys grå veggfylling
COLOR_WALL_HATCH = Color(0.55, 0.55, 0.55)      # Mørkere grå for skraveringslinjer
COLOR_SECTION_CUT = Color(0.45, 0.45, 0.45)     # Grå for snitt-kuttflater
COLOR_SWING_ARC = Color(0, 0, 0)                # Svart stiplet slagbue
COLOR_SECTION_LINE = Color(0, 0, 0.7)           # Blå for snittlinje A-A

# Karmprofil-dimensjoner for horisontalsnitt (mm)
KARM_SECTION_PROFILES = {
    'SD1': {
        'listverk_w': 60, 'listverk_t': 7,
        'kobling_t': 5,
        'anslag_w': 20, 'anslag_d': 44,
        'blade_t': 40,
        'both_sides': True,
        'no_listverk': False,
        'kobling_depth_fixed': None,  # Bruker wall_t
    },
    'SD2': {
        'listverk_w': 60, 'listverk_t': 7,
        'kobling_t': 5,
        'anslag_w': 20, 'anslag_d': 44,
        'blade_t': 40,
        'both_sides': False,
        'no_listverk': False,
        'kobling_depth_fixed': 77,
    },
    'SD3/ID': {
        'body_w': 24,
        'kobling_t': 5,
        'anslag_w': 20, 'anslag_d': 52,
        'blade_t': 40,
        'karm_depth': 92,
        'both_sides': False,
        'no_listverk': True,
    },
    'KD1': {
        'listverk_w': 80, 'listverk_t': 7,
        'kobling_t': 5,
        'anslag_w': 20, 'anslag_d': 24,
        'blade_t': 60,
        'both_sides': True,
        'no_listverk': False,
        'kobling_depth_fixed': None,
    },
    'KD2': {
        'listverk_w': 80, 'listverk_t': 7,
        'kobling_t': 5,
        'anslag_w': 20, 'anslag_d': 24,
        'blade_t': 60,
        'both_sides': False,
        'no_listverk': False,
        'kobling_depth_fixed': 97,
    },
}

# Sidedimensjoner (A3 liggende for dør-tegninger)
A3_WIDTH, A3_HEIGHT = landscape(A3)
A4_WIDTH, A4_HEIGHT = landscape(A4)
A3_MARGIN = 15 * mm
A4_MARGIN = 10 * mm

# A4 portrett (for kappeliste etc.)
A4_PORT_WIDTH, A4_PORT_HEIGHT = A4          # 595 x 842 pt
A4_PORT_MARGIN = 15 * mm

# Firmainformasjon for tittelfelt
COMPANY_NAME = "KVANNE INDUSTRIER AS"
COMPANY_ADDRESS = "6652 Surnadal - post@kvanne.no"
DRAWING_STATUS = "Produksjonstegning"
COLOR_COMPANY_BLUE = Color(0, 0.2, 0.5)
COLOR_KIAS_YELLOW = Color(1.0, 0.757, 0.027)   # #FFC107

# Logo-fil (SVG, renderes via svglib)
LOGO_PATH = get_base_path() / "assets" / "KIAS-dorer-logo.svg"
