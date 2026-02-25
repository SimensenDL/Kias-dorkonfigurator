"""
Branndør B30 (BD) – komplett dørtype-definisjon.

Alle mål i millimeter (mm). Ingen imports fra resten av kodebasen.
"""

BRANNDOR = {
    # Identifikasjon
    'key': 'BD',
    'name': 'Branndør B30',

    # Standardmål (utsparing)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['BD1'],

    # Visningsnavn for karmtyper i GUI (BD1 vises som SD1)
    'karm_display_names': {'BD1': 'SD1'},

    # Antall fløyer
    'floyer': [1],

    # Tillatte fløyer per karmtype
    'karm_floyer': {
        'BD1': [1],
    },

    # Dørbladtyper
    'blade_types': {
        'BD': {
            'name': 'Branndørblad B30',
            'thicknesses': [52],
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'BD1': ['BD'],
    },

    # Hengseltyper
    'hengsel_typer': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },

    # Kompatible hengseltyper per karmtype
    'karm_hengsel_typer': {
        'BD1': ['ROCA_SF'],
    },

    # Terskeltyper per karmtype
    'karm_threshold_types': {
        'BD1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    },

    # Utforing: BD1 (som SD1)
    'karm_has_utforing': {'BD1'},

    # Transportmål-offsets (fra utsparingsmål)
    'transport_width_offsets': {
        'BD1': {1: {'90': -120, '180': -90}},
    },

    # Transporthøyde-offsets per karmtype og terskeltype
    'transport_height_offsets': {
        'BD1': {'ingen': -50, 'slepelist': -50, 'anslag_37': -67, 'anslag_kjorbar_25': -55, 'hc20': -50},
    },

    # Karmmål-offsets (utsparing → karm)
    'karm_size_offsets': {
        'BD1': {'width': 70, 'height': 30},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'BD1': 80,
    },

    # Karmtyper der dørblad er flush med framkant
    'karm_blade_flush': {'BD1'},

    # Produksjons-offsets: dørblad (karm → dørblad)
    'dorblad_offsets': {
        'BD1': {1: {'bredde': 128, 'hoyde': 81}},
    },

    # Karmtyper der luftspalte trekkes fra i dørblad-høyde
    'dorblad_hoyde_inkl_luftspalte': set(),

    # Terskel-offsets (karm bredde → terskel lengde)
    'terskel_offsets': {
        'BD1': {1: 130},
    },

    # Laminat-offsets (dørblad → laminat 1)
    'laminat_offsets': {
        'BD1': 12,
    },

    # Laminat 2-offsets (laminat 1 → laminat 2: laminat_2 = laminat_1 - offset)
    'laminat_2_offsets': {
        'BD1': 40,
    },

    # Dekklist for 2-fløyet (lengde = karmhøyde - offset)
    'dekklist_2floyet_offset': 102,

    # Standard antall hengsler per fløy (andre dørtyper bruker DoorParams-default = 2)
    'default_hinge_count': 3,

    # Hengsler (nøkkel = hengseltype, antall styres av brukeren)
    'hengsler': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },
}
