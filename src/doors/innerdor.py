"""
Innerdør (SDI) – komplett dørtype-definisjon.

Alle mål i millimeter (mm). Ingen imports fra resten av kodebasen.
"""

INNERDOR = {
    # Identifikasjon
    'key': 'SDI',
    'name': 'Innerdør',

    # Standardmål (utsparing)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['SD1', 'SD2', 'SD3/ID1'],

    # Antall fløyer
    'floyer': [1, 2],

    # Dørbladtyper
    'blade_types': {
        'SDI_ROCA': {
            'name': 'Innerdørblad m/ROCA',
            'thicknesses': [40],
        },
        'SDI_SNAPIN': {
            'name': 'Innerdørblad m/Snap-in',
            'thicknesses': [40],
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'SD1':     ['SDI_ROCA', 'SDI_SNAPIN'],
        'SD2':     ['SDI_ROCA', 'SDI_SNAPIN'],
        'SD3/ID1': ['SDI_ROCA', 'SDI_SNAPIN'],
    },

    # Terskeltyper per karmtype
    'karm_threshold_types': {
        'SD1':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'SD2':     ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'SD3/ID1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20', 'hcid'],
    },

    # Utforing: kun SD1
    'karm_has_utforing': {'SD1'},

    # U-verdi
    'u_value': 0.56,
    'brutt_kuldebro_karm': set(),       # Ingen karmer med brutt kuldebro
    'brutt_kuldebro_dorramme': False,    # Ikke brutt kuldebro på dørramme

    # Transportmål-offsets (fra utsparingsmål)
    # Struktur: {karmtype: {floyer: {'90': offset, '180': offset}}}
    'transport_width_offsets': {
        'SD1':     {1: {'90': -120, '180': -90}},
        'SD2':     {1: {'90': -100, '180': -70}},
        'SD3/ID1': {1: {'90': -143, '180': -108}},
    },

    # Transporthøyde-offsets per karmtype og terskeltype
    'transport_height_offsets': {
        'SD1':     {'ingen': -50, 'slepelist': -50, 'anslag_37': -67, 'anslag_kjorbar_25': -55, 'hc20': -50, 'hcid': None},
        'SD2':     {'ingen': -20, 'slepelist': -20, 'anslag_37': -57, 'anslag_kjorbar_25': -45, 'hc20': -40, 'hcid': None},
        'SD3/ID1': {'ingen': -64, 'slepelist': -64, 'anslag_37': -101, 'anslag_kjorbar_25': -89, 'hc20': -84, 'hcid': -84},
    },

    # Karmmål-offsets (utsparing → karm)
    'karm_size_offsets': {
        'SD1':     {'width': 70, 'height': 30},
        'SD2':     {'width': 90, 'height': 40},
        'SD3/ID1': {'width': -20, 'height': -20},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'SD1': 80,
        'SD2': 80,
        'SD3/ID1': 44,
    },

    # Karmtyper der dørblad er flush med framkant
    'karm_blade_flush': {'SD1', 'SD2'},

    # Produksjons-offsets: dørblad (karm → dørblad)
    # Struktur: {karmtype: {floyer: {'bredde': offset, 'hoyde': offset}}}
    'dorblad_offsets': {
        'SD1': {1: {'bredde': 128, 'hoyde': 85}, 2: {'bredde': 132, 'hoyde': 85}},
        'SD2': {2: {'bredde': 132, 'hoyde': 85}},
    },

    # Terskel-offsets (karm bredde → terskel lengde)
    # Struktur: {karmtype: {floyer: offset}}
    'terskel_offsets': {
        'SD1': {1: 160, 2: 160},
    },

    # Laminat-offsets (dørblad → laminat)
    'laminat_offsets': {
        'SD1': 8,
    },

    # Dekklist for 2-fløyet (lengde = karmhøyde - offset)
    'dekklist_2floyet_offset': 102,
}
