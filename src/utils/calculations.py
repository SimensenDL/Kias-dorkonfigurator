"""
Beregningsmodul for dørkonfigurator.

Alle beregninger tar karmmål (bredde, høyde) som input.
Karmmål beregnes fra utsparingsmål: karm = utsparing + offset

Alle mål i millimeter (mm).
"""
from typing import Optional

from .constants import (
    KARM_SIZE_OFFSETS,
    KARM_SIDESTOLPE_WIDTH,
    KARM_BLADE_FLUSH,
    TRANSPORT_WIDTH_OFFSETS,
    TRANSPORT_HEIGHT_OFFSETS,
    WINDOW_GLASS_DEDUCTION,
    WINDOW_LIGHT_DEDUCTION,
    DORBLAD_OFFSETS,
    TERSKEL_OFFSETS,
    LAMINAT_OFFSETS,
    LAMINAT_OFFSET_DEFAULT,
    PD_DORBLAD_OFFSETS,
    PD_KOMPONENTER,
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

    # Konverter fra utsparing-basert til karm-basert offset
    size_offset = KARM_SIZE_OFFSETS.get(karm_type, {}).get('width', 0)
    transport_offset = floyer_offsets['90']

    # transport = utsp + transport_offset = (karm - size_offset) + transport_offset
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
# DØRBLADMÅL (fra karmmål) - Produksjonsformler
# =============================================================================

def dorblad_bredde(karm_type: str, karm_b: int, floyer: int = 1) -> int:
    """Dørbladbredde for produksjon (per fløy).

    Formel 1-fløyet: Dørblad = Karm - offset
    Formel 2-fløyet: Dørblad = (Karm - offset) / 2

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Dørbladbredde i mm (for én fløy)
    """
    offsets = DORBLAD_OFFSETS.get(karm_type, {}).get(floyer)
    if offsets:
        blad_b = karm_b - offsets['bredde']
        # For 2-fløyet deles bredden etter fradrag
        if floyer == 2:
            blad_b = blad_b // 2
        return blad_b

    # Fallback: prøv 1-fløyet offset og del på antall fløyer
    offsets_1 = DORBLAD_OFFSETS.get(karm_type, {}).get(1)
    if offsets_1:
        blad_b = karm_b - offsets_1['bredde']
        if floyer == 2:
            blad_b = blad_b // 2
        return blad_b

    # Fallback til transportmål hvis ikke definert
    transport = transport_bredde_90(karm_type, karm_b, floyer)
    if transport is not None:
        return transport

    # Siste fallback: karm - sidestolper
    sidestolpe = KARM_SIDESTOLPE_WIDTH.get(karm_type, 50)
    return karm_b - (sidestolpe * 2)


def dorblad_hoyde(karm_type: str, karm_h: int, floyer: int = 1) -> int:
    """Dørbladhøyde for produksjon.

    Formel: Dørblad høyde = Karm høyde - offset

    Args:
        karm_type: Karmtype
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Dørbladhøyde i mm
    """
    offsets = DORBLAD_OFFSETS.get(karm_type, {}).get(floyer)
    if offsets:
        return karm_h - offsets['hoyde']

    # Fallback til transportmål hvis ikke definert
    transport = transport_hoyde(karm_type, karm_h, 'ingen')
    if transport is not None:
        return transport

    # Siste fallback
    return karm_h - 85


# =============================================================================
# TERSKEL (fra karmmål)
# =============================================================================

def terskel_lengde(karm_type: str, karm_b: int, floyer: int = 1) -> int:
    """Terskel-lengde for produksjon.

    Formel: Terskel = Karm bredde - offset

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Terskel-lengde i mm
    """
    offset = TERSKEL_OFFSETS.get(karm_type, {}).get(floyer)
    if offset is not None:
        return karm_b - offset

    # Fallback: transportbredde ved 180° (åpning uten dørblad)
    transport = transport_bredde_180(karm_type, karm_b, floyer)
    if transport is not None:
        return transport

    # Siste fallback
    return karm_b - 160


# =============================================================================
# LAMINAT (fra dørbladmål)
# =============================================================================

def laminat_offset(karm_type: str) -> int:
    """Hent laminat-offset for karmtype.

    KD2 har større offset (48mm) pga ekstra isolasjonslag.
    Andre karmtyper bruker standard 8mm.

    Args:
        karm_type: Karmtype

    Returns:
        Laminat-offset i mm
    """
    return LAMINAT_OFFSETS.get(karm_type, LAMINAT_OFFSET_DEFAULT)


def laminat_bredde(karm_type: str, karm_b: int, floyer: int = 1) -> int:
    """Laminat-bredde for produksjon.

    Formel: Laminat = Dørblad - offset (varierer per karmtype)

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Laminat-bredde i mm
    """
    blad_b = dorblad_bredde(karm_type, karm_b, floyer)
    return blad_b - laminat_offset(karm_type)


def laminat_hoyde(karm_type: str, karm_h: int, floyer: int = 1) -> int:
    """Laminat-høyde for produksjon.

    Formel: Laminat = Dørblad - offset (varierer per karmtype)

    Args:
        karm_type: Karmtype
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Laminat-høyde i mm
    """
    blad_h = dorblad_hoyde(karm_type, karm_h, floyer)
    return blad_h - laminat_offset(karm_type)


# =============================================================================
# PD-KOMPONENTER (Pendeldør) - varierer per dørbladtype
# =============================================================================

def pd_dorblad_bredde(blade_type: str, karm_b: int, floyer: int = 1) -> int:
    """Dørbladbredde for pendeldør (per fløy).

    Args:
        blade_type: Dørbladtype (PDI_ISOLERT, PDPC_POLY, PDPO_OPAL)
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Dørbladbredde i mm (for én fløy)
    """
    offsets = PD_DORBLAD_OFFSETS.get(blade_type, {}).get(floyer)
    if offsets:
        blad_b = karm_b - offsets['bredde']
        if floyer == 2:
            blad_b = blad_b // 2
        return blad_b
    return karm_b - 300  # Fallback


def pd_dorblad_hoyde(blade_type: str, karm_h: int, floyer: int = 1) -> int:
    """Dørbladhøyde for pendeldør.

    Args:
        blade_type: Dørbladtype (PDI_ISOLERT, PDPC_POLY, PDPO_OPAL)
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Dørbladhøyde i mm
    """
    offsets = PD_DORBLAD_OFFSETS.get(blade_type, {}).get(floyer)
    if offsets:
        return karm_h - offsets['hoyde']
    return karm_h - 186  # Fallback


def pd_sparkeplate_bredde(blade_type: str, karm_b: int, floyer: int = 1) -> int:
    """Sparkeplate-bredde for pendeldør.

    Args:
        blade_type: Dørbladtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Sparkeplate-bredde i mm
    """
    blad_b = pd_dorblad_bredde(blade_type, karm_b, floyer)
    komp = PD_KOMPONENTER.get(blade_type, {})
    return blad_b + komp.get('sparkeplate_bredde', -37)


def pd_ryggforsterkning_hoyde(blade_type: str, karm_h: int, floyer: int = 1) -> Optional[int]:
    """Ryggforsterkning-høyde for pendeldør (kun PDPC/PDPO).

    Args:
        blade_type: Dørbladtype
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Ryggforsterkning-høyde i mm, eller None hvis ikke aktuelt
    """
    komp = PD_KOMPONENTER.get(blade_type, {})
    if 'ryggforsterkning_hoyde' not in komp:
        return None
    blad_h = pd_dorblad_hoyde(blade_type, karm_h, floyer)
    return blad_h + komp['ryggforsterkning_hoyde']


def pd_ryggforst_overdel(blade_type: str, karm_b: int, floyer: int = 1) -> Optional[int]:
    """Ryggforsterkning overdel for pendeldør (kun PDPC/PDPO).

    Args:
        blade_type: Dørbladtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Ryggforst overdel i mm, eller None hvis ikke aktuelt
    """
    komp = PD_KOMPONENTER.get(blade_type, {})
    if 'ryggforst_overdel' not in komp:
        return None
    blad_b = pd_dorblad_bredde(blade_type, karm_b, floyer)
    return blad_b + komp['ryggforst_overdel']


def pd_avviserboyler_lengde(blade_type: str, karm_b: int, floyer: int = 1) -> int:
    """Avviserbøyler-lengde for pendeldør.

    Args:
        blade_type: Dørbladtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Avviserbøyler-lengde i mm
    """
    blad_b = pd_dorblad_bredde(blade_type, karm_b, floyer)
    komp = PD_KOMPONENTER.get(blade_type, {})
    return blad_b + komp.get('avviserboyler_lengde', 199)


def pd_laminat_bredde(blade_type: str, karm_b: int, floyer: int = 1) -> Optional[int]:
    """Laminat-bredde for pendeldør (kun PDI_ISOLERT).

    Args:
        blade_type: Dørbladtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Laminat-bredde i mm, eller None hvis ikke aktuelt
    """
    komp = PD_KOMPONENTER.get(blade_type, {})
    if not komp.get('har_laminat'):
        return None
    blad_b = pd_dorblad_bredde(blade_type, karm_b, floyer)
    return blad_b - komp.get('laminat_offset', 8)


def pd_laminat_hoyde(blade_type: str, karm_h: int, floyer: int = 1) -> Optional[int]:
    """Laminat-høyde for pendeldør (kun PDI_ISOLERT).

    Args:
        blade_type: Dørbladtype
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Laminat-høyde i mm, eller None hvis ikke aktuelt
    """
    komp = PD_KOMPONENTER.get(blade_type, {})
    if not komp.get('har_laminat'):
        return None
    blad_h = pd_dorblad_hoyde(blade_type, karm_h, floyer)
    return blad_h - komp.get('laminat_offset', 8)


def produksjonsmal_pd(blade_type: str, karm_b: int, karm_h: int, floyer: int = 1) -> dict:
    """Komplett produksjonsmål for pendeldør.

    Args:
        blade_type: Dørbladtype (PDI_ISOLERT, PDPC_POLY, PDPO_OPAL)
        karm_b: Karmbredde i mm
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Dict med alle PD-produksjonsmål
    """
    blad_b = pd_dorblad_bredde(blade_type, karm_b, floyer)
    blad_h = pd_dorblad_hoyde(blade_type, karm_h, floyer)
    komp = PD_KOMPONENTER.get(blade_type, {})

    result = {
        'karm': {
            'bredde': karm_b,
            'hoyde': karm_h,
        },
        'dorblad': {
            'antall': floyer,
            'bredde': blad_b,
            'hoyde': blad_h,
        },
        'sparkeplate': {
            'antall': floyer,
            'bredde': pd_sparkeplate_bredde(blade_type, karm_b, floyer),
        },
        'avviserboyler': {
            'antall': floyer,
            'lengde': pd_avviserboyler_lengde(blade_type, karm_b, floyer),
        },
    }

    # PDPC/PDPO har ryggforsterkning
    if 'ryggforsterkning_hoyde' in komp:
        result['ryggforsterkning'] = {
            'antall': floyer,
            'hoyde': pd_ryggforsterkning_hoyde(blade_type, karm_h, floyer),
        }
        result['ryggforst_overdel'] = {
            'antall': floyer,
            'lengde': pd_ryggforst_overdel(blade_type, karm_b, floyer),
        }

    # PDI har laminat
    if komp.get('har_laminat'):
        result['laminat'] = {
            'antall': floyer * 2,
            'bredde': pd_laminat_bredde(blade_type, karm_b, floyer),
            'hoyde': pd_laminat_hoyde(blade_type, karm_h, floyer),
        }

    return result


# =============================================================================
# KARM-KOMPONENTER
# =============================================================================

def sidestolpe_bredde(karm_type: str) -> int:
    """Sidestolpe-bredde for karmtypen.

    Args:
        karm_type: Karmtype

    Returns:
        Sidestolpe-bredde i mm
    """
    return KARM_SIDESTOLPE_WIDTH.get(karm_type, 50)


def toppstykke_lengde(karm_type: str, karm_b: int) -> int:
    """Toppstykke-lengde (karmbredde).

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm

    Returns:
        Toppstykke-lengde i mm
    """
    return karm_b


def sidestolpe_lengde(karm_type: str, karm_h: int) -> int:
    """Sidestolpe-lengde (karmhøyde).

    Args:
        karm_type: Karmtype
        karm_h: Karmhøyde i mm

    Returns:
        Sidestolpe-lengde i mm
    """
    return karm_h


def er_blad_flush(karm_type: str) -> bool:
    """Sjekk om dørblad er flush med framkant.

    Type 1 og 2 karmer har flush dørblad.
    Type 3 karmer har sentrert dørblad.

    Args:
        karm_type: Karmtype

    Returns:
        True hvis flush, False hvis sentrert
    """
    return karm_type in KARM_BLADE_FLUSH


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
# AREAL OG DIVERSE
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


# =============================================================================
# HJELPEFUNKSJONER FOR PRODUKSJONSGRUNNLAG
# =============================================================================

def kappliste_karm(karm_type: str, karm_b: int, karm_h: int) -> dict:
    """Generer kappliste for karm.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        karm_h: Karmhøyde i mm

    Returns:
        Dict med kapp-lengder for karm-komponenter
    """
    return {
        'toppstykke': {
            'antall': 1,
            'lengde': toppstykke_lengde(karm_type, karm_b),
        },
        'sidestolpe': {
            'antall': 2,
            'lengde': sidestolpe_lengde(karm_type, karm_h),
        },
    }


def kappliste_dorblad(karm_type: str, karm_b: int, karm_h: int,
                      floyer: int = 1) -> dict:
    """Generer kappliste for dørblad og laminat.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Dict med dørblad- og laminat-dimensjoner
    """
    blad_b = dorblad_bredde(karm_type, karm_b, floyer)
    blad_h = dorblad_hoyde(karm_type, karm_h, floyer)
    lam_b = laminat_bredde(karm_type, karm_b, floyer)
    lam_h = laminat_hoyde(karm_type, karm_h, floyer)

    return {
        'dorblad': {
            'antall': floyer,
            'bredde': blad_b,
            'hoyde': blad_h,
        },
        'laminat': {
            'antall': floyer * 2,  # 2 sider per dørblad
            'bredde': lam_b,
            'hoyde': lam_h,
        },
    }


def kappliste_terskel(karm_type: str, karm_b: int, floyer: int = 1) -> dict:
    """Generer kappliste for terskel.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        floyer: Antall fløyer

    Returns:
        Dict med terskel-dimensjoner
    """
    return {
        'terskel': {
            'antall': 1,
            'lengde': terskel_lengde(karm_type, karm_b, floyer),
        },
    }


def produksjonsmal(karm_type: str, karm_b: int, karm_h: int, floyer: int = 1) -> dict:
    """Komplett produksjonsmål for en dør.

    Args:
        karm_type: Karmtype
        karm_b: Karmbredde i mm
        karm_h: Karmhøyde i mm
        floyer: Antall fløyer

    Returns:
        Dict med alle produksjonsmål
    """
    blad_b = dorblad_bredde(karm_type, karm_b, floyer)
    blad_h = dorblad_hoyde(karm_type, karm_h, floyer)

    return {
        'karm': {
            'bredde': karm_b,
            'hoyde': karm_h,
        },
        'dorblad': {
            'bredde': blad_b,
            'hoyde': blad_h,
        },
        'terskel': {
            'lengde': terskel_lengde(karm_type, karm_b, floyer),
        },
        'laminat': {
            'bredde': laminat_bredde(karm_type, karm_b, floyer),
            'hoyde': laminat_hoyde(karm_type, karm_h, floyer),
        },
    }


# =============================================================================
# TILGJENGELIGHET OG ADVARSLER
# =============================================================================

def sjekk_kalkyle_status(karm_type: str, blade_type: str, floyer: int = 1) -> dict:
    """Sjekk om kalkyler er tilgjengelige for en konfigurasjon.

    Args:
        karm_type: Karmtype (f.eks. 'SD1', 'KD2', 'PD1')
        blade_type: Dørbladtype (f.eks. 'SDI_ROCA', 'PDI_ISOLERT')
        floyer: Antall fløyer

    Returns:
        Dict med status:
        - 'tilgjengelig': bool - True hvis alle kalkyler finnes
        - 'mangler': list - Liste over manglende kalkyler
        - 'advarsel': str - Advarselstekst for GUI
    """
    mangler = []

    # Sjekk om det er PD-type (bruker egen struktur)
    er_pd = karm_type.startswith('PD')

    if er_pd:
        # Sjekk PD-spesifikke offsets
        if blade_type not in PD_DORBLAD_OFFSETS:
            mangler.append(f'Dørbladtype {blade_type}')
        elif floyer not in PD_DORBLAD_OFFSETS.get(blade_type, {}):
            mangler.append(f'{floyer}-fløyet for {blade_type}')

        if blade_type not in PD_KOMPONENTER:
            mangler.append(f'PD-komponenter for {blade_type}')
    else:
        # Sjekk standard offsets
        if karm_type not in DORBLAD_OFFSETS:
            mangler.append(f'Dørblad-offsets for {karm_type}')
        elif floyer not in DORBLAD_OFFSETS.get(karm_type, {}):
            mangler.append(f'{floyer}-fløyet for {karm_type}')

        if karm_type not in TERSKEL_OFFSETS:
            mangler.append(f'Terskel-offset for {karm_type}')
        elif floyer not in TERSKEL_OFFSETS.get(karm_type, {}):
            mangler.append(f'{floyer}-fløyet terskel for {karm_type}')

        if karm_type not in LAMINAT_OFFSETS:
            mangler.append(f'Laminat-offset for {karm_type}')

    # Bygg advarselstekst
    if mangler:
        advarsel = f"Produksjonskalkyler mangler: {', '.join(mangler)}"
    else:
        advarsel = ""

    return {
        'tilgjengelig': len(mangler) == 0,
        'mangler': mangler,
        'advarsel': advarsel,
    }


def hent_alle_manglende_kalkyler() -> dict:
    """Hent oversikt over alle karmtyper som mangler kalkyler.

    Returns:
        Dict med {karmtype: [manglende kalkyler]}
    """
    from .constants import DOOR_KARM_TYPES, KARM_BLADE_TYPES

    manglende = {}

    for door_type, karm_types in DOOR_KARM_TYPES.items():
        for karm_type in karm_types:
            blade_types = KARM_BLADE_TYPES.get(karm_type, [])

            for blade_type in blade_types:
                for floyer in [1, 2]:
                    status = sjekk_kalkyle_status(karm_type, blade_type, floyer)
                    if not status['tilgjengelig']:
                        key = f"{karm_type} ({blade_type}, {floyer}-fl)"
                        manglende[key] = status['mangler']

    return manglende


# Liste over karmtyper med fullstendige kalkyler
KALKYLER_TILGJENGELIG = {
    # Format: (karm_type, floyer): [blade_types]
    ('SD1', 1): ['SDI_ROCA', 'SDI_SNAPIN'],
    ('BD1', 1): ['BD_ROCKWOOL'],
    ('KD1', 1): ['KD_ISOLERT'],
    ('KD2', 1): ['KD_ISOLERT'],
    ('PD1', 1): ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    ('PD1', 2): ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    ('PD2', 1): ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
    ('PD2', 2): ['PDI_ISOLERT', 'PDPC_POLY', 'PDPO_OPAL'],
}
