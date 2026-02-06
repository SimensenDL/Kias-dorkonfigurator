"""
Beregningsmodul for dørkonfigurator.

Alle beregninger tar karmmål (bredde, høyde) som input.
Karmmål beregnes fra utsparingsmål: karm = utsparing + offset

Alle mål i millimeter (mm).
"""
from typing import Optional

from .constants import (
    KARM_SIZE_OFFSETS,
    TRANSPORT_WIDTH_OFFSETS,
    TRANSPORT_HEIGHT_OFFSETS,
    WINDOW_GLASS_DEDUCTION,
    WINDOW_LIGHT_DEDUCTION,
)


# =============================================================================
# KARMMÅL (fra utsparing)
# =============================================================================

def karm_bredde(karm_type: str, utsparing_bredde: int) -> int:
    """Beregn karmbredde fra utsparingsbredde.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'KD2')
        utsparing_bredde: Utsparingsbredde i mm (BM)

    Returns:
        Karmbredde i mm
    """
    offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('width', 0)
    return utsparing_bredde + offset


def karm_hoyde(karm_type: str, utsparing_hoyde: int) -> int:
    """Beregn karmhøyde fra utsparingshøyde.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'KD2')
        utsparing_hoyde: Utsparingshøyde i mm (HM)

    Returns:
        Karmhøyde i mm
    """
    offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('height', 0)
    return utsparing_hoyde + offset


def utsparing_fra_karm(karm_type: str, karm_b: int, karm_h: int) -> tuple[int, int]:
    """Beregn utsparingsmål fra karmmål (invers).

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        karm_h: Karmhøyde i mm

    Returns:
        Tuple (utsparing_bredde, utsparing_hoyde) i mm
    """
    offsets = KARM_SIZE_OFFSETS.get(karm_type, {'width': 0, 'height': 0})
    return (karm_b - offsets['width'], karm_h - offsets['height'])


# =============================================================================
# TRANSPORTMÅL (fra karmmål)
# =============================================================================

def transport_bredde_90(karm_type: str, karm_b: int, floyer: int = 1) -> Optional[int]:
    """Transportbredde ved 90° døråpning.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer (1 eller 2)

    Returns:
        Transportbredde i mm, eller None hvis ikke støttet
    """
    karm_offsets = TRANSPORT_WIDTH_OFFSETS.get(karm_type)
    if not karm_offsets:
        return None

    floyer_offsets = karm_offsets.get(floyer) or karm_offsets.get(1)
    if not floyer_offsets or floyer_offsets.get('90') is None:
        return None

    size_offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('width', 0)
    transport_offset = floyer_offsets['90']

    return karm_b - size_offset + transport_offset


def transport_bredde_180(karm_type: str, karm_b: int, floyer: int = 1) -> Optional[int]:
    """Transportbredde ved 180° døråpning.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer (1 eller 2)

    Returns:
        Transportbredde i mm, eller None hvis ikke støttet
    """
    karm_offsets = TRANSPORT_WIDTH_OFFSETS.get(karm_type)
    if not karm_offsets:
        return None

    floyer_offsets = karm_offsets.get(floyer) or karm_offsets.get(1)
    if not floyer_offsets or floyer_offsets.get('180') is None:
        return None

    size_offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('width', 0)
    transport_offset = floyer_offsets['180']

    return karm_b - size_offset + transport_offset


def transport_hoyde(karm_type: str, karm_h: int, terskel_type: str = 'ingen') -> Optional[int]:
    """Transporthøyde basert på terskeltype.

    Args:
        karm_type: Karmtype
        karm_h: Karmhøyde i mm
        terskel_type: Terskeltype (f.eks. 'ingen', 'anslag_37', 'hc20')

    Returns:
        Transporthøyde i mm, eller None hvis ikke støttet
    """
    offsets = TRANSPORT_HEIGHT_OFFSETS.get(karm_type)
    if not offsets:
        return None

    transport_offset = offsets.get(terskel_type)
    if transport_offset is None:
        return None

    size_offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('height', 0)

    return karm_h - size_offset + transport_offset


# =============================================================================
# VINDU-MÅL
# =============================================================================

def vindu_glasmal(utsparing_b: int, utsparing_h: int) -> tuple[int, int]:
    """Beregn glassmål fra vindusutsparing.

    Glassmål = utsparing - 36mm

    Args:
        utsparing_b: Vindusutsparing bredde i mm
        utsparing_h: Vindusutsparing høyde i mm

    Returns:
        Tuple (glass_bredde, glass_høyde) i mm
    """
    return (
        max(0, utsparing_b - WINDOW_GLASS_DEDUCTION),
        max(0, utsparing_h - WINDOW_GLASS_DEDUCTION)
    )


def vindu_lysapning(utsparing_b: int, utsparing_h: int) -> tuple[int, int]:
    """Beregn lysåpning fra vindusutsparing.

    Lysåpning = glassmål - 26mm = utsparing - 62mm

    Args:
        utsparing_b: Vindusutsparing bredde i mm
        utsparing_h: Vindusutsparing høyde i mm

    Returns:
        Tuple (lys_bredde, lys_høyde) i mm
    """
    glass_b, glass_h = vindu_glasmal(utsparing_b, utsparing_h)
    return (
        max(0, glass_b - WINDOW_LIGHT_DEDUCTION),
        max(0, glass_h - WINDOW_LIGHT_DEDUCTION)
    )


# =============================================================================
# AREAL
# =============================================================================

def areal_m2(bredde: int, hoyde: int) -> float:
    """Beregn areal i kvadratmeter.

    Args:
        bredde: Bredde i mm
        hoyde: Høyde i mm

    Returns:
        Areal i m²
    """
    return (bredde * hoyde) / 1_000_000
