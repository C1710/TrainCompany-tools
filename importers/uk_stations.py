from typing import Any, Optional, Dict

from importer import JsonImporter
from structures import Station, CodeTuple


class UkStationsImporter(JsonImporter):
    def __init__(self):
        super().__init__(encoding="cp1252",
                         top_level_entry=["TIPLOCDATA"])

    def deserialize(self, entry: Dict[str, Any]) -> Optional[Station]:
        assert isinstance(entry, dict)
        if entry['UIC'] and entry['TIPLOC']:
            station = Station(
                name=entry['NLCDESC'].title(),
                station_category=5,
                number=int(entry['UIC']),
                codes=CodeTuple('🇬🇧' + entry['3ALPHA'], '🇬🇧' + entry['TIPLOC']),
                location=None
            )
            return station
        else:
            return None
