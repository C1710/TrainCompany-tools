from __future__ import annotations

from typing import Any, Optional, Dict

from importer import JsonImporter


class UkStationsImporter(JsonImporter):
    def __init__(self):
        super().__init__(encoding="cp1252",
                         top_level_entry=["TIPLOCDATA"])

    def deserialize(self, entry: Dict[str, Any]) -> Optional["Station"]:
        from structures import Station, CodeTuple
        assert isinstance(entry, dict)
        if entry['3ALPHA']:
            codes = CodeTuple('🇬🇧' + entry['3ALPHA'], '🇬🇧' + entry['TIPLOC'])
        else:
            codes = CodeTuple('🇬🇧' + entry['TIPLOC'])
        if entry['UIC'] and entry['TIPLOC']:
            station = Station(
                name=entry['NLCDESC'].title(),
                station_category=5,
                number=int(entry['UIC']),
                codes=codes,
                location=None
            )
            return station
        else:
            return None
