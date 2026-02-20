# Guide: Legge til ny dørtype

Denne guiden dekker alle steg for å legge til en ny dørtype i KIAS Dørkonfigurator.
Basert på implementasjonen av Kjøleromsdør (KD).

## Oversikt over filer

| Fil                                  | Handling    | Beskrivelse                                  |
| ------------------------------------ | ----------- | -------------------------------------------- |
| `src/doors/<dortype>.py`             | **OPPRETT** | Dørtype-definisjon (ren dict, ingen imports) |
| `src/gui/karm_profiles/<prefix>/`    | **OPPRETT** | 3D-profiler for hver karmtype                |
| `src/doors/__init__.py`              | ENDRE       | Importer og registrer i `_DOOR_TYPE_MODULES` |
| `src/gui/karm_profiles/__init__.py`  | ENDRE       | Registrer profiler i `KARM_PROFILES`         |
| `src/gui/widgets/door_preview_3d.py` | ENDRE       | Legg til i `KARM_DEPTHS`                     |
| `src/export/pdf_constants.py`        | ENDRE       | Legg til i `KARM_SECTION_PROFILES`           |
| `src/models/production_list.py`      | ENDRE       | Karmfamilier + evt. nye komponenttyper       |
| `src/utils/constants.py`             | ENDRE       | Evt. nye oppslags-tabeller                   |
| `src/utils/calculations.py`          | ENDRE       | Evt. nye beregningsfunksjoner                |
| `src/gui/widgets/detail_tab.py`      | ENDRE       | Evt. nye felter i detaljvisningen            |

**Filer som IKKE trenger endring** (data-drevet):

- `src/gui/widgets/door_form.py` — GUI-skjema bygges fra registry
- `src/models/door.py` — DoorParams bruker oppslags-tabeller
- `src/export/pdf_exporter.py` — bruker KARM_SECTION_PROFILES generisk
- `src/utils/ordretekst.py` — returnerer `[]` når ordretekst mangler

---

## Steg 1: Opprett dørtype-fil

Opprett `src/doors/<dortype>.py`. Bruk `innerdor.py` eller `kjoleromdor.py` som mal.

### Obligatoriske nøkler

```python
DORTYPE = {
    # Identifikasjon
    'key': 'XX',                    # Kort unik nøkkel (f.eks. 'KD', 'SDI', 'BD')
    'name': 'Dørtypens navn',       # Visningsnavn i GUI

    # Standardmål (utsparing, mm)
    'default_width': 1010,
    'default_height': 2110,
    'default_thickness': 100,

    # Karmtyper
    'karm_types': ['XX1', 'XX2'],

    # Antall fløyer
    'floyer': [1, 2],              # Eller bare [1] hvis kun 1-fløyet

    # Tillatte fløyer per karmtype
    'karm_floyer': {
        'XX1': [1, 2],
        'XX2': [1],
    },

    # Dørbladtyper
    'blade_types': {
        'XX': {
            'name': 'Dørbladnavn',
            'thicknesses': [40],    # Liste med tilgjengelige tykkelser
        },
    },

    # Kompatible dørbladtyper per karmtype
    'karm_blade_types': {
        'XX1': ['XX'],
        'XX2': ['XX'],
    },

    # Hengseltyper
    'hengsel_typer': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål', 'default_antall': 2, 'antall_valg': [2, 3, 4]},
    },

    # Kompatible hengseltyper per karmtype
    'karm_hengsel_typer': {
        'XX1': ['ROCA_SF'],
        'XX2': ['ROCA_SF'],
    },

    # Terskeltyper per karmtype
    'karm_threshold_types': {
        'XX1': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
        'XX2': ['ingen', 'slepelist', 'anslag_37', 'anslag_kjorbar_25', 'hc20'],
    },

    # Utforing (set med karmtyper som støtter utforing)
    'karm_has_utforing': {'XX1'},   # Eller set() hvis ingen

    # Transportmål-offsets (fra utsparingsmål)
    # Struktur: {karmtype: {floyer: {'90': offset, '180': offset}}}
    'transport_width_offsets': {
        'XX1': {1: {'90': -120, '180': -90}},
    },

    # Transporthøyde-offsets per terskeltype
    'transport_height_offsets': {
        'XX1': {'ingen': -50, 'slepelist': -50, 'anslag_37': -67,
                'anslag_kjorbar_25': -55, 'hc20': -50},
    },

    # Karmmål-offsets (utsparing → karm: karm = utsparing + offset)
    'karm_size_offsets': {
        'XX1': {'width': 70, 'height': 30},
    },

    # Sidestolpe-bredder per karmtype
    'karm_sidestolpe_width': {
        'XX1': 80,
    },

    # Karmtyper der dørblad er flush med listverkets framkant
    'karm_blade_flush': {'XX1', 'XX2'},  # Eller set() for smygmontasje

    # Produksjons-offsets: dørblad (karm → dørblad)
    # Standard: {karmtype: {floyer: {'bredde': offset, 'hoyde': offset}}}
    # SD3/ID-variant: {karmtype: {hengseltype: {floyer: {'bredde': offset, 'hoyde_base': offset}}}}
    'dorblad_offsets': {
        'XX1': {1: {'bredde': 128, 'hoyde': 85}, 2: {'bredde': 132, 'hoyde': 85}},
    },

    # Karmtyper der luftspalte trekkes fra i dørblad-høyde
    'dorblad_hoyde_inkl_luftspalte': set(),  # F.eks. {'SD3/ID'} for smygmontasje

    # Terskel-offsets (karm bredde → terskel: terskel = karm_b - offset)
    'terskel_offsets': {
        'XX1': {1: 160, 2: 160},
    },

    # Laminat-offsets (dørblad → laminat: laminat = dørblad - offset)
    'laminat_offsets': {
        'XX1': 8,
    },

    # Dekklist for 2-fløyet (lengde = karmhøyde - offset)
    'dekklist_2floyet_offset': 102,

    # Hengsler
    'hengsler': {
        'ROCA_SF': {'navn': 'Hengsler Roca i SF stål'},
    },
}
```

