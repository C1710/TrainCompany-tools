from __future__ import annotations

import argparse
import os
from os import PathLike
from typing import Dict, Any

from geo import Location
from tc_utils import TcFile


def project_coordinates(tc_directory: PathLike | str = '..', projection_version: int = 1) -> TcFile:
    station_json = TcFile('Station', tc_directory)
    for station in station_json.data:
        project_coordinate_for_station(station, new_projection=projection_version)
    return station_json


def project_coordinate_for_station(station: Dict[str, Any], new_projection: int = 1):
    if 'laea' not in station and 'proj' not in station:
        current_projection = 0
    else:
        if 'proj' in station:
            current_projection = station['proj']
        else:
            current_projection = station.pop('laea')
    location = Location.from_projection(station['x'], station['y'], version=current_projection)
    station['x'], station['y'] = location.to_projection(new_projection)
    if new_projection != 0:
        station['proj'] = new_projection
    else:
        station.pop('proj', 0)


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Importiere neue Betriebsstellen in TrainCompany')
    parser.add_argument('--tc-dir', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--version', metavar="VERSION", type=int, choices=(-1, 0, 1, 2),
                        default=1,
                        help="Die Version der Projektion, die verwendet werden soll:\n"
                        "-1 - WGS84\n"
                        " 0 - Linear von WGS84\n"
                        " 1 - Direkte Projektion auf EPSG:3035\n"
                        " 2 - Von WGS84 auf EPSG:3035\n")
    args = parser.parse_args()

    station_json = project_coordinates(tc_directory=args.tc_directory, projection_version=args.version)
    station_json.save()
