from typing import Optional, List

from importer import CsvImporter
from importers.fr_stations import normalize_french_station_name
from structures.station import Platform


class FrPlatformsImporter (CsvImporter[Platform]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Platform]:
        platform = Platform(
            length=float(entry[7]),
            station=hash(normalize_french_station_name(entry[10]))
        )
        return platform


