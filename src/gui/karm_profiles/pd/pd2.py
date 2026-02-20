"""PD2 karm-profil: Plassholder basert på SD2-mønster med 100mm sidestolpe.

TODO: Korrekt geometri for pendeldørkarm PD2.
"""

from ..base import KarmProfile


class PD2Profile(KarmProfile):
    """PD2: Pendeldørkarm med listverk kun på framside (plassholder).

    Bruker forenklet geometri basert på SD2/KD2-mønsteret.
    Sidestolpe 100mm, list 60mm × 7mm, fast dybde.
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        list_w = 60
        list_t = 7
        kobling_t = 5
        anslag_w = 20
        blade_t = door.blade_thickness

        front_y = wall_t / 2
        kobling_y = front_y + list_t - karm_depth + list_t
        kobling_d = karm_depth - 2 * list_t

        parts = []

        # Listverk kun på framside
        parts.append((-kb / 2, front_y, 0, list_w, list_t, kh))
        parts.append((kb / 2 - list_w, front_y, 0, list_w, list_t, kh))
        parts.append((
            -kb / 2 + list_w, front_y, kh - list_w,
            kb - 2 * list_w, list_t, list_w
        ))

        # Kobling — fast dybde
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — bak dørbladet
        anslag_d = max(1, karm_depth - list_t - blade_t)
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
