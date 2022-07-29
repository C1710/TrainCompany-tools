#!/usr/bin/env python

from __future__ import annotations

import argparse
import os
from os import PathLike
from typing import Any, Dict, Tuple

from cli_utils import add_default_cli_args
from tc_utils import TcFile


def cleanup(tc_directory: PathLike | str, force: bool = False) -> Tuple[TcFile, TcFile]:
    path_json = TcFile('Path', tc_directory)
    for path in path_json.data:
        remove_annotations_from_path(path)
    station_json = TcFile('Station', tc_directory)
    for station in station_json.data:
        remove_annotations_from_station(station)
    return path_json, station_json


def remove_annotations_from_path(path: Dict[str, Any]):
    path.pop('start_long', '')
    path.pop('end_long', '')
    if 'objects' in path:
        for sub_path in path['objects']:
            remove_annotations_from_path(sub_path)


def remove_annotations_from_station(station: Dict[str, Any], force: bool = False):
    if 'group' not in station or station['group'] not in (4,):
        if force or ('platforms' in station and 'platformLength' in station
                     and station['platforms'] and station['platformLength']):
            station.pop('google_maps')
            station.pop('osm')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Entferne nicht mehr benötigte Daten')
    add_default_cli_args(parser, data_directory=False)
    parser.add_argument("--force", action="store_true",
                        help="Löscht alle Annotationen, auch, wenn sie vielleicht noch hilfreich sind.")
    args = parser.parse_args()

    path_json, station_json = cleanup(tc_directory=args.tc_directory, force=args.force)
    path_json.save()
    station_json.save()
