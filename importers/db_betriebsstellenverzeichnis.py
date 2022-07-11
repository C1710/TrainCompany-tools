from __future__ import annotations

import logging
import re
from typing import List, Optional

from importer import CsvImporter
from structures.station import Station, CodeTuple


class DbBetriebsstellenverzeichnisImporter (CsvImporter[Station]):
    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        assert entry[1]
        station = Station(
            name=correct_name(entry[2], entry[1]),
            number=None,
            codes=CodeTuple(entry[1]),
            location=None,
            kind=entry[5],
            station_category=None
        )
        return station


ch_re = re.compile(r' +\(CH\)')


def correct_name(name: str, ril100: str) -> str:
    if ril100.startswith('XF'):
        return correct_fr_name(name)
    elif ril100.startswith('XS'):
        return correct_ch_name(name)
    else:
        return name


def correct_ch_name(name: str) -> str:
    if name == "St Gallen":
        return "St. Gallen"
    name = ch_re.sub(' (CH)', name)
    name = name.replace('Geneve', 'Genève')
    name = name.replace(" / ", "/")
    name = name.replace("Neuchatel", "Neuchâtel")
    name = name.replace("Yverdon", "Yverdon-les-Bains")
    name = name.replace("Delemont", "Delémont")
    return name


def correct_fr_name(name: str) -> str:
    name = name.replace('Lorraine-Louvigny', 'Lorraine-TGV')
    name = name.replace('Champagne-Ardennes', 'Champagne-Ardenne-TGV')
    name = name.replace("Bening", 'Béning')
    return name
