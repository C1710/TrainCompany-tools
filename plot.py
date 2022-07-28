#!/usr/bin/env python

from __future__ import annotations

import argparse
from typing import List, Tuple, Dict, Any

import matplotlib.pyplot as plt
import json
import os

from cli_utils import add_default_cli_args
from geo import Location
from project_coordinates import project_coordinate_for_station
from structures.country import split_country, CountryRepresentation
from tc_utils import TcFile


def get_routes_points(station_data: List[dict], route_data: List[dict]) -> Tuple[
    List[Tuple[str, Tuple[int, int]]],
    List[Tuple[Tuple[int, int], Tuple[int, int]]]
]:
    for station in station_data:
        project_coordinate_for_station(station)
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
    plt.scatter(x, y, s=0.7)
    for x, y, text in zip(x, y, ril100s):
        plt.text(x + 1, y + 4, text, fontsize=1.1)
    plt.gca().invert_yaxis()
    plt.gca().set_aspect('equal', adjustable='box')
    if not save:
        plt.show()
    else:
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = ['Arial']
        plt.rcParams['text.usetex'] = False
        plt.savefig("map_plot.svg")


def plot_map_old(save: bool = False):
    with open("Station.json", encoding="utf-8") as path_f:
        data = json.load(path_f)
        station_data: List[dict] = data["data"]
    with open("Path.json", encoding="utf-8") as path_f:
        data = json.load(path_f)
        route_data: List[dict] = data["data"]
    station_points, route_points = get_routes_points(station_data, route_data)
    plot_points(station_points, route_points, save)


def flag_to_colon(code: str) -> str:
    country, code, representation = split_country(code, strip_ril100=False)
    if country is not None and representation in (CountryRepresentation.FLAG,):
        return country.colon_prefix + code
    else:
        return code


def plot_map(tc_directory: os.PathLike | str = '..',
             projection_version: int = 1,
             station_sizes = (2.8, 1.6, 1.2, 1.2, 1.2, 0.4, 0.4),
             out_file: str = "map_plot.svg"):
    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)
    for station in station_json.data:
        project_coordinate_for_station(station, new_projection=projection_version)
    point_data = [(station['x'], station['y'],
                   station_sizes[station['group']],
                   flag_to_colon(station['ril100'])) for station in station_json.data]
    _, path_data = get_routes_points(station_json.data, path_json.data)
    route_xy = [tuple(zip(*waypoints)) for waypoints in path_data]

    x, y, s, codes = zip(*point_data)
    plt.scatter(x=x, y=y, s=s, marker=".", linewidths=0)
    for (route_x, route_y) in route_xy:
        plt.plot(route_x, route_y, color='teal', linewidth=0.1)
    for x, y, s, text in zip(x, y, s, codes):
        plt.text(x + 1, y + 4, text, fontsize=s * 1.1 / max(station_sizes))
    plt.gca().invert_yaxis()
    plt.gca().set_aspect('equal', adjustable='box')
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.rcParams['text.usetex'] = False
    plt.savefig(out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Aktuelle Karte rendern")
    add_default_cli_args(parser, data_directory=False)
    parser.add_argument('--out_file', metavar="DATEI", type=str,
                        help="Die Datei, in die gespeichert werden soll. Standard: map_plot.svg")
    parser.add_argument('--projection_version', metavar="VERSION", type=int, choices=(-1, 0, 1, 2),
                        default=1,
                        help="Die Version der Projektion, die verwendet werden soll:\n"
                             "-1 - WGS84\n"
                             " 0 - Linear von WGS84\n"
                             " 1 - Direkte Projektion auf EPSG:3035\n"
                             " 2 - Von WGS84 auf EPSG:3035\n")
    args = parser.parse_args()
    if args.out_file is None:
        args.out_file = os.path.join(args.tc_directory, "map_plot.svg")
    plot_map(tc_directory=args.tc_directory, out_file=args.out_file)

