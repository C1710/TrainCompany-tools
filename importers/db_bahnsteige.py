import logging
from typing import List, Dict

from importer import CsvImporter
from structures.station import Station, Platform


class DbBahnsteigeImporter(CsvImporter[Platform]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Platform:
        platform = Platform(
            length=float(entry[4].replace(',', '.')),
            station=int(entry[0])
        )
        return platform


def add_platforms_to_stations(stations: List[Station], platforms: List[Platform]):
    # First we make it easier to look up the stations
    number_to_station: Dict[int, Station] = {station.number: station for station in stations}
    for platform in platforms:
        if isinstance(platform.station, int):
            try:
                station = number_to_station[platform.station]
                station.platforms.append(platform)
            except KeyError:
                logging.debug("Couldn't find station for platform: {}".format(platform.station))
        # TODO: Fail here
