"""
Beregningsmodul for dørkonfigurator.

Alle beregninger tar karmmål (bredde, høyde) som input.
Karmmål beregnes fra utsparingsmål: karm = utsparing + offset

Alle mål i millimeter (mm).
"""
from typing import Optional

from ..doors import DOOR_REGISTRY
from .constants import (
    KARM_SIZE_OFFSETS,
    TRANSPORT_WIDTH_OFFSETS,
    TRANSPORT_HEIGHT_OFFSETS,
    DORBLAD_OFFSETS,
    DORBLAD_HOYDE_INKL_LUFTSPALTE,
    TERSKEL_OFFSETS,
    LAMINAT_OFFSETS,
    LAMINAT_OFFSET_DEFAULT,
    LAMINAT_2_OFFSETS,
    DEKKLIST_2FLOYET_OFFSET,
)


# =============================================================================
# KARMMÅL (fra utsparing)
# =============================================================================

def karm_bredde(karm_type: str, utsparing_bredde: int, adjufix: bool = False) -> int:
    """Beregn karmbredde fra utsparingsbredde.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'KD2')
        utsparing_bredde: Utsparingsbredde i mm (BM)
        adjufix: Adjufix karmhylser (reduserer bredde med 10mm)

    Returns:
        Karmbredde i mm
    """
    offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('width', 0)
    base = utsparing_bredde + offset
    if adjufix:
        base -= 10
    return base


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
                   hinge_type: Optional[str] = None,
                   door_type: Optional[str] = None) -> Optional[int]:
    """Beregn dørbladbredde fra karmbredde.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'PD1')
        karm_b: Karmbredde i mm
        floyer: Antall fløyer (1 eller 2)
        hinge_type: Hengseltype (f.eks. 'ROCA_SF'), kun nødvendig for SD3/ID
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDI'). Slår opp direkte
                   fra DOOR_REGISTRY for å unngå kollisjon ved delte karmtyper.

    Returns:
        Dørbladbredde i mm, eller None hvis ikke støttet
    """
    # Dørtype-bevisst oppslag (unngår kollisjon ved delte karmtyper som PD1/PD2)
    if door_type and door_type in DOOR_REGISTRY:
        offsets = DOOR_REGISTRY[door_type].get('dorblad_offsets', {}).get(karm_type)
    else:
        offsets = DORBLAD_OFFSETS.get(karm_type)

    if not offsets:
        return None

    # Sjekk om offsets er per hengseltype (SD3/ID-struktur)
    if hinge_type and hinge_type in offsets:
        # SD3/ID-struktur: {hengseltype: {floyer: {...}}}
        hinge_offsets = offsets[hinge_type]
        floyer_data = hinge_offsets.get(floyer) or hinge_offsets.get(1)
    else:
        # Standard struktur: {floyer: {...}}
        floyer_data = offsets.get(floyer) or offsets.get(1)

    if not floyer_data:
        return None

    bredde_offset = floyer_data.get('bredde', 0)
    return karm_b - bredde_offset


def dorblad_hoyde(karm_type: str, karm_h: int, floyer: int = 1,
                  hinge_type: Optional[str] = None,
                  luftspalte: int = 0,
                  door_type: Optional[str] = None) -> Optional[int]:
    """Beregn dørbladhøyde fra karmhøyde.

    For SD3/ID trekkes luftspalte fra i tillegg til fast offset.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'PD1')
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer (1 eller 2)
        hinge_type: Hengseltype (f.eks. 'ROCA_SF'), kun nødvendig for SD3/ID
        luftspalte: Luftspalte i mm (brukes kun for karmtyper i DORBLAD_HOYDE_INKL_LUFTSPALTE)
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDI'). Slår opp direkte
                   fra DOOR_REGISTRY for å unngå kollisjon ved delte karmtyper.

    Returns:
        Dørbladhøyde i mm, eller None hvis ikke støttet
    """
    # Dørtype-bevisst oppslag
    if door_type and door_type in DOOR_REGISTRY:
        offsets = DOOR_REGISTRY[door_type].get('dorblad_offsets', {}).get(karm_type)
    else:
        offsets = DORBLAD_OFFSETS.get(karm_type)

    if not offsets:
        return None

    # Sjekk om offsets er per hengseltype (SD3/ID-struktur)
    if hinge_type and hinge_type in offsets:
        # SD3/ID-struktur: {hengseltype: {floyer: {...}}}
        hinge_offsets = offsets[hinge_type]
        floyer_data = hinge_offsets.get(floyer) or hinge_offsets.get(1)
        # SD3/ID bruker 'hoyde_base' i stedet for 'hoyde'
        hoyde_offset = floyer_data.get('hoyde_base', 0) if floyer_data else 0
    else:
        # Standard struktur: {floyer: {...}}
        floyer_data = offsets.get(floyer) or offsets.get(1)
        hoyde_offset = floyer_data.get('hoyde', 0) if floyer_data else 0

    if not floyer_data:
        return None

    # Trekk fra luftspalte hvis karmtypen krever det (SD3/ID, FD1/FD2/FD3)
    if karm_type in DORBLAD_HOYDE_INKL_LUFTSPALTE:
        return karm_h - hoyde_offset - luftspalte

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
                hinge_type: Optional[str] = None,
                door_type: Optional[str] = None) -> tuple[Optional[int], Optional[int]]:
    """Beregn laminatmål fra dørbladmål.

    Args:
        karm_type: Karmtype
        dorblad_b: Dørbladbredde i mm
        dorblad_h: Dørbladhøyde i mm
        hinge_type: Hengseltype (kun nødvendig for SD3/ID)
        door_type: Dørtype-nøkkel for dørtype-bevisst oppslag

    Returns:
        Tuple (laminat_bredde, laminat_høyde) i mm, eller (None, None) hvis ikke støttet
    """
    # Dørtype-bevisst oppslag (unngår kollisjon ved delte karmtyper)
    if door_type and door_type in DOOR_REGISTRY:
        door_laminat = DOOR_REGISTRY[door_type].get('laminat_offsets', {})
        offsets = door_laminat.get(karm_type)
        # Hvis dørtypen har tom laminat_offsets og karmtypen ikke finnes → ingen laminat
        if not door_laminat:
            return (None, None)
    else:
        offsets = LAMINAT_OFFSETS.get(karm_type)

    if offsets is None:
        # Bruk default
        offset = LAMINAT_OFFSET_DEFAULT
    elif isinstance(offsets, dict):
        # SD3/ID-struktur: {hengseltype: offset}
        offset = offsets.get(hinge_type, LAMINAT_OFFSET_DEFAULT)
    else:
        # Standard: enkelt tall
        offset = offsets

    return (dorblad_b - offset, dorblad_h - offset)


