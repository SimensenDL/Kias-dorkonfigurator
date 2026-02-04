"""
3D-forhåndsvisning av konfigurert dør.
Bruker pyqtgraph OpenGL for interaktiv rotérbar visning.
"""
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ...models.door import DoorParams
from ...utils.constants import RAL_COLORS

# Betinget import med fallback
try:
    import pyqtgraph.opengl as gl
    HAS_3D = True
except ImportError:
    HAS_3D = False


class DoorPreview3D(QWidget):
    """
    3D-forhåndsvisning av en konfigurert dør.

    Viser dør med karm, farge, glass, håndtak og hengsler.
    Rotérbar visning med mus (venstre: roter, høyre: pan, scroll: zoom).
    """

    # Skaleringsfaktor: konverterer mm til 3D-enheter (1 enhet = 100 mm)
    SCALE = 1.0 / 100.0

    # Karm-dimensjoner (mm)
    FRAME_WIDTH = 50

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
            self._gl_widget = gl.GLViewWidget()
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

        w = door.width * s
        h = door.height * s
        frame_depth = door.thickness * s  # Karmdybde = veggtykkelse
        blade_t = door.blade_thickness * s  # Dørbladtykkelse fra parametere

        # Bygg scenen i rekkefølge: opake elementer først, transparente sist
        self._add_frame(w, h, frame_depth)
        self._add_door_body(door, w, h, blade_t)
        self._add_handle(door, w, h, blade_t)
        self._add_hinges(door, w, h, blade_t)

        if door.has_window:
            self._add_glass_panel(door, w, h, blade_t)

    def _add_frame(self, w: float, h: float, frame_depth: float):
        """Legger til karm (ramme) rundt døren. Karmdybde = veggtykkelse."""
        s = self.SCALE
        fw = self.FRAME_WIDTH * s
        fd = frame_depth  # Karmdybde basert på veggtykkelse

        frame_color = np.array([0.45, 0.45, 0.48, 1.0])

        # Karm: venstre stolpe, høyre stolpe, toppstykke
        parts = [
            (-w / 2 - fw, -fd / 2, 0, fw, fd, h + fw),
            (w / 2, -fd / 2, 0, fw, fd, h + fw),
            (-w / 2 - fw, -fd / 2, h, w + 2 * fw, fd, fw),
        ]

        for (bx, by, bz, dx, dy, dz) in parts:
            verts, faces = self._make_box(bx, by, bz, dx, dy, dz)
            colors = np.tile(frame_color, (len(faces), 1))
            mesh = gl.GLMeshItem(
                vertexes=verts,
                faces=faces,
                faceColors=colors,
                smooth=False,
                drawEdges=True,
                edgeColor=(0.25, 0.25, 0.28, 1.0)
            )
            self._gl_widget.addItem(mesh)
            self._mesh_items.append(mesh)

    def _add_door_body(self, door: DoorParams, w: float, h: float, t: float):
        """Legger til dørblad med farge."""
        verts, faces = self._make_box(-w / 2, -t / 2, 0, w, t, h)

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

    def _add_glass_panel(self, door: DoorParams, w: float, h: float, t: float):
        """Legger til semi-transparent glasspanel med faktiske mål og form."""
        s = self.SCALE
        shape = door.window_shape  # 'rect', 'circle', eller 'rounded_rect'

        # Bruk faktiske vindusmål fra modellen
        glass_w = door.window_width * s
        glass_h = door.window_height * s

        # Glasset må stikke litt ut fra dørbladet for å være synlig
        glass_t = t + 0.5 * s

        # Standard senterposisjon: midt horisontalt, 65% opp vertikalt
        # + offset fra brukervalg
        center_x = door.window_pos_x * s
        center_z = h * self.GLASS_DEFAULT_Y_RATIO + door.window_pos_y * s

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

    def _add_handle(self, door: DoorParams, w: float, h: float, t: float):
        """Legger til håndtak på korrekt side (motsatt hengsle-side)."""
        s = self.SCALE
        hw = self.HANDLE_WIDTH * s
        hh = self.HANDLE_HEIGHT * s
        hd = self.HANDLE_DEPTH * s
        margin = self.HANDLE_X_MARGIN * s

        if door.swing_direction == 'left':
            hx = w / 2 - margin - hw
        else:
            hx = -w / 2 + margin

        hy = t / 2
        hz = h * self.HANDLE_Y_RATIO - hh / 2

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

    def _add_hinges(self, door: DoorParams, w: float, h: float, t: float):
        """Legger til 3 hengsler på angitt side."""
        s = self.SCALE
        hw = self.HINGE_WIDTH * s
        hh = self.HINGE_HEIGHT * s
        hd = self.HINGE_DEPTH * s

        hinge_color = np.array([0.25, 0.25, 0.25, 1.0])

        for pos in self.HINGE_POSITIONS:
            hz = h * pos - hh / 2

            if door.swing_direction == 'left':
                hx = -w / 2 - hw
            else:
                hx = w / 2

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
