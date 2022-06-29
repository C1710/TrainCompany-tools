from __future__ import annotations

from typing import List, Optional

from importer import CsvImporter
from structures.station import Station


class DbBetriebsstellenverzeichnisImporter (CsvImporter[Station]):
    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        station = Station(
            name=entry[2],
            number=None,
            location=None,
            location_path=None,
            kind=entry[5],
            platforms=[],
            station_category=None
        )
        station.codes.append(entry[1])
        return station
