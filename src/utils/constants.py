"""
Applikasjonskonstanter og standardverdier for KIAS Dørkonfigurator.
Alle dimensjoner i millimeter (mm).
"""

# Applikasjonsinfo
APP_NAME = "KIAS Dørkonfigurator"
APP_VERSION = "0.3.0"
PROJECT_EXTENSION = ".kdf"
PROJECT_FILTER = f"KIAS Dørfil (*{PROJECT_EXTENSION})"

# Dørtyper (intern nøkkel → visningsnavn)
DOOR_TYPES = {
    'SDI':  'Innerdør',
    'KD':   'Kjøleromsdør',
    'YD':   'Ytterdør',
    'PD':   'Pendeldør',
    'BD':   'Branndør',
}

# Standardmål per dørtype (bredde, høyde, veggtykkelse i mm)
DEFAULT_DIMENSIONS = {
    'SDI':  {'width': 1010, 'height': 2110, 'thickness': 100},
    'KD':   {'width': 1010, 'height': 2110, 'thickness': 80},
    'YD':   {'width': 1010, 'height': 2110, 'thickness': 100},
    'PD':   {'width': 1010, 'height': 2110, 'thickness': 100},
    'BD':   {'width': 1010, 'height': 2110, 'thickness': 100},
}

# Karmtyper per dørtype
DOOR_KARM_TYPES = {
    'SDI':  ['SD1', 'SD2', 'SD3/ID1'],
    'KD':   ['KD1', 'KD2', 'KD3'],
    'YD':   ['YD1', 'YD2', 'YD3'],
    'PD':   ['PD1', 'PD2'],
    'BD':   ['BD1', 'BD2'],
}

# Utforing-steg for karmer (veggtykkelse-område i mm)
UTFORING_RANGES = {
    '70-110':  {'min': 70, 'max': 110, 'name': '70-110 mm'},
    '100-140': {'min': 100, 'max': 140, 'name': '100-140 mm'},
    '130-170': {'min': 130, 'max': 170, 'name': '130-170 mm'},
    '160-200': {'min': 160, 'max': 200, 'name': '160-200 mm'},
    '200-300': {'min': 200, 'max': 300, 'name': '200-300 mm'},
}

# Karmer som støtter utforing (kun type 1)
KARM_HAS_UTFORING = {'SD1', 'KD1', 'PD1', 'BD1'}

# Maks veggtykkelse for karmer med utforing (over dette skjules de)
UTFORING_MAX_THICKNESS = 300

# Antall fløyer per dørtype
DOOR_FLOYER = {
    'SDI':  [1, 2],
    'KD':   [1, 2],
    'YD':   [1, 2],
    'PD':   [1, 2],
    'BD':   [1],
}

# Dørbladtyper (nøkkel → navn + tykkelser)
DOOR_BLADE_TYPES = {
    'SDI_ROCA': {
        'name': 'Innerdørblad m/ROCA',
        'thicknesses': [40],
    },
    'SDI_SNAPIN': {
        'name': 'Innerdørblad m/Snap-in',
        'thicknesses': [40],
    },
    'KD_ISOLERT': {
        'name': 'Isolert kjøleromsdørblad',
        'thicknesses': [60],
    },
    'YD_ISOLERT': {
        'name': 'Ytterdørblad isolert',
        'thicknesses': [60],
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
        'name': 'Pendeldørblad opalhvit polykarbonat',
        'thicknesses': [5],
    },
    'BD_ROCKWOOL': {
        'name': 'Branndørblad m/Rockwool',
        'thicknesses': [52],
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
    'YD1':     ['YD_ISOLERT'],
    'YD2':     ['YD_ISOLERT'],
    'YD3':     ['YD_ISOLERT'],
    'PD1':     ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    'PD2':     ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    'BD1':     ['BD_ROCKWOOL'],
    'BD2':     ['BD_ROCKWOOL'],
}

# Dørtype-spesifikke dørbladtyper (overstyrer karm-basert oppslag)
DOOR_TYPE_BLADE_OVERRIDE = {
    # Ingen overrides for nåværende dørtyper
}

# Dimensjonsgrenser (mm)
MIN_WIDTH = 500
MAX_WIDTH = 3000
MIN_HEIGHT = 1500
MAX_HEIGHT = 3500
MIN_THICKNESS = 20
MAX_THICKNESS = 400

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
    'ingen': 'Ingen',
    'slepelist': 'Slepelist',
    'anslag_37': 'Anslag 37',
    'anslag_kjorbar_25': 'Anslag kjørbar 25',
    'hc20': 'HC20',
    'hcid': 'HCID',
}

