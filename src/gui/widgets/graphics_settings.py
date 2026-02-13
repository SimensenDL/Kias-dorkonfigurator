"""
Grafikkinnstillinger for 3D-viewer.

Presets: 'lav', 'middels', 'hoy'
Bare innstillinger som påvirker ytelsen endres mellom presets.
"""
from PyQt6.QtCore import QSettings

# =====================================================================
# PRESETS (kun ytelsesrelevante innstillinger)
# =====================================================================
PRESETS = {
    'lav': {
        'msaa_samples': 0,
        'lever_tube_segments': 16,
        'lever_bend_segments': 8,
        'plate_corner_segments': 6,
        'smooth_curved_parts': False,
    },
    'middels': {
        'msaa_samples': 4,
        'lever_tube_segments': 32,
        'lever_bend_segments': 16,
        'plate_corner_segments': 12,
        'smooth_curved_parts': True,
    },
    'hoy': {
        'msaa_samples': 8,
        'lever_tube_segments': 64,
        'lever_bend_segments': 30,
        'plate_corner_segments': 24,
        'smooth_curved_parts': True,
    },
}

PRESET_LABELS = {'lav': 'Lav', 'middels': 'Middels', 'hoy': 'Høy'}
DEFAULT_PRESET = 'hoy'

# =====================================================================
# Aktive verdier (settes av apply_preset)
# =====================================================================

# Ytelsesrelevante (endres av presets)
MSAA_SAMPLES = 8
DEPTH_BUFFER_SIZE = 24
LEVER_TUBE_SEGMENTS = 64
LEVER_BEND_SEGMENTS = 30
PLATE_CORNER_SEGMENTS = 24
SMOOTH_CURVED_PARTS = True

# Belysning (påvirker ikke ytelse, alltid like)
LIGHT_AMBIENT = 0.65
LIGHT_DIFFUSE = 0.40
LIGHT_SPECULAR = 0.25
LIGHT_SHININESS = 64.0
LIGHT_DIRECTION = (0.3, 0.6, 0.5)
VIEW_DIRECTION = (0.0, 1.0, 0.3)
BOX_FACE_LIGHT = (0.52, 1.12, 0.98, 0.58, 0.68, 0.85)

# Bakgrunn
BACKGROUND_COLOR = (50, 50, 55, 255)

# Aktivt preset-navn
current_preset = DEFAULT_PRESET


def apply_preset(name: str) -> None:
    """Aktiverer et grafikkpreset og lagrer valget."""
    global MSAA_SAMPLES, LEVER_TUBE_SEGMENTS, LEVER_BEND_SEGMENTS
    global PLATE_CORNER_SEGMENTS, SMOOTH_CURVED_PARTS, current_preset

    preset = PRESETS.get(name, PRESETS[DEFAULT_PRESET])
    MSAA_SAMPLES = preset['msaa_samples']
    LEVER_TUBE_SEGMENTS = preset['lever_tube_segments']
    LEVER_BEND_SEGMENTS = preset['lever_bend_segments']
    PLATE_CORNER_SEGMENTS = preset['plate_corner_segments']
    SMOOTH_CURVED_PARTS = preset['smooth_curved_parts']
    current_preset = name

    # Lagre til QSettings slik at valget huskes
    settings = QSettings("KIASDorkonfigurator", "KIASDorkonfigurator")
    settings.setValue('graphics/preset', name)


def load_saved_preset() -> None:
    """Laster lagret preset fra QSettings, eller bruker standard."""
    settings = QSettings("KIASDorkonfigurator", "KIASDorkonfigurator")
    name = settings.value('graphics/preset', DEFAULT_PRESET)
    if name not in PRESETS:
        name = DEFAULT_PRESET
    apply_preset(name)


# Last lagret preset ved import
load_saved_preset()
