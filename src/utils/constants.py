"""
Applikasjonskonstanter og standardverdier for KIAS Dørkonfigurator.
Alle dimensjoner i millimeter (mm).

Dørtype-spesifikke data bygges dynamisk fra src/doors/-modulene.
"""

from ..doors import DOOR_REGISTRY

# Applikasjonsinfo
APP_NAME = "KIAS Dørkonfigurator"
APP_VERSION = "0.3.0"
PROJECT_EXTENSION = ".kdf"
PROJECT_FILTER = f"KIAS Dørfil (*{PROJECT_EXTENSION})"

# =============================================================================
# DYNAMISK OPPBYGGING FRA DOOR_REGISTRY
# =============================================================================

# Dørtyper (intern nøkkel → visningsnavn)
DOOR_TYPES = {d['key']: d['name'] for d in DOOR_REGISTRY.values()}

# Standardmål per dørtype
DEFAULT_DIMENSIONS = {
    d['key']: {
        'width': d['default_width'],
        'height': d['default_height'],
        'thickness': d['default_thickness'],
    }
    for d in DOOR_REGISTRY.values()
}

# Karmtyper per dørtype
DOOR_KARM_TYPES = {d['key']: d['karm_types'] for d in DOOR_REGISTRY.values()}

# Antall fløyer per dørtype
DOOR_FLOYER = {d['key']: d['floyer'] for d in DOOR_REGISTRY.values()}

# Dørbladtyper (samlet fra alle dørtyper)
DOOR_BLADE_TYPES = {}
for d in DOOR_REGISTRY.values():
    DOOR_BLADE_TYPES.update(d['blade_types'])

# Kompatible dørbladtyper per karmtype
KARM_BLADE_TYPES = {}
for d in DOOR_REGISTRY.values():
    KARM_BLADE_TYPES.update(d['karm_blade_types'])

# Tillatte fløyer per karmtype
KARM_FLOYER = {}
for d in DOOR_REGISTRY.values():
    KARM_FLOYER.update(d.get('karm_floyer', {}))

# Dørtype-spesifikke dørbladtyper (overstyrer karm-basert oppslag)
DOOR_TYPE_BLADE_OVERRIDE = {}

# Tillatte terskeltyper per karmtype
KARM_THRESHOLD_TYPES = {}
for d in DOOR_REGISTRY.values():
    KARM_THRESHOLD_TYPES.update(d['karm_threshold_types'])

# Karmer som støtter utforing
KARM_HAS_UTFORING = set()
for d in DOOR_REGISTRY.values():
    KARM_HAS_UTFORING.update(d.get('karm_has_utforing', set()))

# U-verdier per dørtype
DOOR_U_VALUES = {d['key']: d.get('u_value', 0.0) for d in DOOR_REGISTRY.values()}

# Dørtyper/karmer med brutt kuldebro
BRUTT_KULDEBRO_KARM = set()
BRUTT_KULDEBRO_DORRAMME = set()
for d in DOOR_REGISTRY.values():
    BRUTT_KULDEBRO_KARM.update(d.get('brutt_kuldebro_karm', set()))
    if d.get('brutt_kuldebro_dorramme', False):
        BRUTT_KULDEBRO_DORRAMME.add(d['key'])

# Transportmål-offsets (bredde)
TRANSPORT_WIDTH_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    TRANSPORT_WIDTH_OFFSETS.update(d.get('transport_width_offsets', {}))

# Transportmål-offsets (høyde)
TRANSPORT_HEIGHT_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    TRANSPORT_HEIGHT_OFFSETS.update(d.get('transport_height_offsets', {}))

# Karm-dimensjoner
KARM_SIZE_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    KARM_SIZE_OFFSETS.update(d.get('karm_size_offsets', {}))

# Sidestolpe-bredde per karmtype
KARM_SIDESTOLPE_WIDTH = {}
for d in DOOR_REGISTRY.values():
    KARM_SIDESTOLPE_WIDTH.update(d.get('karm_sidestolpe_width', {}))

