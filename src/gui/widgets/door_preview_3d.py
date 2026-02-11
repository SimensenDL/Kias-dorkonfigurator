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
from ...utils.calculations import karm_bredde, karm_hoyde, dorblad_bredde, dorblad_hoyde
from ...doors import DOOR_REGISTRY

# Betinget import med fallback
try:
    import pyqtgraph.opengl as gl
    HAS_3D = True
except ImportError:
    HAS_3D = False

# --- Konstantar ---
WALL_COLOR = (0.55, 0.55, 0.52, 0.6)
WALL_MARGIN = 1000                        # mm synleg vegg rundt opning
KARM_DEPTHS = {'SD1': 77, 'SD2': 84, 'SD3/ID': 92}
LISTVERK_WIDTH = {'SD1': 60, 'SD2': 60, 'SD3/ID': 0}
LISTVERK_THICKNESS = 5                   # mm
BLADE_GAP = 4                            # mm gap mellom 2 dørblad
UTFORING_THICKNESS = 8                   # mm


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
    HANDLE_WIDTH = 20
    HANDLE_HEIGHT = 120
    HANDLE_DEPTH = 30
    HANDLE_Y_RATIO = 0.47
    HANDLE_X_MARGIN = 80

    # Hengsel-dimensjonar (mm)
    HINGE_WIDTH = 15
    HINGE_HEIGHT = 60
    HINGE_DEPTH = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._door: Optional[DoorParams] = None
        self._mesh_items: list = []
        self._wall_items: list = []
        self._show_wall = True
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
            # Toolbar med vegg-toggle
            toolbar = QHBoxLayout()
            toolbar.setContentsMargins(4, 4, 4, 0)
            self._wall_btn = QPushButton("Vegg")
            self._wall_btn.setCheckable(True)
            self._wall_btn.setChecked(True)
            self._wall_btn.setFixedWidth(70)
            self._wall_btn.toggled.connect(self._on_wall_toggled)
            toolbar.addWidget(self._wall_btn)
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
        """Vis/skjul vegg utan full scene-rebuild."""
        self._show_wall = checked
        for item in self._wall_items:
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
        luftspalte_mm = door.effective_luftspalte()
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

        # 3. Dørblad
        self._add_door_blades(door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s)

        # 4. Hengslar
        self._add_hinges(door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s)

        # 5. Håndtak
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
        """SD1 U-profil: karm er STØRRE enn opning, flush med veggfront."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        front_y = wall_t / 2
        back_y = front_y - karm_depth
        listverk_w = LISTVERK_WIDTH.get('SD1', 60)

        parts = []

        # Sidestolpar
        for side in ('left', 'right'):
            x = -kb / 2 if side == 'left' else kb / 2 - sidestolpe_w
            parts.append((x, back_y, 0, sidestolpe_w, karm_depth, kh))

        # Toppstykke (mellom sidestolpane)
        parts.append((
            -kb / 2 + sidestolpe_w, back_y, kh - toppstykke_h,
            kb - 2 * sidestolpe_w, karm_depth, toppstykke_h
        ))

        # Listverk framside (tynne strips på veggflata rundt karmen)
        wall_back_y = -wall_t / 2
        if listverk_w > 0:
            lt = LISTVERK_THICKNESS
            # Framside: venstre, høgre, topp
            parts.append((-kb / 2 - listverk_w, front_y, 0, listverk_w, lt, kh))
            parts.append((kb / 2, front_y, 0, listverk_w, lt, kh))
            parts.append((
                -kb / 2 - listverk_w, front_y, kh,
                kb + 2 * listverk_w, lt, listverk_w
            ))
            # Bakside: venstre, høgre, topp (speglar framsida)
            parts.append((-kb / 2 - listverk_w, wall_back_y - lt, 0, listverk_w, lt, kh))
            parts.append((kb / 2, wall_back_y - lt, 0, listverk_w, lt, kh))
            parts.append((
                -kb / 2 - listverk_w, wall_back_y - lt, kh,
                kb + 2 * listverk_w, lt, listverk_w
            ))

        # Utforing: viss veggen er tjukkare enn karmdybda
        if back_y > wall_back_y + 1:
            ut_depth = back_y - wall_back_y
            ut_t = UTFORING_THICKNESS
            parts.append((-kb / 2, wall_back_y, 0, ut_t, ut_depth, kh))
            parts.append((kb / 2 - ut_t, wall_back_y, 0, ut_t, ut_depth, kh))
            parts.append((-kb / 2, wall_back_y, kh - ut_t, kb, ut_depth, ut_t))

        for (bx, by, bz, dx, dy, dz) in parts:
            self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color
            )

    # =========================================================================
    # KARM SD2 — L-profil
    # =========================================================================

    def _add_frame_sd2(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s):
        """SD2 L-profil: karm er STØRRE enn opning, framkant + bakre bein."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        front_y = wall_t / 2
        listverk_w = LISTVERK_WIDTH.get('SD2', 60)

        # L-profil dimensjonar
        l_front_depth = 28   # Framkant-djupne
        l_back_width = 22    # Bakre bein-breidde
        l_back_depth = karm_depth - l_front_depth

        parts = []

        # Sidestolpar (L-profil: framkant + bakre bein)
        for side in ('left', 'right'):
            x = -kb / 2 if side == 'left' else kb / 2 - sidestolpe_w
            # Framkant (full breidde)
            parts.append((x, front_y - l_front_depth, 0, sidestolpe_w, l_front_depth, kh))
            # Bakre bein (smalare, strekker seg bakover)
            if l_back_depth > 0:
                parts.append((x, front_y - karm_depth, 0, l_back_width, l_back_depth, kh))

        # Toppstykke framkant
        parts.append((
            -kb / 2 + sidestolpe_w, front_y - l_front_depth, kh - toppstykke_h,
            kb - 2 * sidestolpe_w, l_front_depth, toppstykke_h
        ))
        # Toppstykke bakre bein
        if l_back_depth > 0:
            parts.append((
                -kb / 2 + sidestolpe_w, front_y - karm_depth, kh - l_back_width,
                kb - 2 * sidestolpe_w, l_back_depth, l_back_width
            ))

        # Listverk
        if listverk_w > 0:
            lt = LISTVERK_THICKNESS
            parts.append((-kb / 2 - listverk_w, front_y, 0, listverk_w, lt, kh))
            parts.append((kb / 2, front_y, 0, listverk_w, lt, kh))
            parts.append((
                -kb / 2 - listverk_w, front_y, kh,
                kb + 2 * listverk_w, lt, listverk_w
            ))

        for (bx, by, bz, dx, dy, dz) in parts:
            self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color
            )

    # =========================================================================
    # KARM SD3/ID — Smygmontasje
    # =========================================================================

    def _add_frame_sd3id(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w, toppstykke_h, s):
        """SD3/ID smygmontasje: karm er MINDRE enn opning, sentrert i veggdjupna."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        back_y = -karm_depth / 2

        parts = []

        # Sidestolpar
        for side in ('left', 'right'):
            x = -kb / 2 if side == 'left' else kb / 2 - sidestolpe_w
            parts.append((x, back_y, 0, sidestolpe_w, karm_depth, kh))

        # Toppstykke (mellom sidestolpane)
        parts.append((
            -kb / 2 + sidestolpe_w, back_y, kh - toppstykke_h,
            kb - 2 * sidestolpe_w, karm_depth, toppstykke_h
        ))

        for (bx, by, bz, dx, dy, dz) in parts:
            self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color
            )

    # =========================================================================
    # DØRBLAD
    # =========================================================================

    def _add_door_blades(self, door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s):
        """Dørblad med produksjonsmål fra calculations.py."""
        blade_color = np.array(self._ral_to_rgba(door.color))

        # Y-posisjon
        if is_flush:
            blade_y = wall_t / 2 - blade_t_mm
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

    # =========================================================================
    # HENGSLAR
    # =========================================================================

    def _add_hinges(self, door, kb, kh, wall_t, blade_t_mm, luftspalte_mm, is_flush, s):
        """Hengslar frå dørtype-data, plassert på riktig side."""
        hw = self.HINGE_WIDTH
        hh = self.HINGE_HEIGHT
        hd = self.HINGE_DEPTH
        hinge_color = np.array([0.25, 0.25, 0.25, 1.0])

        total_hinges = self._get_hinge_count(door)

        # Y-posisjon: sentrert på bladdjupna
        if is_flush:
            hy = wall_t / 2 - blade_t_mm / 2 - hd / 2
        else:
            hy = -hd / 2

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

                self._add_mesh(
                    hx * s, hy * s, hz * s, hw * s, hd * s, hh * s,
                    hinge_color
                )

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
        """Håndtak på motsett side av hengslene."""
        hw = self.HANDLE_WIDTH
        hh = self.HANDLE_HEIGHT
        hd = self.HANDLE_DEPTH
        margin = self.HANDLE_X_MARGIN

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)
        # Håndtak på blad 1 (aktiv fløy)
        bcx, b_w, b_h, _ = blades[0]

        if door.swing_direction == 'left':
            hx = bcx + b_w / 2 - margin - hw
        else:
            hx = bcx - b_w / 2 + margin

        if is_flush:
            hy = wall_t / 2
        else:
            hy = blade_t_mm / 2

        hz = luftspalte_mm + b_h * self.HANDLE_Y_RATIO - hh / 2

        handle_color = np.array([0.12, 0.12, 0.12, 1.0])
        self._add_mesh(
            hx * s, hy * s, hz * s, hw * s, hd * s, hh * s,
            handle_color
        )

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
                  gl_options=None, is_wall=False):
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
