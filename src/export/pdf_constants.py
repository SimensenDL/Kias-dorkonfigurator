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
COLOR_GLASS = Color(0.8, 0.9, 1.0)              # Lyseblå for glass
COLOR_DIMENSION = Color(0, 0, 0.7)              # Blå for dimensjoner
COLOR_TITLE_BG = white                            # Hvit bakgrunn for tittelfelt
COLOR_HINGE = Color(0.3, 0.3, 0.3)              # Mørk for hengsler
COLOR_HANDLE = Color(0.15, 0.15, 0.15)          # Mørk for håndtak

# Sidedimensjoner (A3 liggende for dør-tegninger)
A3_WIDTH, A3_HEIGHT = landscape(A3)
A4_WIDTH, A4_HEIGHT = landscape(A4)
A3_MARGIN = 15 * mm
A4_MARGIN = 10 * mm

# Firmainformasjon for tittelfelt
COMPANY_NAME = "KVANNE INDUSTRIER AS"
COMPANY_ADDRESS = "6652 Surnadal - post@kvanne.no"
DRAWING_STATUS = "Produksjonstegning"
COLOR_COMPANY_BLUE = Color(0, 0.2, 0.5)

# Logo-fil (SVG, renderes via svglib)
LOGO_PATH = get_base_path() / "assets" / "KIAS-dorer-logo.svg"
