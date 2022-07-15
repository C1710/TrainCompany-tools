from __future__ import annotations

import logging
import os.path
import re
from functools import lru_cache
from typing import List, Optional

from geopy import GoogleV3
from geopy.exc import GeopyError

# https://adamj.eu/tech/2021/05/13/python-type-hints-how-to-fix-circular-imports/
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from structures import Station

from geo import Location


@lru_cache
def load_api_key() -> str:
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    script_dir = os.path.dirname(script_dir)
    with open(os.path.join(script_dir, 'google_api_key.secret'), encoding='utf-8') as api_key:
        return api_key.read()


def with_location_data(station: Station) -> Station:
    from structures import Station
    if not station.location:
        geolocator = GoogleV3(api_key=load_api_key())
        location = geolocator.geocode(create_search_query(station), region = country(station))
        logging.info("Loading station location from Google Maps")
        if location is None:
            logging.warning("Couldn't find station {}. Trying without \" Bahnhof\" suffix".format(station.name))
            location = geolocator.geocode(station.name)
            if location is None:
                logging.warning("Couldn't find station {}.".format(station.name))
        station = Station(
            name=station.name,
            codes=station.codes,
            locations_path=station.locations_path,
            station_category=station.station_category,
            platforms=station.platforms,
            number=station.number,
            kind=station.kind,
            location=Location(
                latitude=location.latitude,
                longitude=location.longitude
            ) if location else None
        )
        return station
    else:
        return station


def create_search_query(station: Station) -> str:
    if country(station) in ('de', 'at', 'ch', 'lu'):
        return station.name + " Bahnhof"
    elif country(station) in ('fr', ):
        return station.name + " gare"
    else:
        return station.name + " station"


ril100_country_codes = {
    'A': 'at',
    'B': 'be',
    'C': 'ru',
    'D': 'dk',
    'E': 'es',
    'F': 'fr',
    'G': 'gr',
    'H': 'fi',
    'I': 'it',
    'J': 'ba',
    'K': 'uk',
    'L': 'lu',
    'M': 'hu',
    'N': 'nl',
    'O': 'no',
    'P': 'pl',
    'Q': 'tr',
    'R': 'rs',
    'S': 'ch',
    'T': 'cz',
    'U': 'ro',
    'V': 'se',
    'W': 'bg',
    'X': 'pt',
    'Y': 'sk',
    'Z': 'si',
}


flag_re = re.compile(r'[🇦-🇿]{2}')


def country(station: Station) -> Optional[str]:
    for code in station.codes:
        if code.startswith('X') or code.startswith('Z'):
            country_code = code[1]
            return ril100_country_codes[country_code]
        elif flag_re.search(code):
            return chr(ord(code[0]) - 127365) + chr(ord(code[1]) - 127365)
    return 'de'


def add_location_data_to_list(stations: List[Station]):
    for index, station in enumerate(stations):
        try:
            stations[index] = with_location_data(station)
        except TimeoutError:
            logging.warning("Konnte Standortdaten für {} nicht abrufen.".format(station.name))
        except GeopyError:
            logging.warning("Konnte Standortdaten für {} nicht abrufen.".format(station.name))
        except FileNotFoundError:
            logging.warning("Couldn't find google_api_key.secret")
