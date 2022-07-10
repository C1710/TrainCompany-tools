from typing import List, Optional

from importer import CsvImporter
from structures import Station
from structures.station import CodeTuple


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
            codes=CodeTuple()
        )


def normalize_french_station_name(name: str) -> str:
    name = name.replace('-Souterrain', '')
    name = name.replace('-Surface', '')
    name = name.replace('Lille-Europe', 'Lille Europe')
    return name
