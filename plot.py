from __future__ import annotations

from typing import List, Tuple

import matplotlib.pyplot as plt
import json
import os

from transform_to_laea import transform_coordinate_for_station


def get_routes_points(station_data: List[dict], route_data: List[dict]) -> Tuple[
    List[Tuple[str, Tuple[int, int]]],
    List[Tuple[Tuple[int, int], Tuple[int, int]]]
]:
    for station in station_data:
        transform_coordinate_for_station(station)
    station_data = dict(((station['ril100'], (station['x'], station['y'])) for station in station_data))
    route_data = (extract_route_stations(route) for route in route_data)
    route_data = [segment for route in route_data for segment in route]
    route_data = [(station_data[segment[0]], station_data[segment[1]]) for segment in route_data]
    station_data = list(station_data.items())
    return station_data, route_data


def extract_route_stations(route_entry: dict) -> List[Tuple[str, str]]:
    waypoints = []
    if 'objects' in route_entry:
        segments: List[dict] = route_entry['objects']
        waypoints.extend(((segment['start'], segment['end']) for segment in segments))
    else:
        waypoints.append((route_entry['start'], route_entry['end']))
    return waypoints


def plot_points(points: List[Tuple[str, Tuple[int, int]]],
                routes: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                save: bool = False):
    ril100s, points = zip(*points)
    x, y = zip(*points)
    route_xy = [tuple(zip(*waypoints)) for waypoints in routes]
    for (route_x, route_y) in route_xy:
        plt.plot(route_x, route_y, color='teal', linewidth=0.1)
    plt.scatter(x, y, s=1.3)
    for x, y, text in zip(x, y, ril100s):
        plt.text(x * 1.01, y * 1.01, text, fontsize=2)
    plt.gca().invert_yaxis()
    plt.gca().set_aspect('equal', adjustable='box')
    if not save:
        plt.show()
    else:
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = ['Arial']
        plt.rcParams['text.usetex'] = False
        plt.savefig("map_plot.svg")


def plot_map(save: bool = False):
    with open("Station.json", encoding="utf-8") as path_f:
        data = json.load(path_f)
        station_data: List[dict] = data["data"]
    with open("Path.json", encoding="utf-8") as path_f:
        data = json.load(path_f)
        route_data: List[dict] = data["data"]
    station_points, route_points = get_routes_points(station_data, route_data)
    plot_points(station_points, route_points, save)


if __name__ == '__main__':
    if not os.path.exists("Station.json") and os.path.exists("../Station.json"):
        os.chdir('..')
    plot_map(save=True)
