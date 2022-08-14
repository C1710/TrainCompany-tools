import logging
from typing import List, Optional

from geo import Location
from importer import CsvImporter
from structures import Station, CodeTuple
from structures.country import country_for_uic


class TrainlineImporter (CsvImporter[Station]):
    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        name = entry[1]
        name = name.replace("’", "'")
        uic: Optional[int] = int(entry[3]) if entry[3] else None
        if uic is None:
            return None
        # We don't want stations in unknown countries (at least for now)
        if country_for_uic(uic):
            latitude = float(entry[5]) if entry[5] else None
            longitude = float(entry[6]) if entry[6] else None
            main_station: bool = entry[11] == 't'
            sncf_id = entry[16]
            french_code = entry[17]
            if french_code:
                codes = CodeTuple('🇫🇷' + french_code, str(uic))
            else:
                codes = CodeTuple(str(uic))

            return Station(
                name=name,
                codes=codes,
                number=uic,
                location=Location(
                    latitude=latitude,
                    longitude=longitude
                ) if longitude is not None and latitude is not None else None,
                _group=1 if main_station else 2
            )
        else:
            logging.debug("Station in unknown country: {}".format(uic))
            return None
