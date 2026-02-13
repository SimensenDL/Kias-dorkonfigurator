"""SD1 karm-profil: U-profil med listverk på begge sider av veggen."""

from ..base import KarmProfile


class SD1Profile(KarmProfile):
    """SD1: list (60mm bred, 7mm tykk) på begge sider av veggen.

    Komponentar:
      - Listverk (60mm × 7mm) på fram- og bakside
      - Kobling (5mm tykk) gjennom veggen
      - Anslag (20mm bred, 44mm djup) bak dørbladet
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        list_w = 60
        list_t = 7
        kobling_t = 5
        anslag_w = 20
        blade_t = door.blade_thickness

        front_y = wall_t / 2
        back_y = -wall_t / 2 - list_t
        kobling_y = -wall_t / 2
        kobling_d = wall_t

        parts = []

        # Lister på fram- og bakside
        for y in (front_y, back_y):
            parts.append((-kb / 2, y, 0, list_w, list_t, kh))
            parts.append((kb / 2 - list_w, y, 0, list_w, list_t, kh))
            parts.append((
                -kb / 2 + list_w, y, kh - list_w,
                kb - 2 * list_w, list_t, list_w
            ))

        # Kobling gjennom veggen — indre kant av listene
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — bak dørbladet (44mm djup)
        anslag_d = 44
        anslag_front_y = wall_t / 2 + list_t - blade_t
        anslag_back_y = anslag_front_y - anslag_d

        parts.append((-kb / 2 + list_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((kb / 2 - list_w - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((-kb / 2 + list_w, anslag_back_y, kh - list_w - anslag_w,
                       kb - 2 * list_w, anslag_d, anslag_w))

        return parts

    def blade_y(self, wall_t, blade_t, karm_depth):
        return wall_t / 2 + 7 - blade_t

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        return wall_t / 2 + 7 - hinge_depth / 2

    def handle_y(self, wall_t, blade_t, karm_depth):
        return wall_t / 2 + 7

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        return wall_t / 2 - threshold_depth - blade_t
