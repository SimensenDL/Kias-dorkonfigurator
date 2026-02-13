"""
3D-forhåndsvisning av konfigurert dør.
Bruker pyqtgraph OpenGL for interaktiv rotérbar visning.
"""
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QSurfaceFormat, QMatrix4x4

from ...models.door import DoorParams
from ...utils.constants import RAL_COLORS, KARM_SIDESTOLPE_WIDTH
from ...utils.calculations import karm_bredde, karm_hoyde, dorblad_bredde, dorblad_hoyde, terskel_lengde
from ...doors import DOOR_REGISTRY
from ..karm_profiles import KARM_PROFILES
from . import graphics_settings as gfx

# Betinget import med fallback
try:
    import pyqtgraph.opengl as gl
    HAS_3D = True
except ImportError:
    HAS_3D = False

# --- Konstanter ---
WALL_COLOR = (0.55, 0.55, 0.52, 1)
WALL_MARGIN = 800                        # mm synlig vegg rundt åpning
KARM_DEPTHS = {'SD1': 77, 'SD2': 84, 'SD3/ID': 92}
BLADE_GAP = 4                            # mm gap mellom 2 dørblad
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
    """3D-forhåndsvisning av en konfigurert dør med vegg, karm, dørblad, hengsler og håndtak."""

    SCALE = 1.0 / 100.0

    # Håndtak-dimensjoner (mm)
    HANDLE_CENTER_HEIGHT = 1020          # mm fra gulv (senter håndtak)
    HANDLE_X_MARGIN = 80
    # Skilt (bakplate) — avrundede hjørner
    PLATE_WIDTH = 40
    PLATE_HEIGHT = 170
    PLATE_DEPTH = 5
    PLATE_CORNER_RADIUS = 6
    # Grep (spak) — bue fra skilt + horisontal sylinder
    LEVER_RADIUS = 10
    LEVER_BEND_RADIUS = 30                # mm radius på buen fra skilt
    LEVER_STRAIGHT = 85                   # mm rett del etter buen
    LEVER_Z_OFFSET = -45                  # mm under senter av skilt

    # Hengsel-dimensjoner (mm)
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
        self._door_open = False
        self._show_axes = False
        self._axes_items: list = []
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

            # Åpne/lukke dør
            self._open_btn = QPushButton("Åpne")
            self._open_btn.setCheckable(True)
            self._open_btn.setChecked(False)
            self._open_btn.setMinimumWidth(80)
            self._open_btn.toggled.connect(self._on_open_toggled)
            toolbar.addWidget(self._open_btn)

            # Akser toggle
            self._axes_btn = QPushButton("Akser")
            self._axes_btn.setCheckable(True)
            self._axes_btn.setChecked(False)
            self._axes_btn.setMinimumWidth(80)
            self._axes_btn.toggled.connect(self._on_axes_toggled)
            toolbar.addWidget(self._axes_btn)

            toolbar.addStretch()
            layout.addLayout(toolbar)

            # MSAA anti-aliasing for glattere kanter
            fmt = QSurfaceFormat()
            fmt.setSamples(gfx.MSAA_SAMPLES)
            fmt.setDepthBufferSize(gfx.DEPTH_BUFFER_SIZE)
            QSurfaceFormat.setDefaultFormat(fmt)

            self._gl_widget = _PanGLViewWidget()
            self._gl_widget.setBackgroundColor(*gfx.BACKGROUND_COLOR)
            layout.addWidget(self._gl_widget)

            grid = gl.GLGridItem()
            grid.setSize(40, 40)
            grid.setSpacing(1, 1)
            grid.setColor((80, 80, 80, 100))
            self._gl_widget.addItem(grid)

            # Akser ved origo: X=rød, Y=grønn, Z=blå
            axis_len = 5.0
            for color, end, label in [
                ((1, 0, 0, 1), (axis_len, 0, 0), "X"),
                ((0, 1, 0, 1), (0, axis_len, 0), "Y"),
                ((0, 0, 1, 1), (0, 0, axis_len), "Z"),
            ]:
                pts = np.array([[0, 0, 0], list(end)])
                line = gl.GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)
                line.setVisible(self._show_axes)
                self._gl_widget.addItem(line)
                self._axes_items.append(line)
                txt = gl.GLTextItem(pos=np.array(end), text=label, color=color[:3])
                txt.setVisible(self._show_axes)
                self._gl_widget.addItem(txt)
                self._axes_items.append(txt)

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

    def _on_axes_toggled(self, checked: bool):
        """Vis/skjul akser (X/Y/Z)."""
        self._show_axes = checked
        for item in self._axes_items:
            item.setVisible(checked)

    def _on_open_toggled(self, checked: bool):
        """Åpne/lukke dør (90° rotasjon rundt hengsler)."""
        self._door_open = checked
        self._open_btn.setText("Lukk" if checked else "Åpne")
        self._rebuild_scene()

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

        # Karm-profil
        profile = KARM_PROFILES[door.karm_type]
        luftspalte_mm = profile.luftspalte(door)

        # Dørblad-dimensjoner
        blade_t_mm = door.blade_thickness
        karm_depth = KARM_DEPTHS.get(door.karm_type, 77)
        sidestolpe_w = KARM_SIDESTOLPE_WIDTH.get(door.karm_type, 80)

        # 1. Vegg (alltid bygd, synlighet styrt av toggle)
        self._add_wall(bm, hm, wall_t, s)

        # 2. Karm — bygd fra profil
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        parts = profile.build_frame_parts(door, kb, kh, wall_t, karm_depth, sidestolpe_w)
        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)

        # 3. Terskel (bare hvis det er valgt en terskeltype)
        if door.threshold_type != 'ingen':
            self._add_threshold(door, profile, kb, wall_t, karm_depth, blade_t_mm, s)

        # 4. Dørblad
        self._add_door_blades(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 5. Hengsler
        self._add_hinges(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 6. Håndtak
        self._add_handle(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

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
            # Venstre kolonne (full høyde + margin over åpning)
            (-(bm / 2 + M), wy, 0, M, wd, hm + M),
            # Høyre kolonne
            (bm / 2, wy, 0, M, wd, hm + M),
            # Topp-bjelke (mellom kolonnene)
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
    # TERSKEL
    # =========================================================================

    def _add_threshold(self, door, profile, kb, wall_t, karm_depth, blade_t_mm, s):
        """Terskel i bunnen av døråpningen."""
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        t_len = terskel_lengde(door.karm_type, kb, door.floyer)
        if t_len is None:
            return

        t_h = TERSKEL_HEIGHT
        t_depth = karm_depth
        t_x = -t_len / 2
        t_y = profile.threshold_y(wall_t, blade_t_mm, karm_depth, t_depth)

        mesh = self._add_mesh(
            t_x * s, t_y * s, 0,
            t_len * s, t_depth * s, t_h * s,
            karm_color, is_frame=True
        )
        mesh.setVisible(self._show_frame)

    # =========================================================================
    # DØRBLAD
    # =========================================================================

    def _add_door_blades(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Dørblad med produksjonsmål fra calculations.py."""
        blade_color = np.array(self._ral_to_rgba(door.color))
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)

        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.blade_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.blade_type, luftspalte_mm)
            if db_b and db_h:
                blade_x = -db_b / 2
                pivot = self._get_open_pivot(blade_x, db_b, blade_y, blade_t_mm, door.swing_direction, s)
                self._render_single_blade(
                    blade_x, blade_y, luftspalte_mm,
                    db_b, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot
                )
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.blade_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.blade_type, luftspalte_mm)
            if db_b_total and db_h:
                db1_b = round(db_b_total * door.floyer_split / 100)
                db2_b = db_b_total - db1_b
                total_w = db1_b + BLADE_GAP + db2_b
                start_x = -total_w / 2

                # Blad 2 (venstre i 3D-koord = høyre sett fra framsiden, hengsler på venstre)
                blade2_x = start_x
                pivot2 = self._get_open_pivot(blade2_x, db2_b, blade_y, blade_t_mm, 'left', s)
                self._render_single_blade(
                    blade2_x, blade_y, luftspalte_mm,
                    db2_b, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot2
                )
                # Blad 1 (høyre i 3D-koord = venstre sett fra framsiden, hengsler på høyre)
                blade1_x = start_x + db2_b + BLADE_GAP
                pivot1 = self._get_open_pivot(blade1_x, db1_b, blade_y, blade_t_mm, 'right', s)
                self._render_single_blade(
                    blade1_x, blade_y, luftspalte_mm,
                    db1_b, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot1
                )

    def _render_single_blade(self, x, y, z, w, d, h, color, s, pivot=None):
        """Tegner ett dørblad med retningsbasert lys."""
        verts, faces = self._make_box(x * s, y * s, z * s, w * s, d * s, h * s)
        face_colors = self._lit_face_colors(color)

        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        tr = self._build_open_transform(pivot)
        if tr is not None:
            mesh.setTransform(tr)
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

    # =========================================================================
    # HENGSLER
    # =========================================================================

    def _add_hinges(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Hengsler fra dørtype-data, plassert på riktig side."""
        hw = self.HINGE_WIDTH
        hh = self.HINGE_HEIGHT
        hd = self.HINGE_DEPTH
        hinge_color = np.array([0.478, 0.478, 0.478, 1.0])

        total_hinges = self._get_hinge_count(door)
        hy = profile.hinge_y(wall_t, blade_t_mm, karm_depth, hd)
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)

        # Bygg liste over blad å feste hengsler på
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)

        for (bcx, b_w, b_h, count, hinge_side) in blades:
            blade_x = bcx - b_w / 2
            pivot = self._get_open_pivot(blade_x, b_w, blade_y, blade_t_mm, hinge_side, s)
            tr = self._build_open_transform(pivot)

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
                if hinge_side == 'left':
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
                if tr is not None:
                    mesh.setTransform(tr)
                self._gl_widget.addItem(mesh)
                self._mesh_items.append(mesh)
                self._blade_items.append(mesh)
                mesh.setVisible(self._show_blades)

    def _get_hinge_count(self, door) -> int:
        """Hent hengselantall fra DOOR_REGISTRY, med fallback."""
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
        """Returnerer liste av (senter_x, bredde, høyde, hengsler_per_blad, hengselside) for hvert blad.

        hengselside er 'left' eller 'right' — angir hvilken kant hengselet sitter på.
        """
        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.blade_type) or (kb - 128)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.blade_type, luftspalte_mm) or (kh - 85)
            return [(0, db_b, db_h, total_hinges, door.swing_direction)]
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.blade_type) or (kb - 132)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.blade_type, luftspalte_mm) or (kh - 85)
            db1_b = round(db_b_total * door.floyer_split / 100)
            db2_b = db_b_total - db1_b
            total_w = db1_b + BLADE_GAP + db2_b
            per_blade = max(1, total_hinges // 2)

            # 3D-koord er speilvendt: negativ X = høyre sett fra framsiden
            b2_cx = -total_w / 2 + db2_b / 2
            b1_cx = -total_w / 2 + db2_b + BLADE_GAP + db1_b / 2
            return [(b1_cx, db1_b, db_h, per_blade, 'right'),
                    (b2_cx, db2_b, db_h, per_blade, 'left')]

    # =========================================================================
    # HÅNDTAK
    # =========================================================================

    def _add_handle(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Skilthåndtak på motsatt side av hengslene."""
        margin = self.HANDLE_X_MARGIN
        handle_color = np.array([0.478, 0.478, 0.478, 1.0])

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)
        # For 2-fløyet: speilvent i 3D — 'left' → blades[1], 'right' → blades[0]
        if door.floyer == 2 and door.swing_direction == 'left':
            bcx, b_w, b_h, _, hinge_side = blades[1]
        else:
            bcx, b_w, b_h, _, hinge_side = blades[0]

        # Pivot for open-rotasjon
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)
        blade_x = bcx - b_w / 2
        pivot = self._get_open_pivot(blade_x, b_w, blade_y, blade_t_mm, hinge_side, s)
        tr = self._build_open_transform(pivot)

        # Senter-X for skiltet (motsatt side av hengselet)
        if hinge_side == 'left':
            plate_cx = bcx + b_w / 2 - margin
        else:
            plate_cx = bcx - b_w / 2 + margin

        # Y-posisjon (på framside av dørblad)
        plate_y = profile.handle_y(wall_t, blade_t_mm, karm_depth)

        plate_cy = plate_y + self.PLATE_DEPTH / 2
        plate_cz = self.HANDLE_CENTER_HEIGHT

        # Skilt (avrundede hjørner, høyere oppløsning)
        verts, faces = self._make_rounded_rect(
            plate_cx * s, plate_cy * s, plate_cz * s,
            self.PLATE_WIDTH * s, self.PLATE_HEIGHT * s, self.PLATE_DEPTH * s,
            self.PLATE_CORNER_RADIUS * s,
            segments=gfx.PLATE_CORNER_SEGMENTS
        )
        face_colors = self._normal_lit_face_colors(verts, faces, handle_color)
        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=gfx.SMOOTH_CURVED_PARTS, drawEdges=False
        )
        if tr is not None:
            mesh.setTransform(tr)
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

        # Grep (bue fra skilt + rett spak)
        bend_r = self.LEVER_BEND_RADIUS
        lever_cz = plate_cz + self.LEVER_Z_OFFSET
        lever_y_start = plate_y + self.PLATE_DEPTH

        # Bygg bane: bue (kvartssirkel) + rett strekk
        path = []
        bend_segs = gfx.LEVER_BEND_SEGMENTS
        if hinge_side == 'left':
            # Bue fra Y+ retning til X- retning (grep peker mot hengslene)
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
            # Bue fra Y+ retning til X+ retning (grep peker mot hengslene)
            arc_cx = plate_cx + bend_r
            arc_cy = lever_y_start
            for i in range(bend_segs + 1):
                angle = np.pi - i * (np.pi / 2) / bend_segs
                px = arc_cx + bend_r * np.cos(angle)
                py = arc_cy + bend_r * np.sin(angle)
                path.append((px * s, py * s, lever_cz * s))
            # Rett del mot høyre
            end_x = plate_cx + bend_r + self.LEVER_STRAIGHT
            horiz_y = lever_y_start + bend_r
            path.append((end_x * s, horiz_y * s, lever_cz * s))

        verts, faces = self._make_swept_tube(
            path, self.LEVER_RADIUS * s, segments=gfx.LEVER_TUBE_SEGMENTS
        )
        face_colors = self._normal_lit_face_colors(verts, faces, handle_color)
        mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=gfx.SMOOTH_CURVED_PARTS, drawEdges=False
        )
        if tr is not None:
            mesh.setTransform(tr)
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

    # =========================================================================
    # HJELPEMETODER
    # =========================================================================

    def _get_open_pivot(self, blade_x, blade_w, blade_y, blade_d, hinge_side, s):
        """Returnerer (vinkel, pivot_x, pivot_y, y_offset) for open-dør-rotasjon, eller None."""
        if not self._door_open:
            return None
        if hinge_side == 'left':
            px = blade_x * s
            angle = 90.0
        else:
            px = (blade_x + blade_w) * s
            angle = -90.0
        py = (blade_y + blade_d / 2) * s
        y_offset = blade_d * s
        return (angle, px, py, y_offset)

    @staticmethod
    def _build_open_transform(pivot):
        """Bygger QMatrix4x4 for åpen-dør-rotasjon rundt hengselkant."""
        if pivot is None:
            return None
        angle_deg, px, py, y_offset = pivot
        tr = QMatrix4x4()
        tr.translate(px, py + y_offset, 0)
        tr.rotate(angle_deg, 0, 0, 1)
        tr.translate(-px, -py, 0)
        return tr

    _FACE_LIGHT = gfx.BOX_FACE_LIGHT

    @staticmethod
    def _lit_face_colors(base_color, light_factors=None):
        """Beregn 12 flatefarger (2 trekanter × 6 sider) med retningsbasert lys."""
        if light_factors is None:
            light_factors = DoorPreview3D._FACE_LIGHT
        r, g, b, a = base_color[0], base_color[1], base_color[2], base_color[3]
        add = gfx.LIGHT_ADDITIVE
        colors = []
        for f in light_factors:
            c = (min(1.0, r * f + add), min(1.0, g * f + add), min(1.0, b * f + add), a)
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
        """Genererer vertices og faces for en boks."""
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
    def _make_rounded_rect(cx, cy, cz, width, height, depth, radius, segments=8):
        """Ekstrudert rektangel med avrundede hjørner, sentrert på (cx, cy, cz).

        Profil i XZ-planet, ekstrudert langs Y.
        """
        hw = width / 2
        hh = height / 2
        r = min(radius, hw, hh)

        # 2D-profil (X, Z) — fire hjørner med kvartssirkel
        corners = [
            (cx + hw - r, cz - hh + r, np.pi * 1.5, np.pi * 2.0),   # nedre høyre
            (cx + hw - r, cz + hh - r, 0.0,          np.pi * 0.5),   # øvre høyre
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
    def _make_swept_tube(path, radius, segments=24):
        """Rørform langs en bane (liste av (x, y, z) punkt)."""
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
    def _normal_lit_face_colors(verts, faces, base_color):
        """Per-face lys med ambient, diffuse og spekulær refleksjon."""
        light_dir = np.array(gfx.LIGHT_DIRECTION, dtype=float)
        light_dir = light_dir / np.linalg.norm(light_dir)
        view_dir = np.array(gfx.VIEW_DIRECTION, dtype=float)
        view_dir = view_dir / np.linalg.norm(view_dir)

        r, g, b, a = base_color
        ambient = gfx.LIGHT_AMBIENT
        diffuse = gfx.LIGHT_DIFFUSE
        specular = gfx.LIGHT_SPECULAR
        shininess = gfx.LIGHT_SHININESS

        colors = []
        for face in faces:
            v0, v1, v2 = verts[face[0]], verts[face[1]], verts[face[2]]
            normal = np.cross(v1 - v0, v2 - v0)
            norm_len = np.linalg.norm(normal)
            if norm_len > 0:
                normal = normal / norm_len

            # Diffus komponent
            n_dot_l = max(0.0, np.dot(normal, light_dir))
            diff = diffuse * n_dot_l

            # Spekulær komponent (Blinn-Phong)
            halfway = light_dir + view_dir
            halfway = halfway / np.linalg.norm(halfway)
            n_dot_h = max(0.0, np.dot(normal, halfway))
            spec = specular * (n_dot_h ** shininess) if n_dot_l > 0 else 0.0

            brightness = ambient + diff + spec
            add = gfx.LIGHT_ADDITIVE
            colors.append([min(1.0, r * brightness + add), min(1.0, g * brightness + add),
                           min(1.0, b * brightness + add), a])
        return np.array(colors)

    @staticmethod
    def _ral_to_rgba(ral_code: str, alpha: float = 1.0) -> tuple:
        """Konverterer RAL-kode til (r, g, b, a) tuple for OpenGL."""
        if ral_code in RAL_COLORS:
            r, g, b = RAL_COLORS[ral_code]['rgb']
            return (r, g, b, alpha)
        return (0.5, 0.5, 0.5, alpha)
