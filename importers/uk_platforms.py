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
        if entry[0] == "PLT":
            tiploc = '🇬🇧' + entry[2]
            if tiploc in self.tiploc_to_station_number:
                platform = Platform(
                    length=float(entry[6]) if entry[6] else 0.0,
                    station=self.tiploc_to_station_number[tiploc]
                )
                return platform
            else:
                return None
        else:
            return None
