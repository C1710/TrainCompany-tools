import logging
from typing import List

from importer import CsvImporter
from structures.station import Station, CodeTuple


class DbBahnhoefeImporter(CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Station:
        station = Station(
            name=entry[4],
            codes=CodeTuple(entry[5]),
            number=int(entry[3]),
            station_category=int(entry[6]),
            location=None,
            kind=None
        )
        return station
