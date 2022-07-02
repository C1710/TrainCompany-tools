import logging
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
    name_to_index = {station.name: index for index, station in enumerate(stations)}
    for station in new_data:
        try:
            index = name_to_index[station.name]
            existing_data = stations[index].__dict__
            existing_data.pop('station_category')
            stations[index] = Station(
                **existing_data,
                station_category=station.station_category
            )
        except KeyError:
            logging.error("Couldn't find station {}".format(station.name))


def passengers_to_station_category(passengers: int) -> int:
    if passengers > 60000:
        return 1
    if 40000 < passengers < 60000:
        return 2
    if 10000 < passengers < 40000:
        return 3
    else:
        return 4