### Valgfrie nøkler

```python
    # Laminat 2-offsets (kun KD foreløpig)
    # Laminat 2 = Laminat 1 - offset
    'laminat_2_offsets': {
        'XX1': 40,
    },

    # Ordretekst (kan utelates — returnerer tom liste)
    'ordretekst': {
        'tittel': {1: 'XX - DØRTYPE 1-FLØYA', 2: 'XX - DØRTYPE 2-FLØYA'},
        'linjer': [ ... ],
    },
```

---

## Steg 2: Registrer i `src/doors/__init__.py`

```python
from .dortype import DORTYPE

_DOOR_TYPE_MODULES = [
    INNERDOR,
    KJOLEROMDOR,
    DORTYPE,          # ← legg til her
]
```

**Test:** Etter dette steget fungerer GUI-dropdown, mål-beregninger og PDF-snitt automatisk
via den data-drevne arkitekturen.

---

## Steg 3: Opprett 3D-profiler

Opprett mappe `src/gui/karm_profiles/<prefix>/` med:

- `__init__.py` — tom fil
- `xx1.py` — Profil-klasse som arver fra `KarmProfile`
- `xx2.py` — (osv. for hver karmtype)

### Velg riktig baseprofil

| Karmtype              | Bruk som mal   | Karakteristikk                    |
| --------------------- | -------------- | --------------------------------- |
| Listverk begge sider  | `sdi/sd1.py`   | U-profil, kobling = wall_t        |
| Listverk kun framside | `sdi/sd2.py`   | L-profil, fast koblingsdybde      |
| Smygmontasje          | `sdi/sd3id.py` | Ingen listverk, karm i veggåpning |

### Geometri-verdier som typisk endres

```python
list_w = 80          # Listverkbredde (60 for SD, 80 for KD)
anslag_d = 24        # Anslagdybde = karm_depth - blade_t
                     # SD: 84 - 40 = 44, KD: 84 - 60 = 24
```

### Metoder som må implementeres

```python
def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
    """Returnerer liste av (bx, by, bz, dx, dy, dz) bokser."""

def blade_y(self, wall_t, blade_t, karm_depth):
    """Y-posisjon (bakkant) for dørblad. Flush-typer: wall_t/2 + list_t - blade_t"""

def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
    """Y-posisjon for hengsler. Flush-typer: wall_t/2 + list_t - hinge_depth/2"""

def handle_y(self, wall_t, blade_t, karm_depth):
    """Y-posisjon for håndtak (framkant av blad). Flush-typer: wall_t/2 + list_t"""

def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
    """Y-posisjon for terskel. Flush-typer: wall_t/2 - threshold_depth - blade_t"""
```

For flush-typer (SD1/SD2/KD1/KD2) er `list_t = 7` i alle Y-metoder.

---

## Steg 4: Registrer profiler

I `src/gui/karm_profiles/__init__.py`:

