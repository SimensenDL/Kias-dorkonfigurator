"""
Datamodell for dørkonfigurasjon.
Alle dimensjoner i millimeter (mm).
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from ..utils.constants import (
    DEFAULT_DIMENSIONS, DEFAULT_COLOR, THRESHOLD_LUFTSPALTE,
    DOOR_BLADE_TYPES, KARM_BLADE_TYPES, DOOR_KARM_TYPES,
    DOOR_TYPE_BLADE_OVERRIDE,
    HINGE_TYPES, KARM_HINGE_TYPES,
    DIMENSION_DIFFERENTIALS, KARM_THRESHOLD_TYPES,
    TRANSPORT_WIDTH_OFFSETS, TRANSPORT_HEIGHT_OFFSETS,
    KARM_SIZE_OFFSETS, KARM_SIDESTOLPE_WIDTH, KARM_BLADE_FLUSH,
    DEFAULT_THRESHOLDS, DEFAULT_LUFTSPALTE
)


@dataclass
class DoorParams:
    """
    Representerer en komplett dørkonfigurasjon.
    Alle dimensjoner i millimeter (mm).
    """
    # Prosjektinfo
    project_id: str = ""
    customer: str = ""

    # Dørtype og grunnmål
    door_type: str = "SDI"
    karm_type: str = "SD1"
    floyer: int = 1  # Antall fløyer (1 eller 2)
    floyer_split: int = 50  # Prosent av total bredde for fløy 1 (50 = lik oppdeling)
    width: int = 1010    # Utsparingsbredde (BM) i mm
    height: int = 2110   # Utsparingshøyde (HM) i mm
    thickness: int = 100  # Veggtykkelse i mm
    blade_type: str = "SDI"  # Dørbladtype (nøkkel fra DOOR_BLADE_TYPES)
    blade_thickness: int = 40  # Dørbladtykkelse i mm
    utforing: str = ""  # Utforing-steg (nøkkel fra UTFORING_RANGES), tom hvis ikke aktuelt

    # Overflate/utseende
    color: str = DEFAULT_COLOR           # Dørblad farge
    karm_color: str = DEFAULT_COLOR      # Karmfarge
    wall_color: str = "#8C8C84"          # Veggfarge (hex)
    surface_type: str = "glatt"

    # Beslag og lås
    hinge_type: str = "ROCA_SF"     # Hengseltype (nøkkel fra HINGE_TYPES)
    hinge_count: int = 2            # Antall hengsler per fløy
    lock_case: str = "3065_316l"    # Låsekasse (nøkkel fra LOCK_CASES)
    handle_type: str = "vrider_sylinder_oval"  # Vrider/skilt (nøkkel fra HANDLE_TYPES)
    espagnolett: str = "ingen"      # Espagnolett for 2-fløya (nøkkel fra ESPAGNOLETT_TYPES)

    # Tilleggsutstyr
    threshold_type: str = "ingen"
    luftspalte: int = 22  # Luftspalte i mm, kun redigerbar for terskeltype 'ingen'
    adjufix: bool = False  # Adjufix karmhylser (Ja/Nei)
    lock_type: str = ""    # Fritekst, bakoverkompatibilitet (erstattes av lock_case)
    swing_direction: str = "left"

    # Pendeldør-spesifikke felter (sparkeplate tilgjengelig for alle dørtyper)
    sparkeplate: bool = False      # Sparkeplate Ja/Nei
    sparkeplate_hoyde: int = 1000  # Sparkeplate høyde i mm (hardkodet)
    avviserboyler: bool = True     # Avviserbøyler Ja/Nei

    # Spesielle egenskaper (avhenger av dørtype)
    fire_rating: str = ""
    sound_rating: int = 0
    lead_thickness: int = 0  # Blyinnlegg-tykkelse i mm (røntgendør)

    # Merknader
    notes: str = ""

    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = ""

    def apply_defaults_for_type(self) -> None:
        """Setter standardverdier basert på valgt dørtype."""
        defaults = DEFAULT_DIMENSIONS.get(self.door_type)
        if defaults:
            self.width = defaults['width']
            self.height = defaults['height']
            self.thickness = defaults['thickness']

        # Sett standard karmtype
        karm_types = DOOR_KARM_TYPES.get(self.door_type, [])
        if karm_types:
            self.karm_type = karm_types[0]

        # Sett standard dørblad – sjekk dørtype-override først, deretter karmtype
        override_blades = DOOR_TYPE_BLADE_OVERRIDE.get(self.door_type)
        if override_blades:
            self.blade_type = override_blades[0]
            self.blade_thickness = DOOR_BLADE_TYPES[self.blade_type]['thicknesses'][0]
        else:
            if karm_types:
                blade_types = KARM_BLADE_TYPES.get(karm_types[0], [])
                if blade_types:
                    self.blade_type = blade_types[0]
                    self.blade_thickness = DOOR_BLADE_TYPES[self.blade_type]['thicknesses'][0]

        # Sett standard hengseltype basert på karmtype
        hinge_types = KARM_HINGE_TYPES.get(self.karm_type, [])
        if hinge_types:
            self.hinge_type = hinge_types[0]

        # Sett standard terskeltype basert på karmtype og dørtype-default
        allowed_thresholds = KARM_THRESHOLD_TYPES.get(self.karm_type, ['ingen'])
        if allowed_thresholds:
            default_t = DEFAULT_THRESHOLDS.get(self.door_type)
            if default_t and default_t in allowed_thresholds:
                self.threshold_type = default_t
            else:
                self.threshold_type = allowed_thresholds[0]
        default_ls = DEFAULT_LUFTSPALTE.get(self.door_type)
        if default_ls is not None and self.threshold_type == 'ingen':
            self.luftspalte = default_ls
        else:
            self.luftspalte = THRESHOLD_LUFTSPALTE.get(self.threshold_type, 22)

    def effective_luftspalte(self) -> int:
        """Returnerer effektiv luftspalte basert på terskeltype.
        For 'ingen'-typen brukes den lagrede verdien,
        for alle andre typer brukes den faste verdien fra oppslagstabellen.
        """
        if self.threshold_type == 'ingen':
            return self.luftspalte
        return THRESHOLD_LUFTSPALTE.get(self.threshold_type, 22)

    def transport_width(self) -> int:
        """Beregner transportbredde (BT) fra utsparingsbredde (BM).
        BT = BM - differanse per dørtype/fløyer."""
        diffs = DIMENSION_DIFFERENTIALS.get(self.door_type, {})
        diff = diffs.get(self.floyer)
        if diff:
            return self.width - diff[0]
        return self.width  # Ingen kjent differanse

    def transport_height(self) -> int:
        """Beregner transporthøyde (HT) fra utsparingshøyde (HM).
        HT = HM - differanse per dørtype/fløyer."""
        diffs = DIMENSION_DIFFERENTIALS.get(self.door_type, {})
        diff = diffs.get(self.floyer)
        if diff:
            return self.height - diff[1]
        return self.height  # Ingen kjent differanse

    def transport_width_90(self) -> Optional[int]:
        """Transportbredde ved 90° døråpning.
        Beregnet fra karmtype-spesifikke offset-verdier fra Excel-formlene."""
        karm_offsets = TRANSPORT_WIDTH_OFFSETS.get(self.karm_type)
        if not karm_offsets:
            return None
        # Bruk 1-fløyet hvis fløyer ikke finnes for denne karmtypen
        floyer_offsets = karm_offsets.get(self.floyer) or karm_offsets.get(1)
        if floyer_offsets and floyer_offsets.get('90') is not None:
            return self.width + floyer_offsets['90']
        return None

    def transport_width_180(self) -> Optional[int]:
        """Transportbredde ved 180° døråpning.
        Beregnet fra karmtype-spesifikke offset-verdier fra Excel-formlene."""
        karm_offsets = TRANSPORT_WIDTH_OFFSETS.get(self.karm_type)
        if not karm_offsets:
            return None
        floyer_offsets = karm_offsets.get(self.floyer) or karm_offsets.get(1)
        if floyer_offsets and floyer_offsets.get('180') is not None:
            return self.width + floyer_offsets['180']
        return None

    def transport_height_by_threshold(self) -> Optional[int]:
        """Transporthøyde basert på karmtype og valgt terskeltype.
        Beregnet fra Excel-formlene.

        Merk: 'ingen' og 'slepelist' har samme beregning.
        """
        offsets = TRANSPORT_HEIGHT_OFFSETS.get(self.karm_type)
        if not offsets:
            return None
        offset = offsets.get(self.threshold_type)
        if offset is not None:
            return self.height + offset
        return None

    def karm_width(self) -> int:
        """Karmbredde = Utsparing + offset (- 10mm ved Adjufix)."""
        offsets = KARM_SIZE_OFFSETS.get(self.karm_type, {'width': 0})
        base = self.width + offsets['width']
        if self.adjufix and '3' in self.karm_type:
            base -= 10
        return base

    def karm_height(self) -> int:
        """Karmhøyde = Utsparing + offset."""
        offsets = KARM_SIZE_OFFSETS.get(self.karm_type, {'height': 0})
        return self.height + offsets['height']

    def blade_width(self) -> int:
        """Dørbladbredde = transport_width_90 eller fallback."""
        return self.transport_width_90() or self.transport_width()

    def blade_height(self) -> int:
        """Dørbladhøyde = transport_height_by_threshold eller fallback."""
        return self.transport_height_by_threshold() or self.transport_height()

    def sidestolpe_width(self) -> int:
        """Sidestolpe-bredde for denne karmtypen."""
        return KARM_SIDESTOLPE_WIDTH.get(self.karm_type, 50)

    def is_blade_flush(self) -> bool:
        """Returnerer True hvis dørblad skal være flush med framkant."""
        return self.karm_type in KARM_BLADE_FLUSH

    def area_m2(self) -> float:
        """Returnerer dørareal i kvadratmeter."""
        return (self.width * self.height) / 1_000_000

    def to_dict(self) -> dict:
        """Konverterer til dictionary for JSON-serialisering."""
        return {
            'project_id': self.project_id,
            'customer': self.customer,
            'door_type': self.door_type,
            'karm_type': self.karm_type,
            'floyer': self.floyer,
            'floyer_split': self.floyer_split,
            'width': self.width,
            'height': self.height,
            'thickness': self.thickness,
            'blade_type': self.blade_type,
            'blade_thickness': self.blade_thickness,
            'utforing': self.utforing,
            'color': self.color,
            'karm_color': self.karm_color,
            'wall_color': self.wall_color,
            'surface_type': self.surface_type,
            'hinge_type': self.hinge_type,
            'hinge_count': self.hinge_count,
            'lock_case': self.lock_case,
            'handle_type': self.handle_type,
            'espagnolett': self.espagnolett,
            'threshold_type': self.threshold_type,
            'luftspalte': self.luftspalte,
            'adjufix': self.adjufix,
            'lock_type': self.lock_type,
            'swing_direction': self.swing_direction,
            'sparkeplate': self.sparkeplate,
            'sparkeplate_hoyde': self.sparkeplate_hoyde,
            'avviserboyler': self.avviserboyler,
            'fire_rating': self.fire_rating,
            'sound_rating': self.sound_rating,
            'lead_thickness': self.lead_thickness,
            'notes': self.notes,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DoorParams':
        """Oppretter DoorParams fra dictionary."""
        # Migrering av gamle .kdf-filer: blade_type → hinge_type
        old_blade = data.get('blade_type', '')
        if old_blade == 'SDI_ROCA':
            data['blade_type'] = 'SDI'
            if data.get('hinge_type', '') in ('roca_sf', 'ROCA_SF', ''):
                data['hinge_type'] = 'ROCA_SF'
        elif old_blade == 'SDI_SNAPIN':
            data['blade_type'] = 'SDI'
            data['hinge_type'] = 'ARGENTA_100_86A'

        # Migrering av gammel lowercase hinge_type
        if data.get('hinge_type') == 'roca_sf':
            data['hinge_type'] = 'ROCA_SF'

        # Filtrer ut ukjente nøkler for fremoverkompatibilitet
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
