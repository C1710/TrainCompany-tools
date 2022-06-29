from typing import List

from importer import CsvImporter
from structures import Station


class ChBahnhofsbenutzerImporter (CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Station:
        station = Station(
            name=entry[0],
            # It should be included, but it isn'T
            number=None,
            station_category=passengers_to_station_category(int(float(entry[10]))),
            location=None,
            kind=None
        )

        return station


def add_passengers_to_stations_ch(stations: List[Station], new_data: List[Station]):
    name_to_stations = {station.name: station for station in stations}
    for station in new_data:
        name_to_stations[station.name].station_category = station.station_category


def passengers_to_station_category(passengers: int) -> int:
    if passengers > 60000:
        return 1
    if 40000 < passengers < 60000:
        return 2
    if 10000 < passengers < 40000:
        return 3
    else:
        return 4
