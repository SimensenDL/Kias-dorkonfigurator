"""
Frittstående tema-forhåndsvisning for qt-material.
Kjør: uv run python scripts/theme_preview.py
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QPushButton, QLineEdit, QCheckBox,
    QRadioButton, QSlider, QProgressBar, QSpinBox, QGroupBox,
    QTabWidget, QTextEdit, QListWidget,
)
from PyQt6.QtCore import Qt
from qt_material import apply_stylesheet, list_themes


class ThemePreview(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qt-material Tema-forhåndsvisning")
        self.setMinimumSize(700, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Sorter temaer i dark og light
        all_themes = list_themes()
        dark_themes = [t for t in all_themes if t.startswith("dark_")]
        light_themes = [t for t in all_themes if t.startswith("light_")]

        # Tema-velgere
        top = QHBoxLayout()
        top.addWidget(QLabel("Dark:"))
        self.dark_combo = QComboBox()
        self.dark_combo.addItems(dark_themes)
        self.dark_combo.setCurrentText("dark_blue.xml")
        self.dark_combo.currentTextChanged.connect(self._on_dark_selected)
        top.addWidget(self.dark_combo, 1)

        top.addWidget(QLabel("Light:"))
        self.light_combo = QComboBox()
        self.light_combo.addItems(light_themes)
        self.light_combo.currentTextChanged.connect(self._on_light_selected)
        top.addWidget(self.light_combo, 1)
        main_layout.addLayout(top)

        # Tabs med eksempel-widgets
        tabs = QTabWidget()
        tabs.addTab(self._create_buttons_tab(), "Knapper")
        tabs.addTab(self._create_inputs_tab(), "Inputfelter")
        tabs.addTab(self._create_lists_tab(), "Lister og tekst")
        main_layout.addWidget(tabs)

        self._apply_theme(self.dark_combo.currentText())

    def _on_dark_selected(self, theme_name: str):
        self.light_combo.blockSignals(True)
        self.light_combo.setCurrentIndex(-1)
        self.light_combo.blockSignals(False)
        self._apply_theme(theme_name)

    def _on_light_selected(self, theme_name: str):
        self.dark_combo.blockSignals(True)
        self.dark_combo.setCurrentIndex(-1)
        self.dark_combo.blockSignals(False)
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str):
        apply_stylesheet(QApplication.instance(), theme=theme_name)
        self.setWindowTitle(f"qt-material — {theme_name}")

    def _create_buttons_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        grp = QGroupBox("Knapper")
        gl = QVBoxLayout(grp)
        row1 = QHBoxLayout()
        row1.addWidget(QPushButton("Standard"))
        flat = QPushButton("Flat")
        flat.setFlat(True)
        row1.addWidget(flat)
        disabled = QPushButton("Deaktivert")
        disabled.setEnabled(False)
        row1.addWidget(disabled)
        gl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QCheckBox("Avkrysning 1"))
        cb = QCheckBox("Avkrysning 2")
        cb.setChecked(True)
        row2.addWidget(cb)
        row2.addWidget(QRadioButton("Radio A"))
        rb = QRadioButton("Radio B")
        rb.setChecked(True)
        row2.addWidget(rb)
        gl.addLayout(row2)
        layout.addWidget(grp)

        grp2 = QGroupBox("Slider og progresjon")
        gl2 = QVBoxLayout(grp2)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(60)
        gl2.addWidget(slider)
        prog = QProgressBar()
        prog.setValue(75)
        gl2.addWidget(prog)
        layout.addWidget(grp2)

        layout.addStretch()
        return w

    def _create_inputs_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        grp = QGroupBox("Tekstfelter")
        gl = QVBoxLayout(grp)
        gl.addWidget(QLabel("Navn:"))
        gl.addWidget(QLineEdit("Eksempeltekst"))
        gl.addWidget(QLabel("Beskrivelse:"))
        disabled_input = QLineEdit("Deaktivert felt")
        disabled_input.setEnabled(False)
        gl.addWidget(disabled_input)
        layout.addWidget(grp)

        grp2 = QGroupBox("Tallverdier")
        gl2 = QHBoxLayout(grp2)
        gl2.addWidget(QLabel("Bredde (mm):"))
        spin = QSpinBox()
        spin.setRange(0, 5000)
        spin.setValue(900)
        gl2.addWidget(spin)
        gl2.addWidget(QLabel("Høyde (mm):"))
        spin2 = QSpinBox()
        spin2.setRange(0, 5000)
        spin2.setValue(2100)
        gl2.addWidget(spin2)
        layout.addWidget(grp2)

        grp3 = QGroupBox("Nedtrekksliste")
        gl3 = QVBoxLayout(grp3)
        combo = QComboBox()
        combo.addItems(["Innerdør", "Kjøleromsdør", "Branndør", "Skyvedør"])
        gl3.addWidget(combo)
        layout.addWidget(grp3)

        layout.addStretch()
        return w

    def _create_lists_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)

        grp = QGroupBox("Liste")
        gl = QVBoxLayout(grp)
        lst = QListWidget()
        lst.addItems(["SD1 — Listverk begge sider", "SD2 — Listverk framside",
                       "SD3/ID — Smygmontasje", "Terskel — Flat", "Terskel — Nedfelt"])
        gl.addWidget(lst)
        layout.addWidget(grp)

        grp2 = QGroupBox("Tekstområde")
        gl2 = QVBoxLayout(grp2)
        te = QTextEdit()
        te.setPlainText("Dette er et eksempel på et tekstområde.\n"
                        "Her kan man skrive lengre tekster.\n\n"
                        "Brukes for merknader, kommentarer osv.")
        gl2.addWidget(te)
        layout.addWidget(grp2)

        return w


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThemePreview()
    window.show()
    sys.exit(app.exec())
