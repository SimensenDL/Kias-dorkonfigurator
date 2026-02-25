"""
Kjøleromsdør (KD) – komplett dørtype-definisjon.

Alle mål i millimeter (mm). Ingen imports fra resten av kodebasen.
"""

KJOLEROMDOR = {
    # Identifikasjon
    'key': 'KD',
    'name': 'Kjøleromsdør',

    # Standardmål (utsparing)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['KD1', 'KD2'],

    # Antall fløyer
    'floyer': [1, 2],

    # Tillatte fløyer per karmtype
    'karm_floyer': {
        'KD1': [1, 2],
        'KD2': [1, 2],
    },

    # Dørbladtyper
    'blade_types': {
        'KD': {
            'name': 'Kjøleromsdørblad',
            'thicknesses': [60],
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'KD1': ['KD'],
        'KD2': ['KD'],
    },

    # Hengseltyper
    'hengsel_typer': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },

    # Kompatible hengseltyper per karmtype
    'karm_hengsel_typer': {
        'KD1': ['ROCA_SF'],
        'KD2': ['ROCA_SF'],
    },

    # Terskeltyper per karmtype (ingen hcid)
    'karm_threshold_types': {
        'KD1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'KD2': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    },

    # Utforing: kun KD1
    'karm_has_utforing': {'KD1'},

    # Transportmål-offsets (fra utsparingsmål)
    # Struktur: {karmtype: {floyer: {'90': offset, '180': offset}}}
    'transport_width_offsets': {
        'KD1': {1: {'90': -180, '180': -130}},
        'KD2': {1: {'90': -160, '180': -110}},
    },

    # Transporthøyde-offsets per karmtype og terskeltype
    'transport_height_offsets': {
        'KD1': {'ingen': -70, 'slepelist': -70, 'anslag_37': -107, 'anslag_kjorbar_25': -95, 'hc20': -90},
        'KD2': {'ingen': -60, 'slepelist': -60, 'anslag_37': -97, 'anslag_kjorbar_25': -85, 'hc20': -80},
    },

    # Karmmål-offsets (utsparing → karm)
    'karm_size_offsets': {
        'KD1': {'width': 70, 'height': 30},
        'KD2': {'width': 90, 'height': 40},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'KD1': 100,
        'KD2': 100,
    },

    # Karmtyper der dørblad er flush med framkant
    'karm_blade_flush': {'KD1', 'KD2'},

    # Produksjons-offsets: dørblad (karm → dørblad)
    # hoyde er base-offset UTEN luftspalte (105-22=83)
    'dorblad_offsets': {
        'KD1': {1: {'bredde': 168, 'hoyde': 83}, 2: {'bredde': 172, 'hoyde': 83}},
        'KD2': {1: {'bredde': 168, 'hoyde': 83}, 2: {'bredde': 172, 'hoyde': 83}},
    },

    # Karmtyper der luftspalte trekkes fra i dørblad-høyde
    'dorblad_hoyde_inkl_luftspalte': {'KD1', 'KD2'},

    # Terskel-offsets (karm bredde → terskel lengde)
    # Struktur: {karmtype: {floyer: offset}}
    'terskel_offsets': {
        'KD1': {1: 200, 2: 200},
        'KD2': {1: 200, 2: 200},
    },

    # Laminat-offsets (dørblad → laminat 1)
    'laminat_offsets': {
        'KD1': 8,
        'KD2': 8,
    },

    # Laminat 2-offsets (laminat 1 → laminat 2: laminat_2 = laminat_1 - offset)
    'laminat_2_offsets': {
        'KD1': 40,
        'KD2': 40,
    },

    # Dekklist for 2-fløyet (lengde = karmhøyde - offset)
    #Mangler kalkyle for
    'dekklist_2floyet_offset': 102,

    # Standard antall hengsler per fløy (andre dørtyper bruker DoorParams-default = 2)
    'default_hinge_count': 3,

    # Hengsler (nøkkel = hengseltype, antall styres av brukeren)
    'hengsler': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },
}
