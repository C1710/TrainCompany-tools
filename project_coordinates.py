#!/usr/bin/env python

from __future__ import annotations

import argparse
from os import PathLike
from typing import Dict, Any

from cli_utils import add_default_cli_args, use_default_cli_args
from geo import Location, default_projection_version
from tc_utils import TcFile


def project_coordinates(tc_directory: PathLike | str = '..', projection_version: int = 1) -> TcFile:
    station_json = TcFile('Station', tc_directory)
    for station in station_json.data:
        project_coordinate_for_station(station, new_projection=projection_version)
    return station_json


def project_coordinate_for_station(station: Dict[str, Any], new_projection: int = default_projection_version):
    if 'laea' not in station and 'proj' not in station:
        current_projection = 0
    else:
        if 'proj' in station:
            current_projection = station['proj']
        else:
            current_projection = station.pop('laea')
    if current_projection != new_projection:
        location = Location.from_projection(station['x'], station['y'], version=current_projection)
        station['x'], station['y'] = location.to_projection(new_projection)
    if new_projection != 0:
        station['proj'] = new_projection
    else:
        station.pop('proj', 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rechne die Koordinaten auf eine andere Projektion um')
    add_default_cli_args(parser, data_directory=False)
    parser.add_argument('--version', '--projection-version', metavar="VERSION", type=int, choices=(-1, 0, 1, 2, 3),
                        default=1,
                        help="Die Version der Projektion, die verwendet werden soll:\n"
                             "-1 - WGS84\n"
                             " 0 - Linear von WGS84\n"
                             " 1 - Direkte Projektion auf EPSG:3035\n"
                             " 2 - Von WGS84 auf EPSG:3035\n")
    args = parser.parse_args()
    use_default_cli_args(args)

    station_json = project_coordinates(tc_directory=args.tc_directory, projection_version=args.version)
    station_json.save()
