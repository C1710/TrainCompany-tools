from typing import List

from importer import CsvImporter
from structures.station import Station, Location, PathLocation, CodeTuple, StreckenKilometer


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
            codes=CodeTuple(entry[6]),
            location=Location(
                latitude=float(entry[9]),
                longitude=float(entry[10])
            ) if entry[9] and entry[10] else None,
            locations_path=frozenset({
                PathLocation(route_number=int(entry[0]), lfd_km=StreckenKilometer.from_str(entry[3]))
            }),
            kind=entry[5],
            station_category=None
        )

        return station
