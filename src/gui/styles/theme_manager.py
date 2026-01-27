"""
Tema-håndtering for KIAS Dørkonfigurator.
Bruker qt-material for moderne Material Design-utseende.
"""
from enum import Enum
from typing import Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet


# Mapping fra intern tema-enum til qt-material temanavn
_THEME_MAP = {
    "dark": "dark_blue.xml",
    "light": "light_blue.xml",
}


class Theme(Enum):
    """Tilgjengelige temaer."""
    DARK = "dark"
    LIGHT = "light"


class ThemeManager:
    """
    Håndterer tema-lasting og bytte for applikasjonen.
    Lagrer brukerens valg i QSettings.
    """

    SETTINGS_KEY = "theme"
    DEFAULT_THEME = Theme.DARK

    def __init__(self):
        self._settings = QSettings("KIASDorkonfigurator", "KIASDorkonfigurator")
        self._current_theme: Theme = self._load_saved_theme()

    def _load_saved_theme(self) -> Theme:
        """Laster lagret tema fra innstillinger."""
        saved = self._settings.value(self.SETTINGS_KEY, self.DEFAULT_THEME.value)
        try:
            return Theme(saved)
        except ValueError:
            return self.DEFAULT_THEME

    def apply_theme(self, app: Optional[QApplication] = None) -> None:
        """
        Anvender gjeldende tema på applikasjonen.

        Args:
            app: QApplication-instans. Hvis None, brukes QApplication.instance()
        """
        if app is None:
            app = QApplication.instance()

        if app is None:
            return

        theme_file = _THEME_MAP[self._current_theme.value]
        apply_stylesheet(app, theme=theme_file)

    def set_theme(self, theme: Theme, app: Optional[QApplication] = None) -> None:
        """
        Setter og anvender nytt tema.

        Args:
            theme: Tema som skal brukes
            app: QApplication-instans
        """
        self._current_theme = theme
        self._settings.setValue(self.SETTINGS_KEY, theme.value)
        self.apply_theme(app)

    def toggle_theme(self, app: Optional[QApplication] = None) -> Theme:
        """
        Bytter mellom dark og light tema.

        Returns:
            Det nye temaet som ble satt
        """
        new_theme = Theme.LIGHT if self._current_theme == Theme.DARK else Theme.DARK
        self.set_theme(new_theme, app)
        return new_theme

    @property
    def current_theme(self) -> Theme:
        """Returnerer gjeldende tema."""
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """Returnerer True hvis dark mode er aktivt."""
        return self._current_theme == Theme.DARK

    @staticmethod
    def is_available() -> bool:
        """Returnerer True hvis tema-biblioteket er tilgjengelig."""
        return True
