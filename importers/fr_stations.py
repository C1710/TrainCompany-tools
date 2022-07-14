from __future__ import annotations
from typing import List, Optional

from importer import CsvImporter
from structures import Station
from structures.station import CodeTuple
from geo import Location


class FrStationsImporter (CsvImporter[Station]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Station]:
        station = Station(
            name=normalize_french_station_name(entry[1]),
            number=int(entry[0]),
            codes=generate_code_tuple(entry),
            location=Location(
                latitude=float(entry[14]),
                longitude=float(entry[13])
            ) if entry[13] and entry[14] else None,
            kind=None,
            station_category=5 if entry[3] == 'O' else -1
        )

        return station


special_codes = {
    "Montbard": "MBA",
    "Mâlain": "MLI",
    "Blaisy-Bas": "BSB",
    "Villers-les-Pots": "VLP",
    "Genlis": "GLS",
    "Andelot": "AND",
    "Frasne": "FRA",
    "Labergement-Ste-Marie": "LGM",
    "Les Longevilles-Rochejean": "LLR",
    "Beynost": "BNO",
    "Meximieux-Pérouges": "MEX",
    "St-Rambert-d'Albon": "SRA",
    "Seyssel-Corbonod": "SSS",
    "Virieu-le-Grand-Belley": "VRU",
    "Aéroport-Charles-de-Gaulle 2-TGV": "CDG",
    "Lyon-St-Exupéry-TGV": "SXA",
    "Beaune": "BEA",
    "Nuits-St-Georges": "NUI",
    "Sennecey-le-Grand": "SRD",
    "Tournus": "TOS",
    "Fleurville-Pont-de-Vaux": "FLV",
    "Pontanevaux": "PNX",
    "Anse": "ANS"
}


def generate_code_tuple(entry: List[str]) -> CodeTuple:
    number = entry[0]
    name = entry[1]
    codes = []
    for stations_name, code in special_codes.items():
        if name == stations_name:
            codes.append(code)
            break

    for index, code in enumerate(codes):
        codes[index] = '🇫🇷' + code
    codes.append(number)

    return CodeTuple(*codes)


def normalize_french_station_name(name: str) -> str:
    name = name.replace('-Souterraine', '')
    name = name.replace('-Surface', '')
    name = name.replace('Lille-Europe', 'Lille Europe')
    name = name.replace('Dole', 'Dole-Ville')
    name = name.replace('Bellegarde', 'Bellegarde (Ain)')
    return name
