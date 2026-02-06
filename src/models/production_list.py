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
from ..utils.calculations import karm_bredde, karm_hoyde


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
        """Genererer visningsnavn for døren."""
        p = self.params
        karm_b = karm_bredde(p.karm_type, p.width)
        karm_h = karm_hoyde(p.karm_type, p.height)
        size_str = f"{karm_b}x{karm_h}"
        return f"{p.karm_type} {size_str} {p.color}"


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

    def clear(self) -> None:
        """Tømmer hele produksjonslisten."""
        self._doors.clear()
        self._items_cache = None

    def get_all_items(self) -> List[ProductionItem]:
        """Henter alle produksjonskomponenter fra alle dører.

        Returns:
            Liste med alle ProductionItem (tom – bygges ut senere)
        """
        return []

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
