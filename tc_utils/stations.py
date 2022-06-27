from typing import List

from tools.structures import Station
from tools.structures.station import TcStation
from tools.tc_utils import TcFile


def add_stations_to_file(stations: List[Station], file: TcFile):
    existing_station_codes = frozenset([station['ril100'] for station in file.data])
    for station in stations.copy():
        for code in station.codes:
            if code in existing_station_codes:
                stations.remove(station)
    tc_stations = (TcStation.from_station(station) for station in stations)
    # https://stackoverflow.com/a/33797147
    # We remove all entries that are None here
    tc_stations_dicts = [{key: value for key, value in station.__dict__.items() if value is not None}
                         for station in tc_stations]
    file.data.extend(tc_stations_dicts)
