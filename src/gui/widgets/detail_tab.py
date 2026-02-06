"""
Detaljer-tab widget – viser spesielle egenskaper og utregninger.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel
)
from PyQt6.QtCore import Qt

from ...models.door import DoorParams
from ...utils.constants import BRUTT_KULDEBRO_KARM, BRUTT_KULDEBRO_DORRAMME, DOOR_U_VALUES
from ...utils.calculations import (
    karm_bredde, karm_hoyde,
    dorblad_bredde, dorblad_hoyde,
    terskel_lengde, laminat_mal,
    dekklist_lengde
)


class DetailTab(QWidget):
    """Widget som viser spesielle egenskaper og beregnede produksjonsmål."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Bygger opp layouten."""
        layout = QVBoxLayout(self)

        # --- Spesielle egenskaper ---
        special_group = QGroupBox("Spesielle egenskaper")
        special_layout = QFormLayout(special_group)

        self.fire_rating_label = QLabel("Brannklasse:")
        self.fire_rating_value = QLabel("—")
        special_layout.addRow(self.fire_rating_label, self.fire_rating_value)

        self.u_value_label = QLabel("U-verdi:")
        self.u_value_value = QLabel("—")
        special_layout.addRow(self.u_value_label, self.u_value_value)

        self.kuldebro_label = QLabel("Brutt kuldebro:")
        self.kuldebro_value = QLabel("Nei")
        special_layout.addRow(self.kuldebro_label, self.kuldebro_value)

        layout.addWidget(special_group)

        # --- Felles (karm, terskel, dekklist) ---
        self.felles_group = QGroupBox("Felles")
        felles_layout = QFormLayout(self.felles_group)

        self.val_karm_b = QLabel("—")
        self.val_karm_h = QLabel("—")
        self.val_terskel = QLabel("—")
        self.lbl_dekklist = QLabel("Dekklist:")
        self.val_dekklist = QLabel("—")

        felles_layout.addRow("Utv.karm B:", self.val_karm_b)
        felles_layout.addRow("Utv.karm H:", self.val_karm_h)
        felles_layout.addRow("Terskel:", self.val_terskel)
        felles_layout.addRow(self.lbl_dekklist, self.val_dekklist)

        layout.addWidget(self.felles_group)

        # --- Dørblad 1 (eller bare "Dørblad" ved 1-fløyet) ---
        self.blade1_group = QGroupBox("Dørblad")
        blade1_layout = QFormLayout(self.blade1_group)

        self.val_dorblad1_b = QLabel("—")
        self.val_dorblad1_h = QLabel("—")
        self.val_laminat1_b = QLabel("—")
        self.val_laminat1_h = QLabel("—")

        blade1_layout.addRow("Dørblad B:", self.val_dorblad1_b)
        blade1_layout.addRow("Dørblad H:", self.val_dorblad1_h)
        blade1_layout.addRow("Laminat B:", self.val_laminat1_b)
        blade1_layout.addRow("Laminat H:", self.val_laminat1_h)

        layout.addWidget(self.blade1_group)

        # --- Dørblad 2 (kun synlig ved 2-fløyet) ---
        self.blade2_group = QGroupBox("Dørblad 2")
        blade2_layout = QFormLayout(self.blade2_group)

        self.val_dorblad2_b = QLabel("—")
        self.val_dorblad2_h = QLabel("—")
        self.val_laminat2_b = QLabel("—")
        self.val_laminat2_h = QLabel("—")

        blade2_layout.addRow("Dørblad B:", self.val_dorblad2_b)
        blade2_layout.addRow("Dørblad H:", self.val_dorblad2_h)
        blade2_layout.addRow("Laminat B:", self.val_laminat2_b)
        blade2_layout.addRow("Laminat H:", self.val_laminat2_h)

        layout.addWidget(self.blade2_group)

        layout.addStretch()

    def update_door(self, door: DoorParams):
        """Oppdaterer visningen med verdier fra DoorParams."""
        # --- Spesielle egenskaper ---

        # Brannklasse (synlig kun for BD)
        is_fire = door.door_type == 'BD'
        self.fire_rating_label.setVisible(is_fire)
        self.fire_rating_value.setVisible(is_fire)
        if is_fire:
            self.fire_rating_value.setText(door.fire_rating or "(ingen)")

        # U-verdi (synlig kun hvis > 0)
        has_u_value = DOOR_U_VALUES.get(door.door_type, 0.0) > 0
        self.u_value_label.setVisible(has_u_value)
        self.u_value_value.setVisible(has_u_value)
        if has_u_value:
            self.u_value_value.setText(f"{door.insulation_value:.2f} W/m\u00b2K")

        # Brutt kuldebro (alltid synlig)
        has_kuldebro = door.has_brutt_kuldebro()
        self.kuldebro_value.setText("Ja" if has_kuldebro else "Nei")

        # --- Felles utregninger ---
        karm_type = door.karm_type
        blade_type = door.blade_type
        floyer = door.floyer
        luftspalte = door.effective_luftspalte()
        is_2floyet = floyer == 2

        karm_b = karm_bredde(karm_type, door.width)
        karm_h = karm_hoyde(karm_type, door.height)
        self.val_karm_b.setText(f"{karm_b} mm")
        self.val_karm_h.setText(f"{karm_h} mm")

        terskel = terskel_lengde(karm_type, karm_b, floyer)
        self.val_terskel.setText(f"{terskel} mm" if terskel else "—")

        # Dekklist kun synlig ved 2-fløyet
        self.lbl_dekklist.setVisible(is_2floyet)
        self.val_dekklist.setVisible(is_2floyet)
        if is_2floyet:
            self.val_dekklist.setText(f"{dekklist_lengde(karm_h)} mm")

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

                self.val_dorblad1_b.setText(f"{db1_b} mm")
                self.val_dorblad2_b.setText(f"{db2_b} mm")
            else:
                db1_b = None
                db2_b = None
                self.val_dorblad1_b.setText("—")
                self.val_dorblad2_b.setText("—")

            self.val_dorblad1_h.setText(f"{db_h} mm" if db_h else "—")
            self.val_dorblad2_h.setText(f"{db_h} mm" if db_h else "—")

            # Laminat per fløy
            if db1_b and db_h:
                lam1_b, lam1_h = laminat_mal(karm_type, db1_b, db_h, blade_type)
                self.val_laminat1_b.setText(f"{lam1_b} mm")
                self.val_laminat1_h.setText(f"{lam1_h} mm")
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")

            if db2_b and db_h:
                lam2_b, lam2_h = laminat_mal(karm_type, db2_b, db_h, blade_type)
                self.val_laminat2_b.setText(f"{lam2_b} mm")
                self.val_laminat2_h.setText(f"{lam2_h} mm")
            else:
                self.val_laminat2_b.setText("—")
                self.val_laminat2_h.setText("—")
        else:
            # 1-fløyet: én gruppe
            self.blade1_group.setTitle("Dørblad")
            self.blade2_group.setVisible(False)

            db_b = db_b_total
            self.val_dorblad1_b.setText(f"{db_b} mm" if db_b else "—")
            self.val_dorblad1_h.setText(f"{db_h} mm" if db_h else "—")

            if db_b and db_h:
                lam_b, lam_h = laminat_mal(karm_type, db_b, db_h, blade_type)
                self.val_laminat1_b.setText(f"{lam_b} mm")
                self.val_laminat1_h.setText(f"{lam_h} mm")
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")
