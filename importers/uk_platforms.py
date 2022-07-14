from typing import List, Dict, Optional

from importer import CsvImporter
from structures.station import Platform, Station


class UkPlatformImporter(CsvImporter[Platform]):
    tiploc_to_station_number: Dict[str, int]

    def __init__(self, stations: List[Station]):
        super().__init__(
            delimiter='\t',
            encoding='cp1252',
            skip_first_line=False
        )
        self.tiploc_to_station_number = {station.codes[-1]: station.number for station in stations}

    def deserialize(self, entry: List[str]) -> Optional[Platform]:
        if entry[0] == "PLT" and entry[6] and int(entry[6]):
            tiploc = '🇬🇧' + entry[2]
            platform = Platform(
                length=float(entry[6]),
                station=self.tiploc_to_station_number[tiploc]
            )
            return platform
        else:
            return None
