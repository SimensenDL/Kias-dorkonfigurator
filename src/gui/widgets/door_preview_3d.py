"""
3D-forhåndsvisning av konfigurert dør.
Bruker pyqtgraph OpenGL for interaktiv rotérbar visning.
"""
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QMouseEvent

from ...models.door import DoorParams
from ...utils.constants import RAL_COLORS

# Betinget import med fallback
try:
    import pyqtgraph.opengl as gl
    HAS_3D = True
except ImportError:
    HAS_3D = False


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
    """
    3D-forhåndsvisning av en konfigurert dør.

    Viser dør med karm, farge, glass, håndtak og hengsler.
    Rotérbar visning med mus (venstre: roter, midtre/høyre: pan, scroll: zoom).
    """

    # Skaleringsfaktor: konverterer mm til 3D-enheter (1 enhet = 100 mm)
    SCALE = 1.0 / 100.0

    # Standard sidestolpe-bredde (fallback, mm)
    DEFAULT_FRAME_WIDTH = 50

    # Dørblad fast tykkelse (mm)
    DOOR_BLADE_THICKNESS = 40

    # Glasspanel-standardposisjon (Y-ratio fra bunn)
    GLASS_DEFAULT_Y_RATIO = 0.65

    # Håndtak-dimensjoner (mm)
    HANDLE_WIDTH = 20
    HANDLE_HEIGHT = 120
    HANDLE_DEPTH = 30
    HANDLE_Y_RATIO = 0.47
    HANDLE_X_MARGIN = 80

    # Hengsel-dimensjoner (mm)
    HINGE_WIDTH = 15
    HINGE_HEIGHT = 60
    HINGE_DEPTH = 8
    HINGE_POSITIONS = [0.15, 0.50, 0.85]

    # Karmprofil-dimensjoner (mm)
    KARM_FALS_DEPTH = 15        # Dybde på fals/anslag
    KARM_FALS_WIDTH = 12        # Bredde på fals (hvor mye den stikker inn)
    KARM_FRONT_THICKNESS = 20   # Tykkelse på framkant
    KARM_UTFORING_THICKNESS = 8 # Tykkelse på utforing-"ben"

    # Karmtyper gruppert etter profiltype
    KARM_TYPE_1 = {'SD1', 'KD1', 'YD1', 'PD1', 'BD1'}  # U-profil med utforing
    KARM_TYPE_2 = {'SD2', 'KD2', 'YD2', 'PD2', 'BD2'}  # L-profil
    KARM_TYPE_3 = {'SD3/ID1', 'KD3', 'YD3'}            # Enkel profil, sentrert

    def __init__(self, parent=None):
        super().__init__(parent)
        self._door: Optional[DoorParams] = None
        self._mesh_items: list = []
        self._gl_widget = None
        self._init_ui()

    def _init_ui(self):
        """Initialiserer 3D-visning eller viser feilmelding."""
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
            self._gl_widget = _PanGLViewWidget()
            self._gl_widget.setBackgroundColor(50, 50, 55, 255)
            layout.addWidget(self._gl_widget)

            # Bakgrunnsgrid for romlig referanse
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

    def _setup_camera(self):
        """Setter opp initialt kameraperspektiv."""
        self._gl_widget.setCameraPosition(
            distance=30,
            elevation=15,
            azimuth=-30
        )
        self._gl_widget.pan(0, 0, 10)

    def update_door(self, door: DoorParams) -> None:
        """
        Oppdaterer 3D-visningen med nye dørparametere.

        Args:
            door: Oppdatert DoorParams
        """
        if self._gl_widget is None:
            return
        self._door = door
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        """Fjerner alle mesh-elementer og bygger scenen på nytt."""
        if self._gl_widget is None:
            return

        for item in self._mesh_items:
            self._gl_widget.removeItem(item)
        self._mesh_items.clear()

        if self._door is None:
            return

        door = self._door
        s = self.SCALE

        # Karmmål (beregnet fra utsparing + offset)
        karm_w = door.karm_width() * s
        karm_h = door.karm_height() * s
        frame_depth = door.thickness * s  # Karmdybde = veggtykkelse

        # Dørbladmål (transportmål basert på karmtype og terskel)
        blade_w = door.blade_width() * s
        blade_h = door.blade_height() * s
        blade_t = door.blade_thickness * s  # Dørbladtykkelse fra parametere

        # Sidestolpe-bredde fra karmtype
        sidestolpe_w = door.sidestolpe_width() * s

        # Luftspalte ved gulv
        luftspalte = door.effective_luftspalte() * s

        # Dørbladets topp-posisjon (for å beregne toppstykke i karmen)
        blade_top = luftspalte + blade_h

        # Velg karmprofil basert på karmtype
        if door.karm_type in self.KARM_TYPE_1:
            self._add_frame_type1(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)
        elif door.karm_type in self.KARM_TYPE_2:
            self._add_frame_type2(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)
        else:
            self._add_frame_type3(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)

        self._add_door_body(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)
        self._add_handle(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)
        self._add_hinges(door, blade_w, blade_h, blade_t, frame_depth, luftspalte)

        if door.has_window:
            self._add_glass_panel(door, blade_w, blade_h, blade_t, luftspalte)

    def _add_frame_type1(self, door: DoorParams, blade_w: float, blade_h: float,
                          blade_t: float, frame_depth: float, luftspalte: float):
        """Type 1 karm: U-profil med utforing (SD1, KD1, YD1, PD1, BD1).

        U-profilen har:
        - Framkant med fals der dørbladet hviler
        - To "ben" som strekker seg bakover inn i veggen
        - Utforing som fyller gapet til veggen
        """
        s = self.SCALE
        karm_color = np.array(self._ral_to_rgba(door.karm_color))

        # Dimensjoner
        sidestolpe = door.sidestolpe_width() * s
        front_t = self.KARM_FRONT_THICKNESS * s  # Framkant tykkelse
        fals_d = self.KARM_FALS_DEPTH * s        # Fals dybde (Y)
        fals_w = self.KARM_FALS_WIDTH * s        # Fals bredde (hvor mye den stikker inn)
        utforing_t = self.KARM_UTFORING_THICKNESS * s

        # Høyde (fra gulv til over dørbladet)
        karm_h = luftspalte + blade_h + 5 * s  # 5mm over dørbladet

        # Dørbladet er flush med framkant
        # Framkant Y-posisjon: blade_y + blade_t = frame_depth/2
        blade_y = frame_depth / 2 - blade_t
        front_y = blade_y + blade_t - front_t  # Framkant starter her

        # U-profilens deler for venstre sidestolpe:
        # 1. Framkant (vertikal del på forsiden)
        # 2. Bakre ben (strekker seg inn i veggen)
        # 3. Fals (innvendig kant der dørbladet hviler)

        parts = []

        for side in ['left', 'right']:
            if side == 'left':
                x_outer = -blade_w / 2 - sidestolpe
                x_inner = -blade_w / 2
                fals_x = x_inner - fals_w
            else:
                x_outer = blade_w / 2
                x_inner = blade_w / 2 + sidestolpe
                fals_x = blade_w / 2

            # 1. Framkant (tynn vertikal del på forsiden)
            parts.append((x_outer, front_y, 0, sidestolpe, front_t, karm_h))

            # 2. Bakre ben / utforing (strekker seg bakover fra framkant)
            utforing_len = frame_depth - front_t - (frame_depth / 2 - blade_y)
            if utforing_len > 0:
                parts.append((x_outer, front_y - utforing_len, 0, utforing_t, utforing_len, karm_h))
                parts.append((x_inner - utforing_t, front_y - utforing_len, 0, utforing_t, utforing_len, karm_h))

            # 3. Fals/anslag (innvendig kant)
            parts.append((fals_x, front_y - fals_d, luftspalte, fals_w, fals_d, blade_h + 5 * s))

        # Toppstykke (binder sammen sidestolpene)
        parts.append((-blade_w / 2 - sidestolpe, front_y, karm_h,
                      blade_w + 2 * sidestolpe, front_t, sidestolpe / 2))

        # Tegn alle deler
        for (bx, by, bz, dx, dy, dz) in parts:
            verts, faces = self._make_box(bx, by, bz, dx, dy, dz)
            colors = np.tile(karm_color, (len(faces), 1))
            mesh = gl.GLMeshItem(
                vertexes=verts, faces=faces, faceColors=colors,
                smooth=False, drawEdges=True, edgeColor=(0.2, 0.2, 0.22, 1.0)
            )
            self._gl_widget.addItem(mesh)
            self._mesh_items.append(mesh)

    def _add_frame_type2(self, door: DoorParams, blade_w: float, blade_h: float,
                          blade_t: float, frame_depth: float, luftspalte: float):
        """Type 2 karm: L-profil (SD2, KD2, YD2, PD2, BD2).

        L-profilen har:
        - Framkant med fals
        - Ett "ben" som strekker seg bakover (ikke U-form)
        """
        s = self.SCALE
        karm_color = np.array(self._ral_to_rgba(door.karm_color))

        sidestolpe = door.sidestolpe_width() * s
        front_t = self.KARM_FRONT_THICKNESS * s
        fals_d = self.KARM_FALS_DEPTH * s
        fals_w = self.KARM_FALS_WIDTH * s

        karm_h = luftspalte + blade_h + 5 * s
        blade_y = frame_depth / 2 - blade_t
        front_y = blade_y + blade_t - front_t

        parts = []

        for side in ['left', 'right']:
            if side == 'left':
                x_outer = -blade_w / 2 - sidestolpe
                fals_x = -blade_w / 2 - fals_w
            else:
                x_outer = blade_w / 2
                fals_x = blade_w / 2

            # 1. Framkant (L-ens vertikale del)
            parts.append((x_outer, front_y, 0, sidestolpe, front_t, karm_h))

            # 2. L-ens horisontale del (strekker seg bakover)
            l_depth = frame_depth / 2
            parts.append((x_outer, front_y - l_depth, 0, sidestolpe, l_depth, front_t * 1.5))

            # 3. Fals/anslag
            parts.append((fals_x, front_y - fals_d, luftspalte, fals_w, fals_d, blade_h + 5 * s))

        # Toppstykke
        parts.append((-blade_w / 2 - sidestolpe, front_y, karm_h,
                      blade_w + 2 * sidestolpe, front_t, sidestolpe / 2))

        for (bx, by, bz, dx, dy, dz) in parts:
            verts, faces = self._make_box(bx, by, bz, dx, dy, dz)
            colors = np.tile(karm_color, (len(faces), 1))
            mesh = gl.GLMeshItem(
                vertexes=verts, faces=faces, faceColors=colors,
                smooth=False, drawEdges=True, edgeColor=(0.2, 0.2, 0.22, 1.0)
            )
            self._gl_widget.addItem(mesh)
            self._mesh_items.append(mesh)

    def _add_frame_type3(self, door: DoorParams, blade_w: float, blade_h: float,
                          blade_t: float, frame_depth: float, luftspalte: float):
        """Type 3 karm: Enkel profil med sentrert dørblad (SD3/ID1, KD3, YD3).

        Enkel rektangulær profil der dørbladet er sentrert i karmdybden.
        """
        s = self.SCALE
        karm_color = np.array(self._ral_to_rgba(door.karm_color))

        sidestolpe = door.sidestolpe_width() * s
        fals_d = self.KARM_FALS_DEPTH * s
        fals_w = self.KARM_FALS_WIDTH * s

        karm_h = luftspalte + blade_h + 5 * s

        # Dørbladet er sentrert, så karmen er også sentrert
        karm_depth = blade_t + 2 * fals_d  # Litt dypere enn bladet

        parts = []

        for side in ['left', 'right']:
            if side == 'left':
                x_outer = -blade_w / 2 - sidestolpe
                fals_x = -blade_w / 2 - fals_w
            else:
                x_outer = blade_w / 2
                fals_x = blade_w / 2

            # Enkel sidestolpe (rektangulær)
            parts.append((x_outer, -karm_depth / 2, 0, sidestolpe, karm_depth, karm_h))

            # Fals på begge sider (foran og bak)
            parts.append((fals_x, -blade_t / 2 - fals_d, luftspalte, fals_w, fals_d, blade_h))
            parts.append((fals_x, blade_t / 2, luftspalte, fals_w, fals_d, blade_h))

        # Toppstykke
        parts.append((-blade_w / 2 - sidestolpe, -karm_depth / 2, karm_h,
                      blade_w + 2 * sidestolpe, karm_depth, sidestolpe / 2))

        for (bx, by, bz, dx, dy, dz) in parts:
            verts, faces = self._make_box(bx, by, bz, dx, dy, dz)
            colors = np.tile(karm_color, (len(faces), 1))
            mesh = gl.GLMeshItem(
                vertexes=verts, faces=faces, faceColors=colors,
                smooth=False, drawEdges=True, edgeColor=(0.2, 0.2, 0.22, 1.0)
            )
            self._gl_widget.addItem(mesh)
            self._mesh_items.append(mesh)

    def _add_door_body(self, door: DoorParams, blade_w: float, blade_h: float,
                        blade_t: float, frame_depth: float, luftspalte: float):
        """Legger til dørblad med farge og korrekt plassering.

        Args:
            door: Dørparametere
            blade_w: Dørbladbredde (skalert)
            blade_h: Dørbladhøyde (skalert)
            blade_t: Dørbladtykkelse (skalert)
            frame_depth: Karmdybde/veggtykkelse (skalert)
            luftspalte: Luftspalte ved gulv (skalert)
        """
        # Y-posisjon basert på karmtype (flush vs sentrert)
        if door.is_blade_flush():
            # Flush med framkant av karm
            blade_y = frame_depth / 2 - blade_t
        else:
            # Sentrert i karmen
            blade_y = -blade_t / 2

        # Z-posisjon: løftet opp med luftspalte
        blade_z = luftspalte

        verts, faces = self._make_box(-blade_w / 2, blade_y, blade_z, blade_w, blade_t, blade_h)

        color = self._ral_to_rgba(door.color)
        color_edge = self._blend_colors(color, color, 0.5)

        # 12 faces: bunn(2), topp(2), front(2), bak(2), venstre(2), høyre(2)
        face_colors = np.array([
            color_edge, color_edge,    # Bunn
            color_edge, color_edge,    # Topp
            color,      color,         # Front
            color,      color,         # Bak
            color_edge, color_edge,    # Venstre
            color_edge, color_edge,    # Høyre
        ])

        mesh = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            faceColors=face_colors,
            smooth=False,
            drawEdges=True,
            edgeColor=(0.15, 0.15, 0.15, 1.0)
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)

    def _add_glass_panel(self, door: DoorParams, blade_w: float, blade_h: float,
                          blade_t: float, luftspalte: float):
        """Legger til semi-transparent glasspanel med faktiske mål og form."""
        s = self.SCALE
        shape = door.window_shape  # 'rect', 'circle', eller 'rounded_rect'

        # Bruk faktiske vindusmål fra modellen
        glass_w = door.window_width * s
        glass_h = door.window_height * s

        # Glasset må stikke litt ut fra dørbladet for å være synlig
        glass_t = blade_t + 0.5 * s

        # Standard senterposisjon: midt horisontalt, 65% opp vertikalt
        # + offset fra brukervalg, relativ til dørbladets posisjon
        center_x = door.window_pos_x * s
        center_z = luftspalte + blade_h * self.GLASS_DEFAULT_Y_RATIO + door.window_pos_y * s

        # Lys blå farge for glass
        glass_color = np.array([0.6, 0.8, 0.95, 0.5])

        if shape == 'circle':
            # Tegn sylinder (tilnærmet med mange sider)
            radius = glass_w / 2  # Diameter = bredde
            verts, faces = self._make_cylinder(
                center_x, 0, center_z,
                radius, glass_t
            )
        else:
            # 'rect' og 'rounded_rect' - tegn boks (3D har ikke enkel avrunding)
            gx = center_x - glass_w / 2
            gz = center_z - glass_h / 2
            gy = -glass_t / 2
            verts, faces = self._make_box(gx, gy, gz, glass_w, glass_t, glass_h)

        colors = np.tile(glass_color, (len(faces), 1))

        mesh = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            faceColors=colors,
            smooth=False,
            drawEdges=True,
            edgeColor=(0.3, 0.5, 0.7, 1.0),
            glOptions='translucent'
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)

    def _add_handle(self, door: DoorParams, blade_w: float, blade_h: float,
                     blade_t: float, frame_depth: float, luftspalte: float):
        """Legger til håndtak på korrekt side (motsatt hengsle-side)."""
        s = self.SCALE
        hw = self.HANDLE_WIDTH * s
        hh = self.HANDLE_HEIGHT * s
        hd = self.HANDLE_DEPTH * s
        margin = self.HANDLE_X_MARGIN * s

        if door.swing_direction == 'left':
            hx = blade_w / 2 - margin - hw
        else:
            hx = -blade_w / 2 + margin

        # Y-posisjon basert på karmtype (flush vs sentrert)
        if door.is_blade_flush():
            blade_y = frame_depth / 2 - blade_t
            hy = blade_y + blade_t  # På forsiden av dørbladet
        else:
            hy = blade_t / 2  # Sentrert, håndtak på front

        # Z-posisjon: relativt til dørbladets posisjon (inkludert luftspalte)
        hz = luftspalte + blade_h * self.HANDLE_Y_RATIO - hh / 2

        verts, faces = self._make_box(hx, hy, hz, hw, hd, hh)

        handle_color = np.array([0.12, 0.12, 0.12, 1.0])
        colors = np.tile(handle_color, (len(faces), 1))

        mesh = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            faceColors=colors,
            smooth=False,
            drawEdges=True,
            edgeColor=(0.05, 0.05, 0.05, 1.0)
        )
        self._gl_widget.addItem(mesh)
        self._mesh_items.append(mesh)

    def _add_hinges(self, door: DoorParams, blade_w: float, blade_h: float,
                     blade_t: float, frame_depth: float, luftspalte: float):
        """Legger til hengsler på angitt side."""
        s = self.SCALE
        hw = self.HINGE_WIDTH * s
        hh = self.HINGE_HEIGHT * s
        hd = self.HINGE_DEPTH * s

        hinge_color = np.array([0.25, 0.25, 0.25, 1.0])

        # Bruk faktisk antall hengsler fra dørparametere
        hinge_count = door.hinge_count if door.hinge_count > 0 else 3

        # Beregn hengsel-posisjoner basert på antall
        if hinge_count == 2:
            positions = [0.20, 0.80]
        elif hinge_count == 3:
            positions = [0.15, 0.50, 0.85]
        else:
            # For 4+ hengsler: jevnt fordelt
            positions = [i / (hinge_count + 1) for i in range(1, hinge_count + 1)]

        for pos in positions:
            # Z-posisjon: relativt til dørbladets posisjon (inkludert luftspalte)
            hz = luftspalte + blade_h * pos - hh / 2

            if door.swing_direction == 'left':
                hx = -blade_w / 2 - hw
            else:
                hx = blade_w / 2

            hy = -hd / 2

            verts, faces = self._make_box(hx, hy, hz, hw, hd, hh)
            colors = np.tile(hinge_color, (len(faces), 1))

            mesh = gl.GLMeshItem(
                vertexes=verts,
                faces=faces,
                faceColors=colors,
                smooth=False,
                drawEdges=True,
                edgeColor=(0.1, 0.1, 0.1, 1.0)
            )
            self._gl_widget.addItem(mesh)
            self._mesh_items.append(mesh)

    @staticmethod
    def _make_cylinder(cx, cy, cz, radius, depth, segments=24):
        """
        Genererer vertices og faces for en sylinder (sirkulært glass).

        Args:
            cx, cy, cz: Senterposisjon
            radius: Radius
            depth: Dybde (tykkelse i Y-retning)
            segments: Antall segmenter for sirkel-tilnærming

        Returns:
            vertices: np.array
            faces: np.array - trekant-indekser
        """
        verts = []
        faces = []

        # Generer punkter for front- og bak-sirkel
        angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

        # Front sirkel (y = cy - depth/2)
        front_y = cy - depth / 2
        for angle in angles:
            x = cx + radius * np.cos(angle)
            z = cz + radius * np.sin(angle)
            verts.append([x, front_y, z])

        # Bak sirkel (y = cy + depth/2)
        back_y = cy + depth / 2
        for angle in angles:
            x = cx + radius * np.cos(angle)
            z = cz + radius * np.sin(angle)
            verts.append([x, back_y, z])

        # Senterpunkter for front og bak
        front_center = len(verts)
        verts.append([cx, front_y, cz])
        back_center = len(verts)
        verts.append([cx, back_y, cz])

        verts = np.array(verts)

        # Front sirkel (trekanter fra senter)
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([front_center, next_i, i])

        # Bak sirkel
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([back_center, segments + i, segments + next_i])

        # Sidevegger (rektangler som 2 trekanter)
        for i in range(segments):
            next_i = (i + 1) % segments
            # Trekant 1
            faces.append([i, next_i, segments + i])
            # Trekant 2
            faces.append([next_i, segments + next_i, segments + i])

        return verts, np.array(faces)

    @staticmethod
    def _make_box(x, y, z, dx, dy, dz):
        """
        Genererer vertices og faces for en boks (rektangulær prisme).

        Args:
            x, y, z: Minimumshjørne
            dx, dy, dz: Dimensjoner (bredde, dybde, høyde)

        Returns:
            vertices: np.array (8, 3)
            faces: np.array (12, 3) - trekant-indekser
        """
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
            # Bunn (z = z)
            [0, 1, 2], [0, 2, 3],
            # Topp (z = z + dz)
            [4, 6, 5], [4, 7, 6],
            # Front (y = y + dy) - utside
            [3, 2, 6], [3, 6, 7],
            # Bak (y = y) - innside
            [0, 5, 1], [0, 4, 5],
            # Venstre (x = x)
            [0, 3, 7], [0, 7, 4],
            # Høyre (x = x + dx)
            [1, 5, 6], [1, 6, 2],
        ])

        return verts, faces

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
