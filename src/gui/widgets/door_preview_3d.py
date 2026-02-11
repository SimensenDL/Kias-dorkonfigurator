"""
3D-forhåndsvisning av konfigurert dør.
Bruker pyqtgraph OpenGL for interaktiv rotérbar visning.
"""
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent

from ...models.door import DoorParams
from ...utils.constants import RAL_COLORS, KARM_BLADE_FLUSH, KARM_SIDESTOLPE_WIDTH
from ...utils.calculations import karm_bredde, karm_hoyde, dorblad_bredde, dorblad_hoyde, terskel_lengde
from ...doors import DOOR_REGISTRY

# Betinget import med fallback
try:
    import pyqtgraph.opengl as gl
    HAS_3D = True
except ImportError:
    HAS_3D = False

# --- Konstantar ---
WALL_COLOR = (0.55, 0.55, 0.52, 1)
WALL_MARGIN = 1000                        # mm synleg vegg rundt opning
KARM_DEPTHS = {'SD1': 77, 'SD2': 84, 'SD3/ID': 92}
LISTVERK_WIDTH = {'SD1': 60, 'SD2': 60, 'SD3/ID': 0}
LISTVERK_THICKNESS = 7                   # mm
BLADE_GAP = 4                            # mm gap mellom 2 dørblad
UTFORING_THICKNESS = 8                   # mm
TERSKEL_HEIGHT = 50                      # mm (typisk terskelhøyde)


def _remap_right_to_middle(event: QMouseEvent) -> QMouseEvent:
    """Lager en kopi av musehendelsen med midtre knapp i stedet for høyre."""
    return QMouseEvent(
        event.type(),
        event.position(),
        event.globalPosition(),
        Qt.MouseButton.MiddleButton,
        (event.buttons() & ~Qt.MouseButton.RightButton) | Qt.MouseButton.MiddleButton,
        event.modifiers(),
    )


