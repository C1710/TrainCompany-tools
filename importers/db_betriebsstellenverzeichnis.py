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


fr_names = {
    'Lorraine-Louvigny': 'Lorraine-TGV',
    'Champagne-Ardennes': 'Champagne-Ardenne-TGV',
    "Bening": 'Béning',
    "Amberieu": "Ambérieu",
    "Marne-la-Vallee-Chessy": "Marne-la-Vallée-Chessy",
    "Calais-Frethun": "Calais-Fréthun",
    "Selestat": "Sélestat",
    "Chalon-sur-Saone": "Chalon-sur-Saône",
    "Macon-Ville": "Mâcon-Ville",
    "Neufchateau": "Neufchâteau",
    "Varangeville-St-Nicolas": "Varangéville-St-Nicolas",
    "Blainville-Damelevie": "Blainville-Damelevières",
    "Luneville": "Lunéville",
    "Reding": "Réding",
    "Pont-a-Mousson": "Pont-à-Mousson",
    "Noveant": "Novéant",
    "Lerouville": "Lérouville",
    "Remilly": "Rémilly",
    "Nuits-sous-Ravieres": "Nuits-sous-Ravières",
    "Chasse-sur-Rhone": "Chasse-sur-Rhône",
    "Montelimar": "Montélimar",
    "St-Raphael-Valescure": "St-Raphaël-Valescure",
    "Besancon TGV": "Besançon-Franche-Comté-TGV",
    "Nancois-Tronville": "Nançois-Tronville",
    "Vitry-le-Francois": "Vitry-le-François",
    "Chalons-en-Champagne": "Châlons-en-Champagne",
    "Chateau-Thierry": "Château-Thierry",
    "La Ferte-sous-Jouarre": "La Ferté-sous-Jouarre",
    "Montauban-Ville-Bourbon": "Montauban Ville Bourbon",
    "Toulouse-Matabiau": "Toulouse Matabiau",
    "Aix-les-Bains-le-Revard": "Aix-les-Bains—Le Revard",
    "Chambery-Challes-les-Eaux": "Chambéry Challes-les-Eaux",
    "Montmelian": "Montmélian",
    "St-Pierre-d'Albigny": "St-Pierre-d’Albigny",
    "Epierre-St-Leger": "Épierre—St-Léger",
    "St-Avre-la-Chambre": "St-Avre—La Chambre",
    "St-Jean-de-Maurienne-Arvan": "St-Jean-de-Maurienne—Arvan",
    "Nogent-le-Retrou": "Nogent-le-Rotrou"
}


def correct_fr_name(name: str) -> str:
    if name in fr_names:
        return fr_names[name]
    else:
        return name
