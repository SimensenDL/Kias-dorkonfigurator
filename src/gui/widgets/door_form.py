"""
Parameterskjema for dørkonfigurasjon.
Viser input-felt for dørtype, mål, farge og tilleggsutstyr.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QLabel, QTextEdit,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from PyQt6.QtGui import QColor, QPen, QIcon, QPixmap, QPainter

from ...utils.constants import (
    DOOR_TYPES, DEFAULT_DIMENSIONS, RAL_COLORS,
    SWING_DIRECTIONS, FIRE_RATINGS, SOUND_RATINGS,
    THRESHOLD_TYPES, THRESHOLD_LUFTSPALTE,
    DOOR_KARM_TYPES, DOOR_FLOYER,
    MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, MAX_HEIGHT, MIN_THICKNESS, MAX_THICKNESS
)
from ...models.door import DoorParams


class ColorSwatchDelegate(QStyledItemDelegate):
    """Custom delegate som tegner fargerute som ikke påvirkes av hover."""

    def paint(self, painter, option, index):
        # Tegn standard bakgrunn (inkl. hover) først
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QStyle.Style()

        # Tegn bakgrunn uten ikon
        option.icon = QIcon()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        # Hent fargekode fra item data
        color_code = index.data(Qt.ItemDataRole.UserRole)
        hex_color = None
        if color_code and color_code in RAL_COLORS:
            hex_color = RAL_COLORS[color_code]['hex']

        if hex_color:
            # Tegn fargerute med fast farge (upåvirket av hover)
            swatch_size = 14
            swatch_x = option.rect.left() + 4
            swatch_y = option.rect.center().y() - swatch_size // 2
            swatch_rect = QRect(swatch_x, swatch_y, swatch_size, swatch_size)

            # Fyll med farge
            painter.fillRect(swatch_rect, QColor(hex_color))

            # Tegn kant rundt fargeruten
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawRect(swatch_rect)


class DoorForm(QWidget):
    """Skjema for dørparametere med signal ved endring."""

    values_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._block_signals = False
        self._init_ui()

    def _init_ui(self):
        """Bygger opp skjemaet."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Prosjektinfo ---
        project_group = QGroupBox("Prosjektinfo")
        project_layout = QFormLayout(project_group)

        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText("F.eks. 2025-001")
        self.project_id_edit.textChanged.connect(self._on_changed)
        project_layout.addRow("Dør-ID:", self.project_id_edit)

        self.customer_edit = QLineEdit()
        self.customer_edit.setPlaceholderText("Kundenavn")
        self.customer_edit.textChanged.connect(self._on_changed)
        project_layout.addRow("Kunde:", self.customer_edit)

        layout.addWidget(project_group)

        # --- Dørtype og mål ---
        door_group = QGroupBox("Dørtype og mål")
        door_layout = QFormLayout(door_group)

        self.door_type_combo = QComboBox()
        for key, name in DOOR_TYPES.items():
            self.door_type_combo.addItem(name, key)
        self.door_type_combo.currentIndexChanged.connect(self._on_type_changed)
        door_layout.addRow("Dørtype:", self.door_type_combo)

        # Karmtype + antall fløyer på samme rad
        karm_floyer_widget = QWidget()
        karm_floyer_layout = QHBoxLayout(karm_floyer_widget)
        karm_floyer_layout.setContentsMargins(0, 0, 0, 0)

        self.karm_combo = QComboBox()
        self.karm_combo.currentIndexChanged.connect(self._on_changed)
        karm_floyer_layout.addWidget(self.karm_combo, stretch=1)

        self.floyer_combo = QComboBox()
        self.floyer_combo.setMinimumWidth(100)
        self.floyer_combo.currentIndexChanged.connect(self._on_changed)
        karm_floyer_layout.addWidget(self.floyer_combo)

        door_layout.addRow("Karmtype:", karm_floyer_widget)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(MIN_WIDTH, MAX_WIDTH)
        self.width_spin.setValue(900)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setSingleStep(50)
        self.width_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Utsparing bredde:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(MIN_HEIGHT, MAX_HEIGHT)
        self.height_spin.setValue(2100)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setSingleStep(50)
        self.height_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Utsparing høyde:", self.height_spin)

        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(MIN_THICKNESS, MAX_THICKNESS)
        self.thickness_spin.setValue(40)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setSingleStep(5)
        self.thickness_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Veggtykkelse:", self.thickness_spin)

        # Terskeltype + luftspalte på samme rad
        threshold_widget = QWidget()
        threshold_layout = QHBoxLayout(threshold_widget)
        threshold_layout.setContentsMargins(0, 0, 0, 0)

        self.threshold_combo = QComboBox()
        for key, name in THRESHOLD_TYPES.items():
            self.threshold_combo.addItem(name, key)
        idx = self.threshold_combo.findData("standard")
        if idx >= 0:
            self.threshold_combo.setCurrentIndex(idx)
        self.threshold_combo.currentIndexChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(self.threshold_combo, stretch=1)

        self.luftspalte_spin = QSpinBox()
        self.luftspalte_spin.setRange(1, 100)
        self.luftspalte_spin.setValue(22)
        self.luftspalte_spin.setSuffix(" mm")
        self.luftspalte_spin.setSingleStep(1)
        self.luftspalte_spin.setReadOnly(True)
        self.luftspalte_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.luftspalte_spin.setMinimumWidth(100)
        self.luftspalte_spin.valueChanged.connect(self._on_changed)
        threshold_layout.addWidget(self.luftspalte_spin)

        door_layout.addRow("Terskel:", threshold_widget)

        layout.addWidget(door_group)

        # --- Utseende ---
        look_group = QGroupBox("Utseende")
        look_layout = QFormLayout(look_group)

        self.color_combo = QComboBox()
        self._populate_color_combo(self.color_combo)
        self.color_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Farge:", self.color_combo)

        self.hinge_combo = QComboBox()
        for key, name in SWING_DIRECTIONS.items():
            self.hinge_combo.addItem(name, key)
        self.hinge_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Slagretning:", self.hinge_combo)

        layout.addWidget(look_group)

        # --- Tillegg ---
        extras_group = QGroupBox("Tillegg")
        extras_layout = QFormLayout(extras_group)

        self.glass_check = QCheckBox("Glass i dør")
        self.glass_check.stateChanged.connect(self._on_changed)
        extras_layout.addRow(self.glass_check)

        self.glass_type_edit = QLineEdit()
        self.glass_type_edit.setPlaceholderText("F.eks. klart, frosted, laminert")
        self.glass_type_edit.textChanged.connect(self._on_changed)
        self.glass_type_label = QLabel("Glasstype:")
        extras_layout.addRow(self.glass_type_label, self.glass_type_edit)

        self.lock_edit = QLineEdit()
        self.lock_edit.setPlaceholderText("F.eks. ABLOY")
        self.lock_edit.textChanged.connect(self._on_changed)
        extras_layout.addRow("Låstype:", self.lock_edit)

        layout.addWidget(extras_group)

        # --- Spesielle egenskaper (avhengig av dørtype) ---
        self.special_group = QGroupBox("Spesielle egenskaper")
        special_layout = QFormLayout(self.special_group)

        self.fire_rating_combo = QComboBox()
        for rating in FIRE_RATINGS:
            self.fire_rating_combo.addItem(rating or "(ingen)", rating)
        self.fire_rating_combo.currentIndexChanged.connect(self._on_changed)
        self.fire_rating_label = QLabel("Brannklasse:")
        special_layout.addRow(self.fire_rating_label, self.fire_rating_combo)

        self.sound_rating_combo = QComboBox()
        for db in SOUND_RATINGS:
            self.sound_rating_combo.addItem(f"{db} dB" if db else "(ingen)", db)
        self.sound_rating_combo.currentIndexChanged.connect(self._on_changed)
        self.sound_rating_label = QLabel("Lydklasse:")
        special_layout.addRow(self.sound_rating_label, self.sound_rating_combo)

        self.insulation_spin = QSpinBox()
        self.insulation_spin.setRange(0, 100)
        self.insulation_spin.setSuffix(" W/m²K")
        self.insulation_spin.valueChanged.connect(self._on_changed)
        self.insulation_label = QLabel("U-verdi:")
        special_layout.addRow(self.insulation_label, self.insulation_spin)

        layout.addWidget(self.special_group)

        # --- Merknader ---
        notes_group = QGroupBox("Merknader")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Valgfrie merknader...")
        self.notes_edit.textChanged.connect(self._on_changed)
        notes_layout.addWidget(self.notes_edit)
        layout.addWidget(notes_group)

        layout.addStretch()

        # Fyll karmtype og fløyer for standard dørtype
        initial_type = self.door_type_combo.currentData()
        for karm in DOOR_KARM_TYPES.get(initial_type, []):
            self.karm_combo.addItem(karm, karm)
        for f in DOOR_FLOYER.get(initial_type, [1]):
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)

        # Initial visning av typeavhengige felt
        self._update_type_dependent_fields()

    def _populate_color_combo(self, combo: QComboBox):
        """Fyller en farge-combobox med RAL-farger og fargeruter."""
        delegate = ColorSwatchDelegate(combo)
        combo.setItemDelegate(delegate)

        for code, info in RAL_COLORS.items():
            # Lag fargeikon for visning i lukket combobox
            pixmap = QPixmap(14, 14)
            pixmap.fill(QColor(info['hex']))
            p = QPainter(pixmap)
            p.setPen(QPen(QColor(80, 80, 80), 1))
            p.drawRect(0, 0, 13, 13)
            p.end()
            icon = QIcon(pixmap)

            display_text = f"      {code} - {info['name']}"
            combo.addItem(icon, display_text, code)

    def _on_changed(self):
        """Sender signal når verdier endres."""
        if not self._block_signals:
            self._update_type_dependent_fields()
            self.values_changed.emit()

    def _on_threshold_changed(self):
        """Håndterer endring av terskeltype - oppdaterer luftspalte."""
        if self._block_signals:
            return

        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'luftspalte')
        luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 22)

        self.luftspalte_spin.setReadOnly(not is_luftspalte)
        self.luftspalte_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if is_luftspalte
            else QSpinBox.ButtonSymbols.NoButtons
        )
        self._block_signals = True
        self.luftspalte_spin.setValue(luftspalte_value)
        self._block_signals = False

        self._on_changed()

    def _on_type_changed(self):
        """Håndterer endring av dørtype - setter standardmål, karmtyper og fløyer."""
        if self._block_signals:
            return

        door_type = self.door_type_combo.currentData()
        defaults = DEFAULT_DIMENSIONS.get(door_type, {})

        self._block_signals = True
        if defaults:
            self.width_spin.setValue(defaults['width'])
            self.height_spin.setValue(defaults['height'])
            self.thickness_spin.setValue(defaults['thickness'])

        # Oppdater karmtype-valg
        self.karm_combo.clear()
        karm_types = DOOR_KARM_TYPES.get(door_type, [])
        for karm in karm_types:
            self.karm_combo.addItem(karm, karm)

        # Oppdater fløyer-valg
        self.floyer_combo.clear()
        floyer_options = DOOR_FLOYER.get(door_type, [1])
        for f in floyer_options:
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)

        self._block_signals = False

        self._update_type_dependent_fields()
        self.values_changed.emit()

    def _update_type_dependent_fields(self):
        """Viser/skjuler felt basert på valgt dørtype."""
        door_type = self.door_type_combo.currentData()

        # Glass-felt synlighet
        has_glass = self.glass_check.isChecked()
        self.glass_type_label.setVisible(has_glass)
        self.glass_type_edit.setVisible(has_glass)

        # Spesielle egenskaper synlighet
        is_fire = door_type == 'BD'
        is_sound = False  # Ingen dedikert lyddør-type lenger
        is_cold = door_type == 'KD'

        self.fire_rating_label.setVisible(is_fire)
        self.fire_rating_combo.setVisible(is_fire)
        self.sound_rating_label.setVisible(is_sound)
        self.sound_rating_combo.setVisible(is_sound)
        self.insulation_label.setVisible(is_cold)
        self.insulation_spin.setVisible(is_cold)

        # Vis/skjul hele spesialgruppen
        self.special_group.setVisible(is_fire or is_sound or is_cold)

        # Terskel/luftspalte aktivering
        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'luftspalte')
        self.luftspalte_spin.setReadOnly(not is_luftspalte)
        self.luftspalte_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if is_luftspalte
            else QSpinBox.ButtonSymbols.NoButtons
        )
        if not is_luftspalte:
            luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 22)
            self.luftspalte_spin.setValue(luftspalte_value)

    def update_door(self, door: DoorParams) -> None:
        """Oppdaterer DoorParams med verdier fra skjemaet."""
        door.project_id = self.project_id_edit.text()
        door.customer = self.customer_edit.text()
        door.door_type = self.door_type_combo.currentData() or "SDI"
        door.karm_type = self.karm_combo.currentData() or ""
        door.floyer = self.floyer_combo.currentData() or 1
        door.width = self.width_spin.value()
        door.height = self.height_spin.value()
        door.thickness = self.thickness_spin.value()
        door.color = self.color_combo.currentData() or ""
        door.swing_direction = self.hinge_combo.currentData() or "left"
        door.glass = self.glass_check.isChecked()
        door.glass_type = self.glass_type_edit.text()
        door.lock_type = self.lock_edit.text()
        door.threshold_type = self.threshold_combo.currentData() or "standard"
        if door.threshold_type == 'luftspalte':
            door.luftspalte = self.luftspalte_spin.value()
        else:
            door.luftspalte = THRESHOLD_LUFTSPALTE.get(door.threshold_type, 22)
        door.fire_rating = self.fire_rating_combo.currentData() or ""
        door.sound_rating = self.sound_rating_combo.currentData() or 0
        door.insulation_value = float(self.insulation_spin.value())
        door.notes = self.notes_edit.toPlainText()

    def load_door(self, door: DoorParams) -> None:
        """Laster DoorParams-verdier inn i skjemaet."""
        self._block_signals = True

        self.project_id_edit.setText(door.project_id)
        self.customer_edit.setText(door.customer)

        # Dørtype
        idx = self.door_type_combo.findData(door.door_type)
        if idx >= 0:
            self.door_type_combo.setCurrentIndex(idx)

        # Oppdater karmtype- og fløyer-valg for denne dørtypen
        door_type = door.door_type
        self.karm_combo.clear()
        for karm in DOOR_KARM_TYPES.get(door_type, []):
            self.karm_combo.addItem(karm, karm)
        idx = self.karm_combo.findData(door.karm_type)
        if idx >= 0:
            self.karm_combo.setCurrentIndex(idx)

        self.floyer_combo.clear()
        for f in DOOR_FLOYER.get(door_type, [1]):
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)
        idx = self.floyer_combo.findData(door.floyer)
        if idx >= 0:
            self.floyer_combo.setCurrentIndex(idx)

        self.width_spin.setValue(door.width)
        self.height_spin.setValue(door.height)
        self.thickness_spin.setValue(door.thickness)

        # Farge
        idx = self.color_combo.findData(door.color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)

        # Slagretning
        idx = self.hinge_combo.findData(door.swing_direction)
        if idx >= 0:
            self.hinge_combo.setCurrentIndex(idx)

        # Tillegg
        self.glass_check.setChecked(door.glass)
        self.glass_type_edit.setText(door.glass_type)
        self.lock_edit.setText(door.lock_type)
        # Terskeltype
        idx = self.threshold_combo.findData(door.threshold_type)
        if idx >= 0:
            self.threshold_combo.setCurrentIndex(idx)
        # Luftspalte (kun relevant for 'luftspalte'-typen)
        if door.threshold_type == 'luftspalte':
            self.luftspalte_spin.setValue(door.luftspalte)

        # Spesielle
        idx = self.fire_rating_combo.findData(door.fire_rating)
        if idx >= 0:
            self.fire_rating_combo.setCurrentIndex(idx)
        idx = self.sound_rating_combo.findData(door.sound_rating)
        if idx >= 0:
            self.sound_rating_combo.setCurrentIndex(idx)
        self.insulation_spin.setValue(int(door.insulation_value))

        # Merknader
        self.notes_edit.setPlainText(door.notes)

        self._block_signals = False
        self._update_type_dependent_fields()