# Terskelhøyde per type (mm)
THRESHOLD_HEIGHT = {
    'ingen': 0,
    'slepelist': 0,
    'anslag_37': 37,
    'anslag_kjorbar_25': 25,
    'hc20': 20,
    'hcid': 0,
}

# Luftspalte-verdier per terskeltype (mm)
# For 'ingen' er verdien redigerbar, standardverdien er 22
THRESHOLD_LUFTSPALTE = {
    'ingen': 22,           # Valfritt, std. 22
    'slepelist': 22,
    'anslag_37': 22,
    'anslag_kjorbar_25': 13,
    'hc20': 8,
    'hcid': 18,
}

# Tillatte terskeltyper per karmtype
KARM_THRESHOLD_TYPES = {
    'SD1':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'SD2':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'SD3/ID1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20', 'hcid'],
    'BD1':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'BD2':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'KD1':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'KD2':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'KD3':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'YD1':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'YD2':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'YD3':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    'PD1':     ['ingen', 'slepelist'],
    'PD2':     ['ingen', 'slepelist'],
}

# Brannklasser (for branndør) - KIAS produserer kun B30
FIRE_RATINGS = ['', 'B30']

# Lydklasser (dB, for lyddør) - KIAS tilbyr Rw30 og Rw32
SOUND_RATINGS = [0, 30, 32]

# RAL-farger for dører
RAL_COLORS = {
    'RAL 9010': {'name': 'Renhvit', 'hex': '#F1ECE1', 'rgb': (0.945, 0.925, 0.882)},
    'RAL 5008': {'name': 'Gråblå', 'hex': '#2B3A44', 'rgb': (0.169, 0.227, 0.267)},
    'RAL 7016': {'name': 'Antrasittgrå', 'hex': '#383E42', 'rgb': (0.220, 0.243, 0.259)},
    'RAL 7022': {'name': 'Umbragrå', 'hex': '#4C4A44', 'rgb': (0.298, 0.290, 0.267)},
    'RAL 7047': {'name': 'Lysgrå', 'hex': '#C8C8C7', 'rgb': (0.784, 0.784, 0.780)},
    'RAL 9005': {'name': 'Dyp svart', 'hex': '#0E0E10', 'rgb': (0.055, 0.055, 0.063)},
    'RAL 9016': {'name': 'Trafikkhvit', 'hex': '#F1F0EA', 'rgb': (0.945, 0.941, 0.918)},
}

# Standard fargevalg
DEFAULT_COLOR = 'RAL 9010'

# --- Beslag og låsesystemer ---

# Hengseltyper
HINGE_TYPES = {
    'roca_sf':      'ROCA flagg i SF stål',
    'sf_staal':     'SF stål',
    'argenta':      'Argenta 100/86A',
    'kias_92':      'KIAS 92 stop',
}

# Standard hengseltype og antall per dørtype
# (hengsel-nøkkel, antall 1-fløya, antall 2-fløya per fløy)
DOOR_HINGE_DEFAULTS = {
    'SDI':  ('roca_sf', 2, 2),
    'KD':   ('roca_sf', 3, 3),
    'YD':   ('roca_sf', 3, 3),
    'PD':   ('kias_92', 0, 0),     # Pendeldør: selvlukkende hengsler
    'BD':   ('sf_staal', 3, 0),
}

# Låsekasser
LOCK_CASES = {
    '3065_316l':    '3065/316L i SF stål',
    'lk565':        'LK565',
    'assa_lk566':   'ASSA LK566 i SF stål',
    'ingen':        'Ingen (selvlukkende)',
}

# Standard låsekasse per dørtype
DOOR_LOCK_CASE_DEFAULTS = {
    'SDI':  '3065_316l',
    'KD':   '3065_316l',
    'YD':   'lk565',
    'PD':   'ingen',
    'BD':   '3065_316l',
}

# Vrider- og skiltkombinasjoner
HANDLE_TYPES = {
    'vrider_sylinder_oval':   'Vrider 519U / Sylinderskilt oval 530C SF',
    'vrider_sylinder_rund':   'Vrider 519U / Sylinderskilt rund 550C SF',
    'vrider_blindskilt':      'Vrider 519U / Blindskilt 530A SF',
    'vrider_wc':              'Vrider 519U / WC-skilt 530D SF',
    'vrider_alt_sylinder':    'Vrider 8611 / Skilt 8752 RF',
    'vrider_alt_blind':       'Vrider 8611 / Blindskilt 8755 RF',
    'plasthandtak':           'Plasthandtak (varmebestandig)',
    'ingen':                  'Ingen',
}

