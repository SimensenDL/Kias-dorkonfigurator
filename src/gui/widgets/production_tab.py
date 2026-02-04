"""
Produksjons-tab widget for dørkonfigurator.
Viser produksjonsmål og advarsler for valgt konfigurasjon.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ...models.door import DoorParams
from ...utils.calculations import (
    karm_bredde, karm_hoyde,
    sjekk_kalkyle_status, produksjonsmal, produksjonsmal_pd,
)


class ProductionTab(QWidget):
    """Widget som viser produksjonsmål og advarsler."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._door = None

    def _setup_ui(self):
        """Setter opp brukergrensesnittet."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Advarsel-panel (skjult som standard)
        self.warning_frame = QFrame()
        self.warning_frame.setStyleSheet("""
            QFrame {
                background-color: #4a3000;
                border: 1px solid #ff9800;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        warning_layout = QHBoxLayout(self.warning_frame)
        warning_layout.setContentsMargins(12, 8, 12, 8)

        self.warning_icon = QLabel("⚠")
        self.warning_icon.setStyleSheet("font-size: 24px; color: #ff9800;")
        warning_layout.addWidget(self.warning_icon)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: #ffcc80; font-size: 14px;")
        self.warning_label.setWordWrap(True)
        warning_layout.addWidget(self.warning_label, stretch=1)

        self.warning_frame.setVisible(False)
        layout.addWidget(self.warning_frame)

        # Suksess-panel (skjult som standard)
        self.success_frame = QFrame()
        self.success_frame.setStyleSheet("""
            QFrame {
                background-color: #1b3d1b;
                border: 1px solid #4caf50;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        success_layout = QHBoxLayout(self.success_frame)
        success_layout.setContentsMargins(12, 8, 12, 8)

        self.success_icon = QLabel("✓")
        self.success_icon.setStyleSheet("font-size: 24px; color: #4caf50;")
        success_layout.addWidget(self.success_icon)

        self.success_label = QLabel("Produksjonskalkyler tilgjengelig")
        self.success_label.setStyleSheet("color: #a5d6a7; font-size: 14px;")
        success_layout.addWidget(self.success_label, stretch=1)

        self.success_frame.setVisible(False)
        layout.addWidget(self.success_frame)

        # Karmmål-seksjon
        karm_group = QGroupBox("Karmmål")
        karm_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        karm_layout = QHBoxLayout(karm_group)

        self.karm_bredde_label = QLabel("Bredde: —")
        self.karm_bredde_label.setStyleSheet("font-size: 16px;")
        karm_layout.addWidget(self.karm_bredde_label)

        self.karm_hoyde_label = QLabel("Høyde: —")
        self.karm_hoyde_label.setStyleSheet("font-size: 16px;")
        karm_layout.addWidget(self.karm_hoyde_label)

        karm_layout.addStretch()
        layout.addWidget(karm_group)

        # Produksjonsmål-tabell
        self.table_group = QGroupBox("Produksjonsmål")
        self.table_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        table_layout = QVBoxLayout(self.table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Komponent", "Antall", "Bredde", "Høyde"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().resizeSection(1, 100)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().resizeSection(2, 100)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().resizeSection(3, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        table_layout.addWidget(self.table)
        layout.addWidget(self.table_group)

        # Placeholder når ingen data
        self.placeholder_label = QLabel("Velg en dør-konfigurasjon for å se produksjonsmål")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(self.placeholder_label)

        layout.addStretch()

    def update_door(self, door: DoorParams):
        """Oppdaterer visningen med ny dør-konfigurasjon."""
        self._door = door

        if door is None:
            self._show_placeholder()
            return

        # Sjekk kalkyle-status
        er_pd = door.karm_type.startswith('PD')
        status = sjekk_kalkyle_status(door.karm_type, door.blade_type, door.floyer)

        # Vis/skjul advarsler
        self.warning_frame.setVisible(not status['tilgjengelig'])
        self.success_frame.setVisible(status['tilgjengelig'])

        if not status['tilgjengelig']:
            self.warning_label.setText(status['advarsel'])

        # Beregn karmmål
        karm_b = karm_bredde(door.karm_type, door.width)
        karm_h = karm_hoyde(door.karm_type, door.height)

        self.karm_bredde_label.setText(f"Bredde: {karm_b} mm")
        self.karm_hoyde_label.setText(f"Høyde: {karm_h} mm")

        # Skjul placeholder, vis data
        self.placeholder_label.setVisible(False)
        self.table_group.setVisible(True)

        # Hent produksjonsmål
        if status['tilgjengelig']:
            if er_pd:
                mal = produksjonsmal_pd(door.blade_type, karm_b, karm_h, door.floyer)
            else:
                mal = produksjonsmal(door.karm_type, karm_b, karm_h, door.floyer)
            self._populate_table(mal, door.floyer)
        else:
            self._show_missing_table()

    def _show_placeholder(self):
        """Viser placeholder når ingen dør er valgt."""
        self.warning_frame.setVisible(False)
        self.success_frame.setVisible(False)
        self.placeholder_label.setVisible(True)
        self.table_group.setVisible(False)
        self.karm_bredde_label.setText("Bredde: —")
        self.karm_hoyde_label.setText("Høyde: —")

    def _populate_table(self, mal: dict, floyer: int):
        """Fyller tabellen med produksjonsmål."""
        # Format: (komponent, antall, bredde, høyde)
        rows = []

        # Dørblad
        if 'dorblad' in mal:
            d = mal['dorblad']
            rows.append(("Dørblad", d.get('antall', floyer), d['bredde'], d['hoyde']))

        # Terskel
        if 'terskel' in mal:
            t = mal['terskel']
            rows.append(("Terskel", 1, t['lengde'], None))

        # Laminat
        if 'laminat' in mal:
            l = mal['laminat']
            rows.append(("Laminat", l.get('antall', floyer * 2), l['bredde'], l['hoyde']))

        # PD-spesifikke komponenter
        if 'sparkeplate' in mal:
            s = mal['sparkeplate']
            rows.append(("Sparkeplate", s.get('antall', floyer), s['bredde'], None))

        if 'ryggforsterkning' in mal:
            r = mal['ryggforsterkning']
            rows.append(("Ryggforsterkning", r.get('antall', floyer), None, r['hoyde']))

        if 'ryggforst_overdel' in mal:
            ro = mal['ryggforst_overdel']
            rows.append(("Ryggforst. overdel", ro.get('antall', floyer), ro['lengde'], None))

        if 'avviserboyler' in mal:
            a = mal['avviserboyler']
            rows.append(("Avviserbøyler", a.get('antall', floyer), a['lengde'], None))

        # Oppdater tabell
        self.table.setRowCount(len(rows))
        for row_idx, (komponent, antall, bredde, hoyde) in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(komponent))

            # Sentrert antall
            antall_item = QTableWidgetItem(str(antall))
            antall_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, antall_item)

            # Bredde
            bredde_str = f"{bredde} mm" if bredde is not None else "—"
            bredde_item = QTableWidgetItem(bredde_str)
            bredde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 2, bredde_item)

            # Høyde
            hoyde_str = f"{hoyde} mm" if hoyde is not None else "—"
            hoyde_item = QTableWidgetItem(hoyde_str)
            hoyde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 3, hoyde_item)

    def _show_missing_table(self):
        """Viser tom tabell med melding om manglende kalkyler."""
        self.table.setRowCount(1)
        item = QTableWidgetItem("Kalkyler ikke tilgjengelig for denne konfigurasjonen")
        item.setForeground(QColor("#ff9800"))
        self.table.setItem(0, 0, item)
        self.table.setItem(0, 1, QTableWidgetItem(""))
        self.table.setItem(0, 2, QTableWidgetItem(""))
        self.table.setItem(0, 3, QTableWidgetItem(""))