def laminat_2_mal(karm_type: str, laminat_1_b: int, laminat_1_h: int) -> tuple[Optional[int], Optional[int]]:
    """Beregn laminat 2-mål fra laminat 1-mål.

    Laminat 2 er mindre enn laminat 1, typisk for kjøleromsdører.

    Args:
        karm_type: Karmtype (f.eks. 'KD1', 'KD2')
        laminat_1_b: Laminat 1-bredde i mm
        laminat_1_h: Laminat 1-høyde i mm

    Returns:
        Tuple (laminat_2_bredde, laminat_2_høyde) i mm, eller (None, None) hvis ikke aktuelt
    """
    offset = LAMINAT_2_OFFSETS.get(karm_type)
    if offset is None:
        return (None, None)
    return (laminat_1_b - offset, laminat_1_h - offset)


# =============================================================================
# AREAL
# =============================================================================

def sparkeplate_bredde(door_type: str, dorblad_b: int) -> Optional[int]:
    """Beregn sparkeplatebredde fra dørbladbredde.

    Args:
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDI')
        dorblad_b: Dørbladbredde i mm

    Returns:
        Sparkeplatebredde i mm, eller None hvis dørtypen ikke har sparkeplate
    """
    door_def = DOOR_REGISTRY.get(door_type, {})
    offset = door_def.get('sparkeplate_offset')
    if offset is None:
        return None
    return dorblad_b + offset


def avviserboyler_lengde(door_type: str, dorblad_b: int) -> Optional[int]:
    """Beregn avviserbøyler-lengde fra dørbladbredde.

    Args:
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDI')
        dorblad_b: Dørbladbredde i mm

    Returns:
        Avviserbøyler-lengde i mm, eller None hvis dørtypen ikke har avviserbøyler
    """
    door_def = DOOR_REGISTRY.get(door_type, {})
    offset = door_def.get('avviserboyler_offset')
    if offset is None:
        return None
    return dorblad_b + offset


def ryggforsterkning_hoyde(door_type: str, dorblad_h: int) -> Optional[int]:
    """Beregn ryggforsterkning-høyde fra dørbladhøyde.

    Args:
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDPO')
        dorblad_h: Dørbladhøyde i mm

    Returns:
        Ryggforsterkning-høyde i mm, eller None hvis dørtypen ikke har ryggforsterkning
    """
    door_def = DOOR_REGISTRY.get(door_type, {})
    offset = door_def.get('ryggforsterkning_hoyde_offset')
    if offset is None:
        return None
    return dorblad_h + offset


def ryggforsterkning_overdel(door_type: str, dorblad_b: int) -> Optional[int]:
    """Beregn ryggforsterkning overdel-lengde fra dørbladbredde.

    Args:
        door_type: Dørtype-nøkkel (f.eks. 'PDPC', 'PDPO')
        dorblad_b: Dørbladbredde i mm

    Returns:
        Ryggforsterkning overdel-lengde i mm, eller None hvis ikke aktuelt
    """
    door_def = DOOR_REGISTRY.get(door_type, {})
    offset = door_def.get('ryggforsterkning_overdel_offset')
    if offset is None:
        return None
    return dorblad_b + offset


def areal_m2(bredde: int, hoyde: int) -> float:
    """Beregn areal i kvadratmeter.

    Args:
        bredde: Bredde i mm
        hoyde: Høyde i mm

    Returns:
        Areal i m²
    """
    return (bredde * hoyde) / 1_000_000
