"""Baseklasse for karm-profiler i 3D-vieweren."""


class KarmProfile:
    """Felles interface for alle karm-profiler i 3D-vieweren.

    Kvar profil definerer geometrien til karmen (ramme rundt dørbladet)
    og korleis dørblad, hengsler, håndtak og terskel skal plasserast
    relativt til veggen.
    """

    def build_frame_parts(self, door, kb, kh, wall_t, karm_depth, sidestolpe_w):
        """Returnerer liste av (bx, by, bz, dx, dy, dz) boksar for karmen.

        Alle mål i mm. Scaling til GL-einingar skjer i kallaren.
        """
        raise NotImplementedError

    def blade_y(self, wall_t, blade_t, karm_depth):
        """Y-posisjon (bakkant) for dørbladet i mm."""
        raise NotImplementedError

    def hinge_y(self, wall_t, blade_t, karm_depth, hinge_depth):
        """Y-posisjon for hengsler i mm."""
        raise NotImplementedError

    def handle_y(self, wall_t, blade_t, karm_depth):
        """Y-posisjon for håndtak (framkant av blad) i mm."""
        raise NotImplementedError

    def threshold_y(self, wall_t, blade_t, karm_depth, threshold_depth):
        """Y-posisjon for terskel i mm."""
        raise NotImplementedError

    def luftspalte(self, door):
        """Luftspalte-verdi i mm."""
        return 22
