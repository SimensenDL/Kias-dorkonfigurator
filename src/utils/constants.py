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
    'SDI':  'SDI - Innerdør',
    'KD':   'KD - Kjøleromsdør',
    'PD':   'PD - Pendeldør',
    'SK':   'SK - Skyvedør',
    'BD':   'BD - Branndør B30',
    'BR':   'BR - Brakkedør',
    'FD':   'FD - Fjøsdør (ytter)',
    'FDI':  'FDI - Fjøsdør (inner)',
    'BO':   'BO - Bod-/Garasjedør',
    'YD':   'YD - Ytterdør',
    'BA':   'BA - Badstudør',
    'AQI':  'AQI - Aqua innerdør',
    'AQB':  'AQB - Aqua boddør',
    'LDI':  'LDI - Lyddør',
    'RD':   'RD - Røntgendør',
}

# Standardmål per dørtype (bredde, høyde, veggtykkelse i mm)
# Veggtykkelse må samsvare med karmtypens støttede område (se karmtype-dokumentasjon)
DEFAULT_DIMENSIONS = {
    'SDI':  {'width': 1010, 'height': 2110, 'thickness': 100},  # SD1: 70-110 mm
    'KD':   {'width': 1010, 'height': 2110, 'thickness': 80},   # KD1: 70-110 mm
    'PD':   {'width': 1010, 'height': 2110, 'thickness': 100},  # PD1: 70-110 mm
    'SK':   {'width': 1010, 'height': 2110, 'thickness': 50},   # SK1: ikke dokumentert
    'BD':   {'width': 1010, 'height': 2110, 'thickness': 100},  # SD1/BD1: 70-110 mm
    'BR':   {'width': 1010, 'height': 2110, 'thickness': 40},   # BR1: 40-44 mm
    'FD':   {'width': 1010, 'height': 2110, 'thickness': 100},  # FD1: 77 mm karmdybde
    'FDI':  {'width': 1010, 'height': 2110, 'thickness': 100},  # FDI1: 77 mm karmdybde
    'BO':   {'width': 1010, 'height': 2110, 'thickness': 50},   # BO1: 115 mm karmdybde
    'YD':   {'width': 1010, 'height': 2110, 'thickness': 100},  # YD1: brutt kuldebro
    'BA':   {'width': 1010, 'height': 2110, 'thickness': 100},  # YD1: brutt kuldebro
    'AQI':  {'width': 1010, 'height': 2110, 'thickness': 100},  # ID1: smygmontasje
    'AQB':  {'width': 1010, 'height': 2110, 'thickness': 50},   # BO1: 115 mm karmdybde
    'LDI':  {'width': 1010, 'height': 2110, 'thickness': 100},  # SD1: 70-110 mm
    'RD':   {'width': 1010, 'height': 2110, 'thickness': 100},  # SD1: 70-110 mm
}

# Karmtyper per dørtype (hvilke karmtyper som er tilgjengelige)
DOOR_KARM_TYPES = {
    'SDI':  ['SD1', 'SD2', 'SD3/ID1'],
    'KD':   ['KD1', 'KD2', 'KD3'],
    'PD':   ['PD1', 'PD2'],
    'SK':   ['SK1'],
    'BD':   ['BD1'],
    'BR':   ['BR1'],
    'FD':   ['FD1', 'FD3'],
    'FDI':  ['FDI1'],
    'BO':   ['BO1'],
    'YD':   ['YD1'],
    'BA':   ['YD1'],
    'AQI':  ['SD3/ID1'],
    'AQB':  ['BO1'],
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
    'BR':   [1],
    'FD':   [1, 2],
    'FDI':  [1, 2],
    'BO':   [1],
    'YD':   [1, 2],
    'BA':   [1],
    'AQI':  [1],
    'AQB':  [1],
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
        'thicknesses': [40, 60],
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
        'thicknesses': [52],
    },
    'RD_BLY': {
        'name': 'Røntgendørblad m/blyinnlegg',
        'thicknesses': [40],
    },
    'LDI_LYD': {
        'name': 'Lyddørblad m/lyddempning',
        'thicknesses': [40],
    },
    'FD_YTTER': {
        'name': 'Fjøs ytterdørblad',
        'thicknesses': [60],
    },
    'FD_INNER': {
        'name': 'Fjøs innerdørblad',
        'thicknesses': [40],
    },
    'BO_ISOLERT': {
        'name': 'Boddørblad isolert',
        'thicknesses': [60],
    },
    'YD_ISOLERT': {
        'name': 'Ytterdørblad isolert',
        'thicknesses': [60],
    },
    'BA_ISOLERT': {
        'name': 'Badstudørblad isolert',
        'thicknesses': [60],
    },
    'AQI_INNER': {
        'name': 'Aqua innerdørblad',
        'thicknesses': [40],
    },
    'AQB_ISOLERT': {
        'name': 'Aqua boddørblad isolert',
        'thicknesses': [60],
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
    'BD1':     ['BD_ROCKWOOL'],
    'BR1':     ['SDI_ROCA', 'SDI_SNAPIN'],
    'BO1':     ['BO_ISOLERT'],
    'FD1':     ['FD_YTTER'],
    'FDI1':    ['FD_INNER'],
    'FD3':     ['FD_YTTER'],
    'YD1':     ['YD_ISOLERT'],
}

