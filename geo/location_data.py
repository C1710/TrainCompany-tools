import logging
import os.path
from functools import lru_cache
from time import sleep
from typing import List, Union

from geopy import GoogleV3
from geopy.exc import GeopyError

from structures import Station
from structures.station import Location


@lru_cache
def load_api_key() -> str:
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    script_dir = os.path.dirname(script_dir)
    with open(os.path.join(script_dir, 'google_api_key.secret'), encoding='utf-8') as api_key:
        return api_key.read()


def with_location_data(station: Station) -> Station:
    geolocator = GoogleV3(api_key=load_api_key())
    location = geolocator.geocode(station.name + " Bahnhof")
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