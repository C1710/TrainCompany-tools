#!/usr/bin/env python

from __future__ import annotations

import argparse
import itertools
from typing import List, Tuple, Dict, Any, Optional

import matplotlib.pyplot as plt
import json
import os

from cli_utils import add_default_cli_args, process_station_input, add_station_cli_args, parse_station_args
from geo import Location
from project_coordinates import project_coordinate_for_station
from structures import DataSet
from structures.country import split_country, CountryRepresentation
from tc_utils import TcFile, expand_objects, flatten_objects
from validation import get_shortest_path
from validation.graph import graph_from_files
from validation.shortest_paths import get_shortest_path_distance


def get_routes_plot_data(station_data: List[dict], path_data: List[dict],
                         highlighted_path: Optional[List[str]] = None,
                         color_default: str = 'teal',
                         color_highlight: str = 'tomato',
                         line_width_default: float = 0.1,
                         line_width_highlight: float = 0.2) -> Tuple[
    List[Tuple[str, Tuple[int, int]]],
    List[Tuple[Tuple[int, int], Tuple[int, int]]],
    List[str] | str,
    List[float] | float
]:
    """
    :returns: The stations with their RIL100 and coordinates,
              A list of path segments/edges with start and end coordinates
              The color(s) that should be used
    """
    station_data = {station['ril100']: (station['x'], station['y']) for station in station_data}
    path_data = (extract_route_stations(route) for route in path_data)
    segments = [segment for route in path_data for segment in route]
    if highlighted_path:
        highlighted_segments = set()
        for start, end in zip(highlighted_path, highlighted_path[1:]):
            highlighted_segments.add((start, end))
            highlighted_segments.add((end, start))
        colors = [color_highlight if (start.upper(), end.upper()) in highlighted_segments else color_default for start, end in segments]
        line_widths = [line_width_highlight if (start.upper(), end.upper()) in highlighted_segments else line_width_default for start, end in segments]
    else:
        colors = color_default
        line_widths = line_width_default
    path_data = [(station_data[segment[0]], station_data[segment[1]]) for segment in segments]
    station_data = list(station_data.items())
    return station_data, path_data, colors, line_widths


def extract_route_stations(route_entry: dict) -> List[Tuple[str, str]]:
    waypoints = []
    if 'objects' in route_entry:
        segments: List[dict] = route_entry['objects']
        waypoints.extend(((segment['start'], segment['end']) for segment in segments))
    else:
        waypoints.append((route_entry['start'], route_entry['end']))
    return waypoints


def flag_to_colon(code: str) -> str:
    country, code, representation = split_country(code, strip_ril100=False)
    if country is not None and representation in (CountryRepresentation.FLAG,):
        return country.colon_prefix + code
    else:
        return code


def plot_map(tc_directory: os.PathLike | str = '..',
             projection_version: int = 1,
             station_sizes = (2.8, 1.6, 1.2, 1.2, 1.2, 0.4, 0.4),
             out_file: str = "map_plot.svg",
             highlight_path: Optional[List[str]] = None,
             data_directory: Optional[os.PathLike | str] = None,
             add_text: bool = True):
    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)
    for station in station_json.data:
        project_coordinate_for_station(station, new_projection=projection_version)

    if highlight_path is not None:
        assert data_directory is not None
        data_set = DataSet.load_data(data_directory)
        highlight_path = process_station_input(highlight_path, data_set)

    point_data = [(station['x'], station['y'],
                   station_sizes[station['group']],
                   flag_to_colon(station['ril100']),
                   'maroon' if highlight_path and station['ril100'] in highlight_path else '#1f77b4') for station in
                  station_json.data]

    if highlight_path is not None:
        graph = graph_from_files(station_json, path_json)
        highlight_path = get_shortest_path(graph, highlight_path)

    _, path_data, colors, line_widths = get_routes_plot_data(station_json.data, path_json.data,
                                                             highlighted_path=highlight_path)
    if not isinstance(colors, list):
        colors = itertools.repeat(colors)
    if not isinstance(line_widths, list):
        line_widths = itertools.repeat(line_widths)

    route_xy = [(*tuple(zip(*waypoints)), color, line_width) for waypoints, color, line_width in
                zip(path_data, colors, line_widths)]

    x, y, s, codes, colors = zip(*point_data)
    plt.scatter(x=x, y=y, s=s, marker=".", linewidths=0, c=colors)
    for route_x, route_y, color, linewidth in route_xy:
        plt.plot(route_x, route_y, color=color, linewidth=linewidth, solid_capstyle='round')
    if add_text:
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
    add_default_cli_args(parser)
    parser.add_argument('--out_file', metavar="DATEI", type=str,
                        help="Die Datei, in die gespeichert werden soll. Standard: map_plot.svg")
    parser.add_argument('--projection_version', metavar="VERSION", type=int, choices=(-1, 0, 1, 2),
                        default=1,
                        help="Die Version der Projektion, die verwendet werden soll:\n"
                             "-1 - WGS84\n"
                             " 0 - Linear von WGS84\n"
                             " 1 - Direkte Projektion auf EPSG:3035\n"
                             " 2 - Von WGS84 auf EPSG:3035\n")
    add_station_cli_args(parser,
                         allow_unordered=False,
                         help="Ein Pfad, der hervorgehoben werden soll",
                         allow_multiple_stations=False)
    # TODO: Allow to highlight multiple paths at once
    parser.add_argument('--hide-text', action='store_true',
                        help="Fügt keine Stationscodes hinzu")
    args = parser.parse_args()
    highlight_path = parse_station_args(args)
    if args.out_file is None:
        args.out_file = os.path.join(args.tc_directory, "map_plot.svg")
    plot_map(tc_directory=args.tc_directory,
             data_directory=args.data_directory,
             out_file=args.out_file,
             highlight_path=highlight_path,
             add_text=not args.hide_text)

