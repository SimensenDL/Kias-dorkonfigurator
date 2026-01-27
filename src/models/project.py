"""
Prosjektfil lagring og lasting.
Filformat: JSON med .kdf utvidelse (KIAS Door File)
"""
import json
from pathlib import Path
from datetime import datetime

from .door import DoorParams

PROJECT_FILE_VERSION = "1.0"
PROJECT_EXTENSION = ".kdf"


def save_project(door: DoorParams, filepath: Path | str) -> None:
    """
    Lagrer dørkonfigurasjon til en .kdf fil.

    Args:
        door: DoorParams instans
        filepath: Sti til fil (legger til .kdf hvis mangler)
    """
    filepath = Path(filepath)
    if not str(filepath).endswith(PROJECT_EXTENSION):
        filepath = Path(str(filepath) + PROJECT_EXTENSION)

    # Oppdater modifisert dato
    door.modified_date = datetime.now().isoformat()

    data = {
        "version": PROJECT_FILE_VERSION,
        "door": door.to_dict()
    }

    # Opprett mappe hvis den ikke finnes
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_project(filepath: Path | str) -> DoorParams:
    """
    Laster dørkonfigurasjon fra en .kdf fil.

    Args:
        filepath: Sti til .kdf fil

    Returns:
        DoorParams instans

    Raises:
        FileNotFoundError: Hvis filen ikke finnes
        ValueError: Hvis filformatet er ugyldig
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Filen finnes ikke: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    door_data = data.get("door")

    if door_data is None:
        raise ValueError("Ugyldig prosjektfil: mangler 'door' data")

    return DoorParams.from_dict(door_data)


def new_project() -> DoorParams:
    """Oppretter et nytt prosjekt med standardverdier."""
    return DoorParams()