```python
from .xx.xx1 import XX1Profile

KARM_PROFILES = {
    ...,
    'XX1': XX1Profile(),
}
```

---

## Steg 5: KARM_DEPTHS i 3D-viewer

I `src/gui/widgets/door_preview_3d.py`, legg til i `KARM_DEPTHS`:

```python
KARM_DEPTHS = {'SD1': 77, 'SD2': 84, 'SD3/ID': 92, 'KD1': 97, 'KD2': 104, 'XX1': ...}
```

**Formel for flush-typer:**

- Begge sider (SD1/KD1): `karm_depth = blade_t + anslag_d + list_t` (f.eks. 60+24+7=91... men justeres etter faktisk design)
- Kun framside (SD2/KD2): `karm_depth = begge_sider_depth + list_t`

---

## Steg 6: PDF-snittprofiler

I `src/export/pdf_constants.py`, legg til i `KARM_SECTION_PROFILES`:

```python
'XX1': {
    'listverk_w': 80, 'listverk_t': 7,
    'kobling_t': 5,
    'anslag_w': 20, 'anslag_d': 24,
    'blade_t': 60,
    'both_sides': True,          # Listverk på begge sider?
    'no_listverk': False,        # Smygmontasje?
    'kobling_depth_fixed': None, # None = wall_t, eller fast verdi
},
```

For smygmontasje (SD3/ID-variant) brukes i stedet:

```python
'XX1': {
    'body_w': 24, 'kobling_t': 5,
    'anslag_w': 20, 'anslag_d': 52,
    'blade_t': 40, 'karm_depth': 92,
    'both_sides': False, 'no_listverk': True,
},
```

---

## Steg 7: Kappeliste-gruppering

I `src/models/production_list.py`:

### 7a) Karmfamilier

```python
KARM_FAMILY_GROUPS = {
    ...,
    'XX1': 'XX1_XX2',
    'XX2': 'XX1_XX2',
}

KARM_FAMILY_TITLES = {
    ...,
    'XX1_XX2': 'Beskrivende familienavn (XX1 og XX2)',
}

KARM_FAMILY_ORDER = [..., 'XX1_XX2']
```

### 7b) Dørramme-navn

Allerede dynamisk: `DR{blade_thickness}` (f.eks. DR40, DR60).

### 7c) Spesielle komponenter

Hvis dørtypen har unike komponenter (f.eks. Laminat 2), legg dem til i
`_build_items_for_door()`. Velg om de skal vises i kappeliste-diverse
(`get_diverse_rows()` → `diverse_komps`) eller kun i detaljvisningen.

### 7d) Dekklist

Dekklist genereres kun for SDI 2-fløyet (`p.door_type == 'SDI'`).
Nye dørtyper trenger ingen endring — de er automatisk ekskludert.

---

## Steg 8: Nye konstanter/beregninger (valgfritt)

Hvis dørtypen har nye felt (som `laminat_2_offsets`):

1. **`src/utils/constants.py`** — Bygg oppslags-tabell fra registry:

   ```python
   LAMINAT_2_OFFSETS = {}
   for d in DOOR_REGISTRY.values():
       LAMINAT_2_OFFSETS.update(d.get('laminat_2_offsets', {}))
   ```

2. **`src/utils/calculations.py`** — Importer og lag beregningsfunksjon

3. **`src/gui/widgets/detail_tab.py`** — Legg til felter i detaljvisningen,
   med `setVisible()` for å skjule når ikke aktuelt

---

## Steg 9: Verifisering

```bash
# 1. Kjør appen
uv run python main.py

# 2. Sjekk i GUI:
#    - Ny dørtype vises i dropdown
#    - Karmtyper, fløyer, hengsler fungerer
#    - 3D-viewer viser riktig geometri
#    - Detaljside viser korrekte beregninger
#    - Transportmål beregnes

# 3. Generer PDF — verifiser horisontalsnitt

# 4. Legg til dør i dørlisten — sjekk kappeliste
```

---

## Sjekkliste

- [ ] Dørtype-fil opprettet (`src/doors/`)
- [ ] Registrert i `__init__.py`
- [ ] 3D-profiler opprettet og registrert
- [ ] KARM_DEPTHS oppdatert
- [ ] KARM_SECTION_PROFILES oppdatert
- [ ] Karmfamilier i production_list.py
- [ ] Evt. nye konstanter/beregninger
- [ ] Evt. nye felter i detail_tab.py
- [ ] Dekklist håndtert (aktiv eller ekskludert)
- [ ] Test i GUI, PDF og kappeliste
