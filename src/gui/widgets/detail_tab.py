"""
Detaljer-tab widget – viser spesielle egenskaper og utregninger.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QTimer

from ...models.door import DoorParams
from ...utils.calculations import (
    karm_bredde, karm_hoyde,
    dorblad_bredde, dorblad_hoyde,
    terskel_lengde, laminat_mal, laminat_2_mal,
    dekklist_lengde,
    sparkeplate_bredde, avviserboyler_lengde,
    ryggforsterkning_hoyde, ryggforsterkning_overdel,
)
from ...doors import DOOR_REGISTRY
from ...utils.ordretekst import generer_ordretekst


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
        lbl.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 13px;")
        lbl.setMinimumWidth(self._LABEL_MIN_WIDTH)
        return lbl

    def _make_value(self) -> QLabel:
        """Lager en verdi-label med fremhevet stil."""
        val = QLabel("—")
        val.setStyleSheet("color: rgba(255, 255, 255, 0.95); font-weight: bold; font-size: 13px;")
        val.setTextFormat(Qt.TextFormat.RichText)
        return val

    @staticmethod
    def _fmt(value, unit: str = "mm") -> str:
        """Formaterer en verdi med dempet enhet."""
        if value is None:
            return "—"
        return (
            f"{value}"
            f" <span style='color:rgba(255,255,255,0.50); font-weight:normal; font-size:11px'>"
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
        self.lbl_laminat1_b = self._make_label("Laminat B:")
        self.val_laminat1_b = self._make_value()
        self.lbl_laminat1_h = self._make_label("Laminat H:")
        self.val_laminat1_h = self._make_value()
        self.lbl_laminat1_2_b = self._make_label("Laminat 2 B:")
        self.val_laminat1_2_b = self._make_value()
        self.lbl_laminat1_2_h = self._make_label("Laminat 2 H:")
        self.val_laminat1_2_h = self._make_value()

        blade1_layout.addRow(self._make_label("Dørblad B:"), self.val_dorblad1_b)
        blade1_layout.addRow(self._make_label("Dørblad H:"), self.val_dorblad1_h)
        blade1_layout.addRow(self.lbl_laminat1_b, self.val_laminat1_b)
        blade1_layout.addRow(self.lbl_laminat1_h, self.val_laminat1_h)
        blade1_layout.addRow(self.lbl_laminat1_2_b, self.val_laminat1_2_b)
        blade1_layout.addRow(self.lbl_laminat1_2_h, self.val_laminat1_2_h)

        # --- Dørblad 2 (kun synlig ved 2-fløyet) ---
        self.blade2_group = QGroupBox("Dørblad 2")
        blade2_layout = self._make_form_layout(self.blade2_group)

        self.val_dorblad2_b = self._make_value()
        self.val_dorblad2_h = self._make_value()
        self.lbl_laminat2_b = self._make_label("Laminat B:")
        self.val_laminat2_b = self._make_value()
        self.lbl_laminat2_h = self._make_label("Laminat H:")
        self.val_laminat2_h = self._make_value()
        self.lbl_laminat2_2_b = self._make_label("Laminat 2 B:")
        self.val_laminat2_2_b = self._make_value()
        self.lbl_laminat2_2_h = self._make_label("Laminat 2 H:")
        self.val_laminat2_2_h = self._make_value()

        blade2_layout.addRow(self._make_label("Dørblad B:"), self.val_dorblad2_b)
        blade2_layout.addRow(self._make_label("Dørblad H:"), self.val_dorblad2_h)
        blade2_layout.addRow(self.lbl_laminat2_b, self.val_laminat2_b)
        blade2_layout.addRow(self.lbl_laminat2_h, self.val_laminat2_h)
        blade2_layout.addRow(self.lbl_laminat2_2_b, self.val_laminat2_2_b)
        blade2_layout.addRow(self.lbl_laminat2_2_h, self.val_laminat2_2_h)

        # Dørblad 1 og 2 side om side
        blade_row = QHBoxLayout()
        blade_row.setSpacing(10)
        blade_row.addWidget(self.blade1_group)
        blade_row.addWidget(self.blade2_group)
        layout.addLayout(blade_row)

        # --- Pendeldør-spesifikke felt ---
        self.pendel_group = QGroupBox("Pendeldør-komponenter")
        pendel_layout = self._make_form_layout(self.pendel_group)

        self.lbl_sparkeplate = self._make_label("Sparkeplate B:")
        self.val_sparkeplate = self._make_value()
        self.lbl_sparkeplate_h = self._make_label("Sparkeplate H:")
        self.val_sparkeplate_h = self._make_value()
        self.lbl_avviserboyler = self._make_label("Avviserbøyler:")
        self.val_avviserboyler = self._make_value()
        self.lbl_ryggforst_h = self._make_label("Ryggforst. H:")
        self.val_ryggforst_h = self._make_value()
        self.lbl_ryggforst_overdel = self._make_label("Ryggforst. overdel:")
        self.val_ryggforst_overdel = self._make_value()

        pendel_layout.addRow(self.lbl_sparkeplate, self.val_sparkeplate)
        pendel_layout.addRow(self.lbl_sparkeplate_h, self.val_sparkeplate_h)
        pendel_layout.addRow(self.lbl_avviserboyler, self.val_avviserboyler)
        pendel_layout.addRow(self.lbl_ryggforst_h, self.val_ryggforst_h)
        pendel_layout.addRow(self.lbl_ryggforst_overdel, self.val_ryggforst_overdel)

        layout.addWidget(self.pendel_group)

        # --- Ordretekst ---
        self.ordretekst_group = QGroupBox("Ordretekst")
        ordretekst_layout = QVBoxLayout(self.ordretekst_group)
        ordretekst_layout.setContentsMargins(16, 8, 16, 12)

        # Kopier-knapp øverst til høyre
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.kopier_btn = QPushButton("Kopier")
        self.kopier_btn.setFixedWidth(90)
        self.kopier_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.kopier_btn.clicked.connect(self._kopier_ordretekst)
        btn_row.addWidget(self.kopier_btn)
        ordretekst_layout.addLayout(btn_row)

        self.ordretekst_label = QLabel("—")
        self.ordretekst_label.setTextFormat(Qt.TextFormat.RichText)
        self.ordretekst_label.setWordWrap(True)
        self.ordretekst_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        ordretekst_layout.addWidget(self.ordretekst_label)

        self._ordretekst_ren = ""  # Ren tekst for kopiering

        layout.addWidget(self.ordretekst_group)

        layout.addStretch()

    # ── Oppdatering ───────────────────────────────────────────────

    def update_door(self, door: DoorParams):
        """Oppdaterer visningen med verdier fra DoorParams."""
        fmt = self._fmt

        # --- Felles utregninger ---
        karm_type = door.karm_type
        hinge_type = door.hinge_type
        floyer = door.floyer
        luftspalte = door.effective_luftspalte()
        is_2floyet = floyer == 2

        karm_b = karm_bredde(karm_type, door.width, adjufix=door.adjufix)
        karm_h = karm_hoyde(karm_type, door.height)
        self.val_karm_b.setText(fmt(karm_b))
        self.val_karm_h.setText(fmt(karm_h))

        terskel = terskel_lengde(karm_type, karm_b, floyer)
        self.val_terskel.setText(fmt(terskel) if terskel else "—")

        # Dekklist kun for SDI 2-fløyet
        show_dekklist = is_2floyet and door.door_type == 'SDI'
        self.lbl_dekklist.setVisible(show_dekklist)
        self.val_dekklist.setVisible(show_dekklist)
        if show_dekklist:
            self.val_dekklist.setText(fmt(dekklist_lengde(karm_h)))

        # Har denne dørtypen laminat?
        has_laminat = laminat_mal(karm_type, 100, 100, door_type=door.door_type) != (None, None)
        # Har denne dørtypen laminat 2?
        has_lam2 = has_laminat and laminat_2_mal(karm_type, 100, 100) != (None, None)

        # --- Dørblad-beregninger ---
        db_b_total = dorblad_bredde(karm_type, karm_b, floyer, hinge_type, door_type=door.door_type)
        db_h = dorblad_hoyde(karm_type, karm_h, floyer, hinge_type, luftspalte, door_type=door.door_type)

        # Oppdater laminat-labels basert på om laminat 2 finnes
        lam_label = "Laminat 1 B:" if has_lam2 else "Laminat B:"
        lam_h_label = "Laminat 1 H:" if has_lam2 else "Laminat H:"
        self.lbl_laminat1_b.setText(lam_label)
        self.lbl_laminat1_h.setText(lam_h_label)
        self.lbl_laminat2_b.setText(lam_label)
        self.lbl_laminat2_h.setText(lam_h_label)

        # Vis/skjul laminat 1-felter basert på om dørtypen har laminat
        for w in (self.lbl_laminat1_b, self.val_laminat1_b,
                  self.lbl_laminat1_h, self.val_laminat1_h):
            w.setVisible(has_laminat)

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
                lam1_b, lam1_h = laminat_mal(karm_type, db1_b, db_h, hinge_type, door_type=door.door_type)
                self.val_laminat1_b.setText(fmt(lam1_b))
                self.val_laminat1_h.setText(fmt(lam1_h))
                if has_lam2:
                    l2b, l2h = laminat_2_mal(karm_type, lam1_b, lam1_h)
                    self.val_laminat1_2_b.setText(fmt(l2b))
                    self.val_laminat1_2_h.setText(fmt(l2h))
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")
                self.val_laminat1_2_b.setText("—")
                self.val_laminat1_2_h.setText("—")

            if db2_b and db_h:
                lam2_b, lam2_h = laminat_mal(karm_type, db2_b, db_h, hinge_type, door_type=door.door_type)
                self.val_laminat2_b.setText(fmt(lam2_b))
                self.val_laminat2_h.setText(fmt(lam2_h))
                if has_lam2:
                    l2b, l2h = laminat_2_mal(karm_type, lam2_b, lam2_h)
                    self.val_laminat2_2_b.setText(fmt(l2b))
                    self.val_laminat2_2_h.setText(fmt(l2h))
            else:
                self.val_laminat2_b.setText("—")
                self.val_laminat2_h.setText("—")
                self.val_laminat2_2_b.setText("—")
                self.val_laminat2_2_h.setText("—")

            # Vis/skjul laminat-felter
            for w in (self.lbl_laminat2_b, self.val_laminat2_b,
                      self.lbl_laminat2_h, self.val_laminat2_h):
                w.setVisible(has_laminat)
            for w in (self.lbl_laminat1_2_b, self.val_laminat1_2_b,
                      self.lbl_laminat1_2_h, self.val_laminat1_2_h,
                      self.lbl_laminat2_2_b, self.val_laminat2_2_b,
                      self.lbl_laminat2_2_h, self.val_laminat2_2_h):
                w.setVisible(has_lam2)
        else:
            # 1-fløyet: én gruppe
            self.blade1_group.setTitle("Dørblad")
            self.blade2_group.setVisible(False)

            db_b = db_b_total
            self.val_dorblad1_b.setText(fmt(db_b) if db_b else "—")
            self.val_dorblad1_h.setText(fmt(db_h) if db_h else "—")

            if db_b and db_h:
                lam_b, lam_h = laminat_mal(karm_type, db_b, db_h, hinge_type, door_type=door.door_type)
                self.val_laminat1_b.setText(fmt(lam_b))
                self.val_laminat1_h.setText(fmt(lam_h))
                if has_lam2:
                    l2b, l2h = laminat_2_mal(karm_type, lam_b, lam_h)
                    self.val_laminat1_2_b.setText(fmt(l2b))
                    self.val_laminat1_2_h.setText(fmt(l2h))
                else:
                    self.val_laminat1_2_b.setText("—")
                    self.val_laminat1_2_h.setText("—")
            else:
                self.val_laminat1_b.setText("—")
                self.val_laminat1_h.setText("—")
                self.val_laminat1_2_b.setText("—")
                self.val_laminat1_2_h.setText("—")

            # Vis/skjul laminat 2-felter
            for w in (self.lbl_laminat1_2_b, self.val_laminat1_2_b,
                      self.lbl_laminat1_2_h, self.val_laminat1_2_h):
                w.setVisible(has_lam2)

        # --- Pendeldør-komponenter ---
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        has_sparkeplate = 'sparkeplate_offset' in door_def
        has_avviserboyler = 'avviserboyler_offset' in door_def
        has_ryggforst_h = 'ryggforsterkning_hoyde_offset' in door_def
        has_ryggforst_overdel = 'ryggforsterkning_overdel_offset' in door_def
        show_pendel = has_sparkeplate or has_avviserboyler or has_ryggforst_h or has_ryggforst_overdel

        self.pendel_group.setVisible(show_pendel)

        if show_pendel:
            # Bruk første blad-bredde for beregning
            ref_db_b = db_b_total
            if is_2floyet and db_b_total:
                split_pct = door.floyer_split / 100.0
                ref_db_b = round(db_b_total * split_pct)

            # Sparkeplate
            self.lbl_sparkeplate.setVisible(has_sparkeplate)
            self.val_sparkeplate.setVisible(has_sparkeplate)
            self.lbl_sparkeplate_h.setVisible(has_sparkeplate)
            self.val_sparkeplate_h.setVisible(has_sparkeplate)
            if has_sparkeplate and ref_db_b:
                sp_b = sparkeplate_bredde(door.door_type, ref_db_b)
                self.val_sparkeplate.setText(fmt(sp_b))
                self.val_sparkeplate_h.setText(fmt(door.sparkeplate_hoyde))
            elif has_sparkeplate:
                self.val_sparkeplate.setText("—")
                self.val_sparkeplate_h.setText(fmt(door.sparkeplate_hoyde))

            # Avviserbøyler
            show_avviserboyler = has_avviserboyler and door.avviserboyler
            self.lbl_avviserboyler.setVisible(show_avviserboyler)
            self.val_avviserboyler.setVisible(show_avviserboyler)
            if show_avviserboyler and ref_db_b:
                av_l = avviserboyler_lengde(door.door_type, ref_db_b)
                self.val_avviserboyler.setText(fmt(av_l))
            elif show_avviserboyler:
                self.val_avviserboyler.setText("—")

            # Ryggforsterkning høyde
            self.lbl_ryggforst_h.setVisible(has_ryggforst_h)
            self.val_ryggforst_h.setVisible(has_ryggforst_h)
            if has_ryggforst_h and db_h:
                rf_h = ryggforsterkning_hoyde(door.door_type, db_h)
                self.val_ryggforst_h.setText(fmt(rf_h))
            elif has_ryggforst_h:
                self.val_ryggforst_h.setText("—")

            # Ryggforsterkning overdel
            self.lbl_ryggforst_overdel.setVisible(has_ryggforst_overdel)
            self.val_ryggforst_overdel.setVisible(has_ryggforst_overdel)
            if has_ryggforst_overdel and ref_db_b:
                rfo = ryggforsterkning_overdel(door.door_type, ref_db_b)
                self.val_ryggforst_overdel.setText(fmt(rfo))
            elif has_ryggforst_overdel:
                self.val_ryggforst_overdel.setText("—")

        # --- Ordretekst ---
        linjer = generer_ordretekst(door)
        if linjer:
            tittel = linjer[0]
            undertittel = linjer[1] if len(linjer) > 1 else ''
            kropp = linjer[2:]
            kulepunkter = ''.join(f"<li>{l}</li>" for l in kropp)
            html = (
                f"<b>{tittel}</b><br>"
                f"{undertittel}"
                f"<ul style='margin-top:4px; margin-bottom:0;'>{kulepunkter}</ul>"
            )
            self.ordretekst_label.setText(html)
            # Lagre ren tekst for kopiering
            ren_kropp = '\n'.join(f"- {l}" for l in kropp)
            self._ordretekst_ren = f"{tittel}\n{undertittel}\n{ren_kropp}"
        else:
            self.ordretekst_label.setText("—")
            self._ordretekst_ren = ""

    def _kopier_ordretekst(self):
        """Kopierer ordreteksten til utklippstavlen."""
        if not self._ordretekst_ren:
            return
        QApplication.clipboard().setText(self._ordretekst_ren)
        # Visuell tilbakemelding
        self.kopier_btn.setText("Kopiert!")
        QTimer.singleShot(1500, lambda: self.kopier_btn.setText("Kopier"))