# Dørtype-spesifikke dørbladtyper (overstyrer karm-basert oppslag)
# Disse dørtypene har spesialisert dørblad som skiller seg fra standard innerdørblad
DOOR_TYPE_BLADE_OVERRIDE = {
    'RD':   ['RD_BLY'],         # Røntgendør: blyinnlegg i dørblad
    'LDI':  ['LDI_LYD'],        # Lyddør: lyddempende materialer
    'BA':   ['BA_ISOLERT'],      # Badstudør: varmebestandig isolert blad
    'AQI':  ['AQI_INNER'],      # Aqua innerdør: Adjufix, Argenta-hengsler
    'AQB':  ['AQB_ISOLERT'],    # Aqua boddør: Adjufix, Argenta-hengsler
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
    'standard': 'Standard terskel (37 mm)',
    'hc_terskel': 'HC-terskel (20 mm)',
    'slepelist': 'Slepelist (25,4 mm)',
    'kjorbar_terskel': 'Kjørbar terskel (25 mm)',
    'heveterskel': 'Heveterskel (Total Junior)',
    'luftspalte': 'Luftspalte',
}

# Terskelhøyde per type (mm)
THRESHOLD_HEIGHT = {
    'standard': 37,
    'hc_terskel': 20,
    'slepelist': 25,
    'kjorbar_terskel': 25,
    'heveterskel': 0,  # Hev/senk, variabel
    'luftspalte': 0,
}

# Faste luftspalte-verdier per terskeltype (mm)
# For 'luftspalte' er verdien redigerbar, standardverdien er her
THRESHOLD_LUFTSPALTE = {
    'standard': 0,
    'hc_terskel': 8,
    'slepelist': 22,
    'kjorbar_terskel': 0,
    'heveterskel': 0,
    'luftspalte': 22,
}

