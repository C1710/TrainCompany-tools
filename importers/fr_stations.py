from __future__ import annotations
from typing import List, Optional

from importer import CsvImporter
from structures import Station
from structures.station import CodeTuple, Location


class FrStationsImporter (CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        station = Station(
            name=normalize_french_station_name(entry[1]),
            number=int(entry[0]),
            codes=CodeTuple(entry[0]),
            location=Location(
                latitude=float(entry[14]),
                longitude=float(entry[13])
            ) if entry[13] and entry[14] else None,
            kind=None,
            station_category=5 if entry[3] == 'O' else -1
        )

        return station


def normalize_french_station_name(name: str) -> str:
    name = name.replace('-Souterraine', '')
    name = name.replace('-Surface', '')
    name = name.replace('Lille-Europe', 'Lille Europe')
    return name
