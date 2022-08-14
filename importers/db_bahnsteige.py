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
    station_to_plattforms: Dict[Station, List[Platform]] = {}
    for platform in platforms:
        if isinstance(platform.station, int):
            try:
                station = number_to_station[platform.station]
                if station not in station_to_plattforms:
                    station_to_plattforms[station] = []
                station_to_plattforms[station].append(platform)
            except KeyError:
                if platform.station >= 0:
                    logging.debug("Couldn't find station for platform: {}".format(platform.station))
        # TODO: Fail here
    for index, station in enumerate(stations):
        if station in station_to_plattforms:
            stations[index] = Station(
                name=station.name,
                number=station.number,
                codes=station.codes,
                location=station.location,
                locations_path=station.locations_path,
                station_category=station.station_category,
                _group=station._group,
                kind=station.kind,
                platforms=tuple(station_to_plattforms[station])
            )
