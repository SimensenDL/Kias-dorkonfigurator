# Plan: Legg til sammenleggbar "Utregninger"-seksjon i door_form

## Mål

Legge til en sammenleggbar seksjon nederst i door_form som viser beregnede produksjonsmål (dørblad, laminat, terskel). Kun for lesing, oppdateres automatisk når parametere endres.

## Implementasjon

### 1. Oppdater imports i door_form.py

**Fil:** `src/gui/widgets/door_form.py` (linje ~13-26)

Legg til import av beregningsfunksjoner:

```python
from ...utils.calculations import (
    karm_bredde, karm_hoyde,
    dorblad_bredde, dorblad_hoyde,
    terskel_lengde, laminat_mal
)
```

### 2. Opprett "Utregninger" QGroupBox

**Fil:** `src/gui/widgets/door_form.py` (etter linje ~410, før `layout.addStretch()`)

Legg til ny seksjon med:

- `QGroupBox("Utregninger")` med `setCheckable(True)` for sammenlegging
- Read-only `QLabel` widgets for visning:
  - Karmmål (bredde × høyde)
  - Dørbladmål (bredde × høyde)
  - Laminatmål (bredde × høyde)
  - Terskellengde

```python
# Utregninger (sammenleggbar)
self.utregninger_group = QGroupBox("Utregninger")
self.utregninger_group.setCheckable(True)
self.utregninger_group.setChecked(False)  # Lukket som standard
utregninger_layout = QFormLayout(self.utregninger_group)

self.calc_karm_label = QLabel("—")
self.calc_dorblad_label = QLabel("—")
self.calc_laminat_label = QLabel("—")
self.calc_terskel_label = QLabel("—")

utregninger_layout.addRow("Karmmål:", self.calc_karm_label)
utregninger_layout.addRow("Dørbladmål:", self.calc_dorblad_label)
utregninger_layout.addRow("Laminatmål:", self.calc_laminat_label)
utregninger_layout.addRow("Terskel:", self.calc_terskel_label)

layout.addWidget(self.utregninger_group)
```

### 3. Opprett oppdateringsmetode

**Fil:** `src/gui/widgets/door_form.py` (ny metode, f.eks. etter `_update_window_visibility`)

```python
def _update_utregninger_display(self):
    """Oppdaterer beregnede produksjonsmål."""
    karm_type = self.karm_combo.currentData()
    blade_type = self.blade_combo.currentData()
    floyer = self.floyer_combo.currentData() or 1

    # Karmmål
    karm_b = karm_bredde(karm_type, self.width_spin.value())
    karm_h = karm_hoyde(karm_type, self.height_spin.value())
    self.calc_karm_label.setText(f"{karm_b} × {karm_h} mm")

    # Luftspalte (fra terskel)
    luftspalte = self.luftspalte_spin.value()

    # Dørbladmål
    db_b = dorblad_bredde(karm_type, karm_b, floyer, blade_type)
    db_h = dorblad_hoyde(karm_type, karm_h, floyer, blade_type, luftspalte)
    if db_b and db_h:
        self.calc_dorblad_label.setText(f"{db_b} × {db_h} mm")
    else:
        self.calc_dorblad_label.setText("—")

    # Laminatmål
    if db_b and db_h:
        lam_b, lam_h = laminat_mal(karm_type, db_b, db_h, blade_type)
        self.calc_laminat_label.setText(f"{lam_b} × {lam_h} mm")
    else:
        self.calc_laminat_label.setText("—")

    # Terskel
    terskel = terskel_lengde(karm_type, karm_b, floyer)
    if terskel:
        self.calc_terskel_label.setText(f"{terskel} mm")
    else:
        self.calc_terskel_label.setText("—")
```

### 4. Koble til signal-kjeden

**Fil:** `src/gui/widgets/door_form.py`

I `_on_changed()` metoden (rundt linje 498), legg til kall:

```python
def _on_changed(self):
    if not self._block_signals:
        self._update_type_dependent_fields()
        self._update_utregninger_display()  # <-- Legg til
        self.values_changed.emit()
```

### 5. Initial oppdatering

Kall `_update_utregninger_display()` i slutten av `_init_ui()` for å vise initiale verdier.

## Filer som endres

| Fil                            | Endring                                                |
| ------------------------------ | ------------------------------------------------------ |
| `src/gui/widgets/door_form.py` | Legg til import, QGroupBox, labels, oppdateringsmetode |

## Verifisering

1. Kjør `uv run python main.py`
2. Åpne en dør-konfigurasjon
3. Klikk på "Utregninger" for å utvide seksjonen
4. Verifiser at verdiene oppdateres når:
   - Karmtype endres
   - Mål endres
   - Bladtype endres (for SD3/ID)
   - Terskel/luftspalte endres
5. Test spesielt SD3/ID med begge bladtyper (ROCA/SNAPIN) for å verifisere at luftspalte påvirker høyden
