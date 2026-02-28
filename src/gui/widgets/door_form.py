"""
Parameterskjema for dørkonfigurasjon.
Viser input-felt for dørtype, mål, farge, beslag og tilleggsutstyr.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QLabel,
    QStyledItemDelegate, QStyle, QPushButton, QColorDialog
)
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QObject, QEvent
from PyQt6.QtGui import QColor, QPen, QIcon, QPixmap, QPainter

from ...utils.constants import (
    DOOR_TYPES, DEFAULT_DIMENSIONS, RAL_COLORS, POLYKARBONAT_COLORS,
    SWING_DIRECTIONS, FIRE_RATINGS, SOUND_RATINGS,
    THRESHOLD_TYPES, THRESHOLD_LUFTSPALTE,
    DOOR_KARM_TYPES, DOOR_FLOYER, KARM_THRESHOLD_TYPES,
    DOOR_BLADE_TYPES, KARM_BLADE_TYPES, KARM_FLOYER, DOOR_TYPE_BLADE_OVERRIDE,
    HINGE_TYPES, KARM_HINGE_TYPES,
    MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, MAX_HEIGHT, MIN_THICKNESS, MAX_THICKNESS,
    UTFORING_RANGES, KARM_HAS_UTFORING, UTFORING_MAX_THICKNESS,
    KARM_DISPLAY_NAMES
)
from ...doors import DOOR_REGISTRY
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


class ScrollGuardFilter(QObject):
    """Blokkerer scroll-hendelser på widgets som ikke har fokus."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and not obj.hasFocus():
            event.ignore()
            return True
        return super().eventFilter(obj, event)


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
        self.customer_edit.setPlaceholderText("F.eks. 1000")
        self.customer_edit.textChanged.connect(self._on_changed)
        project_layout.addRow("Ordre Referanse:", self.customer_edit)

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

        # Karmtype + antall fløyer + fordeling på samme rad
        karm_floyer_widget = QWidget()
        karm_floyer_layout = QHBoxLayout(karm_floyer_widget)
        karm_floyer_layout.setContentsMargins(0, 0, 0, 0)

        self.karm_combo = QComboBox()
        self.karm_combo.currentIndexChanged.connect(self._on_karm_changed)
        karm_floyer_layout.addWidget(self.karm_combo, stretch=1)

        self.floyer_combo = QComboBox()
        self.floyer_combo.currentIndexChanged.connect(self._on_floyer_changed)
        karm_floyer_layout.addWidget(self.floyer_combo, stretch=1)

        self.split_spin = QSpinBox()
        self.split_spin.setRange(20, 80)
        self.split_spin.setValue(50)
        self.split_spin.setSuffix(" %")
        self.split_spin.setSingleStep(5)
        self.split_spin.valueChanged.connect(self._on_changed)
        karm_floyer_layout.addWidget(self.split_spin, stretch=1)

        door_layout.addRow("Karmtype:", karm_floyer_widget)

        # Bredde-rad: BM (input) + Karm + B90° + B180°
        width_widget = QWidget()
        width_layout = QHBoxLayout(width_widget)
        width_layout.setContentsMargins(0, 0, 0, 0)
        width_layout.setSpacing(6)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(MIN_WIDTH, MAX_WIDTH)
        self.width_spin.setValue(1010)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setSingleStep(100)
        self.width_spin.setMaximumWidth(100)
        self.width_spin.valueChanged.connect(self._on_dimension_changed)
        width_layout.addWidget(self.width_spin)

        self.karm_width_label = QLabel("Karm: —")
        width_layout.addWidget(self.karm_width_label)

        self._sep_w = QLabel("|")
        width_layout.addWidget(self._sep_w)

        self.transport_width_90_label = QLabel("BT 90°: —")
        width_layout.addWidget(self.transport_width_90_label)

        self._sep_w2 = QLabel("|")
        width_layout.addWidget(self._sep_w2)

        self.transport_width_180_label = QLabel("BT 180°: —")
        width_layout.addWidget(self.transport_width_180_label)

        width_layout.addStretch()
        door_layout.addRow("Utsparing (BM):", width_widget)

        # Høyde-rad: HM (input) + Karm + H transport
        height_widget = QWidget()
        height_layout = QHBoxLayout(height_widget)
        height_layout.setContentsMargins(0, 0, 0, 0)
        height_layout.setSpacing(6)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(MIN_HEIGHT, MAX_HEIGHT)
        self.height_spin.setValue(2110)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setSingleStep(100)
        self.height_spin.setMaximumWidth(100)
        self.height_spin.valueChanged.connect(self._on_dimension_changed)
        height_layout.addWidget(self.height_spin)

        self.karm_height_label = QLabel("Karm: —")
        height_layout.addWidget(self.karm_height_label)

        self._sep_h = QLabel("|")
        height_layout.addWidget(self._sep_h)

        self.transport_height_label = QLabel("HT: —")
        height_layout.addWidget(self.transport_height_label)

        height_layout.addStretch()
        door_layout.addRow("Utsparing (HM):", height_widget)

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

        door_layout.addRow("Veggtjukkelse:", thickness_widget)

        # Dørblad (kun tykkelse-spin, type settes automatisk)
        self.blade_thickness_spin = QSpinBox()
        self.blade_thickness_spin.setSuffix(" mm")
        self.blade_thickness_spin.setMinimumWidth(100)
        self.blade_thickness_spin.setReadOnly(True)
        self.blade_thickness_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.blade_thickness_spin.valueChanged.connect(self._on_changed)
        door_layout.addRow("Dørblad:", self.blade_thickness_spin)

        # Hengsler: type + antall per fløy
        hinge_widget = QWidget()
        hinge_layout = QHBoxLayout(hinge_widget)
        hinge_layout.setContentsMargins(0, 0, 0, 0)

        self.hinge_type_combo = QComboBox()
        self.hinge_type_combo.currentIndexChanged.connect(self._on_changed)
        hinge_layout.addWidget(self.hinge_type_combo, stretch=1)

        self.hinge_count_combo = QComboBox()
        self.hinge_count_combo.setMinimumWidth(100)
        for n in [2, 3, 4]:
            self.hinge_count_combo.addItem(f"{n} stk.", n)
        self.hinge_count_combo.currentIndexChanged.connect(self._on_changed)
        hinge_layout.addWidget(self.hinge_count_combo)

        door_layout.addRow("Hengsler:", hinge_widget)

        # Adjufix karmhylser
        self.adjufix_combo = QComboBox()
        self.adjufix_combo.addItem("Nei", False)
        self.adjufix_combo.addItem("Ja", True)
        self.adjufix_combo.currentIndexChanged.connect(self._on_dimension_changed)
        door_layout.addRow("Adjufix:", self.adjufix_combo)

        # Terskeltype + luftspalte på samme rad
        threshold_widget = QWidget()
        threshold_layout = QHBoxLayout(threshold_widget)
        threshold_layout.setContentsMargins(0, 0, 0, 0)

        self.threshold_combo = QComboBox()
        self.threshold_combo.currentIndexChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(self.threshold_combo, stretch=1)

        self.luftspalte_spin = QSpinBox()
        self.luftspalte_spin.setRange(0, 100)
        self.luftspalte_spin.setValue(THRESHOLD_LUFTSPALTE.get('ingen', 22))
        self.luftspalte_spin.setSuffix(" mm")
        self.luftspalte_spin.setSingleStep(1)
        self.luftspalte_spin.setReadOnly(True)
        self.luftspalte_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.luftspalte_spin.setMinimumWidth(100)
        self.luftspalte_spin.valueChanged.connect(self._on_changed)
        threshold_layout.addWidget(self.luftspalte_spin)

        door_layout.addRow("Terskel:", threshold_widget)

        # Sparkeplate Ja/Nei (tilgjengelig for alle dørtyper)
        self.sparkeplate_combo = QComboBox()
        self.sparkeplate_combo.addItem("Nei", False)
        self.sparkeplate_combo.addItem("Ja", True)
        self.sparkeplate_combo.currentIndexChanged.connect(self._on_changed)
        self.sparkeplate_label = QLabel("Sparkeplate:")
        door_layout.addRow(self.sparkeplate_label, self.sparkeplate_combo)

        layout.addWidget(door_group)

        # --- Produktdetaljer ---
        look_group = QGroupBox("Produktdetaljer")
        look_layout = QFormLayout(look_group)

        # Veggfarge (color picker)
        self._wall_color = "#8C8C84"
        self.wall_color_btn = QPushButton()
        self.wall_color_btn.setFixedHeight(28)
        self.wall_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_wall_color_btn()
        self.wall_color_btn.clicked.connect(self._pick_wall_color)
        look_layout.addRow("Veggfarge:", self.wall_color_btn)

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
        self.swing_label = QLabel("Slagretning:")
        look_layout.addRow(self.swing_label, self.hinge_combo)

        self.laaskasse_combo = QComboBox()
        laaskasse_typer = [
            "Ingen",
            "3065/316L i SF/rustfritt stål",
            "LK565",
            "ASSA LK566 i SF/rustfritt stål",
            "DL112",
        ]
        self.laaskasse_combo.addItems(laaskasse_typer)
        self.laaskasse_combo.setCurrentText("3065/316L i SF/rustfritt stål")
        self.laaskasse_combo.currentIndexChanged.connect(self._on_changed)
        self.laaskasse_label = QLabel("Låskasse:")
        look_layout.addRow(self.laaskasse_label, self.laaskasse_combo)

        self.beslag_combo = QComboBox()
        beslag_typer = [
            "Ingen",
            "Vrider 8611/Skilt 8752 for sylinder i rustfritt stål",
            "Vrider 8611/Blindskilt 8755 i rustfritt stål",
            "Vrider 8611/Skilt 8659S for sylinder i rustfritt stål",
            "Vrider 519U/Blindskilt 530A i SF stål",
            "Vrider 519U/Sylinderskilt oval 530C i SF stål",
            "Vrider 519U/WC-skilt 530D i SF stål",
            "Vrider 519U/Sylinderskilt rundt 550C i SF stål",
        ]
        self.beslag_combo.addItems(beslag_typer)
        self.beslag_combo.setCurrentText("Vrider 519U/Sylinderskilt oval 530C i SF stål")
        self.beslag_combo.currentIndexChanged.connect(self._on_changed)
        self.beslag_label = QLabel("Beslagstype:")
        look_layout.addRow(self.beslag_label, self.beslag_combo)

        # Pendeldør-felter (inne i Produktdetaljer, skjules for andre dørtyper)
        self.avviserboyler_combo = QComboBox()
        self.avviserboyler_combo.addItem("Ja", True)
        self.avviserboyler_combo.addItem("Nei", False)
        self.avviserboyler_combo.currentIndexChanged.connect(self._on_changed)
        self.avviserboyler_label = QLabel("Avviserbøyler:")
        look_layout.addRow(self.avviserboyler_label, self.avviserboyler_combo)

        layout.addWidget(look_group)

        # --- Skjulte widgets for DoorParams-kompatibilitet ---
        # Disse brukes av update_door() og load_door() men vises ikke i UI
        self.fire_rating_combo = QComboBox()
        for rating in FIRE_RATINGS:
            self.fire_rating_combo.addItem(rating or "(ingen)", rating)
        self.fire_rating_combo.currentIndexChanged.connect(self._on_changed)

        self.sound_rating_combo = QComboBox()
        for db in SOUND_RATINGS:
            self.sound_rating_combo.addItem(f"Rw{db} dB" if db else "(ingen)", db)
        self.sound_rating_combo.currentIndexChanged.connect(self._on_changed)

        layout.addStretch()

        # Fyll karmtype, fløyer, dørblad og hengsler for standard dørtype
        initial_type = self.door_type_combo.currentData()
        for karm in DOOR_KARM_TYPES.get(initial_type, []):
            self.karm_combo.addItem(KARM_DISPLAY_NAMES.get(karm, karm), karm)
        self._update_floyer_for_karm()
        self._update_blade_thickness_for_karm()
        self._update_hinge_for_karm()
        self._update_threshold_for_karm()
        self._update_utforing_options()

        # Sett standardmål fra DEFAULT_DIMENSIONS for initial dørtype
        initial_defaults = DEFAULT_DIMENSIONS.get(initial_type, {})
        if initial_defaults:
            self.width_spin.setValue(initial_defaults['width'])
            self.height_spin.setValue(initial_defaults['height'])
            self.thickness_spin.setValue(initial_defaults['thickness'])

        # Initial visning av typeavhengige felt
        self._update_type_dependent_fields()
        self._update_transport_labels()

        # Scroll-guard: hindre at scroll-hjulet endrer verdier på widgets uten fokus
        self._scroll_guard = ScrollGuardFilter(self)
        for widget in self.findChildren((QSpinBox, QComboBox)):
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            widget.installEventFilter(self._scroll_guard)

    def _populate_color_combo(self, combo: QComboBox):
        """Fyller en farge-combobox med RAL-farger og fargeruter."""
        delegate = ColorSwatchDelegate(combo)
        combo.setItemDelegate(delegate)
        self._fill_combo_with_ral(combo)

    def _fill_combo_with_ral(self, combo: QComboBox):
        """Fyller combo med RAL-farger."""
        combo.clear()
        for code, info in RAL_COLORS.items():
            pixmap = QPixmap(14, 14)
            pixmap.fill(QColor(info['hex']))
            p = QPainter(pixmap)
            p.setPen(QPen(QColor(80, 80, 80), 1))
            p.drawRect(0, 0, 13, 13)
            p.end()
            icon = QIcon(pixmap)
            display_text = f"      {code} - {info['name']}"
            combo.addItem(icon, display_text, code)

    def _fill_combo_with_polykarbonat(self, combo: QComboBox, color_keys: list):
        """Fyller combo med polykarbonat-farger."""
        combo.clear()
        for key in color_keys:
            info = POLYKARBONAT_COLORS.get(key)
            if not info:
                continue
            pixmap = QPixmap(14, 14)
            pixmap.fill(QColor(info['hex']))
            p = QPainter(pixmap)
            p.setPen(QPen(QColor(80, 80, 80), 1))
            p.drawRect(0, 0, 13, 13)
            p.end()
            icon = QIcon(pixmap)
            display_text = f"      {info['name']}"
            combo.addItem(icon, display_text, key)

    def _update_blade_color_combo(self):
        """Oppdaterer dørblad farge-combo basert på dørtype (RAL vs polykarbonat)."""
        door_type = self.door_type_combo.currentData()
        door_def = DOOR_REGISTRY.get(door_type, {})
        blade_colors = door_def.get('blade_colors')

        old_value = self.color_combo.currentData()
        self.color_combo.blockSignals(True)
        if blade_colors:
            self._fill_combo_with_polykarbonat(self.color_combo, blade_colors)
        else:
            self._fill_combo_with_ral(self.color_combo)
        # Forsøk å beholde forrige valg
        idx = self.color_combo.findData(old_value)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        self.color_combo.blockSignals(False)

    def _update_threshold_for_karm(self):
        """Oppdaterer terskel-dropdown med tillatte typer og setter dørtype-default."""
        karm_type = self.karm_combo.currentData()
        door_type = self.door_type_combo.currentData()
        door_def = DOOR_REGISTRY.get(door_type, {})
        allowed = KARM_THRESHOLD_TYPES.get(karm_type, list(THRESHOLD_TYPES.keys()))

        self.threshold_combo.blockSignals(True)
        self.threshold_combo.clear()
        for key in allowed:
            name = THRESHOLD_TYPES.get(key, key)
            self.threshold_combo.addItem(name, key)

        # Sett dørtype-default terskel (eller første tillatte)
        default_threshold = door_def.get('default_threshold')
        idx = -1
        if default_threshold:
            idx = self.threshold_combo.findData(default_threshold)
        if idx >= 0:
            self.threshold_combo.setCurrentIndex(idx)
        self.threshold_combo.blockSignals(False)

        # Oppdater luftspalte til default for dørtypen
        threshold_key = self.threshold_combo.currentData()
        default_ls = door_def.get('default_luftspalte')
        if default_ls is not None and threshold_key == 'ingen':
            self.luftspalte_spin.blockSignals(True)
            self.luftspalte_spin.setValue(default_ls)
            self.luftspalte_spin.blockSignals(False)
        else:
            luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 22)
            self.luftspalte_spin.blockSignals(True)
            self.luftspalte_spin.setValue(luftspalte_value)
            self.luftspalte_spin.blockSignals(False)

    def _update_transport_labels(self):
        """Oppdaterer karm- og transportmål-etikettene."""
        temp_door = DoorParams(
            karm_type=self.karm_combo.currentData() or "",
            floyer=self.floyer_combo.currentData() or 1,
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            threshold_type=self.threshold_combo.currentData() or "ingen",
            adjufix=self.adjufix_combo.currentData() or False,
        )

        # Karmmål — serie-3 karmer har ikke gerikt
        karm_prefix = "Utv. karm" if '3' in temp_door.karm_type else "Utv. karm (inc. gerikt)"
        self.karm_width_label.setText(f"{karm_prefix}: {temp_door.karm_width()} mm")
        self.karm_height_label.setText(f"{karm_prefix}: {temp_door.karm_height()} mm")

        # Transportbredde 90° og 180°
        bt_90 = temp_door.transport_width_90()
        self.transport_width_90_label.setText(f"BT 90°: {bt_90} mm" if bt_90 is not None else "BT 90°: —")

        bt_180 = temp_door.transport_width_180()
        self.transport_width_180_label.setText(f"BT 180°: {bt_180} mm" if bt_180 is not None else "BT 180°: —")

        # Transporthøyde
        ht = temp_door.transport_height_by_threshold()
        self.transport_height_label.setText(f"HT: {ht} mm" if ht is not None else "HT: —")

    def _on_changed(self):
        """Sender signal når verdier endres."""
        if not self._block_signals:
            self._update_type_dependent_fields()
            self.values_changed.emit()

    def _update_wall_color_btn(self):
        """Oppdaterer veggfarge-knappens utseende."""
        self.wall_color_btn.setStyleSheet(
            f"background-color: {self._wall_color}; border: 1px solid #555; border-radius: 3px;"
        )
        self.wall_color_btn.setText(self._wall_color.upper())

    def _pick_wall_color(self):
        """Åpner fargevelger for veggfarge."""
        color = QColorDialog.getColor(
            QColor(self._wall_color), self, "Velg veggfarge"
        )
        if color.isValid():
            self._wall_color = color.name()
            self._update_wall_color_btn()
            self._on_changed()

    def _on_blade_color_changed(self):
        """Synkroniserer karmfarge med dørblad farge ved endring (kun for RAL-farger)."""
        if not self._block_signals:
            # Pendeldør polykarbonat har egne bladfarger — ikke synk med karm
            if not self._is_pendeldor():
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
        self._update_split_visibility()
        self._update_transport_labels()
        self._on_changed()

    def _on_threshold_changed(self):
        """Håndterer endring av terskeltype - oppdaterer luftspalte og transportmål."""
        if self._block_signals:
            return

        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'ingen')
        luftspalte_value = THRESHOLD_LUFTSPALTE.get(threshold_key, 22)

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

    def _on_karm_changed(self):
        """Oppdaterer dørblad, hengsler og terskel basert på valgt karmtype."""
        if self._block_signals:
            return
        self._update_floyer_for_karm()
        self._update_blade_thickness_for_karm()
        self._update_hinge_for_karm()
        self._update_utforing_options()
        self._update_threshold_for_karm()

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
            self.karm_combo.addItem(KARM_DISPLAY_NAMES.get(karm, karm), karm)

        # Forsøk å beholde forrige valg
        idx = self.karm_combo.findData(old_karm)
        if idx >= 0:
            self.karm_combo.setCurrentIndex(idx)

        self.karm_combo.blockSignals(False)

        # Oppdater fløyer, dørblad og hengsler basert på ny karmtype
        self._update_floyer_for_karm()
        self._update_blade_thickness_for_karm()
        self._update_hinge_for_karm()

    def _update_blade_thickness_for_karm(self):
        """Oppdaterer dørblad-tykkelse basert på første tilgjengelige bladtype for karmtypen."""
        door_type = self.door_type_combo.currentData()
        karm = self.karm_combo.currentData()

        # Bruk DOOR_REGISTRY for korrekt oppslag (unngår kollisjon ved delte karmtyper)
        door_def = DOOR_REGISTRY.get(door_type, {})
        blade_keys = door_def.get('karm_blade_types', {}).get(karm, [])
        if not blade_keys:
            blade_keys = DOOR_TYPE_BLADE_OVERRIDE.get(door_type) or KARM_BLADE_TYPES.get(karm, [])

        if blade_keys:
            blade_key = blade_keys[0]
            # Slå opp bladtype fra dørtype-definisjonen først
            info = door_def.get('blade_types', {}).get(blade_key)
            if info is None:
                info = DOOR_BLADE_TYPES.get(blade_key, {})
            thicknesses = info.get('thicknesses', [40])
        else:
            thicknesses = [40]

        multiple = len(thicknesses) > 1
        self.blade_thickness_spin.blockSignals(True)
        self.blade_thickness_spin.setRange(min(thicknesses), max(thicknesses))
        self.blade_thickness_spin.setValue(thicknesses[0])
        if multiple:
            self.blade_thickness_spin.setSingleStep(thicknesses[1] - thicknesses[0])
        else:
            self.blade_thickness_spin.setSingleStep(1)
        self.blade_thickness_spin.blockSignals(False)

        self.blade_thickness_spin.setReadOnly(not multiple)
        self.blade_thickness_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows if multiple
            else QSpinBox.ButtonSymbols.NoButtons
        )

    def _update_hinge_for_karm(self):
        """Fyller hengsel-dropdown basert på valgt karmtype."""
        door_type = self.door_type_combo.currentData()
        karm = self.karm_combo.currentData()

        # Bruk DOOR_REGISTRY for korrekt oppslag (unngår kollisjon ved delte karmtyper)
        door_def = DOOR_REGISTRY.get(door_type, {})
        hinge_keys = door_def.get('karm_hengsel_typer', {}).get(karm)
        if hinge_keys is None:
            hinge_keys = KARM_HINGE_TYPES.get(karm, [])

        old_hinge = self.hinge_type_combo.currentData()
        self.hinge_type_combo.blockSignals(True)
        self.hinge_type_combo.clear()
        for key in hinge_keys:
            info = HINGE_TYPES.get(key, {})
            self.hinge_type_combo.addItem(info.get('navn', key), key)
        # Forsøk å beholde forrige valg
        idx = self.hinge_type_combo.findData(old_hinge)
        if idx >= 0:
            self.hinge_type_combo.setCurrentIndex(idx)
        self.hinge_type_combo.blockSignals(False)


    def _update_floyer_for_karm(self):
        """Oppdaterer fløyer-dropdown basert på tillatte fløyer for valgt karmtype."""
        karm = self.karm_combo.currentData()
        door_type = self.door_type_combo.currentData()
        allowed = KARM_FLOYER.get(karm, DOOR_FLOYER.get(door_type, [1]))

        old_floyer = self.floyer_combo.currentData()
        self.floyer_combo.blockSignals(True)
        self.floyer_combo.clear()
        for f in allowed:
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)
        # Forsøk å beholde forrige valg
        idx = self.floyer_combo.findData(old_floyer)
        if idx >= 0:
            self.floyer_combo.setCurrentIndex(idx)
        self.floyer_combo.blockSignals(False)
        self._update_split_visibility()

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
            self.karm_combo.addItem(KARM_DISPLAY_NAMES.get(karm, karm), karm)

        self._block_signals = False

        # Oppdater fløyer basert på karmtype
        self._update_floyer_for_karm()

        # Oppdater dørblad-tykkelse og hengsler basert på ny karmtype
        self._update_blade_thickness_for_karm()
        self._update_hinge_for_karm()

        # Sett default antall hengsler for dørtypen (f.eks. 3 for branndør)
        door_def = DOOR_REGISTRY.get(door_type, {})
        default_hc = door_def.get('default_hinge_count')
        if default_hc:
            idx = self.hinge_count_combo.findData(default_hc)
            if idx >= 0:
                self.hinge_count_combo.setCurrentIndex(idx)

        # Oppdater terskeltyper med dørtype-default
        self._update_threshold_for_karm()

        # Sparkeplate default: "Ja" for pendeldører, "Nei" for andre
        is_pendel = door_def.get('pendeldor', False)
        sp_default = True if is_pendel else False
        sp_idx = self.sparkeplate_combo.findData(sp_default)
        if sp_idx >= 0:
            self.sparkeplate_combo.setCurrentIndex(sp_idx)

        # Oppdater dørblad farge-combo (RAL vs polykarbonat)
        self._update_blade_color_combo()

        # Oppdater utforing-opsjoner
        self._update_utforing_options()

        # Oppdater transportmål
        self._update_transport_labels()

        self._update_type_dependent_fields()
        self.values_changed.emit()

    def _update_split_visibility(self):
        """Viser/skjuler fordeling-spinbox basert på antall fløyer."""
        is_2floyet = (self.floyer_combo.currentData() or 1) == 2
        self.split_spin.setVisible(is_2floyet)

    def _is_pendeldor(self) -> bool:
        """Sjekker om valgt dørtype er en pendeldør."""
        door_type = self.door_type_combo.currentData()
        door_def = DOOR_REGISTRY.get(door_type, {})
        return door_def.get('pendeldor', False)

    def _update_type_dependent_fields(self):
        """Viser/skjuler felt basert på valgt dørtype."""
        is_pendel = self._is_pendeldor()

        # Låskasse og beslagstype: skjul for pendeldører
        self.laaskasse_label.setVisible(not is_pendel)
        self.laaskasse_combo.setVisible(not is_pendel)
        self.beslag_label.setVisible(not is_pendel)
        self.beslag_combo.setVisible(not is_pendel)

        # Pendeldør-felter i Produktdetaljer
        self.avviserboyler_label.setVisible(is_pendel)
        self.avviserboyler_combo.setVisible(is_pendel)

        # Fordeling: lås til 50% for pendeldører
        if is_pendel:
            self.split_spin.setValue(50)
            self.split_spin.setVisible(False)
        else:
            self._update_split_visibility()

        # Terskel/luftspalte aktivering
        threshold_key = self.threshold_combo.currentData()
        is_luftspalte = (threshold_key == 'ingen')
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
        door.floyer_split = self.split_spin.value()
        door.width = self.width_spin.value()
        door.height = self.height_spin.value()
        door.thickness = self.thickness_spin.value()
        # Dørblad: type settes fra første tilgjengelige bladtype for karmtypen
        door_type = self.door_type_combo.currentData()
        karm = self.karm_combo.currentData()
        door_def = DOOR_REGISTRY.get(door_type, {})
        blade_keys = door_def.get('karm_blade_types', {}).get(karm, [])
        if not blade_keys:
            blade_keys = DOOR_TYPE_BLADE_OVERRIDE.get(door_type) or KARM_BLADE_TYPES.get(karm, [])
        door.blade_type = blade_keys[0] if blade_keys else "SDI"
        door.blade_thickness = self.blade_thickness_spin.value()
        door.hinge_type = self.hinge_type_combo.currentData() or "ROCA_SF"
        door.hinge_count = self.hinge_count_combo.currentData() or 2
        door.utforing = self.utforing_combo.currentData() or ""
        door.color = self.color_combo.currentData() or ""
        door.karm_color = self.karm_color_combo.currentData() or ""
        door.wall_color = self._wall_color
        door.swing_direction = self.hinge_combo.currentData() or "left"
        door.lock_case = self.laaskasse_combo.currentText()
        door.handle_type = self.beslag_combo.currentText()

        # Sparkeplate
        door.sparkeplate = self.sparkeplate_combo.currentData()
        if door.sparkeplate is None:
            door.sparkeplate = False

        # Pendeldør-felter
        door.sparkeplate_hoyde = 1000  # Hardkodet
        door.avviserboyler = self.avviserboyler_combo.currentData()
        if door.avviserboyler is None:
            door.avviserboyler = True

        # Tillegg
        door.adjufix = self.adjufix_combo.currentData() or False
        door.threshold_type = self.threshold_combo.currentData() or "standard"
        if door.threshold_type == 'ingen':
            door.luftspalte = self.luftspalte_spin.value()
        else:
            door.luftspalte = THRESHOLD_LUFTSPALTE.get(door.threshold_type, 0)

        # Spesielle egenskaper
        door.fire_rating = self.fire_rating_combo.currentData() or ""
        door.sound_rating = self.sound_rating_combo.currentData() or 0
        door.notes = self.notes_edit.text()

    def update_accent_color(self, color: str) -> None:
        """Oppdaterer aksentfargen på info-labels."""
        style = f"color: {color};"
        for label in (
            self.karm_width_label, self._sep_w,
            self.transport_width_90_label, self._sep_w2,
            self.transport_width_180_label,
            self.karm_height_label, self._sep_h,
            self.transport_height_label,
        ):
            label.setStyleSheet(style)

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
            self.karm_combo.addItem(KARM_DISPLAY_NAMES.get(karm, karm), karm)
        idx = self.karm_combo.findData(door.karm_type)
        if idx >= 0:
            self.karm_combo.setCurrentIndex(idx)

        # Oppdater fløyer basert på karmtype (filtrert)
        karm = self.karm_combo.currentData()
        allowed_floyer = KARM_FLOYER.get(karm, DOOR_FLOYER.get(door_type, [1]))
        self.floyer_combo.clear()
        for f in allowed_floyer:
            self.floyer_combo.addItem(f"{f} fløy{'er' if f > 1 else ''}", f)
        idx = self.floyer_combo.findData(door.floyer)
        if idx >= 0:
            self.floyer_combo.setCurrentIndex(idx)

        self.split_spin.setValue(door.floyer_split)

        self.width_spin.setValue(door.width)
        self.height_spin.setValue(door.height)
        self.thickness_spin.setValue(door.thickness)

        # Dørblad-tykkelse
        self._update_blade_thickness_for_karm()
        self.blade_thickness_spin.setValue(door.blade_thickness)

        # Hengsler
        self._update_hinge_for_karm()
        idx = self.hinge_type_combo.findData(door.hinge_type)
        if idx >= 0:
            self.hinge_type_combo.setCurrentIndex(idx)
        idx = self.hinge_count_combo.findData(door.hinge_count)
        if idx >= 0:
            self.hinge_count_combo.setCurrentIndex(idx)

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

        # Adjufix
        idx = self.adjufix_combo.findData(door.adjufix)
        if idx >= 0:
            self.adjufix_combo.setCurrentIndex(idx)

        # Dørblad farge (oppdater combo-innhold først for riktig dørtype)
        self._update_blade_color_combo()
        idx = self.color_combo.findData(door.color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)

        # Karmfarge
        idx = self.karm_color_combo.findData(door.karm_color)
        if idx >= 0:
            self.karm_color_combo.setCurrentIndex(idx)

        # Veggfarge
        self._wall_color = door.wall_color
        self._update_wall_color_btn()

        # Slagretning
        idx = self.hinge_combo.findData(door.swing_direction)
        if idx >= 0:
            self.hinge_combo.setCurrentIndex(idx)

        # Spesielle
        idx = self.fire_rating_combo.findData(door.fire_rating)
        if idx >= 0:
            self.fire_rating_combo.setCurrentIndex(idx)
        idx = self.sound_rating_combo.findData(door.sound_rating)
        if idx >= 0:
            self.sound_rating_combo.setCurrentIndex(idx)

        # Sparkeplate
        idx = self.sparkeplate_combo.findData(door.sparkeplate)
        if idx >= 0:
            self.sparkeplate_combo.setCurrentIndex(idx)

        # Pendeldør-felter
        idx = self.avviserboyler_combo.findData(door.avviserboyler)
        if idx >= 0:
            self.avviserboyler_combo.setCurrentIndex(idx)

        # Merknader
        self.notes_edit.setText(door.notes)

        self._block_signals = False
        self._update_type_dependent_fields()
        self._update_transport_labels()
