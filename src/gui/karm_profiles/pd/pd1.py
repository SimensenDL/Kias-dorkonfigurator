"""PD1 karm-profil: Pendeldørkarm med listverk på begge sider.

Bladet er sentrert i veggen (pendeldører svinger begge veier).
Anslaget dekker full vegdybde. Kobling gjennom veggen.
"""

from ..base import KarmProfile


class PD1Profile(KarmProfile):
    """PD1: Pendeldørkarm med listverk på begge sider, sentrert blad.

    Sidestolpe 100mm, list 60mm × 7mm. Blad sentrert ved Y=0 (veggmidten).
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        list_w = 60
        list_t = 7
        kobling_t = 5
        anslag_w = 20

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

        # Kobling gjennom veggen
        parts.append((-kb / 2 + list_w - kobling_t, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((kb / 2 - list_w, kobling_y, 0,
                       kobling_t, kobling_d, kh - list_w + kobling_t))
        parts.append((-kb / 2 + list_w, kobling_y, kh - list_w,
                       kb - 2 * list_w, kobling_d, kobling_t))

        # Anslag — fast 77mm dybde, starter bak framlisten
        pd1_depth = 77
        anslag_d = pd1_depth
        anslag_front_y = wall_t / 2
        anslag_back_y = anslag_front_y - anslag_d

        parts.append((-kb / 2 + list_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((kb / 2 - list_w - anslag_w, anslag_back_y, 0,
                       anslag_w, anslag_d, kh - list_w))
        parts.append((-kb / 2 + list_w, anslag_back_y, kh - list_w - anslag_w,
                       kb - 2 * list_w, anslag_d, anslag_w))

        return parts

    def blade_y(self, wall_t, blade_t, karm_depth):
        # Sentrert i 77mm-kanalen bak framlisten
        pd1_depth = 77
        channel_center = wall_t / 2 - pd1_depth / 2
        return channel_center - blade_t / 2

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        pd1_depth = 77
        channel_center = wall_t / 2 - pd1_depth / 2
        return channel_center - hinge_depth / 2

    def handle_y(self, wall_t, blade_t, karm_depth):
        pd1_depth = 77
        channel_center = wall_t / 2 - pd1_depth / 2
        return channel_center + blade_t / 2

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        # Terskel starter rett bak framlisten, går innover
        return wall_t / 2 - threshold_depth
