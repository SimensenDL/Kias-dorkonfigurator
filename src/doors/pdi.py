"""
Pendeldør isolert (PDI) – komplett dørtype-definisjon.

Isolert pendeldør i glassfiberarmert polyester (40mm dørblad).
Alle mål i millimeter (mm). Ingen imports fra resten av kodebasen.
"""

PDI_DOR = {
    # Identifikasjon
    'key': 'PDI',
    'name': 'Pendeldør isolert',

    # Standardmål (utsparing)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['PD1', 'PD2'],

    # Antall fløyer
    'floyer': [1, 2],

    # Tillatte fløyer per karmtype
    'karm_floyer': {
        'PD1': [1, 2],
        'PD2': [1, 2],
    },

    # Dørbladtyper
    'blade_types': {
        'PDI': {
            'name': 'Glassfiberarmert polyester',
            'thicknesses': [40],
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'PD1': ['PDI'],
        'PD2': ['PDI'],
    },

    # Hengseltyper
    'hengsel_typer': {
        'KIAS_92_STOP': {'navn': 'Hengsler KIAS 92 stop', 'default_antall': 2, 'antall_valg': [2]},
    },

    # Kompatible hengseltyper per karmtype
    'karm_hengsel_typer': {
        'PD1': ['KIAS_92_STOP'],
        'PD2': ['KIAS_92_STOP'],
    },

    # Terskeltyper per karmtype
    'karm_threshold_types': {
        'PD1': ['ingen', 'slepelist'],
        'PD2': ['ingen', 'slepelist'],
    },

    # Utforing: PD1 (skifter til PD2 ved vegg > 300mm)
    'karm_has_utforing': {'PD1'},

    # Transportmål-offsets (fra utsparingsmål)
    'transport_width_offsets': {
        'PD1': {1: {'90': -170}, 2: {'90': -220}},
        'PD2': {1: {'90': -150}, 2: {'90': -200}},
    },

    # Transporthøyde-offsets per karmtype og terskeltype
    'transport_height_offsets': {
        'PD1': {'ingen': -50, 'slepelist': -50},
        'PD2': {'ingen': -40, 'slepelist': -40},
    },

    # Karmmål-offsets (utsparing → karm)
    'karm_size_offsets': {
        'PD1': {'width': 70, 'height': 30},
        'PD2': {'width': 90, 'height': 40},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'PD1': 100,
        'PD2': 100,
    },

    # Karmtyper der dørblad er flush med framkant
    'karm_blade_flush': set(),  # Pendeldør: ikke flush (svinger begge veier)

    # Produksjons-offsets: dørblad (karm → dørblad)
    'dorblad_offsets': {
        'PD1': {1: {'bredde': 205, 'hoyde': 102}, 2: {'bredde': 256, 'hoyde': 102}},
        'PD2': {1: {'bredde': 205, 'hoyde': 102}, 2: {'bredde': 256, 'hoyde': 102}},
    },

    # Karmtyper der luftspalte trekkes fra i dørblad-høyde
    'dorblad_hoyde_inkl_luftspalte': set(),

    # Terskel-offsets (karm bredde → terskel lengde)
    'terskel_offsets': {},  # Pendeldør: ingen terskel

    # Laminat-offsets (dørblad → laminat)
    'laminat_offsets': {
        'PD1': 8,
        'PD2': 8,
    },

    # Dekklist for 2-fløyet
    'dekklist_2floyet_offset': 0,

    # Hengsler
    'hengsler': {
        'KIAS_92_STOP': {'navn': 'Hengsler KIAS 92 stop'},
    },

    # Pendeldør-spesifikke egenskaper
    'pendeldor': True,        # Skjuler slagretning, låser 50/50 split
    'har_dorramme': True,     # PDI (40mm) HAR dørramme (DR40)

    # Pendeldør-spesifikke offsets
    'sparkeplate_offset': -9,                  # sparkeplate_b = dorblad_b - 9
    'avviserboyler_offset': 100,               # avviserbøyler = dorblad_b + 100
    # Ingen ryggforsterkning for PDI
}
