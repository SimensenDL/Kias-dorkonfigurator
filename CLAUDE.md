# CLAUDE.md

Instruksjoner for Claude Code når det arbeides med dette prosjektet.

## Prosjektoversikt

KIAS Dørkonfigurator er en PyQt6 desktop-applikasjon for å konfigurere dører produsert av Kvanne Industrier AS (KIAS). Brukes av selgere for å sette opp dørspesifikasjoner og generere produksjonsunderlag (PDF-tegninger, kapplister).

**Språk:** Kode-kommentarer og UI-tekst er på norsk **bokmål**. Bruk **alltid bokmål, aldri nynorsk**. Bruk alltid korrekte norske tegn (æøå) - f.eks. "dør" ikke "dor", "høyde" ikke "hoyde".

## Kommandoer

**Bruk alltid uv.** Prosjektet bruker [uv](https://docs.astral.sh/uv/) for pakkehåndtering. Avhengigheter defineres i `pyproject.toml`.

```bash
# Installer avhengigheter (første gang / etter endringer)
uv sync

# Kjør applikasjonen
uv run python main.py

# Utviklingsmodus med hot-reloading (anbefalt)
uv run python dev.py

# Legg til ny avhengighet
uv add <pakkenavn>

# Fjern avhengighet
uv remove <pakkenavn>
```

## Arkitektur

### Dataflyt

`DoorParams` → GUI-skjema → PDF-eksport

### Modulstruktur

- **src/doors/** - Dørtype-data som rene dicts (ingen imports). Én fil per dørtype.
  - `__init__.py` - Bygger `DOOR_REGISTRY` fra alle registrerte dørtyper
  - `innerdor.py` - Innerdør (SDI) — mål, karmtyper, hengsler, dorblad-offsets
- **src/models/** - Datamodeller (`DoorParams` dataclass, prosjektfil save/load)
- **src/gui/** - PyQt6 brukergrensesnitt
  - `main_window.py` - Hovedvindu med menyer, toolbar, tabs
  - **widgets/** - `door_form.py` (parameterskjema), `door_preview_3d.py` (3D-viewer)
  - **karm_profiles/** - Karm-geometri for 3D-viewer (én profil per karmtype)
    - `base.py` - `KarmProfile` baseklasse
    - `sdi/` - SD1, SD2, SD3/ID profiler for innerdør
  - **styles/** - `theme_manager.py` (dark/light tema)
- **src/export/** - PDF-eksport (reportlab)
  - `pdf_exporter.py` - Hovedeksport (`export_door_pdf()`)
  - `pdf_title_block.py` - Tittelfelt med prosjektdata og logo
  - `pdf_utils.py` - Hjelpefunksjoner (skalering, fargekonvertering)
  - `pdf_constants.py` - Farger, sidestørrelser, firmainformasjon
- **src/utils/** - `constants.py` (APP_NAME, DOOR_TYPES, RAL_COLORS, standardmål)

### Legge til ny dørtype

1. Opprett datafil i `src/doors/` (som ren dict, se `innerdor.py`)
2. Registrer i `src/doors/__init__.py` (`_DOOR_TYPE_MODULES`)
3. Opprett karm-profiler i `src/gui/karm_profiles/` (arv fra `KarmProfile`)
4. Registrer i `src/gui/karm_profiles/__init__.py` (`KARM_PROFILES`)

### Signal-arkitektur

- `DoorForm.values_changed` → `MainWindow._on_params_changed()` → oppdater dør + tittel

### DoorParams (src/models/door.py)

Dataclass med alle dørparametere: type, mål (mm), farger (RAL), glass, lås, hengsler, brannklasse, lydklasse, U-verdi. Serialiseres til JSON (.kdf-filer).

## Konvensjoner

- **Alle mål i millimeter (mm)**
- Prosjektfiler bruker `.kdf`-format (JSON)
- 10 dørtyper: Innerdør, Kjøleromsdør, Pendeldør, Branndør, Bod-/Garasjedør, Skyvedør, Lyddør, Fjøsdør, Brakkedør, Røntgendør
- Hengsle-side: `'left'` / `'right'`
- Overflatetyper: `'glatt'` / `'struktur'` / `'treverk'`

## Avhengigheter

Se `pyproject.toml` for komplett liste. Hovedavhengigheter:

- PyQt6 (GUI)
- reportlab (PDF-generering)
- openpyxl (Excel-eksport, planlagt)
- qt-material (Material Design tema)
- qtawesome (ikoner)
- pyqtgraph + PyOpenGL + numpy (3D-visualisering)
- svglib (SVG-import)
- jurigged (hot-reloading i utviklingsmodus)
