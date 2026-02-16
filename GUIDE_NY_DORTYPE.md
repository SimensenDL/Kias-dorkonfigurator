# Guide: Legge til ny dørtype i KIAS Dørkonfigurator

> Denne guiden dekker alle steg som kreves for å legge til en komplett ny dørtype slik at
> **produksjonsmål**, **ordretekst**, **kappliste**, **3D-viewer** og **PDF-eksport** fungerer korrekt.

---

## Innholdsfortegnelse

1. [Oversikt — hva påvirkes?](#1-oversikt--hva-påvirkes)
2. [Steg 1 — Opprett dørtype-datafil](#steg-1--opprett-dørtype-datafil)
3. [Steg 2 — Registrer i DOOR_REGISTRY](#steg-2--registrer-i-door_registry)
4. [Steg 3 — Verifiser constants.py](#steg-3--verifiser-constantspy)
5. [Steg 4 — Opprett karm-profiler for 3D-viewer](#steg-4--opprett-karm-profiler-for-3d-viewer)
6. [Steg 5 — Registrer karm-profiler](#steg-5--registrer-karm-profiler)
7. [Steg 6 — Oppdater KARM_DEPTHS i 3D-viewer](#steg-6--oppdater-karm_depths-i-3d-viewer)
8. [Steg 7 — Verifiser GUI (door_form.py)](#steg-7--verifiser-gui-door_formpy)
9. [Steg 8 — Verifiser beregninger (calculations.py)](#steg-8--verifiser-beregninger-calculationspy)
10. [Steg 9 — Verifiser ordretekst](#steg-9--verifiser-ordretekst)
11. [Steg 10 — Verifiser kappliste](#steg-10--verifiser-kappliste)
12. [Steg 11 — Verifiser PDF-eksport](#steg-11--verifiser-pdf-eksport)
13. [Steg 12 — Verifiser detaljfanen](#steg-12--verifiser-detaljfanen)
14. [Steg 13 — Test alt ende-til-ende](#steg-13--test-alt-ende-til-ende)
15. [Referanse — komplett datafil-skjema](#referanse--komplett-datafil-skjema)
16. [Referanse — beregningsformler](#referanse--beregningsformler)
17. [Referanse — filstier](#referanse--filstier)
18. [Vanlige feil](#vanlige-feil)

---

## 1. Oversikt — hva påvirkes?

Når du legger til en ny dørtype flyter data gjennom disse lagene:

```
src/doors/<ny_type>.py          ← DU LAGER DENNE (ren dict, ingen imports)
        ↓
src/doors/__init__.py           ← Registrer i _DOOR_TYPE_MODULES
        ↓
src/utils/constants.py          ← Bygger oppslags-tabeller AUTOMATISK
        ↓
src/models/door.py              ← DoorParams bruker oppslags-tabellene
        ↓
  ┌─────────┬──────────────┬────────────┬──────────────┐
  │  GUI    │  Kappliste   │ Ordretekst │  PDF-eksport │
  │  skjema │  beregninger │  generering│  tegning     │
  └─────────┴──────────────┴────────────┴──────────────┘
```

### Filer du MÅ opprette/endre

| Fil | Handling | Hvorfor |
|-----|----------|---------|
| `src/doors/<ny_type>.py` | **Opprett** | Alle mål og offsets for dørtypen |
| `src/doors/__init__.py` | **Endre** | Registrere ny type i `_DOOR_TYPE_MODULES` |
| `src/gui/karm_profiles/<type>/*.py` | **Opprett** | 3D-geometri for hver karmtype |
| `src/gui/karm_profiles/__init__.py` | **Endre** | Registrere nye karm-profiler i `KARM_PROFILES` |
| `src/gui/widgets/door_preview_3d.py` | **Endre** | Legge til karm-dybder i `KARM_DEPTHS` |

### Filer som fungerer AUTOMATISK (ingen endring nødvendig)

| Fil | Hvorfor den fungerer automatisk |
|-----|-------------------------------|
| `src/utils/constants.py` | Bygger alle tabeller fra `DOOR_REGISTRY` |
| `src/utils/calculations.py` | Bruker offset-tabellene generisk |
| `src/utils/ordretekst.py` | Leser `ordretekst`-maler fra door dict |
| `src/gui/widgets/door_form.py` | Populerer dropdowns fra constants |
| `src/gui/widgets/detail_tab.py` | Bruker calculations.py generisk |
| `src/gui/widgets/door_list_tab.py` | Label genereres fra `DOOR_TYPES` |
| `src/models/production_list.py` | Bruker calculations.py generisk |
| `src/export/docx_ordretekst.py` | Bruker ordretekst.py generisk |
| `src/export/pdf_kappeliste.py` | Bruker production_list generisk |

---

## Steg 1 — Opprett dørtype-datafil

Opprett filen `src/doors/<ny_type>.py`. Den skal være en **ren Python-dict uten imports**.

### Minimal mal

```python
"""
<Beskrivende navn> — KIAS Dørkonfigurator
Alle mål i millimeter (mm).
"""

NY_DORTYPE = {
    # ──────────────────────────────────────────────
    # IDENTIFIKASJON
    # ──────────────────────────────────────────────
    'key': 'XYZ',                    # Unik nøkkel (brukes overalt internt)
    'name': 'Beskrivende Navn',      # Visningsnavn i GUI

    # ──────────────────────────────────────────────
    # STANDARDMÅL (utsparing / bygningsåpning)
    # ──────────────────────────────────────────────
    'default_width': 1010,           # BM bredde (mm)
    'default_height': 2110,          # HM høyde (mm)
    'default_thickness': 100,        # Veggtykkelse (mm)

    # ──────────────────────────────────────────────
    # KARMTYPER OG FLØYER
    # ──────────────────────────────────────────────
    'karm_types': ['KT1', 'KT2'],   # Alle karmtyper for denne dørtypen
    'floyer': [1, 2],                # Mulige antall fløyer (globalt)
    'karm_floyer': {                 # Tillatt fløy-antall per karmtype
        'KT1': [1, 2],
        'KT2': [1],
    },

    # ──────────────────────────────────────────────
    # DØRBLAD-TYPER
    # ──────────────────────────────────────────────
    'blade_types': {
        'XYZ_TYPE_A': {
            'name': 'Dørblad type A',
            'thicknesses': [40],      # Tilgjengelige tykkelser
        },
    },
    'karm_blade_types': {            # Tillatte bladtyper per karmtype
        'KT1': ['XYZ_TYPE_A'],
        'KT2': ['XYZ_TYPE_A'],
    },

    # ──────────────────────────────────────────────
    # TERSKELTYPER PER KARMTYPE
    # ──────────────────────────────────────────────
    'karm_threshold_types': {
        'KT1': ['ingen', 'slepelist', 'anslag_37'],
        'KT2': ['ingen', 'slepelist'],
    },

    # ──────────────────────────────────────────────
    # UTFORING (valgfritt — kun for karmer med utforing)
    # ──────────────────────────────────────────────
    'karm_has_utforing': set(),      # Tomt sett = ingen utforing
    # 'karm_has_utforing': {'KT1'},  # Eksempel: kun KT1 støtter utforing

    # ──────────────────────────────────────────────
    # FLUSH-MONTERING (dørblad flush med listverk)
    # ──────────────────────────────────────────────
    'karm_blade_flush': {'KT1'},     # Karmtyper der blad er flush med list

    # ══════════════════════════════════════════════
    # PRODUKSJONSOFFSETS — KRITISKE MÅL
    # ══════════════════════════════════════════════

    # ── Karm → fra utsparing ──────────────────────
    'karm_size_offsets': {
        'KT1': {'width': 70, 'height': 30},    # karm = utsparing + offset
        'KT2': {'width': -20, 'height': -20},  # negativ = karm mindre enn utsparing
    },

    # ── Sidestolpe bredde (mm) ────────────────────
    'karm_sidestolpe_width': {
        'KT1': 80,
        'KT2': 44,
    },

    # ── Transport bredde (vinkelbasert) ───────────
    # Formel: transport_bredde = utsparing_bredde + offset
    'transport_width_offsets': {
        'KT1': {
            1: {'90': -120, '180': -90},   # 1-fløy: 90° og 180° åpning
            # 2: {'90': -XXX, '180': -XXX},  # Legg til for 2-fløy om aktuelt
        },
        'KT2': {
            1: {'90': -143, '180': -108},
        },
    },

    # ── Transport høyde (terskelbasert) ───────────
    # Formel: transport_hoyde = utsparing_hoyde + offset
    # Sett None for terskeltyper som IKKE er gyldige for denne karmtypen
    'transport_height_offsets': {
        'KT1': {
            'ingen': -50,
            'slepelist': -50,
            'anslag_37': -67,
        },
        'KT2': {
            'ingen': -64,
            'slepelist': -64,
        },
    },

    # ── Dørblad offsets (karm → dørblad) ──────────
    # To mulige strukturer — velg riktig:
    #
    # STRUKTUR A — Standard (som SD1/SD2):
    #   {karmtype: {fløyer: {'bredde': X, 'hoyde': X}}}
    #
    # STRUKTUR B — Bladtype-avhengig (som SD3/ID):
    #   {karmtype: {bladtype: {fløyer: {'bredde': X, 'hoyde_base': X}}}}
    #
    'dorblad_offsets': {
        # Struktur A eksempel:
        'KT1': {
            1: {'bredde': 128, 'hoyde': 85},
            2: {'bredde': 132, 'hoyde': 85},
        },
        # Struktur B eksempel:
        'KT2': {
            'XYZ_TYPE_A': {
                1: {'bredde': 63, 'hoyde_base': 32},
            },
        },
    },

    # ── Dørblad høyde inkl. luftspalte ────────────
    # Karmtyper der luftspalte trekkes fra dørblad-høyde.
    # Gjelder kun Struktur B (med 'hoyde_base').
    'dorblad_hoyde_inkl_luftspalte': {'KT2'},  # Tomt sett hvis ikke aktuelt

    # ── Terskel (anslags) offsets ─────────────────
    # Formel: terskel_lengde = karm_bredde - offset
    'terskel_offsets': {
        'KT1': {1: 160, 2: 160},
        'KT2': {1: 56},
    },

    # ── Laminat offsets ───────────────────────────
    # Formel: laminat = dørblad - offset
    # Kan være int (fast) eller dict (per bladtype)
    'laminat_offsets': {
        'KT1': 8,                           # Fast verdi
        'KT2': {'XYZ_TYPE_A': 8},           # Per bladtype
    },

    # ── Dekklist offset (2-fløy) ──────────────────
    # Felles for alle typer, definert globalt i constants.py (102mm)
    # Inkluderes her kun hvis din type trenger annen verdi:
    # 'dekklist_2floyet_offset': 102,

    # ══════════════════════════════════════════════
    # HENGSLER (bestemt av bladtype, ikke brukervalg)
    # ══════════════════════════════════════════════
    'hengsler': {
        'XYZ_TYPE_A': {
            'navn': 'Hengsler type A i SF stål',
            'antall': {1: 2, 2: 4},          # Antall per fløy-konfigurasjon
            'tekst': {1: '(2 stk.)', 2: '(2 x 2 stk.)'},
        },
    },

    # ══════════════════════════════════════════════
    # ORDRETEKST — maler for ordre/tilbudstekst
    # ══════════════════════════════════════════════
    'karm_beskrivelse': {
        'KT1': 'Aluminiumskarm KT1, dybde XX mm, pulverlakkert {farge}',
        'KT2': 'Aluminiumskarm KT2, dybde XX mm, pulverlakkert {farge}',
    },

    'ordretekst': {
        'tittel': {
            1: 'XYZ - KIAS DØRTYPE 1-FLØYA',
            2: 'XYZ - KIAS DØRTYPE 2-FLØYA',
        },
        'linjer': [
            'Utsparing BM{bm_b} x HM{bm_h}, BT{bt_b} x HT{bt_h} mm',
            'Slagretning {slagretning}',
            'GRP dørblad {blad_tykkelse} mm m/kantlist i pulverlakkert aluminium, {farge}',
            '{karm_beskrivelse}',
            'Låskasse {laaskasse}',
            '{beslag}',
            'KIAS sluttstykke med tett brønn, i SF stål',
            '{hengsler}',
        ],
        'linjer_2floyet': [
            'Espagnolett Roca i SF stål',
            'Dekklist i aluminium {karm_farge}',
        ],
        # Valgfri overstyring av terskel-tekst per type:
        # 'terskel_tekst': {
        #     'spesiell_terskel': 'Spesiell terskel, pulverlakkert {karm_farge}',
        # },
    },
}
```

### Tilgjengelige plassholdere i ordretekst-maler

| Plassholder | Kilde | Eksempel |
|-------------|-------|---------|
| `{bm_b}` | `door.width` | `1010` |
| `{bm_h}` | `door.height` | `2110` |
| `{bt_b}` | `door.transport_width_90()` | `890` |
| `{bt_h}` | `door.transport_height_by_threshold()` | `2060` |
| `{slagretning}` | `SWING_DIRECTIONS[door.swing_direction]` | `Venstre` |
| `{blad_tykkelse}` | `door.blade_thickness` | `40` |
| `{farge}` | RAL-formatert bladfarge | `Renhvit (RAL 9010)` |
| `{karm_farge}` | RAL-formatert karmfarge | `Renhvit (RAL 9010)` |
| `{karm_beskrivelse}` | Fra `karm_beskrivelse`-malen | Hel setning |
| `{laaskasse}` | `door.lock_case` | `3065_316l` |
| `{beslag}` | `door.handle_type` | `vrider_sylinder_oval` |
| `{hengsler}` | Fra `hengsler`-data + tekst | `Hengsler Roca i SF stål (2 stk.)` |
| `{luftspalte}` | `door.effective_luftspalte()` | `22` |
| `{veggtykkelse}` | `door.thickness` | `100` |

### Viktige regler for dorblad_offsets

Det finnes **to offset-strukturer** — du må velge riktig for hver karmtype:

#### Struktur A: Flat (SD1/SD2-mønster)
```python
'KT1': {
    1: {'bredde': 128, 'hoyde': 85},     # Nøkkel 'hoyde'
    2: {'bredde': 132, 'hoyde': 85},
}
```
- Indeksert med **fløy-antall** direkte
- Bruker nøkkelen `'hoyde'`
- Luftspalte trekkes **IKKE** fra

#### Struktur B: Nestet per bladtype (SD3/ID-mønster)
```python
'KT2': {
    'XYZ_TYPE_A': {
        1: {'bredde': 63, 'hoyde_base': 32},  # Nøkkel 'hoyde_base'
    },
}
```
- Indeksert med **bladtype → fløy-antall**
- Bruker nøkkelen `'hoyde_base'`
- Legg karmtypen i `'dorblad_hoyde_inkl_luftspalte'` for at luftspalte trekkes fra

---

## Steg 2 — Registrer i DOOR_REGISTRY

Rediger `src/doors/__init__.py`:

```python
from .innerdor import INNERDOR
from .ny_type import NY_DORTYPE          # ← Legg til import

_DOOR_TYPE_MODULES = [
    INNERDOR,
    NY_DORTYPE,                          # ← Legg til i listen
]

DOOR_REGISTRY = {}
for _door_def in _DOOR_TYPE_MODULES:
    DOOR_REGISTRY[_door_def['key']] = _door_def
```

**Etter dette bygges alle oppslags-tabeller i `constants.py` automatisk.**

---

## Steg 3 — Verifiser constants.py

`src/utils/constants.py` bygger alle tabeller automatisk fra `DOOR_REGISTRY`. Du trenger **ikke endre denne filen** med mindre:

- Din dørtype har en `DOOR_TYPE_BLADE_OVERRIDE` (bladtype bestemt av dørtype, ikke karmtype)
- Du bruker nye terskeltyper som ikke finnes i `THRESHOLD_LUFTSPALTE`
- Du har globale konstanter som avviker (f.eks. annen `DEKKLIST_2FLOYET_OFFSET`)

### Sjekkliste — verifiser at disse tabellene fylles korrekt

Start applikasjonen og sjekk i en Python-konsoll eller legg inn midlertidige print-setninger:

```python
from src.utils.constants import *

# Skal inneholde din nye nøkkel
assert 'XYZ' in DOOR_TYPES
assert 'XYZ' in DEFAULT_DIMENSIONS
assert 'XYZ' in DOOR_KARM_TYPES

# Karmtype-spesifikke tabeller
for kt in ['KT1', 'KT2']:
    assert kt in KARM_SIZE_OFFSETS
    assert kt in KARM_SIDESTOLPE_WIDTH
    assert kt in TRANSPORT_WIDTH_OFFSETS
    assert kt in TRANSPORT_HEIGHT_OFFSETS
    assert kt in DORBLAD_OFFSETS
    assert kt in KARM_THRESHOLD_TYPES
    assert kt in KARM_BLADE_TYPES

# Bladtype-tabeller
assert 'XYZ_TYPE_A' in DOOR_BLADE_TYPES
```

---

## Steg 4 — Opprett karm-profiler for 3D-viewer

For **hver karmtype** i din dørtype trenger du en `KarmProfile`-underklasse.

### Opprett mappe og filer

```
src/gui/karm_profiles/
├── __init__.py          ← Endre (steg 5)
├── base.py              ← Ikke endre
├── sdi/                 ← Eksisterende (innerdør)
│   ├── sd1.py
│   ├── sd2.py
│   └── sd3id.py
└── xyz/                 ← OPPRETT NY MAPPE
    ├── __init__.py      ← Tom eller med imports
    ├── kt1.py           ← Profil for KT1
    └── kt2.py           ← Profil for KT2
```

### KarmProfile-grensesnitt

Baseklassen (`base.py`) definerer disse metodene:

| Metode | Returverdi | Beskrivelse |
|--------|-----------|-------------|
| `build_frame_parts(door, kb, kh, wall_t, karm_depth, sidestolpe_w)` | `list[(bx,by,bz, dx,dy,dz)]` | Alle bokser som utgjør karmen |
| `blade_y(wall_t, blade_t, karm_depth)` | `float` | Y-posisjon (dybde) til dørbladets bakside |
| `hinge_y(wall_t, blade_t, karm_depth, hinge_depth)` | `float` | Y-posisjon for hengselfeste |
| `handle_y(wall_t, blade_t, karm_depth)` | `float` | Y-posisjon for håndtak |
| `threshold_y(wall_t, blade_t, karm_depth, threshold_depth)` | `float` | Y-posisjon for terskel |
| `luftspalte(door)` | `int` | Luftspalte i mm (standard: 22) |

### Koordinatsystem

```
        Y+ (framside/mot deg)
        ↑
        │
        │
  X- ←──┼──→ X+ (høyre sett forfra)
        │
        ↓
        Y- (bakside/gjennom vegg)

  Z+ = oppover (0 = gulvnivå)
```

- Origo = senter av døråpningen (X=0, Z=0)
- Veggen strekker seg fra `y = -wall_t/2` til `y = +wall_t/2`
- Alle mål i millimeter

### Eksempel — enkel karm-profil

```python
from ..base import KarmProfile

class KT1Profile(KarmProfile):
    """Eksempel karm-profil med listverk på framside."""

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        parts = []
        list_w = 60       # Bredde listverk
        list_t = 7        # Tykkelse listverk
        kobling_t = 5     # Tykkelse kobling
        anslag_w = 20     # Bredde anslag
        anslag_d = 44     # Dybde anslag

        front_y = wall_t / 2           # Vegg framkant
        list_y = front_y               # List starter på veggflaten

        # ── Listverk (framside) ──
        # Venstre loddrett list
        parts.append((-kb/2 - list_w, list_y, 0,  list_w, list_t, kh))
        # Høyre loddrett list
        parts.append((kb/2, list_y, 0,  list_w, list_t, kh))
        # Topp vannrett list
        parts.append((-kb/2 - list_w, list_y, kh,  kb + 2*list_w, list_t, list_w))

        # ── Kobling (innerkant, gjennom vegg) ──
        kobling_y = front_y - karm_depth + list_t
        # Venstre
        parts.append((-kb/2 - kobling_t, kobling_y, 0,  kobling_t, karm_depth, kh))
        # Høyre
        parts.append((kb/2, kobling_y, 0,  kobling_t, karm_depth, kh))
        # Topp
        parts.append((-kb/2, kobling_y, kh,  kb, karm_depth, kobling_t))

        # ── Anslag (bak dørblad) ──
        anslag_y = front_y + list_t - anslag_d  # Starter bak bladet
        # Venstre
        parts.append((-kb/2 - kobling_t - anslag_w, anslag_y, 0,  anslag_w, anslag_d, kh))
        # Høyre
        parts.append((kb/2 + kobling_t, anslag_y, 0,  anslag_w, anslag_d, kh))
        # Topp
        parts.append((-kb/2, anslag_y, kh + kobling_t,  kb, anslag_d, anslag_w))

        return parts

    def blade_y(self, wall_t, blade_t, karm_depth):
        # Dørblad flush med listverk framkant
        return wall_t / 2 + 7 - blade_t

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        return wall_t / 2 + 7 - hinge_depth / 2

    def handle_y(self, wall_t, blade_t, karm_depth):
        return wall_t / 2 + 7

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        return wall_t / 2 - threshold_depth - blade_t
```

### Tips for 3D-geometri

- **Flush-montasje** (SD1/SD2): List på veggflaten, referansepunkt er `wall_t/2 + list_tykkelse`
- **Smygmontasje** (SD3/ID): Karm inne i vegg, referansepunkt er `karm_depth/2`
- Sjekk at dørblad, hengsler og håndtak **ikke overlapper** med karmdelene
- Test med ulike veggtykkelser (70mm, 100mm, 200mm) for å se at geometrien skalerer riktig

---

## Steg 5 — Registrer karm-profiler

Rediger `src/gui/karm_profiles/__init__.py`:

```python
from .sdi.sd1 import SD1Profile
from .sdi.sd2 import SD2Profile
from .sdi.sd3id import SD3IDProfile
from .xyz.kt1 import KT1Profile            # ← Ny import
from .xyz.kt2 import KT2Profile            # ← Ny import

KARM_PROFILES = {
    'SD1': SD1Profile(),
    'SD2': SD2Profile(),
    'SD3/ID': SD3IDProfile(),
    'KT1': KT1Profile(),                   # ← Ny registrering
    'KT2': KT2Profile(),                   # ← Ny registrering
}
```

**Nøklene MÅ matche `karm_types`-verdiene i dørtype-datafilen.**

---

## Steg 6 — Oppdater KARM_DEPTHS i 3D-viewer

Rediger `src/gui/widgets/door_preview_3d.py`, finn `KARM_DEPTHS`-dicten (typisk nær toppen):

```python
KARM_DEPTHS = {
    'SD1': 77,
    'SD2': 84,
    'SD3/ID': 92,
    'KT1': XX,    # ← Legg til karmdybde i mm
    'KT2': XX,    # ← Legg til karmdybde i mm
}
```

Denne verdien sendes til alle `KarmProfile`-metoder som `karm_depth`.

---

## Steg 7 — Verifiser GUI (door_form.py)

`door_form.py` bruker constants-tabellene til å populere alle dropdowns. **Normalt kreves ingen endring**, men verifiser:

### Sjekkliste

- [ ] Ny dørtype vises i dørtype-dropdown
- [ ] Karmtyper oppdateres ved valg av ny dørtype
- [ ] Fløyer filtreres korrekt per karmtype
- [ ] Bladtyper filtreres korrekt per karmtype
- [ ] Terskeltyper filtreres korrekt per karmtype
- [ ] Utforing vises/skjules korrekt (kun for karmer i `karm_has_utforing`)
- [ ] Transport-labels (BT90°, BT180°, HT) beregnes korrekt
- [ ] Karm bredde/høyde-labels oppdateres

### Mulige endringer

Hvis din dørtype har **unike GUI-elementer** (f.eks. blytykkelse for røntgendører, brannklasse for branndører), kan det kreves endringer i `door_form.py`. DoorParams har allerede felter for:

- `fire_rating` — Brannklasse
- `sound_rating` — Lydklasse
- `lead_thickness` — Blytykkelse (røntgen)

Disse er gjemt i nåværende GUI, men kan vises betinget for relevante dørtyper.

---

## Steg 8 — Verifiser beregninger (calculations.py)

`calculations.py` er **generisk** og bruker offset-tabellene. Du trenger **ikke endre denne filen**.

### Funksjoner og hva de forventer

| Funksjon | Offset-tabell | Forventet struktur |
|----------|---------------|--------------------|
| `karm_bredde()` | `KARM_SIZE_OFFSETS[karm]['width']` | `int` |
| `karm_hoyde()` | `KARM_SIZE_OFFSETS[karm]['height']` | `int` |
| `transport_bredde_90()` | `TRANSPORT_WIDTH_OFFSETS[karm][fløy]['90']` | `int` |
| `transport_bredde_180()` | `TRANSPORT_WIDTH_OFFSETS[karm][fløy]['180']` | `int` |
| `transport_hoyde()` | `TRANSPORT_HEIGHT_OFFSETS[karm][terskel]` | `int` eller `None` |
| `dorblad_bredde()` | `DORBLAD_OFFSETS[karm]` | Struktur A eller B |
| `dorblad_hoyde()` | `DORBLAD_OFFSETS[karm]` + `DORBLAD_HOYDE_INKL_LUFTSPALTE` | Struktur A eller B |
| `terskel_lengde()` | `TERSKEL_OFFSETS[karm][fløy]` | `int` |
| `laminat_mal()` | `LAMINAT_OFFSETS[karm]` | `int` eller `dict` |
| `dekklist_lengde()` | `DEKKLIST_2FLOYET_OFFSET` (global) | `int` |

### Verifiser med testberegning

```python
from src.utils.calculations import *

# Test med kjente verdier
karm_type = 'KT1'
utsp_b, utsp_h = 1010, 2110

kb = karm_bredde(karm_type, utsp_b)
kh = karm_hoyde(karm_type, utsp_h)
print(f"Karm: {kb} x {kh}")

db_b = dorblad_bredde(karm_type, kb, 1, 'XYZ_TYPE_A')
db_h = dorblad_hoyde(karm_type, kh, 1, 'XYZ_TYPE_A', 22)
print(f"Dørblad: {db_b} x {db_h}")

t90 = transport_bredde_90(karm_type, kb, 1)
t180 = transport_bredde_180(karm_type, kb, 1)
th = transport_hoyde(karm_type, kh, 'ingen')
print(f"Transport: BT90={t90}, BT180={t180}, HT={th}")

t_len = terskel_lengde(karm_type, kb, 1)
print(f"Terskel: {t_len}")

lam_b, lam_h = laminat_mal(karm_type, db_b, db_h, 'XYZ_TYPE_A')
print(f"Laminat: {lam_b} x {lam_h}")
```

Sammenlign resultatene med fysiske produksjonsmål fra KIAS.

---

## Steg 9 — Verifiser ordretekst

`src/utils/ordretekst.py` bruker `ordretekst`-malen fra dørtype-definisjonen. **Ingen endring nødvendig** med mindre:

- Du har egne terskel-tekster → bruk `'terskel_tekst'` i ordretekst-definisjonen
- Du har linjer som skal utelates betinget → sjekk `_skal_utelates()` i ordretekst.py

### Sjekkliste

- [ ] Tittel viser korrekt for 1-fløy og 2-fløy
- [ ] Utsparing BM × HM viser korrekte verdier
- [ ] Transport BT × HT viser korrekte verdier
- [ ] Karm-beskrivelse inkluderer riktig farge
- [ ] Hengsler-tekst er korrekt (fra bladtype)
- [ ] Terskel-tekst vises for riktig terskeltype
- [ ] 2-fløy-linjer (espagnolett, dekklist) vises kun for 2-fløy
- [ ] Ordretekst i detaljfanen matcher Word-eksporten

---

## Steg 10 — Verifiser kappliste

Kapplisten genereres av `production_list.py` som bruker `calculations.py`. **Ingen endring nødvendig.**

### Sjekkliste

- [ ] Overligger: lengde = karm_bredde
- [ ] Hengselside: lengde = karm_høyde, side = V/H basert på slagretning
- [ ] Sluttstykkeside: lengde = karm_høyde, side = V/H (motsatt av hengsel)
- [ ] DR40 over-/underdel: lengde = dørblad_bredde
- [ ] DR40 sidedel: lengde = dørblad_høyde
- [ ] Laminat: bredde × høyde korrekt
- [ ] Terskel: lengde korrekt (kun når terskeltype ≠ 'ingen')
- [ ] Dekklist: lengde korrekt (kun for 2-fløy)
- [ ] Gruppering: karmtyper grupperes korrekt i seksjoner
- [ ] Fargekoding: riktig RAL-farge per komponent

### Kappliste PDF-seksjonering

Kapplisten grupperer komponenter slik:

1. **Karm-seksjoner** — én seksjon per "karmfamilie" (f.eks. SD1+SD2 sammen, SD3/ID alene)
2. **Dørramme-seksjoner** — DR40-deler gruppert etter mål og farge
3. **Diverse** — Laminat, terskel, dekklist i egen tabell

Sjekk at din nye karmtype havner i riktig seksjon.

---

## Steg 11 — Verifiser PDF-eksport

PDF-tegningen (`pdf_exporter.py`) bruker DoorParams direkte. **Normalt ingen endring nødvendig.**

### Sjekkliste

- [ ] Tittelfelt viser korrekt dørtype-navn
- [ ] BM, BT90°, BT180°, HT vises i tittelfelt
- [ ] Dør-tegning skalerer korrekt
- [ ] Hengsler plasseres riktig antall og side

---

## Steg 12 — Verifiser detaljfanen

`detail_tab.py` bruker calculations.py generisk. **Ingen endring nødvendig.**

### Sjekkliste

- [ ] Karm bredde/høyde vises
- [ ] Terskel lengde vises (eller "—" for 'ingen')
- [ ] Dørblad bredde/høyde vises
- [ ] Laminat bredde/høyde vises
- [ ] Dekklist vises for 2-fløy, skjult for 1-fløy
- [ ] 2-fløy viser separat "Dørblad 1" og "Dørblad 2"
- [ ] Ordretekst vises korrekt under detalj-verdiene

---

## Steg 13 — Test alt ende-til-ende

### Test-matrise

For **hver karmtype** i ny dørtype, test:

| Test | Forventet |
|------|-----------|
| Velg dørtype i dropdown | Standardmål lastes, karmtyper populeres |
| Endre karmtype | Fløyer, bladtyper, terskeltyper oppdateres |
| Endre bredde/høyde | Transport-labels oppdateres live |
| Endre terskeltype | Transport-høyde endres |
| 3D-visning | Karm, dørblad, hengsler, håndtak rendres |
| 3D: åpne dør | Dørbladet roterer korrekt |
| Legg til i dørliste | Dør vises med korrekt label |
| Dobbeltklikk i liste | Dør lastes tilbake i skjemaet |
| Eksporter ordretekst (.docx) | Alle verdier korrekte, formatering ok |
| Eksporter kappliste (PDF) | Alle komponenter med riktige mål |
| Eksporter PDF-tegning | Tittelfelt og tegning korrekt |
| Sjekk detaljfanen | Alle produksjonsmål korrekte |

### Test med spesielle kombinasjoner

- [ ] 1-fløy med ulike terskeltyper
- [ ] 2-fløy med ulik split (30/70, 50/50)
- [ ] Minste og største tillatte mål
- [ ] Venstre og høyre slagretning
- [ ] Ulike farger (blade ≠ karm)
- [ ] Utforing (hvis støttet)
- [ ] Flere dører med ulik karmtype i samme kappliste

---

## Referanse — komplett datafil-skjema

Her er **alle nøkler** som kan/må finnes i dørtype-dicten:

### Påkrevde nøkler

| Nøkkel | Type | Beskrivelse |
|--------|------|-------------|
| `key` | `str` | Unik intern nøkkel (f.eks. `'SDI'`, `'SDK'`) |
| `name` | `str` | Visningsnavn (f.eks. `'Innerdør'`) |
| `default_width` | `int` | Standard utsparingsbredde (mm) |
| `default_height` | `int` | Standard utsparingshøyde (mm) |
| `default_thickness` | `int` | Standard veggtykkelse (mm) |
| `karm_types` | `list[str]` | Alle karmtyper |
| `floyer` | `list[int]` | Mulige fløy-antall |
| `karm_floyer` | `dict[str, list[int]]` | Fløyer per karmtype |
| `blade_types` | `dict[str, dict]` | Bladtyper med navn og tykkelser |
| `karm_blade_types` | `dict[str, list[str]]` | Tillatte bladtyper per karmtype |
| `karm_threshold_types` | `dict[str, list[str]]` | Terskeltyper per karmtype |
| `karm_size_offsets` | `dict[str, dict]` | `{'width': int, 'height': int}` per karmtype |
| `karm_sidestolpe_width` | `dict[str, int]` | Sidestolpe-bredde per karmtype |
| `transport_width_offsets` | `dict[str, dict]` | Transport-bredde per karm/fløy/vinkel |
| `transport_height_offsets` | `dict[str, dict]` | Transport-høyde per karm/terskel |
| `dorblad_offsets` | `dict[str, dict]` | Dørblad-offsets (Struktur A eller B) |
| `terskel_offsets` | `dict[str, dict]` | Terskel-lengde offset per karm/fløy |
| `laminat_offsets` | `dict[str, int\|dict]` | Laminat-offset per karm (og evt. bladtype) |
| `hengsler` | `dict[str, dict]` | Hengsel-info per bladtype |
| `karm_beskrivelse` | `dict[str, str]` | Karm-beskrivelse mal per karmtype |
| `ordretekst` | `dict` | Ordretekst-maler (tittel, linjer, etc.) |

### Valgfrie nøkler

| Nøkkel | Type | Standard | Beskrivelse |
|--------|------|----------|-------------|
| `karm_has_utforing` | `set[str]` | `set()` | Karmtyper med utforing |
| `karm_blade_flush` | `set[str]` | `set()` | Karmtyper der blad er flush |
| `dorblad_hoyde_inkl_luftspalte` | `set[str]` | `set()` | Karmtyper der luftspalte inngår i bladhøyde |
| `dekklist_2floyet_offset` | `int` | `102` | Offset for dekklist (2-fløy) |

---

## Referanse — beregningsformler

### Fra utsparing til karm
```
karm_bredde = utsparing_bredde + KARM_SIZE_OFFSETS[karm]['width']
karm_hoyde  = utsparing_hoyde  + KARM_SIZE_OFFSETS[karm]['height']
```

### Fra utsparing til transport
```
transport_bredde_90  = utsparing_bredde + TRANSPORT_WIDTH_OFFSETS[karm][fløy]['90']
transport_bredde_180 = utsparing_bredde + TRANSPORT_WIDTH_OFFSETS[karm][fløy]['180']
transport_hoyde      = utsparing_hoyde  + TRANSPORT_HEIGHT_OFFSETS[karm][terskel]
```

### Fra karm til dørblad (Struktur A)
```
dørblad_bredde = karm_bredde - DORBLAD_OFFSETS[karm][fløy]['bredde']
dørblad_høyde  = karm_hoyde  - DORBLAD_OFFSETS[karm][fløy]['hoyde']
```

### Fra karm til dørblad (Struktur B, med luftspalte)
```
dørblad_bredde = karm_bredde - DORBLAD_OFFSETS[karm][bladtype][fløy]['bredde']
dørblad_høyde  = karm_hoyde  - DORBLAD_OFFSETS[karm][bladtype][fløy]['hoyde_base'] - luftspalte
```

### Terskel
```
terskel_lengde = karm_bredde - TERSKEL_OFFSETS[karm][fløy]
```

### Laminat
```
laminat_bredde = dørblad_bredde - LAMINAT_OFFSETS[karm]       (eller [karm][bladtype])
laminat_høyde  = dørblad_høyde  - LAMINAT_OFFSETS[karm]       (eller [karm][bladtype])
```

### Dekklist (2-fløy)
```
dekklist_lengde = karm_hoyde - 102
```

### 2-fløy bladfordeling
```
blad1_bredde = dørblad_bredde_total × (floyer_split / 100)
blad2_bredde = dørblad_bredde_total - blad1_bredde
```

---

## Referanse — filstier

```
src/
├── doors/
│   ├── __init__.py              # DOOR_REGISTRY
│   ├── innerdor.py              # Innerdør (SDI) — referanseimplementasjon
│   └── <ny_type>.py             # ← DIN NYE DØRTYPE
│
├── models/
│   ├── door.py                  # DoorParams dataclass
│   ├── production_list.py       # Produksjonsliste + komponent-beregninger
│   └── door_list_io.py          # .kdl import/eksport
│
├── utils/
│   ├── constants.py             # Dynamiske oppslags-tabeller
│   ├── calculations.py          # Produksjonsberegninger
│   └── ordretekst.py            # Ordretekst-generering
│
├── gui/
│   ├── main_window.py           # Hovedvindu
│   ├── widgets/
│   │   ├── door_form.py         # Parameterskjema
│   │   ├── door_preview_3d.py   # 3D-viewer (KARM_DEPTHS her)
│   │   ├── door_list_tab.py     # Dørliste-tab
│   │   ├── production_list_tab.py  # Kappliste-tab
│   │   └── detail_tab.py        # Detalj/mål-tab
│   ├── karm_profiles/
│   │   ├── __init__.py          # KARM_PROFILES registrering
│   │   ├── base.py              # KarmProfile baseklasse
│   │   ├── sdi/                 # Innerdør-profiler
│   │   └── <ny_type>/           # ← DINE NYE PROFILER
│   └── styles/
│       └── theme_manager.py     # Tema-håndtering
│
└── export/
    ├── pdf_exporter.py          # PDF-tegning
    ├── pdf_kappeliste.py        # Kappliste PDF
    ├── pdf_title_block.py       # Tittelfelt
    ├── pdf_utils.py             # Hjelpefunksjoner
    ├── pdf_constants.py         # Farger, størrelser
    └── docx_ordretekst.py       # Word ordretekst
```

---

## Vanlige feil

### 1. Manglende offset → `None`-verdier i GUI
**Symptom:** Transport-labels viser "—" eller detaljfanen viser "—".
**Årsak:** En karmtype mangler entry i en offset-tabell.
**Løsning:** Sjekk at ALLE karmtyper har entries i ALLE offset-tabeller i datafilen.

### 2. `KeyError` ved valg av karmtype
**Symptom:** Crash når bruker velger ny karmtype.
**Årsak:** Karmtype-nøkkelen i datafilen matcher ikke nøkkelen i `KARM_PROFILES` eller `KARM_DEPTHS`.
**Løsning:** Sørg for at nøklene er **identiske** i:
- `karm_types` i datafilen
- `KARM_PROFILES` i `karm_profiles/__init__.py`
- `KARM_DEPTHS` i `door_preview_3d.py`

### 3. Feil dorblad_offsets-struktur
**Symptom:** Dørblad-beregning returnerer `None` eller feil verdi.
**Årsak:** Blandet Struktur A og B, eller brukt `'hoyde'` i stedet for `'hoyde_base'`.
**Løsning:**
- Struktur A (flat): bruk `'hoyde'` — luftspalte ignoreres
- Struktur B (nestet per bladtype): bruk `'hoyde_base'` + legg karmtype i `dorblad_hoyde_inkl_luftspalte`

### 4. Terskeltype `None` i transport_height_offsets
**Symptom:** Transport-høyde viser "—" for en terskeltype.
**Årsak:** Terskelverdien er satt til `None` (ugyldig kombinasjon).
**Løsning:** Sett `None` **kun** for terskeltyper som genuint ikke er støttet av den karmtypen. Fjern terskeltypen fra `karm_threshold_types` i stedet.

### 5. 3D-viewer: dørblad "svever" eller overlapper karm
**Symptom:** Visuell feil i 3D-preview.
**Årsak:** `blade_y()` eller `handle_y()` returnerer feil verdi.
**Løsning:** Tegn opp Y-aksen manuelt:
```
Y- (bakside)  ←──  vegg  ──→  Y+ (framside)
                                ↑
                         blade_y + blade_t = handle_y
```

### 6. Ordretekst mangler linjer
**Symptom:** Noen linjer fra `ordretekst['linjer']` utelates.
**Årsak:** `_skal_utelates()` i ordretekst.py filtrerer bort linjer med tomme verdier.
**Løsning:** Sjekk at alle plassholdere har gyldige verdier, eller juster malen.

---

## Oppsummering — minste endringssett

For å legge til en ny dørtype med N karmtyper:

| # | Handling | Fil |
|---|----------|-----|
| 1 | Opprett datafil med alle offsets | `src/doors/<ny_type>.py` |
| 2 | Registrer i _DOOR_TYPE_MODULES | `src/doors/__init__.py` |
| 3 | Opprett N karm-profiler | `src/gui/karm_profiles/<type>/*.py` |
| 4 | Registrer profiler | `src/gui/karm_profiles/__init__.py` |
| 5 | Legg til karmdybder | `src/gui/widgets/door_preview_3d.py` |

**Alt annet fungerer automatisk** via DOOR_REGISTRY → constants.py → resten av applikasjonen.
