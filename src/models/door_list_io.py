"""
Import/eksport av dørlister i .kdl-format (KIAS Door List).
"""
import json
from pathlib import Path

from .production_list import ProductionList


def save_door_list(prod_list: ProductionList, filepath: Path) -> None:
    """Eksporterer dørlisten til en .kdl-fil.

    Args:
        prod_list: ProductionList som skal eksporteres
        filepath: Målsti for .kdl-filen
    """
    data = prod_list.to_list_dict()
    filepath = Path(str(filepath))
    if not filepath.suffix:
        filepath = filepath.with_suffix('.kdl')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_door_list(filepath: Path, prod_list: ProductionList) -> int:
    """Importerer dører fra en .kdl-fil (adderer til eksisterende liste).

    Args:
        filepath: Sti til .kdl-filen
        prod_list: ProductionList å legge til i

    Returns:
        Antall importerte dører
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('type') != 'door_list':
        raise ValueError("Ugyldig filformat: forventet 'door_list'")

    return prod_list.from_list_dict(data)
