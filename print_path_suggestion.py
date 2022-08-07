#!/usr/bin/env python

from __future__ import annotations

import argparse
from os import PathLike
from typing import List, Optional, Set

from cli_utils import process_station_input, add_default_cli_args
from structures import DataSet
from tc_utils import TcFile
from validation.graph import graph_from_files, get_path_suggestion


def print_path_suggestion(station_codes: List[str],
                          tc_directory: PathLike | str = '..',
                          data_directory: PathLike | str = 'data',
                          use_sfs: bool = True,
                          non_electrified: bool = True,
                          avoid_equipments: Optional[Set[str]] = None
                          ):
    data_set = DataSet.load_data(data_directory)
    station_codes = process_station_input(station_codes, data_set)

    station_json = TcFile("Station", tc_directory)
    path_json = TcFile("Path", tc_directory)

    graph = graph_from_files(station_json, path_json)

    path_suggestion = get_path_suggestion(graph, station_codes, use_sfs, non_electrified, avoid_equipments)
    print(", ".join(("\"{}\"".format(code) for code in path_suggestion)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Berechne die pathSuggestion')
    parser.add_argument('--stations', metavar='RIL100', type=str, nargs='+', required=True,
                        help='Die RIL100-Codes des Pfads')
    parser.add_argument('--electrified', action='store_true',
                        help="Versucht, eine nur elektrifizierte Strecke zu finden.")
    parser.add_argument('--avoid-sfs', action='store_true',
                        help="Versucht, SFS zu meiden.")
    parser.add_argument('--avoid-equipments', metavar='EQUIPMENT', type=str, nargs='+',
                        help="Equipments, die gemieden werden sollen")
    add_default_cli_args(parser)
    args = parser.parse_args()

    print_path_suggestion(
        station_codes=args.stations,
        tc_directory=args.tc_directory,
        data_directory=args.data_directory,
        use_sfs=not args.avoid_sfs,
        non_electrified=not args.electrified,
        avoid_equipments=args.avoid_equipments
    )
