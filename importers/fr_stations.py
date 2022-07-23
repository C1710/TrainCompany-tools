from __future__ import annotations

import logging
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
        uic = entry[0]
        if len(uic) == 8:
            uic = uic[:7]
        elif len(uic) != 7:
            logging.warning("UIC-Code hat falsche Länge: {}".format(uic))
        station = Station(
            name=normalize_french_station_name(entry[1]),
            number=int(uic),
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
    "Anse": "ANS",
    "Ruffey": "RFY",
    "Gemeaux": "GMX",
    "Vaux-sous-Aubigny": "VXY",
    "Andilly": "ADY",
    "Bourmont": "BMT",
    "Bariey-la-Côte": "BLC",
    "Liverdun": "LDN",
    "Igney-Avricourt": "IA",
    "Héming": "HMG",
    "Pompey": "PPE",
    "Ars-sur-Moselle": "ASM",
    "Champigny-sur-Yonne": "CSY",
    "Sens": "SES",
    "St-Julien-du-Sault": "SJX",
    "St-Florentin-Vergigny": "SIF",
    "Tonnerre": "TNN",
    "St-Clair-les-Roches": "SKR",
    "Le Péage-de-Roussillon": "PGR",
    "Tain-l'Hermitage-Tournon": "TAI",
    "Livron": "LIV",
    "Pierrelatte": "PRL",
    "Bollène-la-Croisière": "BLN",
    "Bédarrides": "BDR",
    "St-Martin-de-Crau": "SMD",
    "La Penne-sur-Huveaune": "PHE",
    "Aubagne": "AUB",
    "Cassis": "CSI",
    "Bandol": "BND",
    "St-Cyr-les-Lècques-La Cadière": "SAQ",
    "La Seyne-Six-Fours": "LSM",
    "Solliès-Pont": "SIP",
    "Vidauban": "VUB",
    "Théoule-sur-Mer": "THM",
    "Biot": "BJO",
    "St-Laurent-du-Var": "SNV",
    "Commercy": "CCY",
    "Oiry": "OIR",
    "Nogent-l'Artaud-Charly": "NAA",
    "St-Médard-d'Eyrans": "SYS"
}


def generate_code_tuple(entry: List[str]) -> CodeTuple:
    uic_number = entry[0]
    if len(uic_number) == 8:
        uic_number = uic_number[:7]
    name = entry[1]
    codes = []
    for stations_name, code in special_codes.items():
        if name == stations_name:
            codes.append(code)
            break

    for index, code in enumerate(codes):
        codes[index] = '🇫🇷' + code
    codes.append(uic_number)

    return CodeTuple(*codes)


def normalize_french_station_name(name: str) -> str:
    name = name.replace('-Souterraine', '')
    name = name.replace('-Surface', '')
    name = name.replace('Lille-Europe', 'Lille Europe')
    name = name.replace('Dole', 'Dole-Ville')
    name = name.replace('Bellegarde', 'Bellegarde (Ain)')
    name = name.replace('Fréjus', "Fréjus-St-Raphaël")
    name = name.replace("Brest", "Brest (FR)")
    return name
