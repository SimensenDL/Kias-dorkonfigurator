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
    DOOR_TYPE_BLADE_OVERRIDE, DOOR_U_VALUES, DOOR_HINGE_DEFAULTS,
    DOOR_LOCK_CASE_DEFAULTS, DOOR_HANDLE_DEFAULTS,
    DIMENSION_DIFFERENTIALS, DOOR_THRESHOLD_TYPES
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
    width: int = 1010    # Utsparingsbredde (BM) i mm
    height: int = 2110   # Utsparingshøyde (HM) i mm
    thickness: int = 100  # Veggtykkelse i mm
    blade_type: str = "SDI_ROCA"  # Dørbladtype (nøkkel fra DOOR_BLADE_TYPES)
    blade_thickness: int = 40  # Dørbladtykkelse i mm

    # Overflate/utseende
    color: str = DEFAULT_COLOR
    surface_type: str = "glatt"

    # Beslag og lås
    hinge_type: str = "roca_sf"     # Hengseltype (nøkkel fra HINGE_TYPES)
    hinge_count: int = 2            # Antall hengsler per fløy
    lock_case: str = "3065_316l"    # Låsekasse (nøkkel fra LOCK_CASES)
    handle_type: str = "vrider_sylinder_oval"  # Vrider/skilt (nøkkel fra HANDLE_TYPES)
    espagnolett: str = "ingen"      # Espagnolett for 2-fløya (nøkkel fra ESPAGNOLETT_TYPES)

    # Tilleggsutstyr
    glass: bool = False
    glass_type: str = ""
    threshold_type: str = "standard"
    luftspalte: int = 0   # Luftspalte i mm, kun redigerbar for terskeltype 'luftspalte'
    lock_type: str = ""    # Fritekst, bakoverkompatibilitet (erstattes av lock_case)
    swing_direction: str = "left"

    # Spesielle egenskaper (avhenger av dørtype)
    fire_rating: str = ""
    sound_rating: int = 0
    insulation_value: float = 0.0
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

        # Sett beslag-standardverdier
        hinge_defaults = DOOR_HINGE_DEFAULTS.get(self.door_type)
        if hinge_defaults:
            hinge_key, count_1, count_2 = hinge_defaults
            self.hinge_type = hinge_key or ""
            self.hinge_count = count_1 if self.floyer == 1 else count_2

        self.lock_case = DOOR_LOCK_CASE_DEFAULTS.get(self.door_type, "")
        self.handle_type = DOOR_HANDLE_DEFAULTS.get(self.door_type, "")

        # Sett espagnolett for 2-fløya
        self.espagnolett = "roca_sf" if self.floyer == 2 else "ingen"

        # Sett U-verdi automatisk
        self.insulation_value = DOOR_U_VALUES.get(self.door_type, 0.0)

        # Sett standard terskeltype
        allowed_thresholds = DOOR_THRESHOLD_TYPES.get(self.door_type, ['standard'])
        if allowed_thresholds:
            self.threshold_type = allowed_thresholds[0]
        self.luftspalte = THRESHOLD_LUFTSPALTE.get(self.threshold_type, 0)

    def effective_luftspalte(self) -> int:
        """Returnerer effektiv luftspalte basert på terskeltype.
        For 'luftspalte'-typen brukes den lagrede verdien,
        for alle andre typer brukes den faste verdien fra oppslagstabellen.
        """
        if self.threshold_type == 'luftspalte':
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

    def has_brutt_kuldebro(self) -> bool:
        """Sjekker om døren har brutt kuldebro (karm eller dørramme)."""
        from ..utils.constants import BRUTT_KULDEBRO_KARM, BRUTT_KULDEBRO_DORRAMME
        return (self.karm_type in BRUTT_KULDEBRO_KARM or
                self.door_type in BRUTT_KULDEBRO_DORRAMME)

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
            'width': self.width,
            'height': self.height,
            'thickness': self.thickness,
            'blade_type': self.blade_type,
            'blade_thickness': self.blade_thickness,
            'color': self.color,
            'surface_type': self.surface_type,
            'hinge_type': self.hinge_type,
            'hinge_count': self.hinge_count,
            'lock_case': self.lock_case,
            'handle_type': self.handle_type,
            'espagnolett': self.espagnolett,
            'glass': self.glass,
            'glass_type': self.glass_type,
            'threshold_type': self.threshold_type,
            'luftspalte': self.luftspalte,
            'lock_type': self.lock_type,
            'swing_direction': self.swing_direction,
            'fire_rating': self.fire_rating,
            'sound_rating': self.sound_rating,
            'insulation_value': self.insulation_value,
            'lead_thickness': self.lead_thickness,
            'notes': self.notes,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DoorParams':
        """Oppretter DoorParams fra dictionary."""
        # Filtrer ut ukjente nøkler for fremoverkompatibilitet
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
