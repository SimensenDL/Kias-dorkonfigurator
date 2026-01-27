# CLAUDE.md

Instruksjoner for Claude Code når det arbeides med dette prosjektet.

## Prosjektoversikt

KIAS Dørkonfigurator er en PyQt6 desktop-applikasjon for å konfigurere dører produsert av Kvanne Industrier AS (KIAS). Brukes av selgere for å sette opp dørspesifikasjoner og generere produksjonsunderlag (PDF-tegninger, kapplister).

**Språk:** Kode-kommentarer og UI-tekst er på norsk. Bruk alltid korrekte norske tegn (æøå) - f.eks. "dør" ikke "dor", "høyde" ikke "hoyde".

## Kommandoer

**Bruk alltid uv.** Prosjektet bruker [uv](https://docs.astral.sh/uv/) for pakkehåndtering. Avhengigheter defineres i `pyproject.toml`.

```bash
# Installer avhengigheter (første gang / etter endringer)
uv sync

# Kjør applikasjonen
uv run python main.py

# Legg til ny avhengighet
uv add <pakkenavn>

# Fjern avhengighet
uv remove <pakkenavn>
```

## Arkitektur

### Dataflyt
`DoorParams` → GUI-skjema → PDF-eksport

### Modulstruktur
- **src/models/** - Datamodeller (`DoorParams` dataclass, prosjektfil save/load)
- **src/gui/** - PyQt6 brukergrensesnitt
  - `main_window.py` - Hovedvindu med menyer, toolbar, tabs
  - **widgets/** - `door_form.py` (parameterskjema med ColorSwatchDelegate)
  - **styles/** - `theme_manager.py` (dark/light tema)
- **src/export/** - PDF-eksport (reportlab)
  - `pdf_exporter.py` - Hovedeksport (`export_door_pdf()`)
  - `pdf_title_block.py` - Tittelfelt med prosjektdata og logo
  - `pdf_utils.py` - Hjelpefunksjoner (skalering, fargekonvertering)
  - `pdf_constants.py` - Farger, sidestørrelser, firmainformasjon
- **src/utils/** - `constants.py` (APP_NAME, DOOR_TYPES, RAL_COLORS, standardmål)

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
