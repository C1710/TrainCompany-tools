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
    station_number_to_index: Dict[int, int] = {station.number: index for (index, station) in enumerate(stations)}
    for platform in platforms:
        if isinstance(platform.station, int):
            try:
                index: int = station_number_to_index[platform.station]
                stations[index].platforms.append(platform)
            except KeyError:
                logging.debug("Couldn't find station for platform: {}".format(platform.station))
        # TODO: Fail here
