"""
Kappeliste-tab widget – gruppert kappeliste med separat diverse-tabell.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ...models.production_list import get_production_list

_SECTION_HEADER_STYLE = (
    "background-color: #FFC107; color: #000000;"
    "font-weight: bold; font-size: 13px; padding: 4px 8px;"
)


class ProductionListTab(QWidget):
    """Widget som viser kappeliste med grupperte seksjoner."""

    list_changed = pyqtSignal()

    # Hovedtabell-kolonner
    COL_PROFIL = 0
    COL_STK = 1
    COL_MM = 2
    COL_SLAG = 3
    COL_FARGE = 4
    COL_MERKNAD = 5

    # Diverse-tabell-kolonner
    DIV_COL_FORKL = 0
    DIV_COL_STK = 1
    DIV_COL_B = 2
    DIV_COL_H = 3
    DIV_COL_FARGE = 4
    DIV_COL_MERKNAD = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prod_list = get_production_list()
        self._merknader: dict = {}
        self._diverse_merknader: dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Hovedtabell (karm + dørramme) ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "PROFILNAVN", "STK", "MM", "SLAGRETNING", "FARGE", "MERKNAD"
        ])
        self._setup_table(self.table, stretch_col=self.COL_PROFIL)
        self.table.setVisible(False)
        layout.addWidget(self.table)

        # --- Diverse-header ---
        self.diverse_header = QLabel("  Diverse")
        self.diverse_header.setStyleSheet(_SECTION_HEADER_STYLE)
        self.diverse_header.setVisible(False)
        layout.addWidget(self.diverse_header)

        # --- Diverse-tabell ---
        self.diverse_table = QTableWidget()
        self.diverse_table.setColumnCount(6)
        self.diverse_table.setHorizontalHeaderLabels([
            "FORKLARING", "STK", "B MM", "H MM", "FARGE", "MERKNAD"
        ])
        self._setup_table(self.diverse_table, stretch_col=self.DIV_COL_FORKL)
        self.diverse_table.setVisible(False)
        layout.addWidget(self.diverse_table)

        # --- Tom-tilstand ---
        self.empty_label = QLabel("Ingen dører i listen")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px; color: #888; padding: 40px;")
        layout.addWidget(self.empty_label)

        # --- Oppsummering ---
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 13px; padding: 4px;")
        layout.addWidget(self.summary_label)

    @staticmethod
    def _setup_table(table: QTableWidget, stretch_col: int):
        """Felles oppsett for begge tabeller."""
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(table.columnCount()):
            if col == stretch_col:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        table.verticalHeader().setVisible(False)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self):
        """Oppdaterer kappelisten fra produksjonslisten."""
        self._save_merknader()
        self._save_diverse_merknader()

        sections = self._prod_list.get_kappeliste_sections()
        diverse_rows = self._prod_list.get_diverse_rows()

        has_data = bool(sections) or bool(diverse_rows)

        self.empty_label.setVisible(not has_data)

        # --- Hovedtabell ---
        self._refresh_main_table(sections)

        # --- Diverse-tabell ---
        self._refresh_diverse_table(diverse_rows)

        # --- Oppsummering ---
        if has_data:
            door_count = self._prod_list.door_count
            self.summary_label.setText(f"Antall dører: {door_count}")
        else:
            self.summary_label.setText("")

    def _refresh_main_table(self, sections):
        """Oppdaterer hovedtabellen (karm + dørramme)."""
        self.table.clearContents()
        self.table.clearSpans()

        if not sections:
            self.table.setRowCount(0)
            self.table.setVisible(False)
            return

        self.table.setVisible(True)
        total_rows = sum(len(s['rows']) + 1 for s in sections)
        self.table.setRowCount(total_rows)

        row = 0
        for section in sections:
            section_title = section['title']
            self._insert_section_header(row, section_title)
            row += 1

            prev_profil = ''
            for data_row in section['rows']:
                show_name = data_row['profilnavn'] != prev_profil
                prev_profil = data_row['profilnavn']
                self._insert_data_row(row, data_row, section_title, show_name)
                row += 1

    def _refresh_diverse_table(self, diverse_rows):
        """Oppdaterer diverse-tabellen."""
        self.diverse_table.clearContents()

        if not diverse_rows:
            self.diverse_header.setVisible(False)
            self.diverse_table.setRowCount(0)
            self.diverse_table.setVisible(False)
            return

        self.diverse_header.setVisible(True)
        self.diverse_table.setVisible(True)
        self.diverse_table.setRowCount(len(diverse_rows))

        prev_forkl = ''
        for i, data_row in enumerate(diverse_rows):
            show_name = data_row['forklaring'] != prev_forkl
            prev_forkl = data_row['forklaring']
            self._insert_diverse_row(i, data_row, show_name)

    # ------------------------------------------------------------------
    # Hovedtabell — rad-rendering
    # ------------------------------------------------------------------

    def _insert_section_header(self, row: int, title: str):
        """Setter inn en seksjon-overskrift som span over alle kolonner."""
        self.table.setSpan(row, 0, 1, 6)
        label = QLabel(f"  {title}")
        label.setStyleSheet(_SECTION_HEADER_STYLE)
        self.table.setCellWidget(row, 0, label)
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.table.setItem(row, 0, item)

    def _insert_data_row(self, row: int, data: dict, section_title: str,
                         show_name: bool = True):
        """Setter inn en datarad i hovedtabellen."""
        profil_text = data['profilnavn'] if show_name else ''
        self._set_readonly_cell(self.table, row, self.COL_PROFIL, profil_text)
        self._set_readonly_cell(self.table, row, self.COL_STK,
                                str(data['stk']), center=True)
        self._set_readonly_cell(self.table, row, self.COL_MM,
                                data['mm'], center=True)
        self._set_readonly_cell(self.table, row, self.COL_SLAG,
                                data['slagretning'], center=True)
        self._set_readonly_cell(self.table, row, self.COL_FARGE, data['farge'])

        # Merknad (redigerbar)
        merknad_key = (section_title, data['profilnavn'], data['mm'])
        merknad_text = self._merknader.get(merknad_key, '')
        self.table.setItem(row, self.COL_MERKNAD, QTableWidgetItem(merknad_text))

    # ------------------------------------------------------------------
    # Diverse-tabell — rad-rendering
    # ------------------------------------------------------------------

    def _insert_diverse_row(self, row: int, data: dict,
                            show_name: bool = True):
        """Setter inn en datarad i diverse-tabellen."""
        forkl_text = data['forklaring'] if show_name else ''
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_FORKL,
                                forkl_text)
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_STK,
                                str(data['stk']), center=True)
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_B,
                                data['b_mm'], center=True)
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_H,
                                data['h_mm'], center=True)
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_FARGE,
                                data['farge'])

        # Merknad (redigerbar)
        merknad_key = (data['forklaring'], data['b_mm'], data['h_mm'])
        merknad_text = self._diverse_merknader.get(merknad_key, '')
        self.diverse_table.setItem(
            row, self.DIV_COL_MERKNAD, QTableWidgetItem(merknad_text)
        )

    # ------------------------------------------------------------------
    # Hjelpemetoder
    # ------------------------------------------------------------------

    @staticmethod
    def _set_readonly_cell(table: QTableWidget, row: int, col: int,
                           text: str, center: bool = False):
        """Setter en ikke-redigerbar celle."""
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, col, item)

    # ------------------------------------------------------------------
    # Merknad-lagring
    # ------------------------------------------------------------------

    def _save_merknader(self):
        """Lagrer merknader fra hovedtabellen."""
        self._merknader.clear()
        current_section = ''
        current_profil = ''

        for row in range(self.table.rowCount()):
            if self.table.columnSpan(row, 0) > 1:
                widget = self.table.cellWidget(row, 0)
                if widget and isinstance(widget, QLabel):
                    current_section = widget.text().strip()
                current_profil = ''
                continue

            profil_item = self.table.item(row, self.COL_PROFIL)
            mm_item = self.table.item(row, self.COL_MM)
            merknad_item = self.table.item(row, self.COL_MERKNAD)

            if profil_item and profil_item.text():
                current_profil = profil_item.text()

            if current_profil and merknad_item and merknad_item.text():
                key = (current_section, current_profil,
                       mm_item.text() if mm_item else '')
                self._merknader[key] = merknad_item.text()

    def _save_diverse_merknader(self):
        """Lagrer merknader fra diverse-tabellen."""
        self._diverse_merknader.clear()
        current_forkl = ''

        for row in range(self.diverse_table.rowCount()):
            forkl_item = self.diverse_table.item(row, self.DIV_COL_FORKL)
            b_item = self.diverse_table.item(row, self.DIV_COL_B)
            h_item = self.diverse_table.item(row, self.DIV_COL_H)
            merknad_item = self.diverse_table.item(row, self.DIV_COL_MERKNAD)

            if forkl_item and forkl_item.text():
                current_forkl = forkl_item.text()

            if current_forkl and merknad_item and merknad_item.text():
                key = (current_forkl,
                       b_item.text() if b_item else '',
                       h_item.text() if h_item else '')
                self._diverse_merknader[key] = merknad_item.text()
