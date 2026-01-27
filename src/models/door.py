"""
Datamodell for dørkonfigurasjon.
Alle dimensjoner i millimeter (mm).
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from ..utils.constants import (
    DEFAULT_DIMENSIONS, DEFAULT_COLOR_OUTSIDE, DEFAULT_COLOR_INSIDE
)


@dataclass
class DoorParams:
    """
    Representerer en komplett dørkonfigurasjon.

    Attributter:
        project_id: Prosjekt-ID / ordrenummer
        customer: Kundenavn / tiltakshaver
        door_type: Dørtype (nøkkel fra DOOR_TYPES)
        width: Dørbredde i mm
        height: Dørhøyde i mm
        thickness: Dørtykkelse i mm
        color_outside: RAL-farge utside
        color_inside: RAL-farge innside
        surface_type: Overflatetype
        glass: Om døren har glass
        glass_type: Type glass (hvis aktuelt)
        threshold_type: Terskeltype
        lock_type: Låstype
        hinge_side: Hengsle-side ('left' eller 'right')
        fire_rating: Brannklasse (EI30, EI60 etc.)
        sound_rating: Lydklasse i dB
        insulation_value: U-verdi (W/m²K)
        notes: Fritekst merknader
        created_date: Opprettelsesdato (ISO-format)
        modified_date: Sist endret (ISO-format)
    """
    # Prosjektinfo
    project_id: str = ""
    customer: str = ""

    # Dørtype og grunnmål
    door_type: str = "innerdor"
    width: int = 900
    height: int = 2100
    thickness: int = 40

    # Overflate/utseende
    color_outside: str = DEFAULT_COLOR_OUTSIDE
    color_inside: str = DEFAULT_COLOR_INSIDE
    surface_type: str = "glatt"

    # Tilleggsutstyr
    glass: bool = False
    glass_type: str = ""
    threshold_type: str = ""
    lock_type: str = ""
    hinge_side: str = "left"

    # Spesielle egenskaper (avhenger av dørtype)
    fire_rating: str = ""
    sound_rating: int = 0
    insulation_value: float = 0.0

    # Merknader
    notes: str = ""

    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = ""

    def apply_defaults_for_type(self) -> None:
        """Setter standardmål basert på valgt dørtype."""
        defaults = DEFAULT_DIMENSIONS.get(self.door_type)
        if defaults:
            self.width = defaults['width']
            self.height = defaults['height']
            self.thickness = defaults['thickness']

    def area_m2(self) -> float:
        """Returnerer dørareal i kvadratmeter."""
        return (self.width * self.height) / 1_000_000

    def to_dict(self) -> dict:
        """Konverterer til dictionary for JSON-serialisering."""
        return {
            'project_id': self.project_id,
            'customer': self.customer,
            'door_type': self.door_type,
            'width': self.width,
            'height': self.height,
            'thickness': self.thickness,
            'color_outside': self.color_outside,
            'color_inside': self.color_inside,
            'surface_type': self.surface_type,
            'glass': self.glass,
            'glass_type': self.glass_type,
            'threshold_type': self.threshold_type,
            'lock_type': self.lock_type,
            'hinge_side': self.hinge_side,
            'fire_rating': self.fire_rating,
            'sound_rating': self.sound_rating,
            'insulation_value': self.insulation_value,
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
