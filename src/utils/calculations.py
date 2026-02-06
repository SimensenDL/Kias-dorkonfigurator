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
    DORBLAD_OFFSETS,
    DORBLAD_HOYDE_INKL_LUFTSPALTE,
    TERSKEL_OFFSETS,
    LAMINAT_OFFSETS,
    LAMINAT_OFFSET_DEFAULT,
    DEKKLIST_2FLOYET_OFFSET,
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
# PRODUKSJONSMÅL (dørblad, terskel, laminat)
# =============================================================================

def dorblad_bredde(karm_type: str, karm_b: int, floyer: int = 1,
                   blade_type: Optional[str] = None) -> Optional[int]:
    """Beregn dørbladbredde fra karmbredde.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'SD3/ID')
        karm_b: Karmbredde i mm
        floyer: Antall fløyer (1 eller 2)
        blade_type: Bladtype (f.eks. 'SDI_ROCA'), kun nødvendig for SD3/ID

    Returns:
        Dørbladbredde i mm, eller None hvis ikke støttet
    """
    offsets = DORBLAD_OFFSETS.get(karm_type)
    if not offsets:
        return None

    # Sjekk om offsets er per bladtype (SD3/ID-struktur)
    if blade_type and blade_type in offsets:
        # SD3/ID-struktur: {bladtype: {floyer: {...}}}
        blade_offsets = offsets[blade_type]
        floyer_data = blade_offsets.get(floyer) or blade_offsets.get(1)
    else:
        # Standard struktur: {floyer: {...}}
        floyer_data = offsets.get(floyer) or offsets.get(1)

    if not floyer_data:
        return None

    bredde_offset = floyer_data.get('bredde', 0)
    return karm_b - bredde_offset


def dorblad_hoyde(karm_type: str, karm_h: int, floyer: int = 1,
                  blade_type: Optional[str] = None,
                  luftspalte: int = 0) -> Optional[int]:
    """Beregn dørbladhøyde fra karmhøyde.

    For SD3/ID trekkes luftspalte fra i tillegg til fast offset.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'SD3/ID')
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer (1 eller 2)
        blade_type: Bladtype (f.eks. 'SDI_ROCA'), kun nødvendig for SD3/ID
        luftspalte: Luftspalte i mm (brukes kun for karmtyper i DORBLAD_HOYDE_INKL_LUFTSPALTE)

    Returns:
        Dørbladhøyde i mm, eller None hvis ikke støttet
    """
    offsets = DORBLAD_OFFSETS.get(karm_type)
    if not offsets:
        return None

    # Sjekk om offsets er per bladtype (SD3/ID-struktur)
    if blade_type and blade_type in offsets:
        # SD3/ID-struktur: {bladtype: {floyer: {...}}}
        blade_offsets = offsets[blade_type]
        floyer_data = blade_offsets.get(floyer) or blade_offsets.get(1)
        # SD3/ID bruker 'hoyde_base' i stedet for 'hoyde'
        hoyde_offset = floyer_data.get('hoyde_base', 0) if floyer_data else 0
    else:
        # Standard struktur: {floyer: {...}}
        floyer_data = offsets.get(floyer) or offsets.get(1)
        hoyde_offset = floyer_data.get('hoyde', 0) if floyer_data else 0

    if not floyer_data:
        return None

    # Trekk fra luftspalte hvis karmtypen krever det
    if karm_type in DORBLAD_HOYDE_INKL_LUFTSPALTE:
        return karm_h - hoyde_offset - luftspalte
    else:
        return karm_h - hoyde_offset


def terskel_lengde(karm_type: str, karm_b: int, floyer: int = 1) -> Optional[int]:
    """Beregn terskellengde fra karmbredde.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer (1 eller 2)

    Returns:
        Terskellengde i mm, eller None hvis ikke støttet
    """
    offsets = TERSKEL_OFFSETS.get(karm_type)
    if not offsets:
        return None

    offset = offsets.get(floyer) or offsets.get(1)
    if offset is None:
        return None

    return karm_b - offset


def dekklist_lengde(karm_h: int) -> int:
    """Beregn dekklistlengde for 2-fløyet dør.

    Dekklist = karmhøyde - offset (102 mm).

    Args:
        karm_h: Karmhøyde i mm

    Returns:
        Dekklistlengde i mm
    """
    return karm_h - DEKKLIST_2FLOYET_OFFSET


def laminat_mal(karm_type: str, dorblad_b: int, dorblad_h: int,
                blade_type: Optional[str] = None) -> tuple[Optional[int], Optional[int]]:
    """Beregn laminatmål fra dørbladmål.

    Args:
        karm_type: Karmtype
        dorblad_b: Dørbladbredde i mm
        dorblad_h: Dørbladhøyde i mm
        blade_type: Bladtype (kun nødvendig for SD3/ID)

    Returns:
        Tuple (laminat_bredde, laminat_høyde) i mm, eller (None, None) hvis ikke støttet
    """
    offsets = LAMINAT_OFFSETS.get(karm_type)

    if offsets is None:
        # Bruk default
        offset = LAMINAT_OFFSET_DEFAULT
    elif isinstance(offsets, dict):
        # SD3/ID-struktur: {bladtype: offset}
        offset = offsets.get(blade_type, LAMINAT_OFFSET_DEFAULT)
    else:
        # Standard: enkelt tall
        offset = offsets

    return (dorblad_b - offset, dorblad_h - offset)


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