class _PanGLViewWidget(gl.GLViewWidget if HAS_3D else object):
    """GLViewWidget som også tillater pan med høyre museknapp."""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            event = _remap_right_to_middle(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.RightButton:
            event = _remap_right_to_middle(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            event = _remap_right_to_middle(event)
        super().mouseReleaseEvent(event)


class DoorPreview3D(QWidget):
    """3D-forhåndsvisning av ein konfigurert dør med vegg, karm, dørblad, hengslar og håndtak."""

    SCALE = 1.0 / 100.0

    # Håndtak-dimensjonar (mm)
    HANDLE_CENTER_HEIGHT = 1020          # mm frå gulv (senter håndtak)
    HANDLE_X_MARGIN = 80
    # Skilt (bakplate) — avrunda hjørne
    PLATE_WIDTH = 40
    PLATE_HEIGHT = 170
    PLATE_DEPTH = 5
    PLATE_CORNER_RADIUS = 6
    # Grep (spak) — bue frå skilt + horisontal sylinder
    LEVER_RADIUS = 10
    LEVER_BEND_RADIUS = 30                # mm radius på buen frå skilt
    LEVER_STRAIGHT = 85                   # mm rett del etter buen
    LEVER_Z_OFFSET = -45                  # mm under senter av skilt

    # Hengsel-dimensjonar (mm)
    HINGE_WIDTH = 15
    HINGE_HEIGHT = 60
    HINGE_DEPTH = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._door: Optional[DoorParams] = None
        self._mesh_items: list = []
        self._wall_items: list = []
        self._frame_items: list = []
        self._blade_items: list = []
        self._show_wall = False
        self._show_frame = True
        self._show_blades = True
        self._gl_widget = None
        self._init_ui()

    def _init_ui(self):
        """Initialiserer 3D-visning med toolbar og GL-widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not HAS_3D:
            label = QLabel(
                "3D-forhåndsvisning er ikke tilgjengelig.\n\n"
                "Installer pyqtgraph og PyOpenGL:\n"
                "pip install pyqtgraph PyOpenGL numpy"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888;")
            layout.addWidget(label)
            return

        try:
            # Toolbar med toggle-knapper
            toolbar = QHBoxLayout()
            toolbar.setContentsMargins(4, 4, 4, 0)

            for name, checked, handler in [
                ("Vegg", False, self._on_wall_toggled),
                ("Karm", True, self._on_frame_toggled),
                ("Dørblad", True, self._on_blade_toggled),
            ]:
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.setChecked(checked)
                btn.setMinimumWidth(80)
                btn.toggled.connect(handler)
                toolbar.addWidget(btn)
                setattr(self, f'_{name.lower()}_btn', btn)

            toolbar.addStretch()
            layout.addLayout(toolbar)

            self._gl_widget = _PanGLViewWidget()
            self._gl_widget.setBackgroundColor(50, 50, 55, 255)
            layout.addWidget(self._gl_widget)

            grid = gl.GLGridItem()
            grid.setSize(40, 40)
            grid.setSpacing(1, 1)
            grid.setColor((80, 80, 80, 100))
            self._gl_widget.addItem(grid)

            # Akser ved origo: X=rød, Y=grønn, Z=blå
            axis_len = 5.0
            for color, end in [
                ((1, 0, 0, 1), (axis_len, 0, 0)),
                ((0, 1, 0, 1), (0, axis_len, 0)),
                ((0, 0, 1, 1), (0, 0, axis_len)),
            ]:
                pts = np.array([[0, 0, 0], list(end)])
                line = gl.GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)
                self._gl_widget.addItem(line)

            self._setup_camera()
        except Exception:
            self._gl_widget = None
            label = QLabel(
                "3D-visning kunne ikke initialiseres.\n\n"
                "Systemet mangler OpenGL-støtte."
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888;")
            layout.addWidget(label)

    def _on_wall_toggled(self, checked: bool):
        """Vis/skjul vegg."""
        self._show_wall = checked
        for item in self._wall_items:
            item.setVisible(checked)

    def _on_frame_toggled(self, checked: bool):
        """Vis/skjul karm."""
        self._show_frame = checked
        for item in self._frame_items:
            item.setVisible(checked)

    def _on_blade_toggled(self, checked: bool):
        """Vis/skjul dørblad."""
        self._show_blades = checked
        for item in self._blade_items:
            item.setVisible(checked)

    def _setup_camera(self):
        """Setter opp initialt kameraperspektiv."""
        self._gl_widget.setCameraPosition(distance=30, elevation=15, azimuth=-30)
        self._gl_widget.pan(0, 0, 10)

    def update_door(self, door: DoorParams) -> None:
        """Oppdaterer 3D-visningen med nye dørparametere."""
        if self._gl_widget is None:
            return
        self._door = door
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        """Fjerner alle mesh-element og bygger scenen på nytt."""
        if self._gl_widget is None:
            return

        for item in self._mesh_items:
            self._gl_widget.removeItem(item)
        self._mesh_items.clear()
        self._wall_items.clear()
        self._frame_items.clear()
        self._blade_items.clear()

        if self._door is None:
            return

        door = self._door
        s = self.SCALE

        # Grunnmål (mm)
        bm = door.width
        hm = door.height
        wall_t = door.thickness

        # Karmmål (mm)
        kb = karm_bredde(door.karm_type, bm)
        kh = karm_hoyde(door.karm_type, hm)

        # Dørblad-dimensjonar
        luftspalte_mm = 22  # Fast offset i 3D-visning (mm)
        blade_t_mm = door.blade_thickness
        karm_depth = KARM_DEPTHS.get(door.karm_type, 77)
        sidestolpe_w = KARM_SIDESTOLPE_WIDTH.get(door.karm_type, 80)
        is_flush = door.karm_type in KARM_BLADE_FLUSH

        # Berekn bladhøgde for toppstykke-dimensjonering
        db_h = dorblad_hoyde(door.karm_type, kh, door.floyer, door.blade_type, luftspalte_mm)
        if db_h is None:
            db_h = kh - 85
        toppstykke_h = max(20, kh - (luftspalte_mm + db_h) - 5)

        # 1. Vegg (alltid bygd, synlegheit styrt av toggle)
        self._add_wall(bm, hm, wall_t, s)

        # 2. Karm
        if door.karm_type == 'SD1':
            self._add_frame_sd1(door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s)
        elif door.karm_type == 'SD2':
            self._add_frame_sd2(door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s)
        else:
            self._add_frame_sd3id(door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s)

        # 3. Terskel (bare hvis det er valgt en terskeltype)
        if door.threshold_type != 'ingen':
            self._add_threshold(door, kb, wall_t, karm_depth, blade_t_mm, is_flush, s)

        # 4. Dørblad
        self._add_door_blades(door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s)

        # 5. Hengsler
        self._add_hinges(door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s)

        # 6. Håndtak
        self._add_handle(door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s)

    # =========================================================================
    # VEGG
    # =========================================================================

    def _add_wall(self, bm, hm, wall_t, s):
        """Vegg med rektangulær utsparing (BM x HM). Semi-transparent."""
        M = WALL_MARGIN
        color = np.array(WALL_COLOR)
        wy = -wall_t / 2
        wd = wall_t

        parts = [
            # Venstre kolonne (full høgde + margin over opning)
            (-(bm / 2 + M), wy, 0, M, wd, hm + M),
            # Høgre kolonne
            (bm / 2, wy, 0, M, wd, hm + M),
            # Topp-bjelke (mellom kolonnane)
            (-bm / 2, wy, hm, bm, wd, M),
        ]

        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                color,
                gl_options='translucent', is_wall=True
            )
            mesh.setVisible(self._show_wall)

    # =========================================================================
    # KARM SD1 — U-profil med utforing
    # =========================================================================

    def _add_frame_sd1(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s):
        """SD1: list (60mm bred, 7mm tykk) på begge sider av veggen."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        list_w = 60   # mm bredde på listen
        list_t = 7    # mm tykkelse

        # Framside — utover fra veggflaten
        front_y = wall_t / 2
        # Bakside — utover fra veggflaten
        back_y = -wall_t / 2 - list_t

        # Innvendig kobling gjennom veggen (5mm tykk)
        kobling_t = 5     # mm tykkelse
        kobling_y = -wall_t / 2
        kobling_d = wall_t  # full veggdybde

        parts = []

        # Lister på fram- og bakside (tykkelsen utover fra veggen)
        for y in (front_y, back_y):
            # Venstre list — full høyde
            parts.append((-kb / 2, y, 0, list_w, list_t, kh))
            # Høyre list — full høyde
            parts.append((kb / 2 - list_w, y, 0, list_w, list_t, kh))
            # Topp list — mellom sidene
            parts.append((
                -kb / 2 + list_w, y, kh - list_w,
                kb - 2 * list_w, list_t, list_w
            ))

        # Kobling gjennom veggen — indre kant av listene
        # Venstre side (opp til topp-koblingens tykkelse)
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        # Høyre side (opp til topp-koblingens tykkelse)
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        # Topp
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — list bak dørbladet som bladet lukker mot
        anslag_w = 20    # mm, hvor langt inn i åpningen (80mm fra utvendig karm - 60mm list)
        blade_t = door.blade_thickness
        # Bak bladet, 44mm dybde i Y (84mm karm - 40mm dørblad)
        anslag_d = 44
        anslag_front_y = wall_t / 2 + list_t - blade_t
        anslag_back_y = anslag_front_y - anslag_d

        # Venstre anslag
        parts.append((-kb / 2 + list_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        # Høyre anslag
        parts.append((kb / 2 - list_w - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        # Topp anslag
        parts.append((-kb / 2 + list_w, anslag_back_y, kh - list_w - anslag_w,
                       kb - 2 * list_w, anslag_d, anslag_w))

        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)

    # =========================================================================
    # KARM SD2 — L-profil
    # =========================================================================

    def _add_frame_sd2(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s):
        """SD2: som SD1 men kun list på framside, dybde 77mm + 7mm list = 84mm."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        list_w = 60   # mm bredde på listen
        list_t = 7    # mm tykkelse
        sd2_depth = 77  # mm karmdybde (84 - 7mm list)

        # Framside list — utover fra veggflaten
        front_y = wall_t / 2

        parts = []

        # List kun på framside
        parts.append((-kb / 2, front_y, 0, list_w, list_t, kh))
        parts.append((kb / 2 - list_w, front_y, 0, list_w, list_t, kh))
        parts.append((
            -kb / 2 + list_w, front_y, kh - list_w,
            kb - 2 * list_w, list_t, list_w
        ))

        # Kobling gjennom veggen (5mm tykk, 77mm dyp fra veggfront)
        kobling_t = 5
        kobling_y = wall_t / 2 - sd2_depth
        kobling_d = sd2_depth

        # Venstre side
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        # Høyre side
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        # Topp
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — bak dørbladet (44mm = 84mm karm - 40mm dørblad)
        anslag_w = 20
        blade_t = door.blade_thickness
        anslag_d = 44
        # Posisjonert relativt til karmens framkant (list front), ikke veggen
        karm_front = wall_t / 2 + list_t  # listens framside
        anslag_front_y = karm_front - blade_t
        anslag_back_y = anslag_front_y - anslag_d

        # Venstre anslag
        parts.append((-kb / 2 + list_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        # Høyre anslag
        parts.append((kb / 2 - list_w - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        # Topp anslag
        parts.append((-kb / 2 + list_w, anslag_back_y, kh - list_w - anslag_w,
                       kb - 2 * list_w, anslag_d, anslag_w))

        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)

    # =========================================================================
    # KARM SD3/ID — Smygmontasje
    # =========================================================================

    def _add_frame_sd3id(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s):
        """SD3/ID smygmontasje: karm er MINDRE enn opning, sentrert i veggdybden."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        back_y = -karm_depth / 2

        parts = []

        # Sidestolper (original posisjon)
        for side in ('left', 'right'):
            x = -kb / 2 if side == 'left' else kb / 2 - sidestolpe_w
            parts.append((x, back_y, 0, sidestolpe_w, karm_depth, kh))

        # Toppstykke (mellom sidestolpene)
        parts.append((
            -kb / 2 + sidestolpe_w, back_y, kh - toppstykke_h,
            kb - 2 * sidestolpe_w, karm_depth, toppstykke_h
        ))

        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)

    # =========================================================================
    # TERSKEL
    # =========================================================================

    def _add_threshold(self, door, kb, wall_t, karm_depth, blade_t_mm, is_flush, s):
        """Terskel i bunnen av døråpningen. Forskjøvet i Y med blade_thickness."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        t_len = terskel_lengde(door.karm_type, kb, door.floyer)
        if t_len is None:
            return

        t_h = TERSKEL_HEIGHT
        t_depth = karm_depth

        # X: sentrert
        t_x = -t_len / 2

        # Y: forskjøvet med blade_thickness (bak bladets bakside)
        if is_flush:
            t_y = wall_t / 2 - t_depth - blade_t_mm
        else:
            t_y = -t_depth / 2 - blade_t_mm

        mesh = self._add_mesh(
            t_x * s, t_y * s, 0,
            t_len * s, t_depth * s, t_h * s,
            karm_color, is_frame=True
        )
        mesh.setVisible(self._show_frame)

    # =========================================================================
    # DØRBLAD
    # =========================================================================

    def _add_door_blades(self, door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s):
        """Dørblad med produksjonsmål fra calculations.py."""
        blade_color = np.array(self._ral_to_rgba(door.color))

        # Y-posisjon (flush med listverk)
        if is_flush:
            blade_y = wall_t / 2 + LISTVERK_THICKNESS - blade_t_mm
        else:
            blade_y = -blade_t_mm / 2

        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.blade_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.blade_type, luftspalte_mm)
            if db_b and db_h:
                self._render_single_blade(
                    -db_b / 2, blade_y, luftspalte_mm,
                    db_b, blade_t_mm, db_h,
                    blade_color, s
                )
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.blade_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.blade_type, luftspalte_mm)
            if db_b_total and db_h:
                db1_b = round(db_b_total * door.floyer_split / 100)
                db2_b = db_b_total - db1_b
                total_w = db1_b + BLADE_GAP + db2_b
                start_x = -total_w / 2

                # Blad 1 (venstre)
                self._render_single_blade(
                    start_x, blade_y, luftspalte_mm,
                    db1_b, blade_t_mm, db_h,
                    blade_color, s
                )
                # Blad 2 (høyre)
                self._render_single_blade(
                    start_x + db1_b + BLADE_GAP, blade_y, luftspalte_mm,
                    db2_b, blade_t_mm, db_h,
                    blade_color, s
                )

    def _render_single_blade(self, x, y, z, w, d, h, color, s):
        """Tegner ett dørblad med retningsbasert lys."""
        verts, faces = self._make_box(x * s, y * s, z * s, w * s, d * s, h * s)
        face_colors = self._lit_face_colors(color)

        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

    # =========================================================================
    # HENGSLAR
    # =========================================================================

    def _add_hinges(self, door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s):
        """Hengslar frå dørtype-data, plassert på riktig side."""
        hw = self.HINGE_WIDTH
        hh = self.HINGE_HEIGHT
        hd = self.HINGE_DEPTH
        hinge_color = np.array([0.478, 0.478, 0.478, 1.0])

        total_hinges = self._get_hinge_count(door)

        # Y-posisjon: sentrert på framkant av dørblad (synleg frå utsida)
        if is_flush:
            hy = wall_t / 2 + LISTVERK_THICKNESS - hd / 2
        else:
            hy = blade_t_mm / 2 - hd / 2

        # Bygg liste over blad å feste hengslar på: (senter_x, breidde, høgde, antal)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)

        for (bcx, b_w, b_h, count) in blades:
            if count <= 0:
                count = 2
            if count == 2:
                positions = [0.20, 0.80]
            elif count == 3:
                positions = [0.15, 0.50, 0.85]
            else:
                positions = [i / (count + 1) for i in range(1, count + 1)]

            for p in positions:
                hz = luftspalte_mm + b_h * p - hh / 2
                if door.swing_direction == 'left':
                    hx = bcx - b_w / 2 - hw
                else:
                    hx = bcx + b_w / 2

                verts, faces = self._make_box(
                    hx * s, hy * s, hz * s, hw * s, hd * s, hh * s
                )
                face_colors = self._normal_lit_face_colors(verts, faces, hinge_color)
                mesh = gl.GLMeshItem(
                    vertexes=verts, faces=faces, faceColors=face_colors,
                    smooth=False, drawEdges=False
                )
                self._gl_widget.addItem(mesh)
                self._mesh_items.append(mesh)
                self._blade_items.append(mesh)
                mesh.setVisible(self._show_blades)

    def _get_hinge_count(self, door) -> int:
        """Hent hengselantal frå DOOR_REGISTRY, med fallback."""
        try:
            reg = DOOR_REGISTRY.get(door.door_type, {})
            hengsler = reg.get('hengsler', {})
            blade_data = hengsler.get(door.blade_type, {})
            antall = blade_data.get('antall', {})
            count = antall.get(door.floyer)
            if count:
                return count
        except (KeyError, TypeError):
            pass
        return door.hinge_count if door.hinge_count > 0 else 2

    def _get_blade_geometries(self, door, kb, kh, luftspalte_mm, total_hinges):
        """Returnerer liste av (senter_x, breidde, høgde, hengslar_per_blad) for kvart blad."""
        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.blade_type) or (kb - 128)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.blade_type, luftspalte_mm) or (kh - 85)
            return [(0, db_b, db_h, total_hinges)]
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.blade_type) or (kb - 132)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.blade_type, luftspalte_mm) or (kh - 85)
            db1_b = round(db_b_total * door.floyer_split / 100)
            db2_b = db_b_total - db1_b
            total_w = db1_b + BLADE_GAP + db2_b
            per_blade = max(1, total_hinges // 2)

            b1_cx = -total_w / 2 + db1_b / 2
            b2_cx = -total_w / 2 + db1_b + BLADE_GAP + db2_b / 2
            return [(b1_cx, db1_b, db_h, per_blade), (b2_cx, db2_b, db_h, per_blade)]

    # =========================================================================
    # HÅNDTAK
    # =========================================================================

    def _add_handle(self, door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s):
        """Skilthandtak på motsett side av hengslene."""
        margin = self.HANDLE_X_MARGIN
        handle_color = np.array([0.478, 0.478, 0.478, 1.0])

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)
        bcx, b_w, b_h, _ = blades[0]

        # Senter-X for skiltet
        if door.swing_direction == 'left':
            plate_cx = bcx + b_w / 2 - margin
        else:
            plate_cx = bcx - b_w / 2 + margin

        # Y-posisjon (på framside av dørblad)
        if is_flush:
            plate_y = wall_t / 2 + LISTVERK_THICKNESS
        else:
            plate_y = blade_t_mm / 2

        plate_cy = plate_y + self.PLATE_DEPTH / 2
        plate_cz = self.HANDLE_CENTER_HEIGHT

        # Skilt (avrunda hjørne)
        verts, faces = self._make_rounded_rect(
            plate_cx * s, plate_cy * s, plate_cz * s,
            self.PLATE_WIDTH * s, self.PLATE_HEIGHT * s, self.PLATE_DEPTH * s,
            self.PLATE_CORNER_RADIUS * s
        )
        face_colors = self._normal_lit_face_colors(verts, faces, handle_color)
        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

        # Grep (bue frå skilt + rett spak)
        bend_r = self.LEVER_BEND_RADIUS
        lever_cz = plate_cz + self.LEVER_Z_OFFSET
        lever_y_start = plate_y + self.PLATE_DEPTH

        # Bygg bane: bue (kvartssirkel) + rett strekk
        path = []
        bend_segs = 10
        if door.swing_direction == 'left':
            # Bue frå Y+ retning til X- retning
            arc_cx = plate_cx - bend_r
            arc_cy = lever_y_start
            for i in range(bend_segs + 1):
                angle = i * (np.pi / 2) / bend_segs
                px = arc_cx + bend_r * np.cos(angle)
                py = arc_cy + bend_r * np.sin(angle)
                path.append((px * s, py * s, lever_cz * s))
            # Rett del mot venstre
            end_x = plate_cx - bend_r - self.LEVER_STRAIGHT
            horiz_y = lever_y_start + bend_r
            path.append((end_x * s, horiz_y * s, lever_cz * s))
        else:
            # Bue frå Y+ retning til X+ retning
            arc_cx = plate_cx + bend_r
            arc_cy = lever_y_start
            for i in range(bend_segs + 1):
                angle = np.pi - i * (np.pi / 2) / bend_segs
                px = arc_cx + bend_r * np.cos(angle)
                py = arc_cy + bend_r * np.sin(angle)
                path.append((px * s, py * s, lever_cz * s))
            # Rett del mot høgre
            end_x = plate_cx + bend_r + self.LEVER_STRAIGHT
            horiz_y = lever_y_start + bend_r
            path.append((end_x * s, horiz_y * s, lever_cz * s))

        verts, faces = self._make_swept_tube(
            path, self.LEVER_RADIUS * s
        )
        face_colors = self._normal_lit_face_colors(verts, faces, handle_color)
        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

    # =========================================================================
    # HJELPEMETODER
    # =========================================================================

    # Lysfaktorer per flateretning (simulerer lys fra øvre front-høyre)
    # Rekkefølge: bunn, topp, front(Y+), bak(Y-), venstre(X-), høyre(X+)
    _FACE_LIGHT = (0.55, 1.15, 1.0, 0.62, 0.72, 0.88)

    @staticmethod
    def _lit_face_colors(base_color, light_factors=None):
        """Beregn 12 flatefarger (2 trekanter × 6 sider) med retningsbasert lys."""
        if light_factors is None:
            light_factors = DoorPreview3D._FACE_LIGHT
        r, g, b, a = base_color[0], base_color[1], base_color[2], base_color[3]
        colors = []
        for f in light_factors:
            c = (min(1.0, r * f), min(1.0, g * f), min(1.0, b * f), a)
            colors.append(c)
            colors.append(c)  # 2 trekanter per side
        return np.array(colors)

    def _add_mesh(self, x, y, z, dx, dy, dz, color,
                  gl_options=None, is_wall=False, is_frame=False, is_blade=False):
        """Lag GLMeshItem-boks med simulert retningslys."""
        verts, faces = self._make_box(x, y, z, dx, dy, dz)
        face_colors = self._lit_face_colors(color)
        kwargs = dict(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        if gl_options:
            kwargs['glOptions'] = gl_options
        mesh = gl.GLMeshItem(**kwargs)
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        if is_wall:
            self._wall_items.append(mesh)
        if is_frame:
            self._frame_items.append(mesh)
        if is_blade:
            self._blade_items.append(mesh)
        return mesh

    @staticmethod
    def _make_box(x, y, z, dx, dy, dz):
        """Genererer vertices og faces for ein boks."""
        verts = np.array([
            [x,      y,      z],
            [x + dx, y,      z],
            [x + dx, y + dy, z],
            [x,      y + dy, z],
            [x,      y,      z + dz],
            [x + dx, y,      z + dz],
            [x + dx, y + dy, z + dz],
            [x,      y + dy, z + dz],
        ])
        faces = np.array([
            [0, 1, 2], [0, 2, 3],     # Bunn
            [4, 6, 5], [4, 7, 6],     # Topp
            [3, 2, 6], [3, 6, 7],     # Front (y + dy)
            [0, 5, 1], [0, 4, 5],     # Bak (y)
            [0, 3, 7], [0, 7, 4],     # Venstre (x)
            [1, 5, 6], [1, 6, 2],     # Høyre (x + dx)
        ])
        return verts, faces

    @staticmethod
    def _make_cylinder(cx, cy, cz, radius, depth, segments=24):
        """Genererer vertices og faces for ein sylinder."""
        verts = []
        faces = []
        angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

        front_y = cy - depth / 2
        for angle in angles:
            verts.append([cx + radius * np.cos(angle), front_y, cz + radius * np.sin(angle)])

        back_y = cy + depth / 2
        for angle in angles:
            verts.append([cx + radius * np.cos(angle), back_y, cz + radius * np.sin(angle)])

        front_center = len(verts)
        verts.append([cx, front_y, cz])
        back_center = len(verts)
        verts.append([cx, back_y, cz])
        verts = np.array(verts)

        for i in range(segments):
            ni = (i + 1) % segments
            faces.append([front_center, ni, i])
        for i in range(segments):
            ni = (i + 1) % segments
            faces.append([back_center, segments + i, segments + ni])
        for i in range(segments):
            ni = (i + 1) % segments
            faces.append([i, ni, segments + i])
            faces.append([ni, segments + ni, segments + i])

        return verts, np.array(faces)

    @staticmethod
    def _make_rounded_rect(cx, cy, cz, width, height, depth, radius, segments=8):
        """Ekstrudert rektangel med avrunda hjørne, sentrert på (cx, cy, cz).

        Profil i XZ-planet, ekstrudert langs Y.
        """
        hw = width / 2
        hh = height / 2
        r = min(radius, hw, hh)

        # 2D-profil (X, Z) — fire hjørne med kvartssirkel
        corners = [
            (cx + hw - r, cz - hh + r, np.pi * 1.5, np.pi * 2.0),   # nedre høgre
            (cx + hw - r, cz + hh - r, 0.0,          np.pi * 0.5),   # øvre høgre
            (cx - hw + r, cz + hh - r, np.pi * 0.5,  np.pi),         # øvre venstre
            (cx - hw + r, cz - hh + r, np.pi,         np.pi * 1.5),  # nedre venstre
        ]

        profile = []
        for (ccx, ccz, a_start, a_end) in corners:
            for i in range(segments + 1):
                t = i / segments
                angle = a_start + t * (a_end - a_start)
                profile.append((ccx + r * np.cos(angle), ccz + r * np.sin(angle)))

        n = len(profile)
        front_y = cy + depth / 2
        back_y = cy - depth / 2

        verts = []
        for (px, pz) in profile:
            verts.append([px, front_y, pz])
        for (px, pz) in profile:
            verts.append([px, back_y, pz])
        front_center = len(verts)
        verts.append([cx, front_y, cz])
        back_center = len(verts)
        verts.append([cx, back_y, cz])
        verts = np.array(verts)

        faces = []
        # Front
        for i in range(n - 1):
            faces.append([front_center, i, i + 1])
        faces.append([front_center, n - 1, 0])
        # Bak
        for i in range(n - 1):
            faces.append([back_center, n + i + 1, n + i])
        faces.append([back_center, n, n + n - 1])
        # Sider
        for i in range(n - 1):
            faces.append([i, n + i, i + 1])
            faces.append([i + 1, n + i, n + i + 1])
        faces.append([n - 1, n + n - 1, 0])
        faces.append([0, n + n - 1, n])

        return verts, np.array(faces)

    @staticmethod
    def _make_horizontal_cylinder(x, cy, cz, radius, length, segments=16):
        """Sylinder langs X-aksen, start ved x, sentrert på (cy, cz)."""
        angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

        verts = []
        for angle in angles:
            verts.append([x, cy + radius * np.cos(angle), cz + radius * np.sin(angle)])
        for angle in angles:
            verts.append([x + length, cy + radius * np.cos(angle), cz + radius * np.sin(angle)])

        left_c = len(verts)
        verts.append([x, cy, cz])
        right_c = len(verts)
        verts.append([x + length, cy, cz])
        verts = np.array(verts)

        faces = []
        for i in range(segments):
            ni = (i + 1) % segments
            faces.append([left_c, ni, i])
            faces.append([right_c, segments + i, segments + ni])
            faces.append([i, segments + i, ni])
            faces.append([ni, segments + i, segments + ni])

        return verts, np.array(faces)

    @staticmethod
    def _make_swept_tube(path, radius, segments=12):
        """Rørform langs ein bane (liste av (x, y, z) punkt)."""
        n_path = len(path)
        verts = []

        for i in range(n_path):
            # Tangentretning
            if i == 0:
                tangent = np.array(path[1]) - np.array(path[0])
            elif i == n_path - 1:
                tangent = np.array(path[-1]) - np.array(path[-2])
            else:
                tangent = np.array(path[i + 1]) - np.array(path[i - 1])
            tangent = tangent / np.linalg.norm(tangent)

            # Perpendikulær ramme (bruk Z-opp som referanse)
            up = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(tangent, up)) > 0.99:
                up = np.array([0.0, 1.0, 0.0])
            normal = np.cross(tangent, up)
            normal = normal / np.linalg.norm(normal)
            binormal = np.cross(tangent, normal)

            center = np.array(path[i])
            for j in range(segments):
                angle = 2 * np.pi * j / segments
                pt = center + radius * (np.cos(angle) * normal + np.sin(angle) * binormal)
                verts.append(pt.tolist())

        # Endecap-senter
        start_c = len(verts)
        verts.append(list(path[0]))
        end_c = len(verts)
        verts.append(list(path[-1]))
        verts = np.array(verts)

        faces = []
        # Sideflater
        for i in range(n_path - 1):
            for j in range(segments):
                nj = (j + 1) % segments
                c = i * segments
                nx = (i + 1) * segments
                faces.append([c + j, nx + j, c + nj])
                faces.append([c + nj, nx + j, nx + nj])
        # Startcap
        for j in range(segments):
            nj = (j + 1) % segments
            faces.append([start_c, nj, j])
        # Endecap
        last = (n_path - 1) * segments
        for j in range(segments):
            nj = (j + 1) % segments
            faces.append([end_c, last + j, last + nj])

        return verts, np.array(faces)

    @staticmethod
    def _uniform_face_colors(color, num_faces):
        """Éin farge for alle flater (brukt for smooth-shada meshes)."""
        return np.tile(color, (num_faces, 1))

    @staticmethod
    def _normal_lit_face_colors(verts, faces, base_color):
        """Per-face lys basert på flatnormal vs lysretning (øvre front-høgre)."""
        light_dir = np.array([0.3, 0.6, 0.5])
        light_dir = light_dir / np.linalg.norm(light_dir)
        r, g, b, a = base_color
        ambient = 0.55
        diffuse = 0.55

        colors = []
        for face in faces:
            v0, v1, v2 = verts[face[0]], verts[face[1]], verts[face[2]]
            normal = np.cross(v1 - v0, v2 - v0)
            norm_len = np.linalg.norm(normal)
            if norm_len > 0:
                normal = normal / norm_len
            brightness = ambient + diffuse * max(0.0, np.dot(normal, light_dir))
            colors.append([min(1.0, r * brightness), min(1.0, g * brightness),
                           min(1.0, b * brightness), a])
        return np.array(colors)

    @staticmethod
    def _ral_to_rgba(ral_code: str, alpha: float = 1.0) -> tuple:
        """Konverterer RAL-kode til (r, g, b, a) tuple for OpenGL."""
        if ral_code in RAL_COLORS:
            r, g, b = RAL_COLORS[ral_code]['rgb']
            return (r, g, b, alpha)
        return (0.5, 0.5, 0.5, alpha)

    @staticmethod
    def _blend_colors(c1: tuple, c2: tuple, t: float) -> tuple:
        """Lineær blanding mellom to RGBA-farger."""
        return tuple(a * (1 - t) + b * t for a, b in zip(c1, c2))
