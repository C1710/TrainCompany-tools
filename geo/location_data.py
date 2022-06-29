import logging
from functools import lru_cache
from time import sleep
from typing import List, Union

import geopy
from geopy import Nominatim, GoogleV3
from geopy.exc import GeopyError

from structures import Station
from structures.station import Location


@lru_cache
def load_api_key() -> str:
    with open('google_api_key.secret') as api_key:
        return api_key.read()


def with_location_data(station: Station) -> Station:
    geolocator = GoogleV3(api_key=load_api_key())
    location = geolocator.geocode(station.name + " Bahnhof")
    if location is None:
        logging.warning("Konnte Bahnhof {} nicht finden. Versuche es ohne Bahnhof".format(station.name))
        location = geolocator.geocode(station.name)
    print(station.name)
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
        )
    )
    return station


def add_location_data_to_list(stations: List[Station]):
    for index, station in enumerate(stations):
        try:
            stations[index] = with_location_data(station)
        except Union[TimeoutError, GeopyError]:
            logging.warning("Konnte Standortdaten für {} nicht abrufen.".format(station.name))
