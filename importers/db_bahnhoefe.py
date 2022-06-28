import logging
from typing import List

from importer import CsvImporter
from structures.station import Station


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
            number=int(entry[3]),
            station_category=int(entry[6]),
            location=None,
            location_path=None,
            platforms=[],
            kind=None
        )
        station.codes.append(entry[5])
        return station


def add_hp_information_to_stations(stations: List[Station], new_data: List[Station]):
    ril100_to_stations = {ril100: index for (index, station) in enumerate(stations) for ril100 in station.codes}

    for station in new_data:
        # We want to add station number and station category if not present
        for code in station.codes:
            try:
                index = ril100_to_stations[code]
                if stations[index].number is None:
                    stations[index].number = station.number
                if stations[index].station_category is None:
                    stations[index].station_category = station.station_category
                if stations[index].name is None:
                    stations[index].name = station.name
            except KeyError:
                logging.debug("Couldn't find station {}".format(code))
                pass
