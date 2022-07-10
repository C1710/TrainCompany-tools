from __future__ import annotations

import logging
from typing import Optional, List, Dict

from importer import CsvImporter
from importers.fr_stations import normalize_french_station_name
from structures.station import Platform, Station


class FrPlatformsImporter (CsvImporter[Platform]):
    names_to_station_number: Dict[str, int]

    def __init__(self, stations: List[Station]):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )
        self.names_to_station_number = {station.name: station.number for station in stations}

    def deserialize(self, entry: List[str]) -> Optional[Platform]:
        if entry[10]:
            platform = Platform(
                length=float(entry[7]),
                station=self.names_to_station_number[normalize_french_station_name(entry[10])]
                if normalize_french_station_name(entry[10]) in self.names_to_station_number
                else warn_missing_station(normalize_french_station_name(entry[10]))
            )
            return platform
        else:
            return None


def warn_missing_station(station_name: str) -> int:
    logging.debug("Unknown station name: {}".format(station_name))
    return -1
