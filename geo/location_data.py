from __future__ import annotations

import inspect
import logging
import os.path
from functools import lru_cache

import geopy
from geopy import GoogleV3, Photon
from geopy.exc import GeopyError

# https://adamj.eu/tech/2021/05/13/python-type-hints-how-to-fix-circular-imports/
from typing import TYPE_CHECKING, Any

from structures.country import *

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


def with_location_data(station: Station, use_google: bool = False) -> Station:
    from structures import Station
    if not station.location:
        kwargs = {
            "language": query_language(station)
        }
        if use_google:
            geolocator = GoogleV3(api_key=load_api_key())
            logging.debug("Using location data from Google")

            location = geolocator.geocode(create_search_query(station),
                                          region=country_for_station(station).tld)
            if location is None:
                # This is only an issue if we use Google Maps
                logging.warning("Couldn't find station {}. Trying without \" Bahnhof\" suffix".format(station.name))
                location = geolocator.geocode(station.name, region=country_for_station(station).tld)
        else:
            geolocator = Photon()
            logging.debug("Using location data from Photon")

            country_location: geopy.Location = geolocator.geocode(
                country_for_station(station).name,
                osm_tag="place:country"
            )

            location: geopy.Location = geolocator.geocode(station.name,
                                                          osm_tag=['railway:station', 'railway:halt',
                                                                   'railway:junction'],
                                                          location_bias=country_location.point)

            if location is None:
                logging.warning("Couldn't find station {}. Looking for town/village/...".format(station.name))
                location = geolocator.geocode(station.name,
                                              osm_tag=['place:city', 'place:town', 'place:borough', 'place:hamlet',
                                                       'place:village', 'place:municipality'],
                                              location_bias=country_location.point)

            # Extract metadata
            metadata: Dict[str, Any] = location.raw['properties']
            osm_id = metadata['osm_id']
            city = metadata['city']
            value = metadata['osm_value']
            if value == 'station':
                group = 2
            elif value == 'halt':
                group = 5
            elif value == 'junction':
                group = 4
            else:
                group = -1

        if location is None:
            logging.warning("Couldn't find station {}.".format(station.name))

        station = Station(
            name=station.name,
            codes=station.codes,
            locations_path=station.locations_path,
            station_category=station.station_category,
            _group=station._group,
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
    if station.country in (countries['DE'], countries['AT'], countries['CH'], countries['LU']):
        return station.name + " Bahnhof"
    elif station.country in (countries['FR'], ):
        return station.name + " gare"
    else:
        return station.name + " station"


def query_language(station: Station) -> str:
    if station.country in (countries['DE'], countries['AT'], countries['CH'], countries['LU']):
        return "DE"
    elif station.country in (countries['FR'],):
        return "FR"
    else:
        return "EN"


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