# Standard vrider per dørtype
DOOR_HANDLE_DEFAULTS = {
    'SDI':  'vrider_sylinder_oval',
    'KD':   'vrider_sylinder_oval',
    'YD':   'vrider_sylinder_rund',
    'PD':   'ingen',
    'BD':   'vrider_sylinder_oval',
}

# Espagnolett-typer (for 2-fløya dører)
ESPAGNOLETT_TYPES = {
    'roca_sf':      'Espagnolett ROCA SF stål',
    'kantskater':   'Manuelle kantskåter (2 stk) OLDA 33 HZM-R32',
    'ingen':        'Ingen',
}

# --- Tekniske verdier ---

# U-verdier per dørtype (W/m²K)
DOOR_U_VALUES = {
    'SDI':  0.56,
    'KD':   0.39,
    'YD':   0.0,    # Ikke spesifisert
    'PD':   0.0,    # Ikke spesifisert
    'BD':   0.79,
}

# Dørtyper/karmer med brutt kuldebro
BRUTT_KULDEBRO_KARM = {'KD1', 'KD2', 'KD3', 'YD1'}
BRUTT_KULDEBRO_DORRAMME = {'KD', 'YD'}

# --- Dimensjonsberegning (utsparingsmål → transportmål) ---

# Differanse: BM - BT (bredde) og HM - HT (høyde) per dørtype og fløyer
# Transportmål = Utsparingsmål - differanse
DIMENSION_DIFFERENTIALS = {
    'SDI':  {1: (90, 90),   2: (90, 90)},
    'KD':   {1: (130, 70),  2: (130, 70)},
    'YD':   {1: (130, 110), 2: (130, 110)},
    'PD':   {1: (170, 50),  2: (220, 50)},
    'BD':   {1: (90, 50)},
}

# Standardmål for utsparing per dørtype (BM x HM, 1-fløya / 2-fløya)
STANDARD_OPENING_SIZES = {
    'SDI':  {1: (1010, 2110), 2: (1510, 2110)},
    'KD':   {1: (1010, 2110), 2: (1510, 2110)},
    'YD':   {1: (1010, 2110), 2: (1510, 2110)},
    'PD':   {1: (1010, 2110), 2: (1510, 2110)},
    'BD':   {1: (1010, 2110)},
}

# --- Vindu-konstanter ---
WINDOW_MIN_MARGIN = 150           # Min avstand fra kant (mm)
WINDOW_GLASS_DEDUCTION = 36       # Utsparing → glasmål (18mm hver side)
WINDOW_LIGHT_DEDUCTION = 26       # Glasmål → lysåpning (13mm hver side)

DEFAULT_WINDOW_WIDTH = 300
DEFAULT_WINDOW_HEIGHT = 400
MIN_WINDOW_SIZE = 100
MAX_WINDOW_SIZE = 3000
MAX_WINDOW_OFFSET = 500

# Vindusprofiler (presets med form, størrelse og plassering)
WINDOW_PROFILES = {
    'rektangular': {
        'name': 'Rektangulær',
        'shape': 'rect',
        'width': 600,
        'height': 600,
        'pos_x': 0,    # Venstre side (negativ = venstre fra senter)
        'pos_y': 260,     # Øvre del
    },
    'rund': {
        'name': 'Rund',
        'shape': 'circle',
        'width': 570,     # Diameter
        'height': 400,
        'pos_x': 0,     # Høyre side
        'pos_y': 300,     # Øvre del
    },
    'avlang_liten': {
        'name': 'Avlang liten',
        'shape': 'rounded_rect',
        'width': 150,
        'height': 600,
        'pos_x': 220,    # Venstre side
        'pos_y': 220,       # Midten vertikalt
    },
    'avlang_stor': {
        'name': 'Avlang stor',
        'shape': 'rounded_rect',
        'width': 150,
        'height': 1700,   # Nesten full høyde (margin 150mm topp+bunn)
        'pos_x': 0,       # Midt i dørbladet
        'pos_y': -300,       # Sentrert vertikalt
    },
}

# PDF eksportinnstillinger
PDF_SCALE = 10  # 1:10 (dører er mindre enn bygninger)
