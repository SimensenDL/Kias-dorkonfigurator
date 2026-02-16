"""
Dørliste-tab for KIAS Dørkonfigurator.
Viser alle dører i produksjonslisten med mulighet for redigering,
sletting, import og eksport.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...models.production_list import ProductionList, get_production_list
from ...models.door_list_io import save_door_list, load_door_list
from ...utils.constants import DOOR_LIST_FILTER, SWING_DIRECTIONS


class DoorListTab(QWidget):
    """Widget som viser dørlisten med verktøylinje."""

    door_selected = pyqtSignal(str)   # door_id ved dobbeltklikk
    door_deleted = pyqtSignal(str)    # door_id etter sletting
    list_changed = pyqtSignal()       # etter import/tøm

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prod_list: ProductionList = get_production_list()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Verktøylinje ---
        toolbar = QHBoxLayout()

        self.import_btn = QPushButton("Importer...")
        self.import_btn.setStyleSheet("padding: 6px 14px;")
        self.import_btn.clicked.connect(self._import_list)
        toolbar.addWidget(self.import_btn)

        self.export_btn = QPushButton("Eksporter...")
        self.export_btn.setStyleSheet("padding: 6px 14px;")
        self.export_btn.clicked.connect(self._export_list)
        toolbar.addWidget(self.export_btn)

        self.clear_btn = QPushButton("Tøm liste")
        self.clear_btn.setStyleSheet("padding: 6px 14px;")
        self.clear_btn.clicked.connect(self._clear_list)
        toolbar.addWidget(self.clear_btn)

        hint_label = QLabel("Dobbeltklikk på en dør for å forhåndsvise")
        hint_label.setStyleSheet("color: #888888; font-style: italic; padding-left: 12px;")
        toolbar.addWidget(hint_label)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # --- Tabell ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "DØR-ID", "NAVN", "STØRRELSE (BM)", "VEGGTYKKELSE",
            "FARGE", "RETNING", "SLETT"
        ])
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(self.table.columnCount()):
            if col == 2:  # NAVN
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # --- Oppsummering ---
        self.summary_label = QLabel("Antall dører: 0")
        self.summary_label.setStyleSheet("font-size: 13px; padding: 4px;")
        layout.addWidget(self.summary_label)

    # ------------------------------------------------------------------
    # Offentlige metoder
    # ------------------------------------------------------------------

    def select_door(self, door_id: str):
        """Markerer raden til en bestemt dør i tabellen."""
        doors = self._prod_list.doors
        for row, door in enumerate(doors):
            if door.id == door_id:
                self.table.selectRow(row)
                self.table.scrollTo(self.table.model().index(row, 0))
                return

    def refresh(self):
        """Oppdaterer tabellen fra produksjonslisten."""
        doors = self._prod_list.doors
        self.table.setRowCount(len(doors))

        for row, door in enumerate(doors):
            p = door.params

            # #
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, num_item)

            # Dør-ID
            id_item = QTableWidgetItem(p.project_id)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, id_item)

            # Navn
            self.table.setItem(row, 2, QTableWidgetItem(door.label))

            # Størrelse (BM)
            size_str = f"{p.width} x {p.height}"
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, size_item)

            # Veggtykkelse
            thick_item = QTableWidgetItem(f"{p.thickness} mm")
            thick_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, thick_item)

            # Farge
            self.table.setItem(row, 5, QTableWidgetItem(p.color))

            # Retning
            direction = SWING_DIRECTIONS.get(p.swing_direction, p.swing_direction)
            dir_item = QTableWidgetItem(direction)
            dir_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, dir_item)

            # Slett-knapp
            del_btn = QPushButton("Slett")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #d32f2f; }
            """)
            del_btn.clicked.connect(lambda _, did=door.id: self._delete_door(did))
            self.table.setCellWidget(row, 7, del_btn)

        self.summary_label.setText(f"Antall dører: {len(doors)}")

    # ------------------------------------------------------------------
    # Signaler / hendelser
    # ------------------------------------------------------------------

    def _on_double_click(self, index):
        """Håndterer dobbeltklikk – sender door_id til MainWindow."""
        row = index.row()
        doors = self._prod_list.doors
        if 0 <= row < len(doors):
            self.door_selected.emit(doors[row].id)

    def _delete_door(self, door_id: str):
        """Sletter en dør etter bekreftelse."""
        result = QMessageBox.question(
            self,
            "Slett dør",
            "Er du sikker på at du vil fjerne denne døren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            self._prod_list.remove_door(door_id)
            self.refresh()
            self.door_deleted.emit(door_id)

    # ------------------------------------------------------------------
    # Import / eksport / tøm
    # ------------------------------------------------------------------

    def _import_list(self):
        """Importerer dører fra .kdl-fil (adderer til listen)."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importer dørliste", "", DOOR_LIST_FILTER
        )
        if filepath:
            try:
                count = load_door_list(filepath, self._prod_list)
                self.refresh()
                self.list_changed.emit()
                QMessageBox.information(
                    self, "Import fullført",
                    f"{count} dør(er) importert."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Importfeil",
                    f"Kunne ikke importere dørliste:\n{e}"
                )

    def _export_list(self):
        """Eksporterer dørlisten til .kdl-fil."""
        if self._prod_list.door_count == 0:
            QMessageBox.information(
                self, "Tom liste",
                "Det er ingen dører å eksportere."
            )
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Eksporter dørliste", "", DOOR_LIST_FILTER
        )
        if filepath:
            try:
                save_door_list(self._prod_list, filepath)
                QMessageBox.information(
                    self, "Eksport fullført",
                    f"Dørliste eksportert til:\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Eksportfeil",
                    f"Kunne ikke eksportere dørliste:\n{e}"
                )

    def _clear_list(self):
        """Tømmer hele dørlisten etter bekreftelse."""
        if self._prod_list.door_count == 0:
            return

        result = QMessageBox.question(
            self,
            "Tøm dørliste",
            f"Er du sikker på at du vil fjerne alle {self._prod_list.door_count} dører?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            self._prod_list.clear()
            self.refresh()
            self.list_changed.emit()
