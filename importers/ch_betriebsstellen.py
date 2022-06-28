from typing import List

from importer import CsvImporter
from structures import Station
from structures.station import Location


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
            name=entry[2],
            # We want to use international identifieres here to prevent conflicts with German stations
            number=int(entry[1]),
            location=Location(
                latitude=float(entry[25]),
                longitude=float(entry[24])
            ) if entry[25] and entry[24] else None,
            location_path=None,
            kind=None,
            platforms=[],
            # We use a default here, because Switzerland does not have station categories
            station_category=5
        )
        if entry[3]:
            station.codes.append('CH:' + entry[3])
        # Subsitute with BPUIC
        station.codes.append(str(entry[1]))

        return station
