from __future__ import annotations

import argparse
import os
from os import PathLike

from geo import Location
from tc_utils import TcFile


def transform_coordinates(tc_directory: PathLike | str = '..') -> TcFile:
    station_json = TcFile('Station', tc_directory)
    for station in station_json.data:
        if 'laea' not in station or not station['laea']:
            location = Location.from_tc(station['x'], station['y'])
            station['x'], station['y'] = location.to_laea()
            station['laea'] = 1
    return station_json


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Importiere neue Betriebsstellen in TrainCompany')
    parser.add_argument('--tc-dir', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    args = parser.parse_args()

    station_json = transform_coordinates(tc_directory=args.tc_directory)
    station_json.save()
