"""
Produksjonsliste-modell for KIAS Dørkonfigurator.

Håndterer samling av dører til en produksjonsliste med gruppering
av like komponenter for kappeliste-generering.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from collections import defaultdict
import uuid

from .door import DoorParams
from ..utils.calculations import (
    karm_bredde, karm_hoyde,
    dorblad_bredde, dorblad_hoyde,
    terskel_lengde, laminat_mal, dekklist_lengde,
)
from ..utils.constants import DOOR_TYPES


@dataclass
class ProductionItem:
    """En komponent i produksjonslisten."""
    komponent: str           # "Overligger", "Hengselside", "Dørblad", etc.
    antall: int
    bredde: Optional[int] = None
    hoyde: Optional[int] = None
    lengde: Optional[int] = None
    farge: str = 'RAL 9010'
    side: Optional[str] = None  # "V", "H", "1V, 1H", eller None
    dor_id: str = ''           # Referanse til hvilken dør
    karm_type: str = ''        # Karmtype for gruppering


@dataclass
class ProductionDoor:
    """En dør i produksjonslisten med unik ID."""
    id: str
    params: DoorParams
    label: str = ''  # Visningsnavn i listen

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.label:
            self.label = self._generate_label()

    def _generate_label(self) -> str:
        """Genererer visningsnavn, f.eks. 'Innerdør - SD1 10x21'."""
        p = self.params
        door_type_name = DOOR_TYPES.get(p.door_type, p.door_type)
        dm_w = round(p.width / 100)
        dm_h = round(p.height / 100)
        return f"{door_type_name} - {p.karm_type} {dm_w}x{dm_h}"


# Karmtype-familier for kappeliste-gruppering
KARM_FAMILY_GROUPS = {
    'SD1': 'SD1_SD2',
    'SD2': 'SD1_SD2',
    'SD3/ID': 'SD3_ID',
}

KARM_FAMILY_TITLES = {
    'SD1_SD2': 'Slagdørkarm Justerbar (SD1 og SD2)',
    'SD3_ID': 'Slagdørkarm Justerbar (SD3/ID)',
}

KARM_FAMILY_ORDER = ['SD1_SD2', 'SD3_ID']

KARM_KOMPONENT_ORDER = ['Overligger', 'Hengselside', 'Sluttstykkeside']
DORRAMME_KOMPONENT_ORDER = ['DR40 over-/underdel', 'DR40 sidedel']
DIVERSE_KOMPONENT_ORDER = ['Glassfiberlaminat', 'Terskel', 'Dekklist']


class ProductionList:
    """Samling av produksjonskomponenter fra flere dører."""

    def __init__(self):
        self._doors: List[ProductionDoor] = []
        self._items_cache: Optional[List[ProductionItem]] = None

    @property
    def doors(self) -> List[ProductionDoor]:
        """Returnerer alle dører i listen."""
        return self._doors

    @property
    def door_count(self) -> int:
        """Antall dører i listen."""
        return len(self._doors)

    def add_door(self, door: DoorParams) -> str:
        """Legger til en dør i produksjonslisten.

        Args:
            door: DoorParams-objekt

        Returns:
            ID for den tillagte døren
        """
        prod_door = ProductionDoor(id='', params=door)
        self._doors.append(prod_door)
        self._items_cache = None  # Invalider cache
        return prod_door.id

    def remove_door(self, door_id: str) -> bool:
        """Fjerner en dør fra listen.

        Args:
            door_id: ID for døren som skal fjernes

        Returns:
            True hvis døren ble fjernet, False ellers
        """
        for i, door in enumerate(self._doors):
            if door.id == door_id:
                del self._doors[i]
                self._items_cache = None  # Invalider cache
                return True
        return False

    def get_door(self, door_id: str) -> Optional[ProductionDoor]:
        """Henter en dør etter ID."""
        for door in self._doors:
            if door.id == door_id:
                return door
        return None

    def update_door(self, door_id: str, params: DoorParams) -> bool:
        """Oppdaterer parametere for en eksisterende dør.

        Args:
            door_id: ID for døren som skal oppdateres
            params: Nye DoorParams

        Returns:
            True hvis døren ble oppdatert, False ellers
        """
        for door in self._doors:
            if door.id == door_id:
                door.params = params
                door.label = door._generate_label()
                self._items_cache = None
                return True
        return False

    def clear(self) -> None:
        """Tømmer hele produksjonslisten."""
        self._doors.clear()
        self._items_cache = None

    def to_list_dict(self) -> dict:
        """Serialiserer hele dørlisten til dict for .kdl-eksport."""
        return {
            'version': '1.0',
            'type': 'door_list',
            'doors': [
                {
                    'id': d.id,
                    'label': d.label,
                    'params': d.params.to_dict(),
                }
                for d in self._doors
            ],
        }

    def from_list_dict(self, data: dict) -> int:
        """Importerer dører fra dict (adderer til eksisterende liste).

        Args:
            data: Dict fra .kdl-fil

        Returns:
            Antall importerte dører
        """
        doors = data.get('doors', [])
        count = 0
        for entry in doors:
            params = DoorParams.from_dict(entry.get('params', {}))
            self.add_door(params)
            count += 1
        return count

    def get_all_items(self) -> List[ProductionItem]:
        """Henter alle produksjonskomponenter fra alle dører.

        Returns:
            Liste med alle ProductionItem
        """
        if self._items_cache is not None:
            return self._items_cache
        items: List[ProductionItem] = []
        for door in self._doors:
            items.extend(self._build_items_for_door(door))
        self._items_cache = items
        return items

    def _build_items_for_door(self, door: ProductionDoor) -> List[ProductionItem]:
        """Beregner alle produksjonskomponenter for en enkelt dør."""
        p = door.params
        karm_type = p.karm_type
        blade_type = p.blade_type
        floyer = p.floyer
        luftspalte = p.effective_luftspalte()

        karm_b = karm_bredde(karm_type, p.width)
        karm_h = karm_hoyde(karm_type, p.height)

        # Slagretning: left → hengselside=V, sluttstykke=H
        if p.swing_direction == 'left':
            hengsel_side = 'V'
            sluttstykke_side = 'H'
        else:
            hengsel_side = 'H'
            sluttstykke_side = 'V'

        items: List[ProductionItem] = []

        # --- Karm ---
        items.append(ProductionItem(
            komponent='Overligger', antall=1, lengde=karm_b,
            farge=p.karm_color, dor_id=door.id, karm_type=karm_type,
        ))
        items.append(ProductionItem(
            komponent='Hengselside', antall=1, lengde=karm_h,
            farge=p.karm_color, side=hengsel_side,
            dor_id=door.id, karm_type=karm_type,
        ))
        items.append(ProductionItem(
            komponent='Sluttstykkeside', antall=1, lengde=karm_h,
            farge=p.karm_color, side=sluttstykke_side,
            dor_id=door.id, karm_type=karm_type,
        ))

        # --- Dørramme ---
        db_b_total = dorblad_bredde(karm_type, karm_b, floyer, blade_type)
        db_h = dorblad_hoyde(karm_type, karm_h, floyer, blade_type, luftspalte)

        if floyer == 2 and db_b_total:
            split_pct = p.floyer_split / 100.0
            db1_b = round(db_b_total * split_pct)
            db2_b = db_b_total - db1_b
            blade_widths = [db1_b, db2_b]
        elif db_b_total:
            blade_widths = [db_b_total]
        else:
            blade_widths = []

        for bw in blade_widths:
            items.append(ProductionItem(
                komponent='DR40 over-/underdel', antall=2, lengde=bw,
                farge=p.color, dor_id=door.id, karm_type=karm_type,
            ))
            if db_h:
                items.append(ProductionItem(
                    komponent='DR40 sidedel', antall=2, lengde=db_h,
                    farge=p.color, dor_id=door.id, karm_type=karm_type,
                ))

        # --- Tilbehør ---
        # Glassfiberlaminat (2 per fløy: front + bak)
        for bw in blade_widths:
            if bw and db_h:
                lam_b, lam_h = laminat_mal(karm_type, bw, db_h, blade_type)
                if lam_b and lam_h:
                    items.append(ProductionItem(
                        komponent='Glassfiberlaminat', antall=2,
                        bredde=lam_b, hoyde=lam_h,
                        farge=p.color, dor_id=door.id, karm_type=karm_type,
                    ))

        # Terskel (kun hvis type ≠ 'ingen')
        if p.threshold_type != 'ingen':
            t_lengde = terskel_lengde(karm_type, karm_b, floyer)
            if t_lengde:
                items.append(ProductionItem(
                    komponent='Terskel', antall=1, lengde=t_lengde,
                    dor_id=door.id, karm_type=karm_type,
                ))

        # Dekklist (kun 2-fløyet)
        if floyer == 2:
            dk_lengde = dekklist_lengde(karm_h)
            items.append(ProductionItem(
                komponent='Dekklist', antall=1, lengde=dk_lengde,
                farge=p.karm_color, dor_id=door.id, karm_type=karm_type,
            ))

        return items

    def _extract_items(self, mal: dict, dor_id: str, karm_type: str) -> List[ProductionItem]:
        """Ekstraherer ProductionItem fra produksjonsmål-dict.

        Args:
            mal: Dict med produksjonsmål fra hent_produksjonsmal()
            dor_id: Dør-ID
            karm_type: Karmtype

        Returns:
            Liste med ProductionItem
        """
        items = []

        # Karm-komponenter
        if 'karm' in mal:
            karm = mal['karm']

            # Ny struktur med overligger, hengselside, sluttstykkeside
            if 'overligger' in karm:
                ol = karm['overligger']
                items.append(ProductionItem(
                    komponent='Overligger',
                    antall=ol.get('antall', 1),
                    lengde=ol.get('lengde'),
                    farge=ol.get('farge', 'RAL 9010'),
                    dor_id=dor_id,
                    karm_type=karm_type,
                ))

            if 'hengselside' in karm:
                hs = karm['hengselside']
                items.append(ProductionItem(
                    komponent='Hengselside',
                    antall=hs.get('antall', 1),
                    lengde=hs.get('lengde'),
                    farge=hs.get('farge', 'RAL 9010'),
                    side=hs.get('side'),
                    dor_id=dor_id,
                    karm_type=karm_type,
                ))

            if 'sluttstykkeside' in karm:
                ss = karm['sluttstykkeside']
                items.append(ProductionItem(
                    komponent='Sluttstykkeside',
                    antall=ss.get('antall', 1),
                    lengde=ss.get('lengde'),
                    farge=ss.get('farge', 'RAL 9010'),
                    side=ss.get('side'),
                    dor_id=dor_id,
                    karm_type=karm_type,
                ))

            if 'sidedel' in karm:
                sd = karm['sidedel']
                items.append(ProductionItem(
                    komponent='Sidedel',
                    antall=sd.get('antall', 2),
                    lengde=sd.get('lengde'),
                    farge=sd.get('farge', 'RAL 9010'),
                    side=sd.get('side'),
                    dor_id=dor_id,
                    karm_type=karm_type,
                ))

        # Dørblad
        if 'dorblad' in mal:
            db = mal['dorblad']
            items.append(ProductionItem(
                komponent='Dørblad',
                antall=db.get('antall', 1),
                bredde=db.get('bredde'),
                hoyde=db.get('hoyde'),
                farge=db.get('farge', 'RAL 9010'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # Terskel
        if 'terskel' in mal:
            t = mal['terskel']
            items.append(ProductionItem(
                komponent='Terskel',
                antall=t.get('antall', 1),
                lengde=t.get('lengde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # Løfteterskel (BR)
        if 'lofteterskel' in mal:
            lt = mal['lofteterskel']
            items.append(ProductionItem(
                komponent='Løfteterskel',
                antall=lt.get('antall', 1),
                lengde=lt.get('lengde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # Laminat
        if 'laminat' in mal:
            lam = mal['laminat']
            items.append(ProductionItem(
                komponent='Laminat',
                antall=lam.get('antall', 2),
                bredde=lam.get('bredde'),
                hoyde=lam.get('hoyde'),
                farge=lam.get('farge', 'RAL 9010'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # Dekklist (2-fløyet)
        if 'dekklist' in mal:
            dk = mal['dekklist']
            items.append(ProductionItem(
                komponent='Dekklist',
                antall=dk.get('antall', 1),
                lengde=dk.get('lengde'),
                farge=dk.get('farge', 'RAL 9010'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # SKD-spesifikke
        if 'skinne' in mal:
            sk = mal['skinne']
            items.append(ProductionItem(
                komponent='Skinne',
                antall=sk.get('antall', 1),
                lengde=sk.get('lengde'),
                side=sk.get('side'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        if 'innerskinne' in mal:
            isk = mal['innerskinne']
            items.append(ProductionItem(
                komponent='Innerskinne',
                antall=isk.get('antall', 2),
                lengde=isk.get('lengde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        if 'styreskinne' in mal:
            ssk = mal['styreskinne']
            items.append(ProductionItem(
                komponent='Styreskinne',
                antall=ssk.get('antall', 1),
                lengde=ssk.get('lengde'),
                side=ssk.get('side'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        # PD-spesifikke
        if 'sparkeplate' in mal:
            sp = mal['sparkeplate']
            items.append(ProductionItem(
                komponent='Sparkeplate',
                antall=sp.get('antall', 1),
                bredde=sp.get('bredde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        if 'ryggforsterkning' in mal:
            rf = mal['ryggforsterkning']
            items.append(ProductionItem(
                komponent='Ryggforsterkning',
                antall=rf.get('antall', 1),
                hoyde=rf.get('hoyde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        if 'ryggforst_overdel' in mal:
            rfo = mal['ryggforst_overdel']
            items.append(ProductionItem(
                komponent='Ryggforst. overdel',
                antall=rfo.get('antall', 1),
                lengde=rfo.get('lengde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        if 'avviserboyler' in mal:
            ab = mal['avviserboyler']
            items.append(ProductionItem(
                komponent='Avviserbøyler',
                antall=ab.get('antall', 1),
                lengde=ab.get('lengde'),
                dor_id=dor_id,
                karm_type=karm_type,
            ))

        return items

    def get_grouped_items(self) -> Dict[str, Dict[str, List[ProductionItem]]]:
        """Grupperer komponenter for kappeliste.

        Grupperer etter:
        1. Karmtype (SD1, KD1, SKD1, etc.)
        2. Komponenttype (Overligger, Hengselside, Dørblad, etc.)
        3. Like mål og farge akkumuleres

        Returns:
            Nested dict: {karm_type: {komponent: [items]}}
        """
        items = self.get_all_items()

        # Grupper etter karmtype og komponent
        grouped: Dict[str, Dict[str, List[ProductionItem]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for item in items:
            grouped[item.karm_type][item.komponent].append(item)

        # Akkumuler like komponenter innen hver gruppe
        result = {}
        for karm_type, komponent_dict in grouped.items():
            result[karm_type] = {}
            for komponent, items_list in komponent_dict.items():
                result[karm_type][komponent] = self._accumulate_items(items_list)

        return result

    def _accumulate_items(self, items: List[ProductionItem]) -> List[ProductionItem]:
        """Akkumulerer like komponenter.

        Komponenter med samme mål, farge og side slås sammen.

        Args:
            items: Liste med ProductionItem

        Returns:
            Liste med akkumulerte ProductionItem
        """
        # Bruk tuple av (bredde, hoyde, lengde, farge, side) som nøkkel
        accumulated: Dict[tuple, ProductionItem] = {}

        for item in items:
            key = (item.bredde, item.hoyde, item.lengde, item.farge, item.side)

            if key in accumulated:
                accumulated[key].antall += item.antall
            else:
                # Lag kopi uten dor_id (siden vi akkumulerer på tvers av dører)
                new_item = ProductionItem(
                    komponent=item.komponent,
                    antall=item.antall,
                    bredde=item.bredde,
                    hoyde=item.hoyde,
                    lengde=item.lengde,
                    farge=item.farge,
                    side=item.side,
                    karm_type=item.karm_type,
                )
                accumulated[key] = new_item

        return list(accumulated.values())

    def get_summary(self) -> Dict[str, int]:
        """Henter oppsummering av produksjonslisten.

        Returns:
            Dict med antall per karmtype
        """
        summary: Dict[str, int] = defaultdict(int)
        for door in self._doors:
            summary[door.params.karm_type] += 1
        return dict(summary)

    def get_kappeliste_sections(self) -> List[dict]:
        """Returnerer seksjoner for kappeliste-visning.

        Grupperer produksjonskomponenter etter karmtype-familie
        og akkumulerer like komponenter med V/H-telling.

        Returns:
            Liste med seksjoner, hver med 'title' og 'rows'
        """
        items = self.get_all_items()
        if not items:
            return []

        sections: List[dict] = []

        # Kategoriser items
        karm_komps = {'Overligger', 'Hengselside', 'Sluttstykkeside'}
        dorramme_komps = {'DR40 over-/underdel', 'DR40 sidedel'}
        diverse_komps = {'Glassfiberlaminat', 'Terskel', 'Dekklist'}

        karm_items = [i for i in items if i.komponent in karm_komps]
        dorramme_items = [i for i in items if i.komponent in dorramme_komps]
        diverse_items = [i for i in items if i.komponent in diverse_komps]

        # Grupper karm etter familie
        karm_by_family: Dict[str, List[ProductionItem]] = defaultdict(list)
        for item in karm_items:
            family = KARM_FAMILY_GROUPS.get(item.karm_type, item.karm_type)
            karm_by_family[family].append(item)

        for family_key in KARM_FAMILY_ORDER:
            family_items = karm_by_family.get(family_key)
            if not family_items:
                continue
            rows = self._accumulate_karm_items(family_items)
            sections.append({
                'title': KARM_FAMILY_TITLES[family_key],
                'rows': rows,
            })

        # Dørramme (alle karmtyper samlet)
        if dorramme_items:
            rows = self._accumulate_standard_items(
                dorramme_items, DORRAMME_KOMPONENT_ORDER
            )
            sections.append({'title': '40mm Dørramme', 'rows': rows})

        # Diverse
        if diverse_items:
            rows = self._accumulate_standard_items(
                diverse_items, DIVERSE_KOMPONENT_ORDER
            )
            sections.append({'title': 'Diverse', 'rows': rows})

        return sections

    def _accumulate_karm_items(self, items: List[ProductionItem]) -> List[dict]:
        """Akkumulerer karm-items med V/H-telling.

        Grupperer på (komponent, lengde, farge) og teller V/H separat.
        """
        groups: Dict[tuple, Dict[str, int]] = defaultdict(
            lambda: {'V': 0, 'H': 0, 'none': 0}
        )

        for item in items:
            key = (item.komponent, item.lengde, item.farge)
            if item.side == 'V':
                groups[key]['V'] += item.antall
            elif item.side == 'H':
                groups[key]['H'] += item.antall
            else:
                groups[key]['none'] += item.antall

        def sort_key(entry):
            (komponent, lengde, farge) = entry[0]
            order = (KARM_KOMPONENT_ORDER.index(komponent)
                     if komponent in KARM_KOMPONENT_ORDER else 99)
            return (order, lengde or 0)

        rows = []
        for (komponent, lengde, farge), counts in sorted(
            groups.items(), key=sort_key
        ):
            total = counts['V'] + counts['H'] + counts['none']
            parts = []
            if counts['V']:
                parts.append(f"{counts['V']}V")
            if counts['H']:
                parts.append(f"{counts['H']}H")
            slagretning = ', '.join(parts)

            rows.append({
                'profilnavn': komponent,
                'stk': total,
                'mm': str(lengde) if lengde else '',
                'slagretning': slagretning,
                'farge': farge or '',
                'merknad': '',
            })

        return rows

    def _accumulate_standard_items(
        self, items: List[ProductionItem], komponent_order: list
    ) -> List[dict]:
        """Akkumulerer standard-items (dørramme, diverse).

        Grupperer på (komponent, mål-streng, farge) og summerer antall.
        """
        groups: Dict[tuple, int] = defaultdict(int)

        for item in items:
            if item.bredde and item.hoyde:
                mm_str = f"{item.bredde} x {item.hoyde}"
            elif item.lengde:
                mm_str = str(item.lengde)
            else:
                mm_str = ''
            key = (item.komponent, mm_str, item.farge or '')
            groups[key] += item.antall

        def sort_key(entry):
            (komponent, mm_str, farge) = entry[0]
            order = (komponent_order.index(komponent)
                     if komponent in komponent_order else 99)
            return (order, mm_str)

        rows = []
        for (komponent, mm_str, farge), total in sorted(
            groups.items(), key=sort_key
        ):
            rows.append({
                'profilnavn': komponent,
                'stk': total,
                'mm': mm_str,
                'slagretning': '',
                'farge': farge,
                'merknad': '',
            })

        return rows


# Global produksjonsliste (singleton for enkel tilgang)
_production_list: Optional[ProductionList] = None


def get_production_list() -> ProductionList:
    """Henter global produksjonsliste.

    Returns:
        ProductionList singleton
    """
    global _production_list
    if _production_list is None:
        _production_list = ProductionList()
    return _production_list


def reset_production_list() -> None:
    """Nullstiller global produksjonsliste."""
    global _production_list
    _production_list = ProductionList()
