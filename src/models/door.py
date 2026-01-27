"""
Datamodell for dørkonfigurasjon.
Alle dimensjoner i millimeter (mm).
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from ..utils.constants import (
    DEFAULT_DIMENSIONS, DEFAULT_COLOR, THRESHOLD_LUFTSPALTE
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
        color: RAL-farge
        surface_type: Overflatetype
        glass: Om døren har glass
        glass_type: Type glass (hvis aktuelt)
        threshold_type: Terskeltype
        lock_type: Låstype
        swing_direction: Slagretning ('left' eller 'right')
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
    door_type: str = "SDI"
    karm_type: str = "SD1"
    floyer: int = 1  # Antall fløyer (1 eller 2)
    width: int = 900
    height: int = 2100
    thickness: int = 40

    # Overflate/utseende
    color: str = DEFAULT_COLOR
    surface_type: str = "glatt"

    # Tilleggsutstyr
    glass: bool = False
    glass_type: str = ""
    threshold_type: str = "standard"
    luftspalte: int = 22  # Luftspalte i mm, kun redigerbar for terskeltype 'luftspalte'
    lock_type: str = ""
    swing_direction: str = "left"

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

    def effective_luftspalte(self) -> int:
        """Returnerer effektiv luftspalte basert på terskeltype.
        For 'luftspalte'-typen brukes den lagrede verdien,
        for alle andre typer brukes den faste verdien fra oppslagstabellen.
        """
        if self.threshold_type == 'luftspalte':
            return self.luftspalte
        return THRESHOLD_LUFTSPALTE.get(self.threshold_type, 22)

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
            'color': self.color,
            'surface_type': self.surface_type,
            'glass': self.glass,
            'glass_type': self.glass_type,
            'threshold_type': self.threshold_type,
            'luftspalte': self.luftspalte,
            'lock_type': self.lock_type,
            'swing_direction': self.swing_direction,
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