# Tillatte terskeltyper per dørtype
DOOR_THRESHOLD_TYPES = {
    'SDI':  ['standard', 'hc_terskel', 'slepelist', 'luftspalte'],
    'KD':   ['standard', 'hc_terskel', 'kjorbar_terskel', 'slepelist', 'luftspalte'],
    'PD':   ['slepelist'],
    'SK':   ['kjorbar_terskel', 'standard'],
    'BD':   ['heveterskel'],
    'BR':   ['standard'],
    'FD':   ['kjorbar_terskel'],
    'FDI':  ['standard', 'luftspalte'],
    'BO':   ['standard'],
    'YD':   ['kjorbar_terskel'],
    'BA':   ['standard'],
    'AQI':  ['luftspalte', 'hc_terskel'],
    'AQB':  ['standard'],
    'LDI':  ['standard', 'hc_terskel', 'slepelist', 'luftspalte'],
    'RD':   ['standard', 'hc_terskel', 'slepelist', 'luftspalte'],
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
DOOR_HINGE_DEFAULTS = {
    # dørtype: (hengsel-nøkkel, antall 1-fløya, antall 2-fløya per fløy)
    'SDI':  ('roca_sf', 2, 2),
    'KD':   ('roca_sf', 3, 3),
    'PD':   ('kias_92', 0, 0),     # Pendeldør: selvlukkende hengsler, antall N/A
    'SK':   (None, 0, 0),           # Skyvedør: ingen hengsler
    'BD':   ('sf_staal', 3, 0),
    'BR':   ('roca_sf', 2, 0),
    'FD':   ('roca_sf', 3, 3),
    'FDI':  ('roca_sf', 2, 2),
    'BO':   ('argenta', 3, 0),
    'YD':   ('roca_sf', 3, 3),
    'BA':   ('roca_sf', 3, 0),
    'AQI':  ('argenta', 2, 0),
    'AQB':  ('argenta', 3, 0),
    'LDI':  ('roca_sf', 2, 2),
    'RD':   ('roca_sf', 2, 2),
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
    'PD':   'ingen',
    'SK':   'ingen',
    'BD':   '3065_316l',
    'BR':   'lk565',
    'FD':   'lk565',
    'FDI':  'lk565',
    'BO':   'lk565',
    'YD':   'lk565',
    'BA':   'assa_lk566',
    'AQI':  'lk565',
    'AQB':  '3065_316l',
    'LDI':  '3065_316l',
    'RD':   '3065_316l',
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
    'PD':   'ingen',
    'SK':   'ingen',
    'BD':   'vrider_sylinder_oval',
    'BR':   'vrider_sylinder_rund',
    'FD':   'vrider_sylinder_rund',
    'FDI':  'vrider_blindskilt',
    'BO':   'vrider_sylinder_rund',
    'YD':   'vrider_sylinder_rund',
    'BA':   'plasthandtak',
    'AQI':  'vrider_sylinder_oval',
    'AQB':  'vrider_sylinder_oval',
    'LDI':  'vrider_sylinder_oval',
    'RD':   'vrider_sylinder_oval',
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
    'PD':   0.0,    # Ikke spesifisert
    'SK':   0.56,   # 0.56 (standard) / 0.39 (kjøle)
    'BD':   0.79,
    'BR':   0.56,
    'FD':   0.0,    # Ikke spesifisert
    'FDI':  0.0,    # Ikke spesifisert
    'BO':   0.0,    # Ikke spesifisert
    'YD':   0.0,    # Ikke spesifisert
    'BA':   0.0,    # Ikke spesifisert
    'AQI':  0.0,    # Ikke spesifisert
    'AQB':  0.0,    # Ikke spesifisert
    'LDI':  0.56,
    'RD':   0.56,
}

# Dørtyper/karmer med brutt kuldebro
BRUTT_KULDEBRO_KARM = {'KD1', 'KD2', 'KD3', 'YD1', 'FD1', 'BO1', 'BR1'}
BRUTT_KULDEBRO_DORRAMME = {'KD', 'YD', 'FD'}

# Røntgendør: blyinnlegg-tykkelser (mm)
LEAD_THICKNESSES = [1, 2]

# --- Dimensjonsberegning (utsparingsmål → transportmål) ---

# Differanse: BM - BT (bredde) og HM - HT (høyde) per dørtype og fløyer
# Transportmål = Utsparingsmål - differanse
DIMENSION_DIFFERENTIALS = {
    # dørtype: {fløyer: (bredde_diff, høyde_diff)}
    'SDI':  {1: (90, 90),   2: (90, 90)},
    'KD':   {1: (130, 70),  2: (130, 70)},
    'PD':   {1: (170, 50),  2: (220, 50)},   # 2-fløya = port
    'SK':   {1: (90, 50)},
    'BD':   {1: (90, 50)},
    'YD':   {1: (130, 110), 2: (130, 110)},
}

# Standardmål for utsparing per dørtype (BM x HM, 1-fløya / 2-fløya)
STANDARD_OPENING_SIZES = {
    # dørtype: {fløyer: (BM, HM)}
    'SDI':  {1: (1010, 2110), 2: (1510, 2110)},
    'KD':   {1: (1010, 2110), 2: (1510, 2110)},
    'PD':   {1: (1010, 2110), 2: (1510, 2110)},
    'SK':   {1: (1010, 2110)},
    'BD':   {1: (1010, 2110)},
    'BR':   {1: (1010, 2110)},
    'FD':   {1: (1010, 2110), 2: (1510, 2110)},
    'FDI':  {1: (1010, 2110), 2: (1510, 2110)},
    'BO':   {1: (1010, 2110)},
    'YD':   {1: (1010, 2110), 2: (1510, 2110)},
    'BA':   {1: (1010, 2110)},
    'AQI':  {1: (1010, 2110)},
    'AQB':  {1: (1010, 2110)},
    'LDI':  {1: (1010, 2110)},
    'RD':   {1: (1010, 2110)},
}

# PDF eksportinnstillinger
PDF_SCALE = 10  # 1:10 (dører er mindre enn bygninger)
