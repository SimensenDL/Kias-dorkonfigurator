"""
Applikasjonskonstanter og standardverdier for KIAS Dørkonfigurator.
Alle dimensjoner i millimeter (mm).
"""

# Applikasjonsinfo
APP_NAME = "KIAS Dørkonfigurator"
APP_VERSION = "0.1.0"
PROJECT_EXTENSION = ".kdf"
PROJECT_FILTER = f"KIAS Dørfil (*{PROJECT_EXTENSION})"

# Dørtyper (intern nøkkel → visningsnavn)
DOOR_TYPES = {
    'innerdor': 'Innerdør',
    'kjoleromsdor': 'Kjøleromsdør',
    'pendeldor': 'Pendeldør',
    'branndor': 'Branndør',
    'bod_garasje': 'Bod-/Garasjedør',
    'skyvedor': 'Skyvedør',
    'lyddor': 'Lyddør',
    'fjosdor': 'Fjøsdør',
    'brakkedor': 'Brakkedør',
    'rontgendor': 'Røntgendør',
}

# Standardmål per dørtype (bredde, høyde, tykkelse i mm)
DEFAULT_DIMENSIONS = {
    'innerdor':     {'width': 900, 'height': 2100, 'thickness': 40},
    'kjoleromsdor': {'width': 900, 'height': 2100, 'thickness': 80},
    'pendeldor':    {'width': 900, 'height': 2100, 'thickness': 50},
    'branndor':     {'width': 900, 'height': 2100, 'thickness': 60},
    'bod_garasje':  {'width': 900, 'height': 2100, 'thickness': 50},
    'skyvedor':     {'width': 1200, 'height': 2100, 'thickness': 50},
    'lyddor':       {'width': 900, 'height': 2100, 'thickness': 70},
    'fjosdor':      {'width': 1000, 'height': 2100, 'thickness': 50},
    'brakkedor':    {'width': 900, 'height': 2100, 'thickness': 40},
    'rontgendor':   {'width': 900, 'height': 2100, 'thickness': 80},
}

# Dimensjonsgrenser (mm)
MIN_WIDTH = 500
MAX_WIDTH = 3000
MIN_HEIGHT = 1500
MAX_HEIGHT = 3500
MIN_THICKNESS = 20
MAX_THICKNESS = 200

# Hengsle-sider
HINGE_SIDES = {
    'left': 'Venstre',
    'right': 'Høyre',
}

# Overflatetyper
SURFACE_TYPES = {
    'glatt': 'Glatt',
    'struktur': 'Struktur',
    'treverk': 'Treverkimitasjon',
}

# Brannklasser (for branndør)
FIRE_RATINGS = ['', 'EI30', 'EI60', 'EI90', 'EI120']

# Lydklasser (dB, for lyddør)
SOUND_RATINGS = [0, 30, 35, 40, 45, 50]

# RAL-farger (et utvalg vanlige farger for dører)
RAL_COLORS = {
    'RAL 1015': {'name': 'Elfenbenshvit', 'hex': '#E6D2B5', 'rgb': (0.902, 0.824, 0.710)},
    'RAL 3000': {'name': 'Flamrød', 'hex': '#A72920', 'rgb': (0.655, 0.161, 0.125)},
    'RAL 5010': {'name': 'Gentianblå', 'hex': '#004F7C', 'rgb': (0.0, 0.310, 0.486)},
    'RAL 6029': {'name': 'Mintgrønn', 'hex': '#006F3D', 'rgb': (0.0, 0.435, 0.239)},
    'RAL 7016': {'name': 'Antrasittgrå', 'hex': '#383E42', 'rgb': (0.220, 0.243, 0.259)},
    'RAL 7035': {'name': 'Lysgrå', 'hex': '#C5C7C4', 'rgb': (0.773, 0.780, 0.769)},
    'RAL 7040': {'name': 'Vindusgrå', 'hex': '#989EA1', 'rgb': (0.596, 0.620, 0.631)},
    'RAL 8017': {'name': 'Sjokoladebrun', 'hex': '#442F29', 'rgb': (0.267, 0.184, 0.161)},
    'RAL 9001': {'name': 'Kremhvit', 'hex': '#E9E0D2', 'rgb': (0.914, 0.878, 0.824)},
    'RAL 9010': {'name': 'Renhvit', 'hex': '#F1EDE1', 'rgb': (0.945, 0.929, 0.882)},
    'RAL 9016': {'name': 'Trafikkhvit', 'hex': '#F1F0EA', 'rgb': (0.945, 0.941, 0.918)},
}

# Standard fargevalg
DEFAULT_COLOR_OUTSIDE = 'RAL 9010'
DEFAULT_COLOR_INSIDE = 'RAL 9010'

# PDF eksportinnstillinger
PDF_SCALE = 10  # 1:10 (dører er mindre enn bygninger)
