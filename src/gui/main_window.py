"""
Hovedvindu for KIAS Dørkonfigurator.
"""
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QProgressBar, QPushButton, QSplitter, QGroupBox,
    QTabWidget, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon

try:
    import qtawesome as qta
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False

from ..models.door import DoorParams
from ..models.project import save_project, load_project, new_project, PROJECT_EXTENSION
from ..models.production_list import get_production_list
from ..export.pdf_exporter import export_door_pdf
from ..utils.constants import APP_NAME, APP_VERSION, PROJECT_FILTER, DOOR_TYPES

from .widgets.door_form import DoorForm
from .widgets.door_preview_3d import DoorPreview3D
from .widgets import graphics_settings as gfx
from .widgets.door_list_tab import DoorListTab
from .widgets.production_list_tab import ProductionListTab
from .widgets.detail_tab import DetailTab
from .styles import ThemeManager, Theme


class MainWindow(QMainWindow):
    """Hovedvindu for KIAS Dørkonfigurator."""

    theme_manager: ThemeManager = None

    def __init__(self):
        super().__init__()

        self.door: DoorParams = new_project()
        self.current_file: Optional[Path] = None
        self.unsaved_changes: bool = False
        self._editing_door_id: Optional[str] = None
        self._prod_list = get_production_list()

        self._init_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        self._load_settings()
        self._update_title()
        self._update_theme_menu()
        self._apply_accent_colors()

    def _init_ui(self):
        """Initialiserer brukergrensesnittet."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # Venstre panel: Dørparametere (scrollbart)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.door_form = DoorForm()
        self.door_form.values_changed.connect(self._on_params_changed)
        scroll.setWidget(self.door_form)
        left_layout.addWidget(scroll)

        # Knapperad: Generer PDF + Legg til dør
        btn_row = QHBoxLayout()

        self.generate_btn = QPushButton("Generer PDF")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        self.generate_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(self.generate_btn)

        self.add_door_btn = QPushButton("Legg til dør")
        self.add_door_btn.setMinimumHeight(50)
        self._apply_add_door_style()
        self.add_door_btn.clicked.connect(self._on_add_or_update_door)
        btn_row.addWidget(self.add_door_btn)

        left_layout.addLayout(btn_row)

        # Avbryt-knapp (skjult til redigeringsmodus)
        self.cancel_edit_btn = QPushButton("Avbryt")
        self.cancel_edit_btn.setMinimumHeight(36)
        self.cancel_edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        self.cancel_edit_btn.clicked.connect(self._cancel_edit)
        self.cancel_edit_btn.setVisible(False)
        left_layout.addWidget(self.cancel_edit_btn)

        # Fremdriftslinje
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        # Høyre panel: Tabs med forhåndsvisning
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.tab_widget = QTabWidget()
        self.tab_widget.setIconSize(QSize(24, 24))

        # Tab 1: 3D-forhåndsvisning
        self.door_preview = DoorPreview3D()
        self.door_preview.update_door(self.door)
        preview_widget = self.door_preview
        self.tab_widget.addTab(preview_widget, "Forhåndsvisning")

        # Tab 2: Dørliste
        self.door_list_tab = DoorListTab()
        self.door_list_tab.door_selected.connect(self._on_door_selected)
        self.door_list_tab.door_deleted.connect(self._on_door_deleted)
        self.door_list_tab.list_changed.connect(self._on_door_list_changed)
        self.tab_widget.addTab(self.door_list_tab, "Dørliste")

        # Tab 3: Kappeliste (plassholder)
        self.production_list_tab = ProductionListTab()
        self.tab_widget.addTab(self.production_list_tab, "Kappeliste")

        # Tab 4: Detaljer
        self.detail_tab = DetailTab()
        self.door_form.update_door(self.door)
        self.detail_tab.update_door(self.door)
        self.tab_widget.addTab(self.detail_tab, "Detaljer")

        right_layout.addWidget(self.tab_widget)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([380, 620])

        main_layout.addWidget(splitter)

    def _create_menus(self):
        """Oppretter menylinje."""
        menubar = self.menuBar()

        # Fil-meny
        file_menu = menubar.addMenu("&Fil")

        new_action = QAction("&Nytt prosjekt", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Åpne...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Lagre", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Lagre &som...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("&Avslutt", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Eksporter-meny
        export_menu = menubar.addMenu("&Eksporter")

        pdf_action = QAction("&PDF-tegning...", self)
        pdf_action.triggered.connect(self._export_pdf)
        export_menu.addAction(pdf_action)

        # Innstillinger-meny
        settings_menu = menubar.addMenu("&Innstillinger")

        theme_menu = settings_menu.addMenu("Tema")

        self.dark_theme_action = QAction("Mørk modus", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme(Theme.DARK))
        theme_menu.addAction(self.dark_theme_action)

        self.dark_yellow_theme_action = QAction("Mørk gul (KIAS)", self)
        self.dark_yellow_theme_action.setCheckable(True)
        self.dark_yellow_theme_action.triggered.connect(lambda: self._set_theme(Theme.DARK_YELLOW))
        theme_menu.addAction(self.dark_yellow_theme_action)

        self.light_theme_action = QAction("Lys modus", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme(Theme.LIGHT))
        theme_menu.addAction(self.light_theme_action)

        # Grafikk-undermeny
        graphics_menu = settings_menu.addMenu("Grafikk")
        self._graphics_actions = {}
        for key, label in gfx.PRESET_LABELS.items():
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, k=key: self._set_graphics_preset(k))
            graphics_menu.addAction(action)
            self._graphics_actions[key] = action
        self._update_graphics_menu()

        # Hjelp-meny
        help_menu = menubar.addMenu("&Hjelp")

        about_action = QAction("&Om...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Oppretter verktøylinjen."""
        toolbar = QToolBar("Hovedverktøy")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction("Nytt", self._new_project)
        toolbar.addAction("Åpne", self._open_project)
        toolbar.addAction("Lagre", self._save_project)
        toolbar.addSeparator()
        toolbar.addAction("Eksporter PDF", self._export_pdf)

    def _create_statusbar(self):
        """Oppretter statuslinje."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Klar")

    def _on_params_changed(self):
        """Håndterer endringer i dørparametere."""
        self.door_form.update_door(self.door)
        self.unsaved_changes = True
        self._update_title()
        self.door_preview.update_door(self.door)
        self.detail_tab.update_door(self.door)

    # ------------------------------------------------------------------
    # Dørliste-logikk
    # ------------------------------------------------------------------

    def _apply_add_door_style(self):
        """Setter aksentfarge for 'Legg til dør'-knappen."""
        accent = "#FFC107"
        if MainWindow.theme_manager:
            accent = MainWindow.theme_manager.accent_button_color
        text_color = "black" if MainWindow.theme_manager and MainWindow.theme_manager.current_theme == Theme.DARK_YELLOW else "white"
        self.add_door_btn.setText("Legg til dør")
        self.add_door_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: {text_color};
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:pressed {{ opacity: 0.7; }}
        """)

    def _apply_update_door_style(self):
        """Setter oransje stil for 'Oppdater dør'-knappen."""
        self.add_door_btn.setText("Oppdater dør")
        self.add_door_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:pressed { background-color: #EF6C00; }
        """)

    def _on_add_or_update_door(self):
        """Håndterer klikk på 'Legg til dør' / 'Oppdater dør'."""
        self.door_form.update_door(self.door)

        if self._editing_door_id:
            # Oppdater eksisterende dør
            params_copy = DoorParams.from_dict(self.door.to_dict())
            self._prod_list.update_door(self._editing_door_id, params_copy)
            self.door_list_tab.refresh()
            self.statusbar.showMessage("Dør oppdatert i dørlisten")
            self._exit_edit_mode()
        else:
            # Legg til ny dør (klon av gjeldende parametere)
            params_copy = DoorParams.from_dict(self.door.to_dict())
            self._prod_list.add_door(params_copy)
            self.door_list_tab.refresh()
            self.statusbar.showMessage("Dør lagt til i dørlisten")
            # Bytt til Dørliste-tab
            self.tab_widget.setCurrentWidget(self.door_list_tab)

    def _on_door_selected(self, door_id: str):
        """Dobbeltklikk i dørlisten — last inn og aktiver redigeringsmodus."""
        door = self._prod_list.get_door(door_id)
        if not door:
            return

        self._editing_door_id = door_id

        # Last dørens parametere inn i skjemaet
        self.door = DoorParams.from_dict(door.params.to_dict())
        self.door_form.load_door(self.door)
        self.door_form.update_door(self.door)
        self.door_preview.update_door(self.door)
        self.detail_tab.update_door(self.door)

        # Bytt til redigeringsmodus
        self._apply_update_door_style()
        self.cancel_edit_btn.setVisible(True)
        self.statusbar.showMessage(f"Redigerer dør: {door.label}")

    def _on_door_deleted(self, door_id: str):
        """Dør slettet fra listen — avbryt redigering hvis det var denne."""
        if self._editing_door_id == door_id:
            self._exit_edit_mode()
        self.statusbar.showMessage("Dør fjernet fra dørlisten")

    def _on_door_list_changed(self):
        """Dørlisten er endret (import/tøm)."""
        if self._editing_door_id:
            # Sjekk om døren vi redigerer fortsatt finnes
            if not self._prod_list.get_door(self._editing_door_id):
                self._exit_edit_mode()

    def _cancel_edit(self):
        """Avbryter redigeringsmodus."""
        self._exit_edit_mode()
        self.statusbar.showMessage("Redigering avbrutt")

    def _exit_edit_mode(self):
        """Går tilbake til normal modus."""
        self._editing_door_id = None
        self._apply_add_door_style()
        self.cancel_edit_btn.setVisible(False)

    def _update_title(self):
        """Oppdaterer vindustittel."""
        title = f"{APP_NAME} v{APP_VERSION}"
        if self.current_file:
            title += f" - {self.current_file.name}"
        else:
            title += " - Nytt prosjekt"
        if self.unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def _new_project(self):
        """Oppretter nytt prosjekt."""
        if self.unsaved_changes:
            if not self._confirm_discard():
                return

        self.door = new_project()
        self.current_file = None
        self.unsaved_changes = False
        self.door_form.load_door(self.door)
        self.door_form.update_door(self.door)
        self.door_preview.update_door(self.door)
        self.detail_tab.update_door(self.door)
        self._exit_edit_mode()
        self._update_title()
        self.statusbar.showMessage("Nytt prosjekt opprettet")

    def _open_project(self):
        """Åpner eksisterende prosjekt."""
        if self.unsaved_changes:
            if not self._confirm_discard():
                return

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Åpne prosjekt", "", PROJECT_FILTER
        )

        if filepath:
            try:
                self.door = load_project(Path(filepath))
                self.current_file = Path(filepath)
                self.unsaved_changes = False
                self.door_form.load_door(self.door)
                self.door_form.update_door(self.door)
                self.door_preview.update_door(self.door)
                self.detail_tab.update_door(self.door)
                self._exit_edit_mode()
                self._update_title()
                self.statusbar.showMessage(f"Åpnet: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Feil", f"Kunne ikke åpne fil:\n{e}")

    def open_project_file(self, filepath: str):
        """Åpner prosjekt fra angitt filsti (f.eks. dobbeltklikk på .kdf-fil)."""
        if self.unsaved_changes:
            if not self._confirm_discard():
                return

        try:
            self.door = load_project(Path(filepath))
            self.current_file = Path(filepath)
            self.unsaved_changes = False
            self.door_form.load_door(self.door)
            self.door_form.update_door(self.door)
            self.door_preview.update_door(self.door)
            self.detail_tab.update_door(self.door)
            self._exit_edit_mode()
            self._update_title()
            self.statusbar.showMessage(f"Åpnet: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke åpne fil:\n{e}")

    def _save_project(self):
        """Lagrer gjeldende prosjekt."""
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._save_project_as()

    def _save_project_as(self):
        """Lagrer prosjekt med nytt navn."""
        suggested = self._generate_filename()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Lagre prosjekt", suggested, PROJECT_FILTER
        )
        if filepath:
            self._do_save(Path(filepath))

    def _generate_filename(self) -> str:
        """Genererer foreslått filnavn."""
        parts = []
        door_type_name = DOOR_TYPES.get(self.door.door_type, "Dør")
        parts.append(door_type_name)
        parts.append(f"{self.door.width}x{self.door.height}")
        if self.door.customer:
            parts.append(self.door.customer)
        if self.door.project_id:
            parts.append(self.door.project_id)
        return " - ".join(parts)

    def _do_save(self, filepath: Path):
        """Utfører selve lagringen."""
        try:
            self.door_form.update_door(self.door)
            save_project(self.door, filepath)
            self.current_file = filepath if str(filepath).endswith(PROJECT_EXTENSION) else Path(str(filepath) + PROJECT_EXTENSION)
            self.unsaved_changes = False
            self._update_title()
            self.statusbar.showMessage(f"Lagret: {self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke lagre:\n{e}")

    def _confirm_discard(self) -> bool:
        """Spør bruker om å bekrefte forkasting av ulagrede endringer."""
        result = QMessageBox.question(
            self,
            "Ulagrede endringer",
            "Du har ulagrede endringer. Vil du forkaste dem?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return result == QMessageBox.StandardButton.Yes

    def _export_pdf(self):
        """Eksporterer PDF-tegning."""
        suggested = self._generate_filename()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Eksporter PDF-tegning", suggested, "PDF filer (*.pdf)"
        )

        if filepath:
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.statusbar.showMessage("Genererer PDF...")
                QApplication.processEvents()

                self.door_form.update_door(self.door)
                self.progress_bar.setValue(30)

                export_door_pdf(self.door, Path(filepath))
                self.progress_bar.setValue(100)

                self.statusbar.showMessage(f"PDF eksportert: {filepath}")
                QMessageBox.information(
                    self,
                    "PDF-eksport fullført",
                    f"PDF-tegning eksportert til:\n{filepath}\n\n"
                    "Innhold:\n"
                    "- Frontvisning med mål"
                )
            except Exception as e:
                QMessageBox.critical(self, "Feil", f"PDF-eksport feilet:\n{e}")
            finally:
                self.progress_bar.setVisible(False)

    def _show_about(self):
        """Viser om-dialog."""
        QMessageBox.about(
            self,
            f"Om {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Konfigurasjonsverktøy for KIAS-dører.\n\n"
            "Kvanne Industrier AS\n"
            "Genererer produksjonstegninger og kapplister."
        )

    def _set_theme(self, theme: Theme):
        """Setter nytt tema."""
        if MainWindow.theme_manager:
            MainWindow.theme_manager.set_theme(theme)
            self._update_theme_menu()
            self._apply_accent_colors()

    def _apply_accent_colors(self):
        """Oppdaterer alle tema-avhengige aksentfarger."""
        if not MainWindow.theme_manager:
            return

        accent = MainWindow.theme_manager.accent_color
        btn_accent = MainWindow.theme_manager.accent_button_color

        # Tab-ikoner
        if HAS_ICONS:
            tab_icons = [
                (0, 'fa5s.eye'),
                (1, 'fa5s.list'),
                (2, 'fa5s.clipboard-list'),
                (3, 'fa5s.info-circle'),
            ]
            for idx, icon_name in tab_icons:
                self.tab_widget.setTabIcon(idx, qta.icon(icon_name, color=accent))

        # Tab-underline og styling
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #444;
                border-radius: 4px;
            }}
            QTabBar::tab {{
                min-width: 140px;
                min-height: 40px;
                padding: 8px 16px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                border-bottom: 3px solid {accent};
            }}
        """)

        # Info-labels i skjemaet
        self.door_form.update_accent_color(accent)

        # "Legg til dør"-knapp (bare hvis ikke i redigeringsmodus)
        text_color = "black" if MainWindow.theme_manager.current_theme == Theme.DARK_YELLOW else "white"
        if not self._editing_door_id:
            self.add_door_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_accent};
                    color: {text_color};
                    font-size: 15px;
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 8px;
                }}
                QPushButton:hover {{ background-color: {btn_accent}; opacity: 0.85; }}
                QPushButton:pressed {{ background-color: {btn_accent}; opacity: 0.7; }}
            """)

    def _update_theme_menu(self):
        """Oppdaterer avkrysning i tema-menyen."""
        if MainWindow.theme_manager:
            current = MainWindow.theme_manager.current_theme
            self.dark_theme_action.setChecked(current == Theme.DARK)
            self.dark_yellow_theme_action.setChecked(current == Theme.DARK_YELLOW)
            self.light_theme_action.setChecked(current == Theme.LIGHT)

    def _set_graphics_preset(self, preset_key: str):
        """Bytter grafikkpreset og rebuilder 3D-scenen."""
        old_msaa = gfx.MSAA_SAMPLES
        gfx.apply_preset(preset_key)
        self._update_graphics_menu()
        self.door_preview.update_door(self.door)
        if gfx.MSAA_SAMPLES != old_msaa:
            QMessageBox.information(
                self, "Grafikk",
                f"Grafikkvalitet satt til {gfx.PRESET_LABELS[preset_key]}.\n\n"
                "Anti-aliasing (MSAA) krever omstart for å tre i kraft."
            )

    def _update_graphics_menu(self):
        """Oppdaterer avkrysning i grafikk-menyen."""
        for key, action in self._graphics_actions.items():
            action.setChecked(key == gfx.current_preset)

    def _load_settings(self):
        """Laster applikasjonsinnstillinger."""
        settings = QSettings("KIASDorkonfigurator", APP_NAME)
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _save_settings(self):
        """Lagrer applikasjonsinnstillinger."""
        settings = QSettings("KIASDorkonfigurator", APP_NAME)
        settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        """Håndterer vinduslukking."""
        if self.unsaved_changes:
            if not self._confirm_discard():
                event.ignore()
                return

        self._save_settings()
        event.accept()


def run_app():
    """Applikasjonens inngangspunkt."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Initialiser tema-manager og anvend tema
    MainWindow.theme_manager = ThemeManager()
    if ThemeManager.is_available():
        MainWindow.theme_manager.apply_theme(app)
    else:
        app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    # Åpne fil fra kommandolinje
    if len(sys.argv) > 1:
        filepath = Path(sys.argv[1])
        if filepath.suffix.lower() == '.kdf' and filepath.exists():
            window.open_project_file(str(filepath))

    sys.exit(app.exec())