# Karmtyper der dørblad er flush med framkant
KARM_BLADE_FLUSH = set()
for d in DOOR_REGISTRY.values():
    KARM_BLADE_FLUSH.update(d.get('karm_blade_flush', set()))

# Produksjons-offsets
DORBLAD_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    DORBLAD_OFFSETS.update(d.get('dorblad_offsets', {}))

# Karmtyper der luftspalte trekkes fra i dørblad-høyde
DORBLAD_HOYDE_INKL_LUFTSPALTE = set()
for d in DOOR_REGISTRY.values():
    DORBLAD_HOYDE_INKL_LUFTSPALTE.update(d.get('dorblad_hoyde_inkl_luftspalte', set()))

TERSKEL_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    TERSKEL_OFFSETS.update(d.get('terskel_offsets', {}))

LAMINAT_OFFSETS = {}
for d in DOOR_REGISTRY.values():
    LAMINAT_OFFSETS.update(d.get('laminat_offsets', {}))

LAMINAT_OFFSET_DEFAULT = 8

# Dekklist for 2-fløyet
DEKKLIST_2FLOYET_OFFSET = 102

# Differanser for transportmål (brukes av DoorParams.transport_width/height)
DIMENSION_DIFFERENTIALS = {
    d['key']: {1: (90, 90), 2: (90, 90)}
    for d in DOOR_REGISTRY.values()
    if d['key'] == 'SDI'
}

# Standardmål for utsparing per dørtype
STANDARD_OPENING_SIZES = {
    d['key']: {f: (d['default_width'], d['default_height']) for f in d['floyer']}
    for d in DOOR_REGISTRY.values()
}

# =============================================================================
# GENERISKE / DELTE KONSTANTER (ikke dørtype-spesifikke)
# =============================================================================

# Utforing-steg for karmer (veggtykkelse-område i mm)
UTFORING_RANGES = {
    '70-110':  {'min': 70, 'max': 110, 'name': '70-110 mm'},
    '100-140': {'min': 100, 'max': 140, 'name': '100-140 mm'},
    '130-170': {'min': 130, 'max': 170, 'name': '130-170 mm'},
    '160-200': {'min': 160, 'max': 200, 'name': '160-200 mm'},
    '200-300': {'min': 200, 'max': 300, 'name': '200-300 mm'},
}

# Maks veggtykkelse for karmer med utforing
UTFORING_MAX_THICKNESS = 300

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

# Luftspalte-verdier per terskeltype (mm)
THRESHOLD_LUFTSPALTE = {
    'ingen': 22,
    'slepelist': 22,
    'anslag_37': 22,
    'anslag_kjorbar_25': 13,
    'hc20': 8,
    'hcid': 18,
}

# Brannklasser
FIRE_RATINGS = ['', 'B30']

# Lydklasser
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

# --- Vindu-konstanter ---
WINDOW_MIN_MARGIN = 150
WINDOW_GLASS_DEDUCTION = 36
WINDOW_LIGHT_DEDUCTION = 26

DEFAULT_WINDOW_WIDTH = 300
DEFAULT_WINDOW_HEIGHT = 400
MIN_WINDOW_SIZE = 100
MAX_WINDOW_SIZE = 3000
MAX_WINDOW_OFFSET = 500

# Vindusprofiler
WINDOW_PROFILES = {
    'rektangular': {
        'name': 'Rektangulær',
        'shape': 'rect',
        'width': 600,
        'height': 600,
        'pos_x': 0,
        'pos_y': 260,
    },
    'rund': {
        'name': 'Rund',
        'shape': 'circle',
        'width': 570,
        'height': 400,
        'pos_x': 0,
        'pos_y': 300,
    },
    'avlang_liten': {
        'name': 'Avlang liten',
        'shape': 'rounded_rect',
        'width': 150,
        'height': 600,
        'pos_x': 220,
        'pos_y': 220,
    },
    'avlang_stor': {
        'name': 'Avlang stor',
        'shape': 'rounded_rect',
        'width': 150,
        'height': 1700,
        'pos_x': 0,
        'pos_y': -300,
    },
}

# PDF eksportinnstillinger
PDF_SCALE = 10
