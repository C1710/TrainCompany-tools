from __future__ import annotations

import itertools
import logging
import time
from typing import Any, Dict, List, Iterator

# https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0
from urllib.parse import urlencode, quote

import geopy.distance
import numpy as np
import rdp
import requests
from gpxpy.gpx import GPXTrackPoint
from requests import Response


def request_overpass(query: str,
                     overpass_api: str = "https://overpass-api.de/api/interpreter",
                     sleep_time: float = 2.0,
                     max_num_retries: int = 4) -> List[Dict[str, Any]]:
    for i in range(max_num_retries):
        try:
            response = _request_overpass(query, overpass_api)
            time.sleep(sleep_time)
            return response
        except requests.exceptions.Timeout:
            # Exponential waiting time
            sleep_time *= 2 ** (i + 1)
            logging.info(f"Got too many requests. Waiting for {sleep_time} s.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 400:
                raise
            else:
                response: Response = e.response
                logging.error(response.text)
                raise
    else:
        raise TimeoutError("Too many requests")


def _request_overpass(query: str,
                      overpass_api: str = "https://overpass-api.de/api/interpreter") -> List[Dict[str, Any]]:
    response = requests.post(overpass_api,
                             data=query)
    if response.status_code != 429:
        response.raise_for_status()
        return response.json()['elements']
    else:
        # We use this as a dummy here. Actually it's too many requests
        raise requests.exceptions.Timeout


def query_multiple(queries: Iterator[str],
                   overpass_api: str = "https://overpass-api.de/api/interpreter",
                   sleep_time: float = 2.0,
                   max_num_retries: int = 2,
                   timeout: int | None = None,
                   maxsize: int | None = None,
                   out: str = "tags") -> List[List[Dict[str, Any]]]:
    assert out != "count"
    timeout = f"[timeout:{timeout}]" if timeout is not None else ""
    maxsize = f"[maxsize:{maxsize}]" if maxsize is not None else ""
    header = f"[out:json];{timeout}{maxsize}"
    sub_queries = []
    for i, query in enumerate(queries):
        sub_queries.append(f'{query}->.q{i};out count qt;.q{i} out {out} qt;')
    query = header + (''.join(sub_queries))

    logging.debug(query)

    assert len(query) < 100000

    response = request_overpass(query, overpass_api, sleep_time, max_num_retries)
    responses = []
    current_response = []
    for element in response:
        if element["type"] == "count":
            if current_response:
                responses.append(current_response)
            current_response = []
        else:
            current_response.append(element)
    responses.append(current_response)
    return responses


def create_query(query: str,
                 timeout: int | None = None,
                 maxsize: int | None = None,
                 out: str = "tags") -> str:
    timeout = f"[timeout:{timeout}]" if timeout is not None else ""
    maxsize = f"[maxsize:{maxsize}]" if maxsize is not None else ""
    return f"[out:json];{timeout}{maxsize}{query};out {out};"


def query_around_gpx(distance: float, path: List[GPXTrackPoint]) -> str:
    lat_lons = (f"{round(trackpoint.latitude, 4)},{round(trackpoint.longitude, 4)}" for trackpoint in path)
    lat_lons = ','.join(lat_lons)
    return f"(around:{int(distance * 10)},{lat_lons})"


def query_rail_around_gpx(distance: float,
                          segment: List[GPXTrackPoint],
                          only_maxspeed: bool = False) -> str:
    segment = list(douglas_peucker(segment, distance))
    only_maxspeed = '["maxspeed"]' if only_maxspeed else ""
    around = query_around_gpx(distance, segment)
    query = f'way["railway"="rail"]{only_maxspeed}{around}'
    return query


def query_stations_around_gpx(distance: float,
                              path: List[GPXTrackPoint]) -> str:
    path = list(douglas_peucker(path, distance))
    around = query_around_gpx(distance, path)
    query = f'node["railway"="station"]{around}'
    return query


# Based on https://towardsdatascience.com/simplify-polylines-with-the-douglas-peucker-algorithm-ac8ed487a4a1
def douglas_peucker(points: List[GPXTrackPoint], max_radius: float) -> Iterator[GPXTrackPoint]:
    points_array = np.ndarray((len(points), 2), dtype=float)
    for index, point in enumerate(points):
        # We use lat, lon here, because geopy.distance.geodesic uses this format.
        # For the geometric stuff it doesn't matter, as we only care about distances and not directions, etc.
        points_array[index] = (point.latitude, point.longitude)
    selected_points = rdp.rdp(points_array, dist=approximate_distance_to_line, epsilon=max_radius, return_mask=True)
    return itertools.compress(points, selected_points)


def approximate_distance_to_line(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> float:
    # NOTE: We assume here that distances are roughly linear to the longitude and latitude difference
    # Step 1: Get the "scale" - i.e., distance_km / distance_lon_lat.
    km_per_lon_lat = geopy.distance.geodesic(start, end).km / np.linalg.norm(start - end)
    distance_lon_lat = rdp.pldist(point, start, end)
    return distance_lon_lat * km_per_lon_lat
