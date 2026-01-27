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
    'SDI':  'SDI - Innerdør',
    'KD':   'KD - Kjøleromsdør',
    'PD':   'PD - Pendeldør',
    'SK':   'SK - Skyvedør',
    'BD':   'BD - Branndør B30',
    'BR':   'BR - Brakkedør',
    'FD':   'FD - Fjøsdør',
    'BO':   'BO - Bod-/Garasjedør',
    'LDI':  'LDI - Lyddør',
    'RD':   'RD - Røntgendør',
}

# Standardmål per dørtype (bredde, høyde, veggtykkelse i mm)
# Veggtykkelse må samsvare med karmtypens støttede område (se karmtype-dokumentasjon)
DEFAULT_DIMENSIONS = {
    'SDI':  {'width': 900, 'height': 2100, 'thickness': 100},   # SD1: 70-110 mm
    'KD':   {'width': 900, 'height': 2100, 'thickness': 80},    # KD1: 70-110 mm
    'PD':   {'width': 900, 'height': 2100, 'thickness': 100},   # PD1: 70-110 mm
    'SK':   {'width': 1200, 'height': 2100, 'thickness': 50},   # SK1: ikke dokumentert
    'BD':   {'width': 900, 'height': 2100, 'thickness': 100},   # SD1: 70-110 mm
    'BR':   {'width': 900, 'height': 2100, 'thickness': 40},    # BR1: 40-44 mm
    'FD':   {'width': 1000, 'height': 2100, 'thickness': 100},  # SD1 antatt: 70-110 mm
    'BO':   {'width': 900, 'height': 2100, 'thickness': 50},    # BO1: ikke dokumentert
    'LDI':  {'width': 900, 'height': 2100, 'thickness': 100},   # SD1: 70-110 mm
    'RD':   {'width': 900, 'height': 2100, 'thickness': 100},   # SD1: 70-110 mm
}

# Karmtyper per dørtype (hvilke karmtyper som er tilgjengelige)
DOOR_KARM_TYPES = {
    'SDI':  ['SD1', 'SD2', 'SD3/ID1'],
    'KD':   ['KD1', 'KD2', 'KD3'],
    'PD':   ['PD1', 'PD2'],
    'SK':   ['SK1'],
    'BD':   ['SD1'],
    'BR':   ['BR1'],
    'FD':   ['SD1', 'SD2', 'SD3/ID1'],  # Antatt – ikke spesifisert i dokumentasjon
    'BO':   ['BO1'],
    'LDI':  ['SD1', 'SD2', 'SD3/ID1'],
    'RD':   ['SD1', 'SD2', 'SD3/ID1'],
}

# Antall fløyer per dørtype (tillatte verdier)
DOOR_FLOYER = {
    'SDI':  [1, 2],
    'KD':   [1, 2],
    'PD':   [1, 2],
    'SK':   [1],
    'BD':   [1],
    'BR':   [1, 2],
    'FD':   [1, 2],
    'BO':   [1],
    'LDI':  [1, 2],
    'RD':   [1, 2],
}

# Dørbladtyper (nøkkel → navn + tykkelser)
DOOR_BLADE_TYPES = {
    'KD_ISOLERT': {
        'name': 'Isolert kjøleromsdørblad',
        'thicknesses': [40, 60],
    },
    'SDI_ROCA': {
        'name': 'Innerdørblad m/ROCA',
        'thicknesses': [40],
    },
    'SDI_SNAPIN': {
        'name': 'Innerdørblad m/Snap-in',
        'thicknesses': [40],
    },
    'SKD_STYRESPOR': {
        'name': 'Skyvedørblad m/styrespor',
        'thicknesses': [40],
    },
    'PDI_ISOLERT': {
        'name': 'Isolert pendeldørblad',
        'thicknesses': [40],
    },
    'PDPC_POLY': {
        'name': 'Pendeldørblad polykarbonat',
        'thicknesses': [5],
    },
    'PDPO_OPAL': {
        'name': 'Pendeldørblad opalhvit',
        'thicknesses': [5],
    },
    'BD_ROCKWOOL': {
        'name': 'Branndørblad m/Rockwool',
        'thicknesses': [40],
    },
    'RD_BLY': {
        'name': 'Røntgendørblad m/blyinnlegg',
        'thicknesses': [40],
    },
    'LDI_LYD': {
        'name': 'Lyddørblad m/lyddempning',
        'thicknesses': [40],
    },
}

# Kompatible dørbladtyper per karmtype
KARM_BLADE_TYPES = {
    'SD1':     ['SDI_ROCA', 'SDI_SNAPIN'],
    'SD2':     ['SDI_ROCA', 'SDI_SNAPIN'],
    'SD3/ID1': ['SDI_ROCA', 'SDI_SNAPIN'],
    'KD1':     ['KD_ISOLERT'],
    'KD2':     ['KD_ISOLERT'],
    'KD3':     ['KD_ISOLERT'],
    'PD1':     ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    'PD2':     ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    'SK1':     ['SKD_STYRESPOR'],
    'BR1':     ['SDI_ROCA', 'SDI_SNAPIN'],
    'BO1':     ['SDI_ROCA', 'SDI_SNAPIN'],
}

# Dørtype-spesifikke dørbladtyper (overstyrer karm-basert oppslag)
# Disse dørtypene har spesialisert dørblad som skiller seg fra standard innerdørblad
DOOR_TYPE_BLADE_OVERRIDE = {
    'BD':  ['BD_ROCKWOOL'],   # Branndør: Rockwool (steinull) isolasjon
    'RD':  ['RD_BLY'],        # Røntgendør: blyinnlegg i dørblad
    'LDI': ['LDI_LYD'],       # Lyddør: lyddempende materialer
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

# Brannklasser (for branndør) - KIAS produserer kun B30
FIRE_RATINGS = ['', 'B30']

# Lydklasser (dB, for lyddør) - KIAS tilbyr Rw30 og Rw32
SOUND_RATINGS = [0, 30, 32]

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
