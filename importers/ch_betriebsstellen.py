from typing import List

from importer import CsvImporter
from structures import Station
from structures.station import Location, CodeTuple


class ChBetriebsstellenImporter (CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Station:
        station = Station(
            # This is unique
            name=normalize_name(entry[2]),
            # We want to use international identifieres here to prevent conflicts with German stations
            number=int(entry[1]),
            # Subsitute the code with BPUIC if not available
            codes=CodeTuple('CH:' + entry[3], entry[1]) if entry[3] else CodeTuple(entry[1]),
            location=Location(
                latitude=float(entry[25]),
                longitude=float(entry[24])
            ) if entry[25] and entry[24] else None,
            kind=None,
            # We use a default here, because Switzerland does not have station categories
            station_category=5
        )

        return station


def normalize_name(name: str) -> str:
    name = name.replace("St. Margrethen SG", "St. Margrethen")
    return name
