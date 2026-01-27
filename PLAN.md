# KIAS Dørkonfigurator - Prosjektplan

## Oversikt
PyQt6 desktop-app for å konfigurere KIAS-dører (Kvanne Industrier AS). Brukes av selgere for å konfigurere dører og generere produksjonsunderlag (PDF-tegninger, kapplister).

**Dørtyper:** Innerdør, Kjøleromsdør, Pendeldør, Branndør, Bod-/Garasjedør, Skyvedør, Lyddør, Fjøsdør, Brakkedør, Røntgendør

**Output:** 3D-visualisering, PDF-tegninger med mål, kapplister/komponentlister

**Tech stack:** PyQt6, reportlab (PDF), openpyxl (Excel), qt-material, qtawesome

**Kjøring:** `python main.py` (med aktivert venv)

---

## Status: Fase 1 & 2 FERDIG

### Implementert filstruktur
```
kias-dørkonfigurator/
├── main.py                              # Inngangspunkt → run_app()
├── requirements.txt                     # PyQt6, reportlab, openpyxl, qt-material, qtawesome
├── PLAN.md                              # Denne filen
├── CLAUDE.md                            # Claude Code prosjektinstruksjoner
├── .gitignore                           # Git ignore-regler
├── assets/
│   └── KIAS-dorer-logo.svg             # KIAS-logo (SVG)
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── door.py                      # DoorParams dataclass
│   │   └── project.py                   # Save/load .kdf filer (JSON)
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py               # MainWindow med menyer, toolbar, tabs
│   │   ├── styles/
│   │   │   ├── __init__.py              # Eksporterer ThemeManager, Theme
│   │   │   └── theme_manager.py         # Dark/light tema (QSettings: KIASDorkonfigurator)
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── door_form.py             # Parameterskjema + ColorSwatchDelegate
│   │       └── door_preview_3d.py       # 3D-forhåndsvisning (pyqtgraph/OpenGL)
│   ├── export/
│   │   ├── __init__.py
│   │   ├── pdf_exporter.py              # export_door_pdf() - frontvisning med mål
│   │   ├── pdf_utils.py                 # ral_to_color(), mm_to_scaled(), calculate_scale()
│   │   ├── pdf_constants.py             # Sidestørrelser (A3), firma: KVANNE INDUSTRIER AS
│   │   └── pdf_title_block.py           # Profesjonelt tittelfelt med prosjektdata
│   └── utils/
│       ├── __init__.py
│       └── constants.py                 # APP_NAME, DOOR_TYPES, RAL_COLORS, standardmål
```

### Implementerte features
- **GUI:** MainWindow med splitter (venstre: scrollbart skjema, høyre: tabs)
- **Menyer:** Fil (Nytt/Åpne/Lagre/Lagre som/Avslutt), Eksporter (PDF), Innstillinger (Tema), Hjelp (Om)
- **Toolbar:** Nytt, Åpne, Lagre, Eksporter PDF
- **DoorForm:** Parameterskjema med:
  - Prosjektinfo (ID, kunde)
  - Dørtype-dropdown (10 typer) - endrer standardmål automatisk
  - Mål (bredde/høyde/tykkelse med SpinBox)
  - Utseende (farge utside/innside med ColorSwatchDelegate fargeruter, overflate, hengsle-side)
  - Tillegg (glass, glasstype, lås, terskel)
  - Typeavhengige felt (brannklasse for branndør, lydklasse for lyddør, U-verdi for kjøleromsdør)
  - Merknader (fritekst)
- **ColorSwatchDelegate:** Fargede RAL-fargeruter i dropdown (14x14 px swatch)
- **Prosjektfiler:** .kdf format (JSON), save/load med versjonering
- **PDF-eksport:** A3 liggende med frontvisning av dør, karm, glass, håndtak, hengsler, mål-linjer, tittelfelt
- **Tema:** Dark/light mode med qt-material
- **Unsaved changes tracking:** Stjerne i tittel, bekreftelse ved lukking

### DoorParams dataclass (`src/models/door.py`)
```python
@dataclass
class DoorParams:
    project_id: str          # Prosjekt-ID / ordrenummer
    customer: str            # Kundenavn
    door_type: str           # Nøkkel fra DOOR_TYPES (10 typer)
    width: int               # mm (default 900, range 500-3000)
    height: int              # mm (default 2100, range 1500-3500)
    thickness: int           # mm (default 40, range 20-200)
    color_outside: str       # RAL-kode (default RAL 9010)
    color_inside: str        # RAL-kode
    surface_type: str        # glatt/struktur/treverk
    glass: bool              # Har glass
    glass_type: str          # Glasstype
    threshold_type: str      # Terskeltype
    lock_type: str           # Låstype
    hinge_side: str          # left/right
    fire_rating: str         # EI30/EI60/EI90/EI120 (branndør)
    sound_rating: int        # dB (lyddør)
    insulation_value: float  # U-verdi W/m²K (kjøleromsdør)
    notes: str               # Fritekst merknader
    created_date: str        # ISO-format
    modified_date: str       # ISO-format
```
Metoder: `to_dict()`, `from_dict()`, `apply_defaults_for_type()`, `area_m2()`

### Signal-arkitektur
- `DoorForm.values_changed` → `MainWindow._on_params_changed()` → oppdater door + tittel

---

## Status: Fase 2 FERDIG

### Fase 2: 3D-visualisering
- [x] Interaktiv 3D-visning med pyqtgraph/OpenGL (`src/gui/widgets/door_preview_3d.py`)
- [x] Dørblad med utside/innside RAL-farge (per-face-farger)
- [x] Karm (omvendt U-form: venstre stolpe, høyre stolpe, toppstykke)
- [x] Glasspanel (semi-transparent, vises kun når glass=True)
- [x] Håndtak (plassert motsatt side av hengsler)
- [x] 3 hengsler (15%, 50%, 85% av dørhøyden)
- [x] Rotérbar/zoombar/pannerbar visning med mus
- [x] Sanntidsoppdatering ved parameterendringer
- [x] Auto-justert kameraavstand etter dørstørrelse
- [x] Fallback-tekst hvis pyqtgraph/OpenGL mangler
- [x] Nye avhengigheter: pyqtgraph, PyOpenGL, numpy

## Fase 3: Avanserte PDF-tegninger (TODO)
- Sidevisning og snitt i tillegg til frontvisning
- Detaljtegninger med beslag/hengsler
- Flere sider i PDF (frontvisning, sidevisning, snitt)

## Fase 4: Produksjonsunderlag (TODO)
- Kappliste (cut list) per komponent
- Excel-eksport med stykkliste/BOM
- Prisberegning
- Erstatter placeholder i "Detaljer"-tab

## Fase 5: Build & distribusjon (TODO)
- PyInstaller `.spec` fil
- Inno Setup `.iss` installer
- `build_installer.bat`
- Filassosiasjon for `.kdf`-filer

---

## Klargjort for eget repo

Følgende er gjort for å forberede flytting til eget prosjekt:
- [x] `.gitignore` opprettet
- [x] `CLAUDE.md` opprettet med prosjektinstruksjoner
- [x] KIAS-logo lagt til i `assets/` (SVG-format)
- [x] Opprydding: `nul`-fil og `__pycache__`-mapper slettet
- [x] Logo-sti oppdatert i `pdf_constants.py`

### Gjenstående ved flytting
1. Opprett eget venv: `python -m venv venv && venv\Scripts\pip install -r requirements.txt`
2. `git init` og første commit
3. Vurder å konvertere `KIAS-dorer-logo.svg` til PNG for PDF-eksport (reportlab støtter ikke SVG direkte)
