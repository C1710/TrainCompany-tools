from __future__ import annotations

import logging
from typing import List, Optional

from importer import CsvImporter
from structures.station import Station, CodeTuple


class DbBetriebsstellenverzeichnisImporter (CsvImporter[Station]):
    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        assert entry[1]
        station = Station(
            name=correct_ch_name(entry[2]),
            number=None,
            codes=CodeTuple(entry[1]),
            location=None,
            kind=entry[5],
            station_category=None
        )
        return station


def correct_ch_name(name: str) -> str:
    if name == "St Gallen":
        return "St. Gallen"
    return name
