"""
Kappeliste-tab widget – plassholder.
Bygges ut med gruppert kappeliste og eksport senere.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class ProductionListTab(QWidget):
    """Plassholder-widget for kappeliste."""

    list_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Kappeliste")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #888;")
        layout.addWidget(label)

    def refresh(self):
        """Oppdaterer visningen (no-op)."""
        pass
