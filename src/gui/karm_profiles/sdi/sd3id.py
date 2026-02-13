"""SD3/ID karm-profil: Smygmontasje, sentrert i vegg."""

from ..base import KarmProfile


class SD3IDProfile(KarmProfile):
    """SD3/ID smygmontasje: utan listverk, sentrert i veggdjupna.

    Profil (frå karmkant innover):
      body (24mm) | kobling (5mm) | anslag (20mm bak blad)
    Totalt sidestolpe = 44mm.  Karmdybde 92mm sentrert i vegg.
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        anslag_w = 20
        kobling_t = 5
        body_w = sidestolpe_w - anslag_w  # 44 - 20 = 24mm
        blade_t = door.blade_thickness

        karm_back_y = -karm_depth / 2
        karm_front_y = karm_depth / 2

        parts = []

        # Sidestolpe-kropp (full djupne)
        parts.append((-kb / 2, karm_back_y, 0,
                       body_w, karm_depth, kh))
        parts.append((kb / 2 - body_w, karm_back_y, 0,
                       body_w, karm_depth, kh))
        parts.append((
            -kb / 2 + body_w, karm_back_y, kh - body_w,
            kb - 2 * body_w, karm_depth, body_w
        ))

        # Kobling (5mm tykk, full djupne, innerkant av kroppen)
        parts.append((-kb / 2 + body_w, karm_back_y, 0,
                       kobling_t, karm_depth, kh - body_w + kobling_t))
        parts.append((kb / 2 - body_w - kobling_t, karm_back_y, 0,
                       kobling_t, karm_depth, kh - body_w + kobling_t))
        parts.append((-kb / 2 + body_w, karm_back_y, kh - body_w,
                       kb - 2 * body_w, karm_depth, kobling_t))

        # Anslag (20mm bred, djup bak dørbladet)
        anslag_d = karm_depth - blade_t  # 92 - 40 = 52
        anslag_back_y = karm_back_y

        parts.append((-kb / 2 + body_w + kobling_t, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - body_w))
        parts.append((kb / 2 - body_w - kobling_t - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - body_w))
        parts.append((-kb / 2 + body_w + kobling_t, anslag_back_y,
                       kh - body_w - anslag_w,
                       kb - 2 * (body_w + kobling_t), anslag_d, anslag_w))

        return parts

    def blade_y(self, wall_t, blade_t, karm_depth):
        return karm_depth / 2 - blade_t

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        return karm_depth / 2 - hinge_depth / 2

    def handle_y(self, wall_t, blade_t, karm_depth):
        return karm_depth / 2

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        return karm_depth / 2 - blade_t - threshold_depth

    def luftspalte(self, door):
        return door.effective_luftspalte()
