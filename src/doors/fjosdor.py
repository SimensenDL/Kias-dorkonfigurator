"""
Fjøsdør (FD) – komplett dørtype-definisjon.

Alle mål i millimeter (mm). Ingen imports fra resten av kodebasen.
"""

FJOSDOR = {
    # Identifikasjon
    'key': 'FD',
    'name': 'Fjøsdør',

    # Standardmål (utsparing)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['FD1', 'FD2', 'FD3'],

    # Antall fløyer
    'floyer': [1, 2],

    # Tillatte fløyer per karmtype
    'karm_floyer': {
        'FD1': [1, 2],
        'FD2': [1, 2],
        'FD3': [1, 2],
    },

    # Dørbladtyper
    'blade_types': {
        'FD': {
            'name': 'Fjøsdørblad',
            'thicknesses': [60],
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'FD1': ['FD'],
        'FD2': ['FD'],
        'FD3': ['FD'],
    },

    # Hengseltyper
    'hengsel_typer': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },

    # Kompatible hengseltyper per karmtype
    'karm_hengsel_typer': {
        'FD1': ['ROCA_SF'],
        'FD2': ['ROCA_SF'],
        'FD3': ['ROCA_SF'],
    },

    # Terskeltyper per karmtype
    'karm_threshold_types': {
        'FD1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'FD2': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'FD3': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    },

    # Utforing: kun FD1
    'karm_has_utforing': {'FD1'},

    # Transportmål-offsets (fra utsparingsmål)
    # Struktur: {karmtype: {floyer: {'90': offset, '180': offset}}}
    'transport_width_offsets': {
        'FD1': {1: {'90': -180, '180': -130}},
        'FD2': {1: {'90': -160, '180': -110}},
        'FD3': {1: {'90': -162, '180': -112}},
    },

    # Transporthøyde-offsets per karmtype og terskeltype
    'transport_height_offsets': {
        'FD1': {'ingen': -70, 'slepelist': -70, 'anslag_37': -107, 'anslag_kjorbar_25': -95, 'hc20': -90},
        'FD2': {'ingen': -60, 'slepelist': -60, 'anslag_37': -97, 'anslag_kjorbar_25': -85, 'hc20': -80},
        'FD3': {'ingen': -40, 'slepelist': -40, 'anslag_37': -77, 'anslag_kjorbar_25': -65, 'hc20': -60},
    },

    # Karmmål-offsets (utsparing → karm)
    'karm_size_offsets': {
        'FD1': {'width': 70, 'height': 30},
        'FD2': {'width': 90, 'height': 40},
        'FD3': {'width': -20, 'height': -20},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'FD1': 100,
        'FD2': 100,
        'FD3': 46,
    },

    # Karmtyper der dørblad er flush med framkant
    'karm_blade_flush': {'FD1', 'FD2'},

    # Produksjons-offsets: dørblad (karm → dørblad)
    # Struktur: {karmtype: {floyer: {'bredde': offset, 'hoyde': offset}}}
    'dorblad_offsets': {
        'FD1': {1: {'bredde': 168, 'hoyde': 96}, 2: {'bredde': 172, 'hoyde': 96}},
        'FD2': {1: {'bredde': 168, 'hoyde': 96}, 2: {'bredde': 172, 'hoyde': 96}},
        'FD3': {1: {'bredde': 58, 'hoyde': 41}, 2: {'bredde': 62, 'hoyde': 41}},
    },

    # Karmtyper der luftspalte trekkes fra i dørblad-høyde
    'dorblad_hoyde_inkl_luftspalte': set(),

    # Terskel-offsets (karm bredde → terskel lengde)
    # Struktur: {karmtype: {floyer: offset}}
    'terskel_offsets': {
        'FD1': {1: 200, 2: 200},
        'FD2': {1: 200, 2: 200},
        'FD3': {1: 92, 2: 92},
    },

    # Laminat-offsets (dørblad → laminat 1)
    'laminat_offsets': {
        'FD1': 8,
        'FD2': 8,
        'FD3': 8,
    },

    # Laminat 2-offsets (laminat 1 → laminat 2: laminat_2 = laminat_1 - offset)
    'laminat_2_offsets': {
        'FD1': 40,
        'FD2': 40,
        'FD3': 40,
    },

    # Dekklist for 2-fløyet (lengde = karmhøyde - offset)
    'dekklist_2floyet_offset': 102,

    # Standard antall hengsler per fløy
    'default_hinge_count': 3,

    # Hengsler (nøkkel = hengseltype, antall styres av brukeren)
    'hengsler': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },
}
