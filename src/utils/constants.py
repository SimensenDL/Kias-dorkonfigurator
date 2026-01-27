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
    'SDI':  'SDI - Slag/Innerdør',
    'KD':   'KD - Kjøledør',
    'PDPC': 'PDPC - Pendel Polykarbonat',
    'PDPO': 'PDPO - Pendel Opalkvit',
    'PDI':  'PDI - Pendel Isolert',
    'SKD':  'SKD - Skyvedør 40/60',
    'BD':   'BD - Branndør B30',
    'BRY':  'BRY - Brakke Ytter',
    'BRI':  'BRI - Brakke Inner',
    'FD':   'FD - Fjøs Ytter',
    'ID':   'ID - Inner m/notspor',
    'BO':   'BO - Bod m/notspor',
}

# Standardmål per dørtype (bredde, høyde, tykkelse i mm)
DEFAULT_DIMENSIONS = {
    'SDI':  {'width': 900, 'height': 2100, 'thickness': 40},
    'KD':   {'width': 900, 'height': 2100, 'thickness': 80},
    'PDPC': {'width': 900, 'height': 2100, 'thickness': 50},
    'PDPO': {'width': 900, 'height': 2100, 'thickness': 50},
    'PDI':  {'width': 900, 'height': 2100, 'thickness': 50},
    'SKD':  {'width': 1200, 'height': 2100, 'thickness': 50},
    'BD':   {'width': 900, 'height': 2100, 'thickness': 60},
    'BRY':  {'width': 900, 'height': 2100, 'thickness': 40},
    'BRI':  {'width': 900, 'height': 2100, 'thickness': 40},
    'FD':   {'width': 1000, 'height': 2100, 'thickness': 50},
    'ID':   {'width': 900, 'height': 2100, 'thickness': 40},
    'BO':   {'width': 900, 'height': 2100, 'thickness': 50},
}

# Karmtyper per dørtype (hvilke karmtyper som er tilgjengelige)
DOOR_KARM_TYPES = {
    'SDI':  ['SD1', 'SD2', 'SD3'],
    'KD':   ['KD1', 'KD2', 'KD3'],
    'PDPC': ['PD1', 'PD2'],
    'PDPO': ['PD1', 'PD2'],
    'PDI':  ['PD1', 'PD2'],
    'SKD':  ['SKD1', 'SKD2'],
    'BD':   ['SD1'],
    'BRY':  ['BR1'],
    'BRI':  ['BI1'],
    'FD':   ['FD1', 'FD2', 'FD3'],
    'ID':   ['ID1'],
    'BO':   ['BO1'],
}

# Antall fløyer per dørtype (tillatte verdier)
DOOR_FLOYER = {
    'SDI':  [1, 2],
    'KD':   [1, 2],
    'PDPC': [1, 2],
    'PDPO': [1, 2],
    'PDI':  [1, 2],
    'SKD':  [1],
    'BD':   [1],
    'BRY':  [1, 2],
    'BRI':  [1],
    'FD':   [1, 2],
    'ID':   [1],
    'BO':   [1],
}

# Dimensjonsgrenser (mm)
MIN_WIDTH = 500
MAX_WIDTH = 3000
MIN_HEIGHT = 1500
MAX_HEIGHT = 3500
MIN_THICKNESS = 20
MAX_THICKNESS = 200

# Slagretning
SWING_DIRECTIONS = {
    'left': 'Venstre',
    'right': 'Høyre',
}

# Overflatetyper
SURFACE_TYPES = {
    'glatt': 'Glatt',
    'struktur': 'Struktur',
    'treverk': 'Treverkimitasjon',
}

# Terskeltyper (intern nøkkel → visningsnavn)
THRESHOLD_TYPES = {
    'luftspalte': 'Luftspalte',
    'total_hev_senk': 'Total hev/senk',
    'slepelist': 'Slepelist',
    'standard': 'Standard',
    'kjorbar_terskel': 'Kjørbar terskel',
    'hc1': 'HC1',
    'hc2': 'HC2',
}

# Faste luftspalte-verdier per terskeltype (mm)
# For 'luftspalte' er verdien redigerbar, standardverdien er her
THRESHOLD_LUFTSPALTE = {
    'luftspalte': 22,
    'total_hev_senk': 18,
    'slepelist': 22,
    'standard': 22,
    'kjorbar_terskel': 13,
    'hc1': 8,
    'hc2': 15,
}

# Brannklasser (for branndør)
FIRE_RATINGS = ['', 'EI30', 'EI60', 'EI90', 'EI120']

# Lydklasser (dB, for lyddør)
SOUND_RATINGS = [0, 30, 35, 40, 45, 50]

# RAL-farger for dører
RAL_COLORS = {
    'RAL 9010': {'name': 'Renhvit', 'hex': '#F1ECE1', 'rgb': (0.945, 0.925, 0.882)},
    'RAL 7047': {'name': 'Lysgrå', 'hex': '#C8C8C7', 'rgb': (0.784, 0.784, 0.780)},
    'RAL 7004': {'name': 'Signalgrå', 'hex': '#9B9B9B', 'rgb': (0.608, 0.608, 0.608)},
    'RAL 9005': {'name': 'Dyp svart', 'hex': '#0E0E10', 'rgb': (0.055, 0.055, 0.063)},
    'RAL 7016': {'name': 'Antrasittgrå', 'hex': '#383E42', 'rgb': (0.220, 0.243, 0.259)},
    'RAL 1018': {'name': 'Sinkgul', 'hex': '#FACA30', 'rgb': (0.980, 0.792, 0.188)},
    'RAL 6027': {'name': 'Lysgrønn', 'hex': '#7EBAB5', 'rgb': (0.494, 0.729, 0.710)},
    'RAL 5012': {'name': 'Lysblå', 'hex': '#0089B6', 'rgb': (0.0, 0.537, 0.714)},
    'RAL 8024': {'name': 'Beigebrun', 'hex': '#795038', 'rgb': (0.475, 0.314, 0.220)},
}

# Standard fargevalg
DEFAULT_COLOR = 'RAL 9010'

# PDF eksportinnstillinger
PDF_SCALE = 10  # 1:10 (dører er mindre enn bygninger)
