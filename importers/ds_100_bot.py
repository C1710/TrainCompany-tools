from typing import Optional, List

from importer import CsvImporter
from structures import Station, CodeTuple
from structures.country import countries, Country


class Ds100Importer(CsvImporter[Station]):
    country: Country

    def __init__(self, country: Country):
        super().__init__(
            delimiter=';',
            encoding="utf-8",
            skip_first_line=True
        )
        self.country = country

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        station = Station(
            name=entry[1].title(),
            number=hash(self.country.colon_prefix + entry[0]),
            codes=CodeTuple(self.country.flag + entry[0], self.country.colon_prefix + entry[0])
        )

        return station
