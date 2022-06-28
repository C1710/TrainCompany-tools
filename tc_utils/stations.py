from typing import List

from structures import Station
from structures.station import TcStation
from tc_utils import TcFile


def add_stations_to_file(stations: List[Station],
                         file: TcFile,
                         override_stations: bool = False,
                         update_stations: bool = False):
    existing_station_codes = frozenset([station['ril100'] for station in file.data])
    code_to_existing_station = {station['ril100']: station for station in file.data}
    # We only want to add new stations
    if not override_stations and not update_stations:
        for station in stations.copy():
            for code in station.codes:
                if code in existing_station_codes:
                    stations.remove(station)
    # We only want to update existing stations
    if update_stations:
        for station in stations.copy():
            is_existing: bool = False
            for code in station.codes:
                if code in existing_station_codes:
                    is_existing = True
            if not is_existing:
                stations.remove(station)
    # Update or append the data
    for station in stations:
        # Convert to dict for insertion
        tc_station = TcStation.from_station(station)
        tc_station_dict = {key: value for key, value in tc_station.__dict__.items() if value is not None}

        updated: bool = False
        for code in station.codes:
            if code in existing_station_codes:
                # Update data
                code_to_existing_station[code].update(tc_station_dict)
                updated = True
                break
        # There is no station with that code there, so we need to append it
        if not updated:
            file.data.append(tc_station_dict)
