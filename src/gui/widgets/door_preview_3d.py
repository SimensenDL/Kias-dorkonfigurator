"""
3D-forhåndsvisning av konfigurert dør.
Bruker pyqtgraph OpenGL for interaktiv rotérbar visning.
"""
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QSurfaceFormat, QMatrix4x4, QColor

from ...models.door import DoorParams
from ...utils.constants import RAL_COLORS, POLYKARBONAT_COLORS, KARM_SIDESTOLPE_WIDTH
from ...utils.calculations import karm_bredde, karm_hoyde, dorblad_bredde, dorblad_hoyde, sparkeplate_bredde
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
KARM_DEPTHS = {'SD1': 77, 'SD2': 84, 'SD3/ID': 92, 'KD1': 97, 'KD2': 104,
               'PD1': 77, 'PD2': 84, 'BD1': 77,
               'FD1': 97, 'FD2': 104, 'FD3': 112}
BLADE_GAP = 4                            # mm gap mellom 2 dørblad
SPARKEPLATE_THICKNESS = 1                # mm tykkelse
SPARKEPLATE_COLOR = (0.0, 0.0, 0.0, 1.0)  # Svart
KLEMSIKRING_COLOR = (0.05, 0.05, 0.05, 1.0)  # Svart silikon
PIVOT_PLATE_COLOR = (0.75, 0.75, 0.73, 1.0)  # Sølv/aluminium hengsleplate
PIVOT_HOLE_COLOR = (0.08, 0.08, 0.08, 1.0)   # Mørke skruehull
RYGGFORST_DEPTH = 40    # mm — dybde ryggforsterkning (lik PDI-bladtykkelse)
RYGGFORST_OVERLAP = 10  # mm — sidestolpe overlapper bladkant innover


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
    HANDLE_CENTER_HEIGHT = 1020          # mm fra gulv (senter håndtak, uten sparkeplate)
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
        kb = karm_bredde(door.karm_type, bm, adjufix=door.adjufix)
        kh = karm_hoyde(door.karm_type, hm)

        # Karm-profil
        profile = KARM_PROFILES[door.karm_type]
        luftspalte_mm = profile.luftspalte(door)

        # Dørblad-dimensjoner
        blade_t_mm = door.blade_thickness
        karm_depth = KARM_DEPTHS.get(door.karm_type, 77)
        sidestolpe_w = KARM_SIDESTOLPE_WIDTH.get(door.karm_type, 80)

        # 1. Vegg (alltid bygd, synlighet styrt av toggle)
        self._add_wall(bm, hm, wall_t, s, door.wall_color)

        # 2. Karm — bygd fra profil
        karm_color = np.array(self._ral_to_rgba(door.karm_color))
        parts = profile.build_frame_parts(door, kb, kh, wall_t, karm_depth, sidestolpe_w)
        for (bx, by, bz, dx, dy, dz) in parts:
            mesh = self._add_mesh(
                bx * s, by * s, bz * s, dx * s, dy * s, dz * s,
                karm_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)

        # 2b. Klemsikring (PDI)
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        if door_def.get('klemsikring', False):
            self._add_klemsikring(door, profile, kb, kh, wall_t, karm_depth, s)

        # 4. Dørblad
        self._add_door_blades(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 4b. Ryggforsterkning (PDPC/PDPO)
        if door_def.get('ryggforsterkning_hoyde_offset'):
            self._add_ryggforsterkning(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 5. Slepelist (terskel under dørblad)
        if door.threshold_type == 'slepelist':
            self._add_slepelist(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 6. Hengsler
        self._add_hinges(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 7. Håndtak (ikke for pendeldører)
        if not door_def.get('pendeldor', False):
            self._add_handle(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

        # 7. Sparkeplater (for alle dørtyper med sparkeplate aktivert)
        if door.sparkeplate:
            self._add_sparkeplater(door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s)

    # =========================================================================
    # VEGG
    # =========================================================================

    def _add_wall(self, bm, hm, wall_t, s, wall_color_hex="#8C8C84"):
        """Vegg med rektangulær utsparing (BM x HM). Semi-transparent."""
        M = WALL_MARGIN
        qc = QColor(wall_color_hex)
        color = np.array((qc.redF(), qc.greenF(), qc.blueF(), WALL_COLOR[3]))
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
    # SLEPELIST (TERSKEL)
    # =========================================================================

    def _add_slepelist(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Slepelist under hvert dørblad — følger bladet ved åpning."""
        sl_color = np.array(SPARKEPLATE_COLOR)  # Svart
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)
        sl_h = 22  # mm, samme som luftspalte
        sl_depth = blade_t_mm  # Like tykk som dørbladet

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)

        for (bcx, b_w, b_h, _count, hinge_side) in blades:
            blade_x = bcx - b_w / 2
            eff_x, eff_w, eff_y, eff_d = self._effective_pivot_params(
                door, blade_x, b_w, blade_y, blade_t_mm,
                kb=kb, hinge_side=hinge_side
            )
            pivot = self._get_open_pivot(eff_x, eff_w, eff_y, eff_d, hinge_side, s)

            verts, faces = self._make_box(
                blade_x * s, blade_y * s, 0,
                b_w * s, sl_depth * s, sl_h * s
            )
            face_colors = self._lit_face_colors(sl_color)
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
    # DØRBLAD
    # =========================================================================

    def _add_door_blades(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Dørblad med produksjonsmål fra calculations.py."""
        blade_color = np.array(self._ral_to_rgba(door.color))
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)

        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.hinge_type, door_type=door.door_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.hinge_type, luftspalte_mm, door_type=door.door_type)
            if db_b and db_h:
                # 3D-koord er speilvendt: inverter slagretning for korrekt visuell plassering
                hinge_3d = 'right' if door.swing_direction == 'left' else 'left'
                # Ryggforsterkning: skyv blad til karmkant på ikke-hengselsiden
                door_def_b = DOOR_REGISTRY.get(door.door_type, {})
                if 'ryggforsterkning_hoyde_offset' in door_def_b:
                    anslag_inner = 80
                    if hinge_3d == 'left':
                        blade_x = kb / 2 - anslag_inner - db_b
                    else:
                        blade_x = -kb / 2 + anslag_inner
                else:
                    offset_x = self._klemsikring_blade_offset(door)
                    blade_x = -db_b / 2 + offset_x
                eff_x, eff_w, eff_y, eff_d = self._effective_pivot_params(
                    door, blade_x, db_b, blade_y, blade_t_mm,
                    kb=kb, hinge_side=hinge_3d
                )
                pivot = self._get_open_pivot(eff_x, eff_w, eff_y, eff_d, hinge_3d, s)
                self._render_single_blade(
                    blade_x, blade_y, luftspalte_mm,
                    db_b, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot
                )
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.hinge_type, door_type=door.door_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.hinge_type, luftspalte_mm, door_type=door.door_type)
            if db_b_total and db_h:
                db1_b = round(db_b_total * door.floyer_split / 100)
                db2_b = db_b_total - db1_b

                # Primærblad (aktivt) plasseres på slagretning-siden
                if door.swing_direction == 'left':
                    left_w, right_w = db1_b, db2_b
                else:
                    left_w, right_w = db2_b, db1_b

                total_w = left_w + BLADE_GAP + right_w
                start_x = -total_w / 2

                # Visuelt høyre blad (negativ X i 3D), hengsler på ytre kant
                right_x = start_x
                eff_rx, eff_rw, eff_ry, eff_rd = self._effective_pivot_params(
                    door, right_x, right_w, blade_y, blade_t_mm,
                    kb=kb, hinge_side='left'
                )
                pivot_r = self._get_open_pivot(eff_rx, eff_rw, eff_ry, eff_rd, 'left', s)
                self._render_single_blade(
                    right_x, blade_y, luftspalte_mm,
                    right_w, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot_r
                )
                # Visuelt venstre blad (positiv X i 3D), hengsler på ytre kant
                left_x = start_x + right_w + BLADE_GAP
                eff_lx, eff_lw, eff_ly, eff_ld = self._effective_pivot_params(
                    door, left_x, left_w, blade_y, blade_t_mm,
                    kb=kb, hinge_side='right'
                )
                pivot_l = self._get_open_pivot(eff_lx, eff_lw, eff_ly, eff_ld, 'right', s)
                self._render_single_blade(
                    left_x, blade_y, luftspalte_mm,
                    left_w, blade_t_mm, db_h,
                    blade_color, s, pivot=pivot_l
                )

    def _render_single_blade(self, x, y, z, w, d, h, color, s, pivot=None):
        """Tegner ett dørblad med retningsbasert lys."""
        verts, faces = self._make_box(x * s, y * s, z * s, w * s, d * s, h * s)
        face_colors = self._lit_face_colors(color)

        kwargs = dict(
            vertexes=verts, faces=faces, faceColors=face_colors,
            smooth=False, drawEdges=False
        )
        if color[3] < 1.0:
            kwargs['glOptions'] = 'translucent'
        mesh = gl.GLMeshItem(**kwargs)
        tr = self._build_open_transform(pivot)
        if tr is not None:
            mesh.setTransform(tr)
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)
        self._blade_items.append(mesh)
        mesh.setVisible(self._show_blades)

    # =========================================================================
    # RYGGFORSTERKNING (PDPC/PDPO)
    # =========================================================================

    def _add_ryggforsterkning(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """U-formet aluminiumsramme (2 sider + overdel) rundt hvert dørblad.

        PDPC/PDPO har 5mm polykarbonat-blad som trenger ryggforsterkning
        for å gi 40mm total dybde der pivot-hengsler monteres.
        """
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        h_offset = door_def.get('ryggforsterkning_hoyde_offset', 99)  # 99mm
        o_offset = door_def.get('ryggforsterkning_overdel_offset', 98)  # 98mm
        side_w = o_offset / 2  # 49mm

        # Natureloksert aluminium (sølvgrå med svak varm tone)
        frame_color = np.array([0.75, 0.73, 0.70, 1.0])
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)
        # Rammen er 40mm dyp, sentrert rundt 5mm bladet
        frame_y = blade_y + blade_t_mm / 2 - RYGGFORST_DEPTH / 2

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)

        is_double = door.floyer == 2

        for (bcx, b_w, b_h, _count, hinge_side) in blades:
            blade_x = bcx - b_w / 2
            side_h = b_h + h_offset  # Sidestolpe-høyde

            # Pivot basert på rammens dimensjoner
            eff_x, eff_w, eff_y, eff_d = self._effective_pivot_params(
                door, blade_x, b_w, blade_y, blade_t_mm,
                kb=kb, hinge_side=hinge_side
            )
            pivot = self._get_open_pivot(eff_x, eff_w, eff_y, eff_d, hinge_side, s)

            parts = []
            lap = RYGGFORST_OVERLAP

            if is_double:
                # 2-fløyet: sidestolpe fra etter klemsikring (35mm) + 5mm margin
                klem_offset = 120  # anslag(80) + klemsikring(35) + margin(5)
                if hinge_side == 'left':
                    outer_x = -kb / 2 + klem_offset
                    post_w = blade_x + lap - outer_x
                    parts.append((outer_x, frame_y, luftspalte_mm,
                                  post_w, RYGGFORST_DEPTH, side_h))
                    parts.append((outer_x, frame_y, luftspalte_mm + b_h,
                                  blade_x + b_w - outer_x, RYGGFORST_DEPTH, h_offset))
                else:
                    outer_x = kb / 2 - klem_offset
                    post_w = outer_x - (blade_x + b_w - lap)
                    parts.append((blade_x + b_w - lap, frame_y, luftspalte_mm,
                                  post_w, RYGGFORST_DEPTH, side_h))
                    parts.append((blade_x, frame_y, luftspalte_mm + b_h,
                                  outer_x - blade_x, RYGGFORST_DEPTH, h_offset))
            else:
                # 1-fløyet: sidestolpe fra klemsikring + overdel, kun hengslesiden
                klem_offset = 120  # anslag(80) + klemsikring(35) + margin(5)
                if hinge_side == 'left':
                    outer_x = -kb / 2 + klem_offset
                    post_w = blade_x + lap - outer_x
                    parts.append((outer_x, frame_y, luftspalte_mm,
                                  post_w, RYGGFORST_DEPTH, side_h))
                    parts.append((outer_x, frame_y, luftspalte_mm + b_h,
                                  blade_x + b_w - outer_x, RYGGFORST_DEPTH, h_offset))
                else:
                    outer_x = kb / 2 - klem_offset
                    post_w = outer_x - (blade_x + b_w - lap)
                    parts.append((blade_x + b_w - lap, frame_y, luftspalte_mm,
                                  post_w, RYGGFORST_DEPTH, side_h))
                    parts.append((blade_x, frame_y, luftspalte_mm + b_h,
                                  outer_x - blade_x, RYGGFORST_DEPTH, h_offset))

            for (bx, by, bz, dx, dy, dz) in parts:
                verts, faces = self._make_box(
                    bx * s, by * s, bz * s, dx * s, dy * s, dz * s
                )
                face_colors = self._lit_face_colors(frame_color)
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
        hinge_color = np.array([0.478, 0.478, 0.478, 1.0])
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        is_pendel = door_def.get('pendeldor', False)

        total_hinges = self._get_hinge_count(door)
        blade_y_pos = profile.blade_y(wall_t, blade_t_mm, karm_depth)

        # Bygg liste over blad å feste hengsler på
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)

        if is_pendel:
            self._add_pivot_hinges(door, blades, blade_y_pos, blade_t_mm, luftspalte_mm, hinge_color, s, kb)
        else:
            hw = self.HINGE_WIDTH
            hh = self.HINGE_HEIGHT
            hd = self.HINGE_DEPTH
            hy = profile.hinge_y(wall_t, blade_t_mm, karm_depth, hd)

            for (bcx, b_w, b_h, count, hinge_side) in blades:
                blade_x = bcx - b_w / 2
                pivot = self._get_open_pivot(blade_x, b_w, blade_y_pos, blade_t_mm, hinge_side, s)
                tr = self._build_open_transform(pivot)

                z_positions = self._hinge_z_positions(b_h, max(count, 2))

                for z_center in z_positions:
                    hz = luftspalte_mm + z_center - hh / 2
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

    def _add_pivot_hinges(self, door, blades, blade_y_pos, blade_t_mm, luftspalte_mm, hinge_color, s, kb=None):
        """Pivot-hengsler (KIAS 92 stop) for pendeldører — én solid boks per hengsel."""
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        has_rygg = 'ryggforsterkning_hoyde_offset' in door_def

        # Dimensjoner (mm)
        pw = 80   # Bredde (X)
        if has_rygg:
            pd = RYGGFORST_DEPTH + 2 + 2  # 44mm: rammedybde + 2mm plate på hver side
            frame_y = blade_y_pos + blade_t_mm / 2 - RYGGFORST_DEPTH / 2
            py = frame_y - 2
        else:
            pd = blade_t_mm + 2 + 2
            py = blade_y_pos - 2
        ph = 60   # Høyde (Z)

        h_offset = door_def.get('ryggforsterkning_hoyde_offset', 0)
        is_double = door.floyer == 2

        for (bcx, b_w, b_h, count, hinge_side) in blades:
            blade_x = bcx - b_w / 2
            if has_rygg and kb is not None:
                # Hengsler etter klemsikring (35mm) + 5mm margin
                klem_offset = 120  # anslag(80) + klemsikring(35) + margin(5)
                if hinge_side == 'left':
                    px = -kb / 2 + klem_offset
                else:
                    px = kb / 2 - klem_offset - pw
            else:
                overhang = 5  # mm utenfor bladkanten
                if hinge_side == 'left':
                    px = blade_x - overhang
                else:
                    px = blade_x + b_w + overhang - pw

            # Hengsel-Z basert på rammehøyde (inkl. ryggforsterkning)
            ref_h = b_h + h_offset if has_rygg else b_h
            z_positions = self._hinge_z_positions(ref_h, max(count, 2))

            # Skruehull-dimensjoner og 2×2 mønster (relativt til hengselets hjørne)
            hole_size = 8   # mm
            hole_t = 0.3    # mm tykkelse
            hole_offsets_x = [pw * 0.25 - hole_size / 2, pw * 0.75 - hole_size / 2]
            hole_offsets_z = [ph * 0.25 - hole_size / 2, ph * 0.75 - hole_size / 2]

            for z_center in z_positions:
                pz = luftspalte_mm + z_center - ph / 2

                # Hengselkropp
                verts, faces = self._make_box(
                    px * s, py * s, pz * s, pw * s, pd * s, ph * s
                )
                face_colors = self._normal_lit_face_colors(verts, faces, PIVOT_PLATE_COLOR)
                mesh = gl.GLMeshItem(
                    vertexes=verts, faces=faces, faceColors=face_colors,
                    smooth=False, drawEdges=False
                )
                self._gl_widget.addItem(mesh)
                self._mesh_items.append(mesh)
                self._blade_items.append(mesh)
                mesh.setVisible(self._show_blades)

                # 4 skruehull på fram- og bakside
                for hox in hole_offsets_x:
                    for hoz in hole_offsets_z:
                        hx = px + hox
                        hz = pz + hoz
                        for face_y in (py + pd, py - hole_t):  # fram / bak
                            verts, faces = self._make_box(
                                hx * s, face_y * s, hz * s,
                                hole_size * s, hole_t * s, hole_size * s
                            )
                            face_colors = self._normal_lit_face_colors(verts, faces, PIVOT_HOLE_COLOR)
                            mesh = gl.GLMeshItem(
                                vertexes=verts, faces=faces, faceColors=face_colors,
                                smooth=False, drawEdges=False
                            )
                            self._gl_widget.addItem(mesh)
                            self._mesh_items.append(mesh)
                            self._blade_items.append(mesh)
                            mesh.setVisible(self._show_blades)

    def _get_hinge_count(self, door) -> int:
        """Hent hengselantall fra DoorParams."""
        count = door.hinge_count
        if door.floyer == 2:
            count *= 2  # Per fløy → totalt
        return count if count > 0 else 2

    HINGE_EDGE_OFFSET = 250  # mm fra bunn/topp av dørblad til nærmeste hengsel (senter)

    def _hinge_z_positions(self, blade_h, count):
        """Returnerer hengsel-senterposisjoner (mm fra bunn av dørblad)."""
        d = self.HINGE_EDGE_OFFSET
        bottom = d
        top = blade_h - d
        if count == 2:
            return [bottom, top]
        elif count == 3:
            return [bottom, top, blade_h - 2 * d]
        elif count == 4:
            return [bottom, top, blade_h - 2 * d, 2 * d]
        else:
            positions = [bottom, top]
            inner_start = 2 * d
            inner_end = blade_h - 2 * d
            extras = count - 2
            for i in range(extras):
                positions.append(inner_start + (inner_end - inner_start) * i / max(extras - 1, 1))
            return positions

    def _get_blade_geometries(self, door, kb, kh, luftspalte_mm, total_hinges):
        """Returnerer liste av (senter_x, bredde, høyde, hengsler_per_blad, hengselside) for hvert blad.

        hengselside er 'left' eller 'right' — angir hvilken kant hengselet sitter på.
        """
        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.hinge_type, door_type=door.door_type) or (kb - 128)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.hinge_type, luftspalte_mm, door_type=door.door_type) or (kh - 85)
            # 3D-koord er speilvendt: inverter slagretning for korrekt visuell plassering
            hinge_3d = 'right' if door.swing_direction == 'left' else 'left'
            per_blade = max(1, total_hinges)
            # Ryggforsterkning 1-fløyet: skyv blad til karmkant på ikke-hengselsiden
            door_def = DOOR_REGISTRY.get(door.door_type, {})
            if 'ryggforsterkning_hoyde_offset' in door_def:
                anslag_inner = 80  # list(60) + anslag(20)
                if hinge_3d == 'left':
                    offset_x = kb / 2 - anslag_inner - db_b / 2
                else:
                    offset_x = -kb / 2 + anslag_inner + db_b / 2
            else:
                offset_x = self._klemsikring_blade_offset(door)
            return [(offset_x, db_b, db_h, per_blade, hinge_3d)]
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.hinge_type, door_type=door.door_type) or (kb - 132)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.hinge_type, luftspalte_mm, door_type=door.door_type) or (kh - 85)
            db1_b = round(db_b_total * door.floyer_split / 100)
            db2_b = db_b_total - db1_b
            per_blade = max(1, total_hinges // 2)

            # Primærblad (aktivt) plasseres på slagretning-siden
            if door.swing_direction == 'left':
                left_w, right_w = db1_b, db2_b
            else:
                left_w, right_w = db2_b, db1_b

            total_w = left_w + BLADE_GAP + right_w
            # Visuelt høyre (negativ X i 3D), visuelt venstre (positiv X)
            right_cx = -total_w / 2 + right_w / 2
            left_cx = -total_w / 2 + right_w + BLADE_GAP + left_w / 2
            return [(left_cx, left_w, db_h, per_blade, 'right'),
                    (right_cx, right_w, db_h, per_blade, 'left')]

    # =========================================================================
    # HÅNDTAK
    # =========================================================================

    def _add_handle(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Skilthåndtak på motsatt side av hengslene."""
        margin = self.HANDLE_X_MARGIN
        handle_color = np.array([0.478, 0.478, 0.478, 1.0])

        total_hinges = self._get_hinge_count(door)
        blades = self._get_blade_geometries(door, kb, kh, luftspalte_mm, total_hinges)
        # Håndtak på aktivt blad (slagretning-siden)
        if door.floyer == 2 and door.swing_direction == 'right':
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
        plate_cz = door.sparkeplate_hoyde + 100 + door.effective_luftspalte()

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

        # --- Bakside skilt (speilet i Y-retning) ---
        back_plate_y = blade_y
        back_plate_cy = back_plate_y - self.PLATE_DEPTH / 2

        verts, faces = self._make_rounded_rect(
            plate_cx * s, back_plate_cy * s, plate_cz * s,
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

        # Grep (bue fra skilt + rett spak) — framside
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

        # --- Bakside grep (speilet i Y-retning) ---
        back_lever_y_start = back_plate_y - self.PLATE_DEPTH

        back_path = []
        if hinge_side == 'left':
            arc_cx = plate_cx - bend_r
            arc_cy = back_lever_y_start
            for i in range(bend_segs + 1):
                angle = i * (np.pi / 2) / bend_segs
                px = arc_cx + bend_r * np.cos(angle)
                py = arc_cy - bend_r * np.sin(angle)
                back_path.append((px * s, py * s, lever_cz * s))
            end_x = plate_cx - bend_r - self.LEVER_STRAIGHT
            horiz_y = back_lever_y_start - bend_r
            back_path.append((end_x * s, horiz_y * s, lever_cz * s))
        else:
            arc_cx = plate_cx + bend_r
            arc_cy = back_lever_y_start
            for i in range(bend_segs + 1):
                angle = np.pi - i * (np.pi / 2) / bend_segs
                px = arc_cx + bend_r * np.cos(angle)
                py = arc_cy - bend_r * np.sin(angle)
                back_path.append((px * s, py * s, lever_cz * s))
            end_x = plate_cx + bend_r + self.LEVER_STRAIGHT
            horiz_y = back_lever_y_start - bend_r
            back_path.append((end_x * s, horiz_y * s, lever_cz * s))

        verts, faces = self._make_swept_tube(
            back_path, self.LEVER_RADIUS * s, segments=gfx.LEVER_TUBE_SEGMENTS
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
    # SPARKEPLATER
    # =========================================================================

    def _add_sparkeplater(self, door, profile, kb, kh, wall_t, blade_t_mm, karm_depth, luftspalte_mm, s):
        """Sparkeplater på begge sider av hvert dørblad (pendeldører)."""
        sp_color = np.array(SPARKEPLATE_COLOR)
        blade_y = profile.blade_y(wall_t, blade_t_mm, karm_depth)
        sp_t = SPARKEPLATE_THICKNESS

        # Sparkeplater monteres alltid på dørbladets overflate (5mm for PDPC/PDPO)
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        has_rygg = 'ryggforsterkning_hoyde_offset' in door_def
        sp_surface_y = blade_y
        sp_surface_depth = blade_t_mm

        if door.floyer == 1:
            db_b = dorblad_bredde(door.karm_type, kb, 1, door.hinge_type, door_type=door.door_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 1, door.hinge_type, luftspalte_mm, door_type=door.door_type)
            if db_b and db_h:
                sp_b = sparkeplate_bredde(door.door_type, db_b)
                if sp_b:
                    sp_h = min(door.sparkeplate_hoyde, db_h)
                    hinge_3d = 'right' if door.swing_direction == 'left' else 'left'
                    if has_rygg:
                        anslag_inner = 80
                        if hinge_3d == 'left':
                            blade_x = kb / 2 - anslag_inner - db_b
                        else:
                            blade_x = -kb / 2 + anslag_inner
                    else:
                        offset_x = self._klemsikring_blade_offset(door)
                        blade_x = -db_b / 2 + offset_x
                    sp_x = blade_x + (db_b - sp_b) / 2
                    eff_x, eff_w, eff_y, eff_d = self._effective_pivot_params(
                        door, blade_x, db_b, blade_y, blade_t_mm,
                        kb=kb, hinge_side=hinge_3d
                    )
                    pivot = self._get_open_pivot(eff_x, eff_w, eff_y, eff_d, hinge_3d, s)
                    # Framside
                    self._render_sparkeplate(sp_x, sp_surface_y + sp_surface_depth, luftspalte_mm, sp_b, sp_t, sp_h, sp_color, s, pivot)
                    # Bakside
                    self._render_sparkeplate(sp_x, sp_surface_y - sp_t, luftspalte_mm, sp_b, sp_t, sp_h, sp_color, s, pivot)
        else:
            db_b_total = dorblad_bredde(door.karm_type, kb, 2, door.hinge_type, door_type=door.door_type)
            db_h = dorblad_hoyde(door.karm_type, kh, 2, door.hinge_type, luftspalte_mm, door_type=door.door_type)
            if db_b_total and db_h:
                db1_b = round(db_b_total * door.floyer_split / 100)
                db2_b = db_b_total - db1_b

                if door.swing_direction == 'left':
                    left_w, right_w = db1_b, db2_b
                else:
                    left_w, right_w = db2_b, db1_b

                total_w = left_w + BLADE_GAP + right_w
                start_x = -total_w / 2

                sp_h = min(door.sparkeplate_hoyde, db_h)

                # Visuelt høyre blad
                right_x = start_x
                sp_b_r = sparkeplate_bredde(door.door_type, right_w)
                if sp_b_r:
                    sp_x_r = right_x + (right_w - sp_b_r) / 2
                    eff_rx, eff_rw, eff_ry, eff_rd = self._effective_pivot_params(
                        door, right_x, right_w, blade_y, blade_t_mm,
                        kb=kb, hinge_side='left'
                    )
                    pivot_r = self._get_open_pivot(eff_rx, eff_rw, eff_ry, eff_rd, 'left', s)
                    self._render_sparkeplate(sp_x_r, sp_surface_y + sp_surface_depth, luftspalte_mm, sp_b_r, sp_t, sp_h, sp_color, s, pivot_r)
                    self._render_sparkeplate(sp_x_r, sp_surface_y - sp_t, luftspalte_mm, sp_b_r, sp_t, sp_h, sp_color, s, pivot_r)

                # Visuelt venstre blad
                left_x = start_x + right_w + BLADE_GAP
                sp_b_l = sparkeplate_bredde(door.door_type, left_w)
                if sp_b_l:
                    sp_x_l = left_x + (left_w - sp_b_l) / 2
                    eff_lx, eff_lw, eff_ly, eff_ld = self._effective_pivot_params(
                        door, left_x, left_w, blade_y, blade_t_mm,
                        kb=kb, hinge_side='right'
                    )
                    pivot_l = self._get_open_pivot(eff_lx, eff_lw, eff_ly, eff_ld, 'right', s)
                    self._render_sparkeplate(sp_x_l, sp_surface_y + sp_surface_depth, luftspalte_mm, sp_b_l, sp_t, sp_h, sp_color, s, pivot_l)
                    self._render_sparkeplate(sp_x_l, sp_surface_y - sp_t, luftspalte_mm, sp_b_l, sp_t, sp_h, sp_color, s, pivot_l)

    def _render_sparkeplate(self, x, y, z, w, d, h, color, s, pivot=None):
        """Tegner én sparkeplate med retningsbasert lys."""
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
    # KLEMSIKRING
    # =========================================================================

    def _klemsikring_blade_offset(self, door):
        """Returnerer X-offset for dørblad pga. klemsikring (kun PDI 1-fløyet)."""
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        if not door_def.get('klemsikring', False) or door.floyer != 1:
            return 0
        bredde = door_def.get('klemsikring_bredde', 8)
        hinge_3d = 'right' if door.swing_direction == 'left' else 'left'
        if hinge_3d == 'left':
            return bredde / 2
        else:
            return -bredde / 2

    def _add_klemsikring(self, door, profile, kb, kh, wall_t, karm_depth, s):
        """Tegner svarte klemsikring-striper på innsiden av anslagene."""
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        ks_bredde = door_def.get('klemsikring_bredde', 8)
        ks_color = np.array(KLEMSIKRING_COLOR)

        list_w = 60    # listverk bredde
        anslag_w = 20  # anslag bredde

        # Klemsikring-dimensjoner
        ks_depth = door.blade_thickness  # Dekker hele bladtykkelsen
        blade_y = profile.blade_y(wall_t, door.blade_thickness, karm_depth)
        ks_y = blade_y
        ks_h = kh - list_w  # Full anslagshøyde

        # Anslag innerkant: -kb/2 + list_w + anslag_w = -kb/2 + 80
        left_x = -kb / 2 + list_w + anslag_w
        right_x = kb / 2 - list_w - anslag_w - ks_bredde

        if door.floyer == 1:
            # Kun på hengslesiden
            hinge_3d = 'right' if door.swing_direction == 'left' else 'left'
            if hinge_3d == 'left':
                # Hengsel på negativ X (visuelt høyre) → klemsikring på venstre side
                x = left_x
            else:
                # Hengsel på positiv X (visuelt venstre) → klemsikring på høyre side
                x = right_x
            mesh = self._add_mesh(
                x * s, ks_y * s, 0,
                ks_bredde * s, ks_depth * s, ks_h * s,
                ks_color, is_frame=True
            )
            mesh.setVisible(self._show_frame)
        else:
            # 2-fløyet: begge sider
            for x in [left_x, right_x]:
                mesh = self._add_mesh(
                    x * s, ks_y * s, 0,
                    ks_bredde * s, ks_depth * s, ks_h * s,
                    ks_color, is_frame=True
                )
                mesh.setVisible(self._show_frame)

    # =========================================================================
    # HJELPEMETODER
    # =========================================================================

    def _effective_pivot_params(self, door, blade_x, blade_w, blade_y, blade_t,
                                kb=None, hinge_side=None):
        """Returnerer (eff_x, eff_w, eff_y, eff_d) for pivot-beregning.

        Når ryggforsterkning finnes (PDPC/PDPO), brukes rammens dimensjoner
        i stedet for bladets for korrekt rotasjon rundt hengselkant.
        For 2-fløyet strekker rammen seg fra karm innerkant til over bladet.
        """
        door_def = DOOR_REGISTRY.get(door.door_type, {})
        if 'ryggforsterkning_hoyde_offset' in door_def:
            frame_y = blade_y + blade_t / 2 - RYGGFORST_DEPTH / 2
            if kb is not None and hinge_side is not None:
                # Ramme fra etter klemsikring (35mm) + 5mm margin
                klem_offset = 120  # anslag(80) + klemsikring(35) + margin(5)
                lap = RYGGFORST_OVERLAP
                if hinge_side == 'left':
                    outer_x = -kb / 2 + klem_offset
                    return (outer_x, blade_x + blade_w + lap - outer_x,
                            frame_y, RYGGFORST_DEPTH)
                else:
                    outer_x = kb / 2 - klem_offset
                    return (blade_x - lap, outer_x - blade_x + lap,
                            frame_y, RYGGFORST_DEPTH)
            else:
                # Fallback uten kb/hinge_side
                side_w = door_def['ryggforsterkning_overdel_offset'] / 2  # 49mm
                return (blade_x - side_w, blade_w + 2 * side_w,
                        frame_y, RYGGFORST_DEPTH)
        return (blade_x, blade_w, blade_y, blade_t)

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
        """Konverterer RAL-kode eller polykarbonat-farge til (r, g, b, a) tuple for OpenGL."""
        if ral_code in RAL_COLORS:
            r, g, b = RAL_COLORS[ral_code]['rgb']
            return (r, g, b, alpha)
        if ral_code in POLYKARBONAT_COLORS:
            entry = POLYKARBONAT_COLORS[ral_code]
            r, g, b = entry['rgb']
            return (r, g, b, entry.get('alpha', alpha))
        return (0.5, 0.5, 0.5, alpha)
