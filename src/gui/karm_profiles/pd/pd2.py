"""PD2 karm-profil: Pendeldørkarm med listverk kun på framside.

Fast dybde 84mm (77mm karm + 7mm list). Anslag full 77mm dybde.
Bladet sentrert i kanalen (pendeldører svinger begge veier).
"""

from ..base import KarmProfile


class PD2Profile(KarmProfile):
    """PD2: Pendeldørkarm med listverk kun på framside, sentrert blad.

    Sidestolpe 100mm, list 60mm × 7mm. Fast 84mm total dybde.
    Blad sentrert i 77mm-kanalen bak listen.
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        list_w = 60
        list_t = 7
        kobling_t = 5
        anslag_w = 20
        pd2_depth = 77  # Fast karmdybde bak listen

        front_y = wall_t / 2
        kobling_y = front_y - pd2_depth
        kobling_d = pd2_depth

        parts = []

        # Listverk kun på framside
        parts.append((-kb / 2, front_y, 0, list_w, list_t, kh))
        parts.append((kb / 2 - list_w, front_y, 0, list_w, list_t, kh))
        parts.append((
            -kb / 2 + list_w, front_y, kh - list_w,
            kb - 2 * list_w, list_t, list_w
        ))

        # Kobling — fast 77mm dybde
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — full 77mm dybde (helt til koblingens bakside)
        anslag_d = pd2_depth
        anslag_back_y = front_y - pd2_depth

        parts.append((-kb / 2 + list_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((kb / 2 - list_w - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((-kb / 2 + list_w, anslag_back_y, kh - list_w - anslag_w,
                       kb - 2 * list_w, anslag_d, anslag_w))

        return parts

    def blade_y(self, wall_t, blade_t, karm_depth):
        # Sentrert i 77mm-kanalen bak listen
        pd2_depth = 77
        channel_center = wall_t / 2 - pd2_depth / 2
        return channel_center - blade_t / 2

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        pd2_depth = 77
        channel_center = wall_t / 2 - pd2_depth / 2
        return channel_center - hinge_depth / 2

    def handle_y(self, wall_t, blade_t, karm_depth):
        pd2_depth = 77
        channel_center = wall_t / 2 - pd2_depth / 2
        return channel_center + blade_t / 2

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        # Terskel starter rett bak listen (wall_t/2), går innover
        return wall_t / 2 - threshold_depth

    def luftspalte(self, door):
        return door.effective_luftspalte()
