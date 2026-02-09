"""
Genererer ordretekst (ordrelinjetekst) fra DoorParams og DOOR_REGISTRY.
"""

from ..doors import DOOR_REGISTRY
from .constants import RAL_COLORS, SWING_DIRECTIONS, THRESHOLD_LUFTSPALTE


# Globale terskel-tekster (felles for alle dørtyper)
# Dørtyper kan overstyre enkelt-nøkler via 'terskel_tekst' i sin ordretekst-def.
TERSKEL_TEKST = {
    'ingen': None,
    'slepelist': 'Slepelist i pvc',
    'anslag_37': 'Terskel (37 mm), pulverlakkert {karm_farge}',
    'anslag_kjorbar_25': 'Kjørbar terskel (h=25 mm) i aluminium, pulverlakkert {karm_farge}',
    'hc20': 'HC-terskel 20 mm (8 mm luftespalte)',
    'hcid': 'Luftespalte {luftspalte} mm ev. terskel (HC), pulverlakkert {karm_farge}',
}


def _farge_tekst(ral_kode: str) -> str:
    """Formaterer RAL-kode til lesbar tekst, f.eks. 'Renhvit (RAL 9010)'."""
    info = RAL_COLORS.get(ral_kode)
    if info:
        return f"{info['name']} ({ral_kode})"
    return ral_kode or "—"


def generer_ordretekst(door) -> list[str]:
    """Genererer ordretekst-linjer fra DoorParams.

    Returnerer [tittel, linje1, linje2, ...].
    Linjer med verdien 'Ingen' eller None utelates.
    """
    door_def = DOOR_REGISTRY.get(door.door_type)
    if not door_def or 'ordretekst' not in door_def:
        return []

    ordretekst = door_def['ordretekst']
    floyer = door.floyer
    karm_type = door.karm_type
    blade_type = door.blade_type

    # --- Tittel ---
    tittel = ordretekst['tittel'].get(floyer, '')

    # --- Farge-tekst ---
    farge = _farge_tekst(door.color)
    karm_farge = _farge_tekst(door.karm_color)

    # --- Slagretning ---
    slagretning = SWING_DIRECTIONS.get(door.swing_direction, door.swing_direction)

    # --- Transportmål ---
    bt_b = door.transport_width_90()
    bt_h = door.transport_height_by_threshold()

    # --- Karmbeskrivelse ---
    karm_besk_maler = door_def.get('karm_beskrivelse', {})
    karm_beskrivelse = karm_besk_maler.get(karm_type, '')
    karm_beskrivelse = karm_beskrivelse.format(farge=karm_farge, veggtykkelse=door.thickness)

    # --- Hengsler ---
    hengsler_data = door_def.get('hengsler', {})
    hengsel_info = hengsler_data.get(blade_type, {})
    hengsler_tekst = ''
    if hengsel_info:
        navn = hengsel_info['navn']
        tekst = hengsel_info['tekst'].get(floyer, '')
        hengsler_tekst = f"{navn} {tekst}".strip()

    # --- Låskasse og beslag (fra DoorParams) ---
    laaskasse = door.lock_case if door.lock_case else ''
    beslag = door.handle_type if door.handle_type else ''

    # --- Luftspalte ---
    luftspalte = door.effective_luftspalte()

    # --- Placeholder-verdier ---
    verdier = {
        'bm_b': door.width,
        'bm_h': door.height,
        'bt_b': bt_b if bt_b else '—',
        'bt_h': bt_h if bt_h else '—',
        'slagretning': slagretning,
        'blad_tykkelse': door.blade_thickness,
        'farge': farge,
        'karm_farge': karm_farge,
        'karm_beskrivelse': karm_beskrivelse,
        'laaskasse': laaskasse,
        'beslag': beslag,
        'hengsler': hengsler_tekst,
        'luftspalte': luftspalte,
    }

    # --- Bygg linjer ---
    resultat = [tittel, 'Produktdetaljer:']

    for mal in ordretekst['linjer']:
        linje = mal.format(**verdier)
        # Hopp over linjer der verdien er "Ingen" eller tom
        if _skal_utelates(linje, verdier, mal):
            continue
        resultat.append(linje)

    # 2-fløyet ekstra-linjer
    if floyer == 2:
        for mal in ordretekst.get('linjer_2floyet', []):
            linje = mal.format(**verdier)
            resultat.append(linje)

    # Terskel (dørtype-spesifikk overstyrer global)
    terskel_overstyr = ordretekst.get('terskel_tekst', {})
    terskel_mal = terskel_overstyr.get(door.threshold_type) or TERSKEL_TEKST.get(door.threshold_type)
    if terskel_mal:
        resultat.append(terskel_mal.format(**verdier))

    return resultat


def _skal_utelates(linje: str, verdier: dict, mal: str) -> bool:
    """Sjekker om en linje skal utelates fordi verdien er 'Ingen' eller tom."""
    # Sjekk om malen kun er en placeholder ({laaskasse}, {beslag}, {hengsler})
    stripped = mal.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        nøkkel = stripped[1:-1]
        verdi = verdier.get(nøkkel, '')
        if not verdi or verdi == 'Ingen':
            return True
    # Sjekk for "Låskasse Ingen" osv.
    if 'Ingen' in linje and ('Låskasse' in mal or '{laaskasse}' in mal):
        return True
    if 'Ingen' in linje and ('{beslag}' in mal):
        return True
    return False
