from typing import List

from importer import CsvImporter
from structures.station import Station, Location, PathLocation


class DbBetriebsstellenImporter (CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=',',
            encoding='cp852',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Station:
        station = Station(
            name=entry[4],
            number=None,
            location=Location(
                latitude=float(entry[9]),
                longitude=float(entry[10])
            ) if entry[9] and entry[10] else None,
            location_path=PathLocation(
                route_number=int(entry[0]),
                lfd_km=int(entry[2])
            ),
            kind=entry[5],
            platforms=[],
            station_category=None
        )
        station.codes.append(entry[6])

        return station