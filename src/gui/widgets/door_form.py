"""
Parameterskjema for dørkonfigurasjon.
Viser input-felt for dørtype, mål, farge, beslag og tilleggsutstyr.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QLabel,
    QStyledItemDelegate, QStyle, QDoubleSpinBox, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from PyQt6.QtGui import QColor, QPen, QIcon, QPixmap, QPainter

from ...utils.constants import (
    DOOR_TYPES, DEFAULT_DIMENSIONS, RAL_COLORS,
    SWING_DIRECTIONS, FIRE_RATINGS, SOUND_RATINGS,
    THRESHOLD_TYPES, THRESHOLD_LUFTSPALTE, THRESHOLD_HEIGHT,
    DOOR_KARM_TYPES, DOOR_FLOYER, KARM_THRESHOLD_TYPES,
    DOOR_BLADE_TYPES, KARM_BLADE_TYPES, DOOR_TYPE_BLADE_OVERRIDE,
    MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, MAX_HEIGHT, MIN_THICKNESS, MAX_THICKNESS,
    DOOR_U_VALUES, BRUTT_KULDEBRO_KARM, BRUTT_KULDEBRO_DORRAMME,
    DIMENSION_DIFFERENTIALS,
    SURFACE_TYPES, WINDOW_PROFILES,
    WINDOW_MIN_MARGIN, MIN_WINDOW_SIZE, MAX_WINDOW_SIZE, MAX_WINDOW_OFFSET,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    UTFORING_RANGES, KARM_HAS_UTFORING, UTFORING_MAX_THICKNESS
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

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Valgfrie merknader...")
        self.notes_edit.textChanged.connect(self._on_changed)
        project_layout.addRow("Merknad:", self.notes_edit)

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
        self.karm_combo.currentIndexChanged.connect(self._on_karm_changed)
        karm_floyer_layout.addWidget(self.karm_combo, stretch=1)

        self.floyer_combo = QComboBox()
        self.floyer_combo.setMinimumWidth(100)
        self.floyer_combo.currentIndexChanged.connect(self._on_floyer_changed)
        karm_floyer_layout.addWidget(self.floyer_combo)

        door_layout.addRow("Karmtype:", karm_floyer_widget)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(MIN_WIDTH, MAX_WIDTH)
        self.width_spin.setValue(1010)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setSingleStep(50)
        self.width_spin.valueChanged.connect(self._on_dimension_changed)
        door_layout.addRow("Utsparing bredde (BM):", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(MIN_HEIGHT, MAX_HEIGHT)
        self.height_spin.setValue(2110)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setSingleStep(50)
        self.height_spin.valueChanged.connect(self._on_dimension_changed)
        door_layout.addRow("Utsparing høyde (HM):", self.height_spin)

        # Transportmål (beregnet, readonly) - B90°, B180°, H
        transport_widget = QWidget()
        transport_layout = QHBoxLayout(transport_widget)
        transport_layout.setContentsMargins(0, 0, 0, 0)

        self.transport_width_90_label = QLabel("—")
        self.transport_width_180_label = QLabel("—")
        self.transport_height_label = QLabel("—")
        transport_layout.addWidget(QLabel("B90°:"))
        transport_layout.addWidget(self.transport_width_90_label)
        transport_layout.addWidget(QLabel("  B180°:"))
        transport_layout.addWidget(self.transport_width_180_label)
        transport_layout.addWidget(QLabel("  H:"))
        transport_layout.addWidget(self.transport_height_label)
        transport_layout.addStretch()

        door_layout.addRow("Transportmål:", transport_widget)

        # Veggtykkelse + utforing på samme rad
        thickness_widget = QWidget()
        thickness_layout = QHBoxLayout(thickness_widget)
        thickness_layout.setContentsMargins(0, 0, 0, 0)

        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(MIN_THICKNESS, MAX_THICKNESS)
        self.thickness_spin.setValue(100)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setSingleStep(5)
        self.thickness_spin.setMaximumWidth(100)
        self.thickness_spin.valueChanged.connect(self._on_thickness_changed)
        thickness_layout.addWidget(self.thickness_spin)

        self.utforing_label = QLabel("Utforing:")
        thickness_layout.addWidget(self.utforing_label)

        self.utforing_combo = QComboBox()
        self.utforing_combo.setMinimumWidth(110)
        self.utforing_combo.currentIndexChanged.connect(self._on_changed)
        thickness_layout.addWidget(self.utforing_combo, stretch=1)

        door_layout.addRow("Veggtykkelse:", thickness_widget)

        # Dørblad + tykkelse på samme rad
        blade_widget = QWidget()
        blade_layout = QHBoxLayout(blade_widget)
        blade_layout.setContentsMargins(0, 0, 0, 0)

        self.blade_combo = QComboBox()
        self.blade_combo.currentIndexChanged.connect(self._on_blade_changed)
        blade_layout.addWidget(self.blade_combo, stretch=1)

        self.blade_thickness_spin = QSpinBox()
        self.blade_thickness_spin.setSuffix(" mm")
        self.blade_thickness_spin.setMinimumWidth(100)
        self.blade_thickness_spin.setReadOnly(True)
        self.blade_thickness_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.blade_thickness_spin.valueChanged.connect(self._on_changed)
        blade_layout.addWidget(self.blade_thickness_spin)

        door_layout.addRow("Dørblad:", blade_widget)

        # Terskeltype + luftspalte på samme rad
        threshold_widget = QWidget()
        threshold_layout = QHBoxLayout(threshold_widget)
        threshold_layout.setContentsMargins(0, 0, 0, 0)

        self.threshold_combo = QComboBox()
        self.threshold_combo.currentIndexChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(self.threshold_combo, stretch=1)

        self.luftspalte_spin = QSpinBox()
        self.luftspalte_spin.setRange(0, 100)
        self.luftspalte_spin.setValue(0)
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
        self.color_combo.currentIndexChanged.connect(self._on_blade_color_changed)
        look_layout.addRow("Dørblad farge:", self.color_combo)

        self.karm_color_combo = QComboBox()
        self._populate_color_combo(self.karm_color_combo)
        self.karm_color_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Karmfarge:", self.karm_color_combo)

        self.hinge_combo = QComboBox()
        for key, name in SWING_DIRECTIONS.items():
            self.hinge_combo.addItem(name, key)
        self.hinge_combo.currentIndexChanged.connect(self._on_changed)
        look_layout.addRow("Slagretning:", self.hinge_combo)

        layout.addWidget(look_group)

        # --- Vindu ---
        window_group = QGroupBox("Vindu")
        window_layout = QFormLayout(window_group)

        self.window_check = QCheckBox("Vindu i dør")
        self.window_check.stateChanged.connect(self._on_window_changed)
        window_layout.addRow(self.window_check)

        # Vindusprofil
        self.window_profile_combo = QComboBox()
        for key, profile in WINDOW_PROFILES.items():
            self.window_profile_combo.addItem(profile['name'], key)
        self.window_profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        self.window_profile_label = QLabel("Profil:")
        window_layout.addRow(self.window_profile_label, self.window_profile_combo)

        # Utsparing (mm)
        window_layout.addRow(QLabel("Utsparing (mm):"))

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(MIN_WINDOW_SIZE, MAX_WINDOW_SIZE)
        self.window_width_spin.setValue(DEFAULT_WINDOW_WIDTH)
        self.window_width_spin.setSuffix(" mm")
        self.window_width_spin.setSingleStep(10)
        self.window_width_spin.valueChanged.connect(self._on_window_size_changed)
        self.window_width_label = QLabel("Bredde:")
        window_layout.addRow(self.window_width_label, self.window_width_spin)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(MIN_WINDOW_SIZE, MAX_WINDOW_SIZE)
        self.window_height_spin.setValue(DEFAULT_WINDOW_HEIGHT)
        self.window_height_spin.setSuffix(" mm")
        self.window_height_spin.setSingleStep(10)
        self.window_height_spin.valueChanged.connect(self._on_window_size_changed)
        self.window_height_label = QLabel("Høyde:")
        window_layout.addRow(self.window_height_label, self.window_height_spin)

        # Beregnet (glasmål og lysåpning)
        self.glass_dims_label = QLabel("Glasmål:")
        self.glass_dims_value = QLabel("— × — mm")
        window_layout.addRow(self.glass_dims_label, self.glass_dims_value)

        self.light_dims_label = QLabel("Lysåpning:")
        self.light_dims_value = QLabel("— × — mm")
        window_layout.addRow(self.light_dims_label, self.light_dims_value)

        # Plassering
        window_layout.addRow(QLabel("Plassering:"))

        # Horisontal (X)
        x_widget = QWidget()
        x_layout = QHBoxLayout(x_widget)
        x_layout.setContentsMargins(0, 0, 0, 0)
        self.window_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_x_slider.setRange(-MAX_WINDOW_OFFSET, MAX_WINDOW_OFFSET)
        self.window_x_slider.setValue(0)
        self.window_x_slider.valueChanged.connect(self._on_window_x_slider_changed)
        x_layout.addWidget(self.window_x_slider, stretch=1)
        self.window_x_spin = QSpinBox()
        self.window_x_spin.setRange(-MAX_WINDOW_OFFSET, MAX_WINDOW_OFFSET)
        self.window_x_spin.setValue(0)
        self.window_x_spin.setSuffix(" mm")
        self.window_x_spin.setMinimumWidth(90)
        self.window_x_spin.valueChanged.connect(self._on_window_x_spin_changed)
        x_layout.addWidget(self.window_x_spin)
        self.window_x_label = QLabel("Horisontal (X):")
        window_layout.addRow(self.window_x_label, x_widget)

        # Vertikal (Y)
        y_widget = QWidget()
        y_layout = QHBoxLayout(y_widget)
        y_layout.setContentsMargins(0, 0, 0, 0)
        self.window_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_y_slider.setRange(-MAX_WINDOW_OFFSET, MAX_WINDOW_OFFSET)
        self.window_y_slider.setValue(0)
        self.window_y_slider.valueChanged.connect(self._on_window_y_slider_changed)
        y_layout.addWidget(self.window_y_slider, stretch=1)
        self.window_y_spin = QSpinBox()
        self.window_y_spin.setRange(-MAX_WINDOW_OFFSET, MAX_WINDOW_OFFSET)
        self.window_y_spin.setValue(0)
        self.window_y_spin.setSuffix(" mm")
        self.window_y_spin.setMinimumWidth(90)
        self.window_y_spin.valueChanged.connect(self._on_window_y_spin_changed)
        y_layout.addWidget(self.window_y_spin)
        self.window_y_label = QLabel("Vertikal (Y):")
        window_layout.addRow(self.window_y_label, y_widget)

        # Advarsel for margin
        self.window_warning_label = QLabel("")
        self.window_warning_label.setStyleSheet("color: #cc3333; font-weight: bold;")
        self.window_warning_label.setWordWrap(True)
        window_layout.addRow(self.window_warning_label)

        layout.addWidget(window_group)

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
            self.sound_rating_combo.addItem(f"Rw{db} dB" if db else "(ingen)", db)
        self.sound_rating_combo.currentIndexChanged.connect(self._on_changed)
        self.sound_rating_label = QLabel("Lydklasse:")
        special_layout.addRow(self.sound_rating_label, self.sound_rating_combo)

        # U-verdi (readonly, automatisk fra dørtype)
        self.insulation_spin = QDoubleSpinBox()
        self.insulation_spin.setRange(0.0, 10.0)
        self.insulation_spin.setDecimals(2)
        self.insulation_spin.setSuffix(" W/m²K")
        self.insulation_spin.setReadOnly(True)
        self.insulation_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.insulation_label = QLabel("U-verdi:")
        special_layout.addRow(self.insulation_label, self.insulation_spin)

        # Brutt kuldebro indikator (readonly)
        self.kuldebro_label = QLabel("Brutt kuldebro:")
        self.kuldebro_value = QLabel("Nei")
        special_layout.addRow(self.kuldebro_label, self.kuldebro_value)

        layout.addWidget(self.special_group)

        layout.addStretch()

        # Fyll karmtype, fløyer og dørbladtykkelse for standard dørtype
        initial_type = self.door_type_combo.currentData()
        for karm in DOOR_KARM_TYPES.get(initial_type, []):
            self.karm_combo.addItem(karm, karm)
        for f in DOOR_FLOYER.get(initial_type, [1]):
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)
        self._update_blade_for_karm()
        self._update_threshold_for_karm()
        self._update_utforing_options()

        # Sett standardmål fra DEFAULT_DIMENSIONS for initial dørtype
        initial_defaults = DEFAULT_DIMENSIONS.get(initial_type, {})
        if initial_defaults:
            self.width_spin.setValue(initial_defaults['width'])
            self.height_spin.setValue(initial_defaults['height'])
            self.thickness_spin.setValue(initial_defaults['thickness'])

        # Sett U-verdi for initial dørtype
        self.insulation_spin.setValue(DOOR_U_VALUES.get(initial_type, 0.0))

        # Initial visning av typeavhengige felt
        self._update_type_dependent_fields()
        self._update_transport_labels()

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

    def _update_threshold_for_karm(self):
        """Oppdaterer terskel-dropdown med tillatte typer for valgt karmtype."""
        karm_type = self.karm_combo.currentData()
        allowed = KARM_THRESHOLD_TYPES.get(karm_type, list(THRESHOLD_TYPES.keys()))

        old_threshold = self.threshold_combo.currentData()
        self.threshold_combo.blockSignals(True)
        self.threshold_combo.clear()
        for key in allowed:
            name = THRESHOLD_TYPES.get(key, key)
            self.threshold_combo.addItem(name, key)
        # Forsøk å beholde forrige valg
        idx = self.threshold_combo.findData(old_threshold)
        if idx >= 0:
            self.threshold_combo.setCurrentIndex(idx)
        self.threshold_combo.blockSignals(False)

    def _update_transport_labels(self):
        """Oppdaterer transportmål-etikettene basert på karmtype og terskeltype."""
        # Opprett midlertidig DoorParams for å bruke beregningsmetodene
        temp_door = DoorParams(
            karm_type=self.karm_combo.currentData() or "",
            floyer=self.floyer_combo.currentData() or 1,
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            threshold_type=self.threshold_combo.currentData() or "ingen",
        )

        # Bredde ved 90°
        bt_90 = temp_door.transport_width_90()
        if bt_90 is not None:
            self.transport_width_90_label.setText(f"{bt_90} mm")
        else:
            self.transport_width_90_label.setText("—")

        # Bredde ved 180°
        bt_180 = temp_door.transport_width_180()
        if bt_180 is not None:
            self.transport_width_180_label.setText(f"{bt_180} mm")
        else:
            self.transport_width_180_label.setText("—")

        # Høyde basert på terskeltype
        ht = temp_door.transport_height_by_threshold()
        if ht is not None:
            self.transport_height_label.setText(f"{ht} mm")
        else:
            self.transport_height_label.setText("—")

    def _on_changed(self):
        """Sender signal når verdier endres."""
        if not self._block_signals:
            self._update_type_dependent_fields()
            self.values_changed.emit()

    def _on_blade_color_changed(self):
        """Synkroniserer karmfarge med dørblad farge ved endring."""
        if not self._block_signals:
            idx = self.color_combo.currentIndex()
            self.karm_color_combo.setCurrentIndex(idx)
            self._on_changed()

    def _on_dimension_changed(self):
        """Håndterer endring av dimensjoner - oppdaterer transportmål."""
        if not self._block_signals:
            self._update_transport_labels()
            self._on_changed()

    def _on_floyer_changed(self):
        """Håndterer endring av antall fløyer."""
        if self._block_signals:
            return
        self._update_transport_labels()
        self._on_changed()

    def _on_threshold_changed(self):
        """Håndterer endring av terskeltype - oppdaterer luftspalte og transportmål."""
        if self._block_signals:
            return

        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'ingen')
        luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 0)

        self.luftspalte_spin.setReadOnly(not is_luftspalte)
        self.luftspalte_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if is_luftspalte
            else QSpinBox.ButtonSymbols.NoButtons
        )
        self._block_signals = True
        self.luftspalte_spin.setValue(luftspalte_value)
        self._block_signals = False

        # Oppdater transportmål siden høyde avhenger av terskeltype
        self._update_transport_labels()

        self._on_changed()

    def _on_window_changed(self):
        """Håndterer endring av vindu-checkbox."""
        if self._block_signals:
            return
        self._update_window_visibility()
        self._on_changed()

    def _on_profile_changed(self):
        """Håndterer endring av vindusprofil - setter alle verdier fra profilen."""
        if self._block_signals:
            return

        profile_key = self.window_profile_combo.currentData()
        profile = WINDOW_PROFILES.get(profile_key, {})

        self._block_signals = True
        self.window_width_spin.setValue(profile.get('width', 400))
        self.window_height_spin.setValue(profile.get('height', 400))
        self.window_x_spin.setValue(profile.get('pos_x', 0))
        self.window_x_slider.setValue(profile.get('pos_x', 0))
        self.window_y_spin.setValue(profile.get('pos_y', 0))
        self.window_y_slider.setValue(profile.get('pos_y', 0))
        self._block_signals = False

        # Oppdater beregnede mål og validering
        self._update_window_calculated()
        self._validate_window_position()
        self._on_changed()

    def _on_window_size_changed(self):
        """Håndterer endring av vindus-størrelse."""
        if self._block_signals:
            return
        self._update_window_calculated()
        self._validate_window_position()
        self._on_changed()

    def _on_window_x_slider_changed(self, value: int):
        """Synkroniserer X-slider med spinbox."""
        if self._block_signals:
            return
        self._block_signals = True
        self.window_x_spin.setValue(value)
        self._block_signals = False
        self._validate_window_position()
        self._on_changed()

    def _on_window_x_spin_changed(self, value: int):
        """Synkroniserer X-spinbox med slider."""
        if self._block_signals:
            return
        self._block_signals = True
        self.window_x_slider.setValue(value)
        self._block_signals = False
        self._validate_window_position()
        self._on_changed()

    def _on_window_y_slider_changed(self, value: int):
        """Synkroniserer Y-slider med spinbox."""
        if self._block_signals:
            return
        self._block_signals = True
        self.window_y_spin.setValue(value)
        self._block_signals = False
        self._validate_window_position()
        self._on_changed()

    def _on_window_y_spin_changed(self, value: int):
        """Synkroniserer Y-spinbox med slider."""
        if self._block_signals:
            return
        self._block_signals = True
        self.window_y_slider.setValue(value)
        self._block_signals = False
        self._validate_window_position()
        self._on_changed()

    def _update_window_visibility(self):
        """Viser/skjuler vinduskontroller basert på checkbox."""
        has_window = self.window_check.isChecked()
        self.window_profile_label.setVisible(has_window)
        self.window_profile_combo.setVisible(has_window)
        self.window_width_label.setVisible(has_window)
        self.window_width_spin.setVisible(has_window)
        self.window_height_label.setVisible(has_window)
        self.window_height_spin.setVisible(has_window)
        self.glass_dims_label.setVisible(has_window)
        self.glass_dims_value.setVisible(has_window)
        self.light_dims_label.setVisible(has_window)
        self.light_dims_value.setVisible(has_window)
        self.window_x_label.setVisible(has_window)
        self.window_x_slider.parent().setVisible(has_window)
        self.window_y_label.setVisible(has_window)
        self.window_y_slider.parent().setVisible(has_window)
        self.window_warning_label.setVisible(has_window and bool(self.window_warning_label.text()))

        if has_window:
            self._update_window_calculated()
            self._validate_window_position()

    def _update_window_calculated(self):
        """Oppdaterer beregnede mål for glasmål og lysåpning."""
        utsp_w = self.window_width_spin.value()
        utsp_h = self.window_height_spin.value()

        glass_w = max(0, utsp_w - 36)
        glass_h = max(0, utsp_h - 36)
        light_w = max(0, glass_w - 26)
        light_h = max(0, glass_h - 26)

        self.glass_dims_value.setText(f"{glass_w} × {glass_h} mm")
        self.light_dims_value.setText(f"{light_w} × {light_h} mm")

    def _validate_window_position(self):
        """Validerer at vinduet holder 150mm margin fra kanter."""
        if not self.window_check.isChecked():
            self.window_warning_label.setText("")
            self.window_warning_label.setVisible(False)
            return

        door_w = self.width_spin.value()
        door_h = self.height_spin.value()
        karm_offset = 90  # Antatt karm-bredde
        blade_w = door_w - karm_offset
        blade_h = door_h - 50  # Antatt karm-høyde differanse

        win_w = self.window_width_spin.value()
        win_h = self.window_height_spin.value()
        pos_x = self.window_x_spin.value()
        pos_y = self.window_y_spin.value()

        # Senter-posisjon (standard: midt horisontalt, 65% opp vertikalt)
        center_x = blade_w / 2 + pos_x
        center_y = blade_h * 0.65 + pos_y

        # Kanter
        left = center_x - win_w / 2
        right = center_x + win_w / 2
        bottom = center_y - win_h / 2
        top = center_y + win_h / 2

        warnings = []
        min_margin = WINDOW_MIN_MARGIN

        if left < min_margin:
            warnings.append(f"Venstre: {int(left)}mm (min {min_margin}mm)")
        if blade_w - right < min_margin:
            warnings.append(f"Høyre: {int(blade_w - right)}mm (min {min_margin}mm)")
        if bottom < min_margin:
            warnings.append(f"Bunn: {int(bottom)}mm (min {min_margin}mm)")
        if blade_h - top < min_margin:
            warnings.append(f"Topp: {int(blade_h - top)}mm (min {min_margin}mm)")

        if warnings:
            self.window_warning_label.setText("⚠ For nær kant: " + ", ".join(warnings))
            self.window_warning_label.setVisible(True)
        else:
            self.window_warning_label.setText("")
            self.window_warning_label.setVisible(False)

    def _on_karm_changed(self):
        """Oppdaterer dørblad-valg basert på valgt karmtype."""
        if self._block_signals:
            return
        self._update_blade_for_karm()
        self._update_utforing_options()
        self._update_threshold_for_karm()

        # Oppdater brutt kuldebro
        self._update_kuldebro_indicator()

        # Oppdater transportmål (avhenger av karmtype)
        self._update_transport_labels()

        self._on_changed()

    def _on_thickness_changed(self):
        """Håndterer veggtykkelse-endring - oppdaterer utforing og karmtype-filter."""
        if self._block_signals:
            return
        self._filter_karm_by_thickness()
        self._update_utforing_options()
        self._on_changed()

    def _update_utforing_options(self):
        """Oppdaterer utforing-dropdown basert på veggtykkelse og karmtype."""
        karm = self.karm_combo.currentData()
        thickness = self.thickness_spin.value()

        # Sjekk om karmen støtter utforing
        if karm not in KARM_HAS_UTFORING:
            self.utforing_combo.setEnabled(False)
            self.utforing_combo.setVisible(False)
            self.utforing_label.setVisible(False)
            self.utforing_combo.clear()
            # Utvid veggtykkelse-input når utforing er skjult
            self.thickness_spin.setMaximumWidth(16777215)  # Default max
            return

        self.utforing_combo.setEnabled(True)
        self.utforing_combo.setVisible(True)
        self.utforing_label.setVisible(True)
        # Begrens veggtykkelse-input når utforing vises
        self.thickness_spin.setMaximumWidth(100)
        old_utforing = self.utforing_combo.currentData()
        self.utforing_combo.blockSignals(True)
        self.utforing_combo.clear()

        # Finn passende utforinger og velg beste match
        best_match = None
        for key, info in UTFORING_RANGES.items():
            if info['min'] <= thickness <= info['max']:
                self.utforing_combo.addItem(info['name'], key)
                if best_match is None:
                    best_match = key

        # Forsøk å beholde forrige valg, ellers velg beste match
        idx = self.utforing_combo.findData(old_utforing)
        if idx >= 0:
            self.utforing_combo.setCurrentIndex(idx)
        elif best_match:
            idx = self.utforing_combo.findData(best_match)
            if idx >= 0:
                self.utforing_combo.setCurrentIndex(idx)

        self.utforing_combo.blockSignals(False)

    def _filter_karm_by_thickness(self):
        """Filtrerer karmtype-dropdown basert på veggtykkelse."""
        thickness = self.thickness_spin.value()
        door_type = self.door_type_combo.currentData()

        old_karm = self.karm_combo.currentData()
        self.karm_combo.blockSignals(True)
        self.karm_combo.clear()

        for karm in DOOR_KARM_TYPES.get(door_type, []):
            # Skjul karmer med utforing hvis tykkelse > 300mm
            if karm in KARM_HAS_UTFORING and thickness > UTFORING_MAX_THICKNESS:
                continue
            self.karm_combo.addItem(karm, karm)

        # Forsøk å beholde forrige valg
        idx = self.karm_combo.findData(old_karm)
        if idx >= 0:
            self.karm_combo.setCurrentIndex(idx)

        self.karm_combo.blockSignals(False)

        # Oppdater dørblad basert på ny karmtype
        self._update_blade_for_karm()

    def _on_blade_changed(self):
        """Oppdaterer tykkelse-valg basert på valgt dørblad."""
        if self._block_signals:
            return
        self._update_thickness_for_blade()
        self._on_changed()

    def _update_blade_for_karm(self):
        """Fyller dørblad-dropdown basert på dørtype (override) eller valgt karmtype."""
        door_type = self.door_type_combo.currentData()
        # Sjekk om dørtypen har spesifikke dørbladtyper
        blade_keys = DOOR_TYPE_BLADE_OVERRIDE.get(door_type)
        if blade_keys is None:
            karm = self.karm_combo.currentData()
            blade_keys = KARM_BLADE_TYPES.get(karm, [])

        old_blade = self.blade_combo.currentData()
        self.blade_combo.blockSignals(True)
        self.blade_combo.clear()
        for key in blade_keys:
            info = DOOR_BLADE_TYPES.get(key, {})
            self.blade_combo.addItem(info.get('name', key), key)
        # Forsøk å beholde forrige valg
        idx = self.blade_combo.findData(old_blade)
        if idx >= 0:
            self.blade_combo.setCurrentIndex(idx)
        self.blade_combo.blockSignals(False)

        self._update_thickness_for_blade()

    def _update_thickness_for_blade(self):
        """Oppdaterer tykkelse-spin basert på valgt dørbladtype.
        Readonly uten piler når bare 1 valg, redigerbar med piler når flere."""
        blade_key = self.blade_combo.currentData()
        info = DOOR_BLADE_TYPES.get(blade_key, {})
        self._blade_thicknesses = info.get('thicknesses', [40])

        multiple = len(self._blade_thicknesses) > 1
        self.blade_thickness_spin.blockSignals(True)
        self.blade_thickness_spin.setRange(
            min(self._blade_thicknesses), max(self._blade_thicknesses)
        )
        self.blade_thickness_spin.setValue(self._blade_thicknesses[0])
        self.blade_thickness_spin.setSingleStep(
            self._blade_thicknesses[1] - self._blade_thicknesses[0] if multiple else 1
        )
        self.blade_thickness_spin.blockSignals(False)

        self.blade_thickness_spin.setReadOnly(not multiple)
        self.blade_thickness_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if multiple
            else QSpinBox.ButtonSymbols.NoButtons
        )

    def _update_kuldebro_indicator(self):
        """Oppdaterer brutt kuldebro-indikator."""
        door_type = self.door_type_combo.currentData()
        karm_type = self.karm_combo.currentData() or ""
        has_kuldebro = (karm_type in BRUTT_KULDEBRO_KARM or
                        door_type in BRUTT_KULDEBRO_DORRAMME)
        self.kuldebro_value.setText("Ja" if has_kuldebro else "Nei")

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

        # Oppdater dørblad basert på ny karmtype
        self._update_blade_for_karm()

        # Oppdater terskeltyper for denne dørtypen
        self._update_threshold_for_karm()

        # Oppdater utforing-opsjoner
        self._update_utforing_options()

        # Oppdater U-verdi
        u_value = DOOR_U_VALUES.get(door_type, 0.0)
        self.insulation_spin.setValue(u_value)

        # Oppdater kuldebro
        self._update_kuldebro_indicator()

        # Oppdater transportmål
        self._update_transport_labels()

        self._update_type_dependent_fields()
        self.values_changed.emit()

    def _update_type_dependent_fields(self):
        """Viser/skjuler felt basert på valgt dørtype."""
        door_type = self.door_type_combo.currentData()
        floyer = self.floyer_combo.currentData() or 1

        # Vindu-felt synlighet
        self._update_window_visibility()

        # Spesielle egenskaper synlighet
        is_fire = door_type == 'BD'
        has_u_value = DOOR_U_VALUES.get(door_type, 0.0) > 0

        self.fire_rating_label.setVisible(is_fire)
        self.fire_rating_combo.setVisible(is_fire)
        self.sound_rating_label.setVisible(False)  # Lyddør fjernet
        self.sound_rating_combo.setVisible(False)
        self.insulation_label.setVisible(has_u_value)
        self.insulation_spin.setVisible(has_u_value)

        # Brutt kuldebro vises alltid
        self._update_kuldebro_indicator()

        # Vis/skjul hele spesialgruppen
        show_special = is_fire or has_u_value or True  # Alltid vis pga kuldebro
        self.special_group.setVisible(show_special)

        # Terskel/luftspalte aktivering
        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'ingen')
        self.luftspalte_spin.setReadOnly(not is_luftspalte)
        self.luftspalte_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if is_luftspalte
            else QSpinBox.ButtonSymbols.NoButtons
        )
        if not is_luftspalte:
            luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 0)
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
        door.blade_type = self.blade_combo.currentData() or "SDI_ROCA"
        door.blade_thickness = self.blade_thickness_spin.value()
        door.utforing = self.utforing_combo.currentData() or ""
        door.color = self.color_combo.currentData() or ""
        door.karm_color = self.karm_color_combo.currentData() or ""
        door.swing_direction = self.hinge_combo.currentData() or "left"

        # Vindu
        door.has_window = self.window_check.isChecked()
        door.window_width = self.window_width_spin.value()
        door.window_height = self.window_height_spin.value()
        door.window_pos_x = self.window_x_spin.value()
        door.window_pos_y = self.window_y_spin.value()
        door.window_profile = self.window_profile_combo.currentData() or "rektangular"

        # Tillegg
        door.threshold_type = self.threshold_combo.currentData() or "standard"
        if door.threshold_type == 'ingen':
            door.luftspalte = self.luftspalte_spin.value()
        else:
            door.luftspalte = THRESHOLD_LUFTSPALTE.get(door.threshold_type, 0)

        # Spesielle egenskaper
        door.fire_rating = self.fire_rating_combo.currentData() or ""
        door.sound_rating = self.sound_rating_combo.currentData() or 0
        door.insulation_value = self.insulation_spin.value()
        door.notes = self.notes_edit.text()

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

        # Dørblad og tykkelse
        self._update_blade_for_karm()
        idx = self.blade_combo.findData(door.blade_type)
        if idx >= 0:
            self.blade_combo.setCurrentIndex(idx)
        self._update_thickness_for_blade()
        self.blade_thickness_spin.setValue(door.blade_thickness)

        # Utforing
        self._update_utforing_options()
        idx = self.utforing_combo.findData(door.utforing)
        if idx >= 0:
            self.utforing_combo.setCurrentIndex(idx)

        # Terskel
        self._update_threshold_for_karm()
        idx = self.threshold_combo.findData(door.threshold_type)
        if idx >= 0:
            self.threshold_combo.setCurrentIndex(idx)
        if door.threshold_type == 'ingen':
            self.luftspalte_spin.setValue(door.luftspalte)

        # Farge
        idx = self.color_combo.findData(door.color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)

        # Karmfarge
        idx = self.karm_color_combo.findData(door.karm_color)
        if idx >= 0:
            self.karm_color_combo.setCurrentIndex(idx)

        # Slagretning
        idx = self.hinge_combo.findData(door.swing_direction)
        if idx >= 0:
            self.hinge_combo.setCurrentIndex(idx)

        # Vindu
        self.window_check.setChecked(door.has_window)
        idx = self.window_profile_combo.findData(door.window_profile)
        if idx >= 0:
            self.window_profile_combo.setCurrentIndex(idx)
        self.window_width_spin.setValue(door.window_width)
        self.window_height_spin.setValue(door.window_height)
        self.window_x_spin.setValue(door.window_pos_x)
        self.window_x_slider.setValue(door.window_pos_x)
        self.window_y_spin.setValue(door.window_pos_y)
        self.window_y_slider.setValue(door.window_pos_y)

        # Spesielle
        idx = self.fire_rating_combo.findData(door.fire_rating)
        if idx >= 0:
            self.fire_rating_combo.setCurrentIndex(idx)
        idx = self.sound_rating_combo.findData(door.sound_rating)
        if idx >= 0:
            self.sound_rating_combo.setCurrentIndex(idx)
        self.insulation_spin.setValue(door.insulation_value)

        # Merknader
        self.notes_edit.setText(door.notes)

        self._block_signals = False
        self._update_type_dependent_fields()
        self._update_transport_labels()
        self._update_kuldebro_indicator()
