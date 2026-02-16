"""
Kappeliste-tab widget – gruppert kappeliste med redigerbar merknad-kolonne.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ...models.production_list import get_production_list
from ...utils.constants import DEFAULT_COLOR


class ProductionListTab(QWidget):
    """Widget som viser kappeliste med grupperte seksjoner."""

    list_changed = pyqtSignal()

    COL_PROFIL = 0
    COL_STK = 1
    COL_MM = 2
    COL_SLAG = 3
    COL_FARGE = 4
    COL_MERKNAD = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prod_list = get_production_list()
        self._merknader: dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Tabell
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "PROFILNAVN", "STK", "MM", "SLAGRETNING", "FARGE", "MERKNAD"
        ])

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(self.table.columnCount()):
            if col == self.COL_PROFIL:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.verticalHeader().setVisible(False)
        self.table.setVisible(False)
        layout.addWidget(self.table)

        # Tom-tilstand
        self.empty_label = QLabel("Ingen dører i listen")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px; color: #888; padding: 40px;")
        layout.addWidget(self.empty_label)

        # Oppsummering
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 13px; padding: 4px;")
        layout.addWidget(self.summary_label)

    def refresh(self):
        """Oppdaterer kappelisten fra produksjonslisten."""
        self._save_merknader()

        sections = self._prod_list.get_kappeliste_sections()

        if not sections:
            self.table.clearContents()
            self.table.clearSpans()
            self.table.setRowCount(0)
            self.table.setVisible(False)
            self.empty_label.setVisible(True)
            self.summary_label.setText("")
            return

        self.table.setVisible(True)
        self.empty_label.setVisible(False)

        # Rydd opp stale spans/items fra forrige render
        self.table.clearContents()
        self.table.clearSpans()

        # Tell totalt antall rader (datarader + seksjon-headere)
        total_rows = sum(len(s['rows']) + 1 for s in sections)
        self.table.setRowCount(total_rows)

        row = 0
        total_data_rows = 0
        current_section_title = ''

        for section in sections:
            current_section_title = section['title']
            self._insert_section_header(row, section['title'])
            row += 1

            prev_profil = ''
            for data_row in section['rows']:
                # Vis profilnavn kun på første rad i hver komponentgruppe
                show_name = data_row['profilnavn'] != prev_profil
                prev_profil = data_row['profilnavn']
                self._insert_data_row(
                    row, data_row, current_section_title, show_name
                )
                total_data_rows += 1
                row += 1

        door_count = self._prod_list.door_count
        self.summary_label.setText(
            f"Antall dører: {door_count} | Antall rader: {total_data_rows}"
        )

    def _insert_section_header(self, row: int, title: str):
        """Setter inn en seksjon-overskrift som span over alle kolonner."""
        self.table.setSpan(row, 0, 1, 6)
        # Bruk QLabel-widget for å tvinge farger (qt-material overstyrer item-farger)
        label = QLabel(f"  {title}")
        label.setStyleSheet(
            "background-color: #FFC107; color: #000000;"
            "font-weight: bold; font-size: 13px; padding: 4px 8px;"
        )
        self.table.setCellWidget(row, 0, label)
        # Sett tom item for å blokkere redigering/seleksjon
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.table.setItem(row, 0, item)

    def _insert_data_row(self, row: int, data: dict, section_title: str,
                         show_name: bool = True):
        """Setter inn en datarad med redigerbar merknad."""
        # Profilnavn — kun på første rad i komponentgruppen
        profil_text = data['profilnavn'] if show_name else ''
        profil_item = QTableWidgetItem(profil_text)
        profil_item.setFlags(profil_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_PROFIL, profil_item)

        # STK
        stk_item = QTableWidgetItem(str(data['stk']))
        stk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        stk_item.setFlags(stk_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_STK, stk_item)

        # MM
        mm_item = QTableWidgetItem(data['mm'])
        mm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        mm_item.setFlags(mm_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_MM, mm_item)

        # Slagretning
        slag_item = QTableWidgetItem(data['slagretning'])
        slag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        slag_item.setFlags(slag_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_SLAG, slag_item)

        # Farge — skjul standardfarge (RAL 9010)
        farge_text = data['farge'] if data['farge'] != DEFAULT_COLOR else ''
        farge_item = QTableWidgetItem(farge_text)
        farge_item.setFlags(farge_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_FARGE, farge_item)

        # Merknad (redigerbar — dobbeltklikk for å skrive)
        merknad_key = (section_title, data['profilnavn'], data['mm'])
        merknad_text = self._merknader.get(merknad_key, '')
        merknad_item = QTableWidgetItem(merknad_text)
        self.table.setItem(row, self.COL_MERKNAD, merknad_item)

    def _save_merknader(self):
        """Lagrer merknader fra tabellen til intern dict."""
        self._merknader.clear()
        current_section = ''
        current_profil = ''

        for row in range(self.table.rowCount()):
            # Seksjon-header (span > 1)
            if self.table.columnSpan(row, 0) > 1:
                widget = self.table.cellWidget(row, 0)
                if widget and isinstance(widget, QLabel):
                    current_section = widget.text().strip()
                current_profil = ''
                continue

            profil_item = self.table.item(row, self.COL_PROFIL)
            mm_item = self.table.item(row, self.COL_MM)
            merknad_item = self.table.item(row, self.COL_MERKNAD)

            # Profilnavn vises kun på første rad — bruk sist kjente navn
            if profil_item and profil_item.text():
                current_profil = profil_item.text()

            if current_profil and merknad_item and merknad_item.text():
                key = (current_section, current_profil,
                       mm_item.text() if mm_item else '')
                self._merknader[key] = merknad_item.text()
