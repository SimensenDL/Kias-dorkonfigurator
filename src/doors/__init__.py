"""
Dørtype-register for KIAS Dørkonfigurator.

Samler alle dørtype-definisjoner og bygger oppslags-tabeller.
Nye dørtyper registreres ved å legge dem til i _DOOR_TYPE_MODULES.
"""

from .innerdor import INNERDOR
from .kjoleromdor import KJOLEROMDOR
from .pdpc import PDPC_DOR
from .pdpo import PDPO_DOR
from .pdi import PDI_DOR
from .branndor import BRANNDOR

# Liste over alle registrerte dørtyper
_DOOR_TYPE_MODULES = [
    INNERDOR,
    KJOLEROMDOR,
    PDPC_DOR,
    PDPO_DOR,
    PDI_DOR,
    BRANNDOR,
]

# Hovedregister: {key: door_def}
DOOR_REGISTRY = {}
for _door_def in _DOOR_TYPE_MODULES:
    DOOR_REGISTRY[_door_def['key']] = _door_def
