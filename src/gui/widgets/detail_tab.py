"""
Detaljer-tab widget – viser spesielle egenskaper og utregninger.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel
)
from PyQt6.QtCore import Qt

from ...models.door import DoorParams
from ...utils.calculations import (
    karm_bredde, karm_hoyde,
    dorblad_bredde, dorblad_hoyde,
    terskel_lengde, laminat_mal,
    dekklist_lengde
)


class DetailTab(QWidget):
    """Widget som viser spesielle egenskaper og beregnede produksjonsmål."""

    _LABEL_MIN_WIDTH = 110

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    # ── Hjelpemetoder for oppbygging ──────────────────────────────

    def _make_label(self, text: str) -> QLabel:
        """Lager en form-label med dempet stil."""
        lbl = QLabel(text)
        lbl.setProperty("class", "detail-label")
        lbl.setMinimumWidth(self._LABEL_MIN_WIDTH)
        return lbl

    def _make_value(self) -> QLabel:
        """Lager en verdi-label med fremhevet stil."""
        val = QLabel("—")
        val.setProperty("class", "detail-value")
        val.setTextFormat(Qt.TextFormat.RichText)
        return val

    @staticmethod
    def _fmt(value, unit: str = "mm") -> str:
        """Formaterer en verdi med dempet enhet."""
        if value is None:
            return "—"
        return (
            f"{value}"
            f" <span style='color:gray; font-weight:normal; font-size:11px'>"
            f"{unit}</span>"
        )

    @staticmethod
    def _make_form_layout(parent: QGroupBox) -> QFormLayout:
        """Lager et QFormLayout med konsistent spacing og padding."""
        fl = QFormLayout(parent)
        fl.setContentsMargins(16, 8, 16, 12)
        fl.setVerticalSpacing(8)
        fl.setHorizontalSpacing(20)
        return fl

    # ── UI-oppbygging ─────────────────────────────────────────────

    def _init_ui(self):
        """Bygger opp layouten."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- Felles (karm, terskel, dekklist) ---
        self.felles_group = QGroupBox("Felles")
        felles_layout = self._make_form_layout(self.felles_group)

        self.val_karm_b = self._make_value()
        self.val_karm_h = self._make_value()
        self.val_terskel = self._make_value()
        self.lbl_dekklist = self._make_label("Dekklist:")
        self.val_dekklist = self._make_value()

        felles_layout.addRow(self._make_label("Utv.karm B:"), self.val_karm_b)
        felles_layout.addRow(self._make_label("Utv.karm H:"), self.val_karm_h)
        felles_layout.addRow(self._make_label("Terskel:"), self.val_terskel)
        felles_layout.addRow(self.lbl_dekklist, self.val_dekklist)

        layout.addWidget(self.felles_group)

        # --- Dørblad 1 (eller bare "Dørblad" ved 1-fløyet) ---
        self.blade1_group = QGroupBox("Dørblad")
        blade1_layout = self._make_form_layout(self.blade1_group)

        self.val_dorblad1_b = self._make_value()
        self.val_dorblad1_h = self._make_value()
        self.val_laminat1_b = self._make_value()
        self.val_laminat1_h = self._make_value()

        blade1_layout.addRow(self._make_label("Dørblad B:"), self.val_dorblad1_b)
        blade1_layout.addRow(self._make_label("Dørblad H:"), self.val_dorblad1_h)
        blade1_layout.addRow(self._make_label("Laminat B:"), self.val_laminat1_b)
        blade1_layout.addRow(self._make_label("Laminat H:"), self.val_laminat1_h)

        layout.addWidget(self.blade1_group)

        # --- Dørblad 2 (kun synlig ved 2-fløyet) ---
        self.blade2_group = QGroupBox("Dørblad 2")
        blade2_layout = self._make_form_layout(self.blade2_group)

        self.val_dorblad2_b = self._make_value()
        self.val_dorblad2_h = self._make_value()
        self.val_laminat2_b = self._make_value()
        self.val_laminat2_h = self._make_value()

        blade2_layout.addRow(self._make_label("Dørblad B:"), self.val_dorblad2_b)
        blade2_layout.addRow(self._make_label("Dørblad H:"), self.val_dorblad2_h)
        blade2_layout.addRow(self._make_label("Laminat B:"), self.val_laminat2_b)
        blade2_layout.addRow(self._make_label("Laminat H:"), self.val_laminat2_h)

        layout.addWidget(self.blade2_group)

        layout.addStretch()

    # ── Oppdatering ───────────────────────────────────────────────

    def update_door(self, door: DoorParams):
        """Oppdaterer visningen med verdier fra DoorParams."""
        fmt = self._fmt

        # --- Felles utregninger ---
        karm_type = door.karm_type
        blade_type = door.blade_type
        floyer = door.floyer
        luftspalte = door.effective_luftspalte()
        is_2floyet = floyer == 2

        karm_b = karm_bredde(karm_type, door.width)
        karm_h = karm_hoyde(karm_type, door.height)
        self.val_karm_b.setText(fmt(karm_b))
        self.val_karm_h.setText(fmt(karm_h))

        terskel = terskel_lengde(karm_type, karm_b, floyer)
        self.val_terskel.setText(fmt(terskel) if terskel else "—")

        # Dekklist kun synlig ved 2-fløyet
        self.lbl_dekklist.setVisible(is_2floyet)
        self.val_dekklist.setVisible(is_2floyet)
        if is_2floyet:
            self.val_dekklist.setText(fmt(dekklist_lengde(karm_h)))

        # --- Dørblad-beregninger ---
        db_b_total = dorblad_bredde(karm_type, karm_b, floyer, blade_type)
        db_h = dorblad_hoyde(karm_type, karm_h, floyer, blade_type, luftspalte)

        if is_2floyet:
            # Prosentvis oppdeling
            self.blade1_group.setTitle("Dørblad 1")
            self.blade2_group.setVisible(True)

            if db_b_total:
                split_pct = door.floyer_split / 100.0
                db1_b = round(db_b_total * split_pct)
                db2_b = db_b_total - db1_b

                self.val_dorblad1_b.setText(fmt(db1_b))
                self.val_dorblad2_b.setText(fmt(db2_b))
            else:
                db1_b = None
                db2_b = None
                self.val_dorblad1_b.setText("—")
                self.val_dorblad2_b.setText("—")

            self.val_dorblad1_h.setText(fmt(db_h) if db_h else "—")
            self.val_dorblad2_h.setText(fmt(db_h) if db_h else "—")

            # Laminat per fløy
            if db1_b and db_h:
                lam1_b, lam1_h = laminat_mal(karm_type, db1_b, db_h, blade_type)
                self.val_laminat1_b.setText(fmt(lam1_b))
                self.val_laminat1_h.setText(fmt(lam1_h))
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")

            if db2_b and db_h:
                lam2_b, lam2_h = laminat_mal(karm_type, db2_b, db_h, blade_type)
                self.val_laminat2_b.setText(fmt(lam2_b))
                self.val_laminat2_h.setText(fmt(lam2_h))
            else:
                self.val_laminat2_b.setText("—")
                self.val_laminat2_h.setText("—")
        else:
            # 1-fløyet: én gruppe
            self.blade1_group.setTitle("Dørblad")
            self.blade2_group.setVisible(False)

            db_b = db_b_total
            self.val_dorblad1_b.setText(fmt(db_b) if db_b else "—")
            self.val_dorblad1_h.setText(fmt(db_h) if db_h else "—")

            if db_b and db_h:
                lam_b, lam_h = laminat_mal(karm_type, db_b, db_h, blade_type)
                self.val_laminat1_b.setText(fmt(lam_b))
                self.val_laminat1_h.setText(fmt(lam_h))
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")
