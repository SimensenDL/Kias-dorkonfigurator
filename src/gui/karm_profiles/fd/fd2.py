"""FD2 karm-profil: L-profil med listverk kun på framside (som KD2)."""

from ..base import KarmProfile


class FD2Profile(KarmProfile):
    """FD2: list (80mm bred, 7mm tykk) kun på framside, fast dybde 104mm.

    Komponentar:
      - Listverk (80mm × 7mm) kun på framside
      - Kobling (5mm tykk, 97mm djup frå veggfront)
      - Anslag (20mm bred, 24mm djup) bak dørbladet (84mm karm - 60mm blad)
    Total: 97mm karm + 7mm list = 104mm
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        list_w = 80
        list_t = 7
        kd2_depth = 97
        kobling_t = 5
        anslag_w = 20
        blade_t = door.blade_thickness

        front_y = wall_t / 2

        parts = []

        # List kun på framside
        parts.append((-kb / 2, front_y, 0, list_w, list_t, kh))
        parts.append((kb / 2 - list_w, front_y, 0, list_w, list_t, kh))
        parts.append((
            -kb / 2 + list_w, front_y, kh - list_w,
            kb - 2 * list_w, list_t, list_w
        ))

        # Kobling (5mm tykk, 97mm djup frå veggfront)
        kobling_y = wall_t / 2 - kd2_depth
        kobling_d = kd2_depth

        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — bak dørbladet (24mm = 84mm karm - 60mm blad)
        anslag_d = 24
        karm_front = wall_t / 2 + list_t
        anslag_front_y = karm_front - blade_t
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
