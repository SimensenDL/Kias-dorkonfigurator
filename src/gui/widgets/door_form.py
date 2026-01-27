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
from PyQt6.QtGui import QColor, QPen, QIcon

from ...utils.constants import (
    DOOR_TYPES, DEFAULT_DIMENSIONS, RAL_COLORS,
    HINGE_SIDES, SURFACE_TYPES, FIRE_RATINGS, SOUND_RATINGS,
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
        project_layout.addRow("Prosjekt-ID:", self.project_id_edit)

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

        self.width_spin = QSpinBox()
        self.width_spin.setRange(MIN_WIDTH, MAX_WIDTH)
        self.width_spin.setValue(900)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setSingleStep(50)
        self.width_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Bredde:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(MIN_HEIGHT, MAX_HEIGHT)
        self.height_spin.setValue(2100)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setSingleStep(50)
        self.height_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Høyde:", self.height_spin)

        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(MIN_THICKNESS, MAX_THICKNESS)
        self.thickness_spin.setValue(40)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setSingleStep(5)
        self.thickness_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Tykkelse:", self.thickness_spin)

        layout.addWidget(door_group)

        # --- Utseende ---
        look_group = QGroupBox("Utseende")
        look_layout = QFormLayout(look_group)

        self.color_outside_combo = QComboBox()
        self._populate_color_combo(self.color_outside_combo)
        self.color_outside_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Farge utside:", self.color_outside_combo)

        self.color_inside_combo = QComboBox()
        self._populate_color_combo(self.color_inside_combo)
        self.color_inside_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Farge innside:", self.color_inside_combo)

        self.surface_combo = QComboBox()
        for key, name in SURFACE_TYPES.items():
            self.surface_combo.addItem(name, key)
        self.surface_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Overflate:", self.surface_combo)

        self.hinge_combo = QComboBox()
        for key, name in HINGE_SIDES.items():
            self.hinge_combo.addItem(name, key)
        self.hinge_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Hengsle-side:", self.hinge_combo)

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

        self.threshold_edit = QLineEdit()
        self.threshold_edit.setPlaceholderText("F.eks. flat, hevet")
        self.threshold_edit.textChanged.connect(self._on_changed)
        extras_layout.addRow("Terskel:", self.threshold_edit)

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

        # Initial visning av typeavhengige felt
        self._update_type_dependent_fields()

    def _populate_color_combo(self, combo: QComboBox):
        """Fyller en farge-combobox med RAL-farger og fargeruter."""
        delegate = ColorSwatchDelegate(combo)
        combo.setItemDelegate(delegate)

        for code, info in RAL_COLORS.items():
            # Tekst med padding for fargeruten
            display_text = f"      {code} - {info['name']}"
            combo.addItem(display_text, code)

    def _on_changed(self):
        """Sender signal når verdier endres."""
        if not self._block_signals:
            self._update_type_dependent_fields()
            self.values_changed.emit()

    def _on_type_changed(self):
        """Håndterer endring av dørtype - setter standardmål."""
        if self._block_signals:
            return

        door_type = self.door_type_combo.currentData()
        defaults = DEFAULT_DIMENSIONS.get(door_type, {})

        self._block_signals = True
        if defaults:
            self.width_spin.setValue(defaults['width'])
            self.height_spin.setValue(defaults['height'])
            self.thickness_spin.setValue(defaults['thickness'])
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
        is_fire = door_type == 'branndor'
        is_sound = door_type == 'lyddor'
        is_cold = door_type == 'kjoleromsdor'

        self.fire_rating_label.setVisible(is_fire)
        self.fire_rating_combo.setVisible(is_fire)
        self.sound_rating_label.setVisible(is_sound)
        self.sound_rating_combo.setVisible(is_sound)
        self.insulation_label.setVisible(is_cold)
        self.insulation_spin.setVisible(is_cold)

        # Vis/skjul hele spesialgruppen
        self.special_group.setVisible(is_fire or is_sound or is_cold)

    def update_door(self, door: DoorParams) -> None:
        """Oppdaterer DoorParams med verdier fra skjemaet."""
        door.project_id = self.project_id_edit.text()
        door.customer = self.customer_edit.text()
        door.door_type = self.door_type_combo.currentData() or "innerdor"
        door.width = self.width_spin.value()
        door.height = self.height_spin.value()
        door.thickness = self.thickness_spin.value()
        door.color_outside = self.color_outside_combo.currentData() or ""
        door.color_inside = self.color_inside_combo.currentData() or ""
        door.surface_type = self.surface_combo.currentData() or "glatt"
        door.hinge_side = self.hinge_combo.currentData() or "left"
        door.glass = self.glass_check.isChecked()
        door.glass_type = self.glass_type_edit.text()
        door.lock_type = self.lock_edit.text()
        door.threshold_type = self.threshold_edit.text()
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

        self.width_spin.setValue(door.width)
        self.height_spin.setValue(door.height)
        self.thickness_spin.setValue(door.thickness)

        # Farger
        idx = self.color_outside_combo.findData(door.color_outside)
        if idx >= 0:
            self.color_outside_combo.setCurrentIndex(idx)
        idx = self.color_inside_combo.findData(door.color_inside)
        if idx >= 0:
            self.color_inside_combo.setCurrentIndex(idx)

        # Overflate
        idx = self.surface_combo.findData(door.surface_type)
        if idx >= 0:
            self.surface_combo.setCurrentIndex(idx)

        # Hengsle
        idx = self.hinge_combo.findData(door.hinge_side)
        if idx >= 0:
            self.hinge_combo.setCurrentIndex(idx)

        # Tillegg
        self.glass_check.setChecked(door.glass)
        self.glass_type_edit.setText(door.glass_type)
        self.lock_edit.setText(door.lock_type)
        self.threshold_edit.setText(door.threshold_type)

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
