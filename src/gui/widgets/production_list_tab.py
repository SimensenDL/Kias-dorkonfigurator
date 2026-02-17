"""
Kappeliste-tab widget – gruppert kappeliste med separat diverse-tabell.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QAbstractItemView, QPushButton,
    QFileDialog, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from ...models.production_list import get_production_list
from ...export.pdf_kappeliste import export_kappeliste_pdf

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
    COL_ORDRE = 5
    COL_MERKNAD = 6

    # Diverse-tabell-kolonner
    DIV_COL_FORKL = 0
    DIV_COL_STK = 1
    DIV_COL_B = 2
    DIV_COL_H = 3
    DIV_COL_FARGE = 4
    DIV_COL_ORDRE = 5
    DIV_COL_MERKNAD = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prod_list = get_production_list()
        self._diverse_merknader: dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Eksportknapp ---
        toolbar = QHBoxLayout()
        self.export_btn = QPushButton("Eksporter kappeliste")
        self.export_btn.setStyleSheet(
            "QPushButton { background-color: #1976D2; color: white;"
            "  padding: 6px 16px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1565C0; }"
            "QPushButton:disabled { background-color: #666666; color: #999999; }"
        )
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_kappeliste_pdf)
        toolbar.addWidget(self.export_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # --- Felles skrollområde for begge tabeller ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Hovedtabell (karm + dørramme) ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "PROFILNAVN", "STK", "MM", "SLAGRETNING", "FARGE", "ORDRE", "MERKNAD"
        ])
        self._setup_table(self.table, stretch_col=self.COL_PROFIL)
        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVisible(False)
        self._content_layout.addWidget(self.table)

        # --- Diverse-header ---
        self.diverse_header = QLabel("  Diverse")
        self.diverse_header.setStyleSheet(_SECTION_HEADER_STYLE)
        self.diverse_header.setVisible(False)
        self._content_layout.addWidget(self.diverse_header)

        # --- Diverse-tabell ---
        self.diverse_table = QTableWidget()
        self.diverse_table.setColumnCount(7)
        self.diverse_table.setHorizontalHeaderLabels([
            "FORKLARING", "STK", "B MM", "H MM", "FARGE", "ORDRE", "MERKNAD"
        ])
        self._setup_table(self.diverse_table, stretch_col=self.DIV_COL_FORKL)
        self.diverse_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.diverse_table.setVisible(False)
        self._content_layout.addWidget(self.diverse_table)

        # --- Tom-tilstand ---
        self.empty_label = QLabel("Ingen dører i listen")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px; color: #888; padding: 40px;")
        self._content_layout.addWidget(self.empty_label)

        self._content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

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
        self._save_diverse_merknader()

        sections = self._prod_list.get_kappeliste_sections()
        diverse_rows = self._prod_list.get_diverse_rows()

        has_data = bool(sections) or bool(diverse_rows)

        self.export_btn.setEnabled(has_data)
        self.empty_label.setVisible(not has_data)

        # --- Hovedtabell ---
        self._refresh_main_table(sections)

        # --- Diverse-tabell ---
        self._refresh_diverse_table(diverse_rows)

        # --- Juster tabellhøyder til innhold (deferred for at Qt skal layoute først) ---
        QTimer.singleShot(0, self._update_table_heights)

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
        self.table.setSpan(row, 0, 1, 7)
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
        self._set_readonly_cell(self.table, row, self.COL_ORDRE, data.get('ordre', ''))

        # Merknad (read-only, fra modellen)
        self._set_readonly_cell(self.table, row, self.COL_MERKNAD,
                                data.get('merknad', ''))

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
        self._set_readonly_cell(self.diverse_table, row, self.DIV_COL_ORDRE,
                                data.get('ordre', ''))

        # Merknad (redigerbar)
        merknad_key = (data['forklaring'], data['b_mm'], data['h_mm'])
        merknad_text = self._diverse_merknader.get(merknad_key, '')
        self.diverse_table.setItem(
            row, self.DIV_COL_MERKNAD, QTableWidgetItem(merknad_text)
        )

    # ------------------------------------------------------------------
    # Hjelpemetoder
    # ------------------------------------------------------------------

    def _update_table_heights(self):
        """Oppdaterer begge tabellers høyde etter at Qt har layoutet."""
        self._resize_table_to_content(self.table)
        self._resize_table_to_content(self.diverse_table)

    @staticmethod
    def _resize_table_to_content(table: QTableWidget):
        """Justerer tabellens høyde til å vise alle rader uten egen skrollbar."""
        if table.rowCount() == 0:
            table.setFixedHeight(0)
            return
        height = table.horizontalHeader().height()
        for row in range(table.rowCount()):
            h = table.rowHeight(row)
            if h < 1:
                h = 30  # fallback hvis Qt ikke har beregnet ennå
            height += h
        height += 2  # ramme
        table.setFixedHeight(height)

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
    # PDF-eksport
    # ------------------------------------------------------------------

    def _export_kappeliste_pdf(self):
        """Eksporterer kappelisten til PDF."""
        self._save_diverse_merknader()

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Eksporter kappeliste",
            "Kappeliste",
            "PDF-filer (*.pdf)"
        )
        if not filepath:
            return

        try:
            export_kappeliste_pdf(
                self._prod_list, filepath,
                diverse_merknader=self._diverse_merknader,
            )
            QMessageBox.information(
                self, "Eksport fullført",
                f"Kappelisten ble eksportert til:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Eksportfeil",
                f"Kunne ikke eksportere kappeliste:\n{e}"
            )

    # ------------------------------------------------------------------
    # Merknad-lagring
    # ------------------------------------------------------------------

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
