#!/usr/bin/env python

from __future__ import annotations

import argparse
from os import PathLike
from typing import List, Optional, Set

from cli_utils import process_station_input, add_default_cli_args, add_station_cli_args, parse_station_args
from structures import DataSet
from tc_utils import TcFile
from validation.graph import graph_from_files, get_path_suggestion, PathSuggestionConfig


def print_path_suggestion(station_codes: List[str],
                          tc_directory: PathLike | str = '..',
                          data_directory: PathLike | str = 'data',
                          config: PathSuggestionConfig = PathSuggestionConfig
                          ):
    station_json = TcFile("Station", tc_directory)
    path_json = TcFile("Path", tc_directory)

    graph = graph_from_files(station_json, path_json)

    station_groups = {station['ril100']: station.get('group') for station in station_json.data}

    path_suggestion = get_path_suggestion(graph, station_codes, config=config,
                                          station_to_group=station_groups)
    print(", ".join(("\"{}\"".format(code) for code in path_suggestion)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Berechne die pathSuggestion')
    add_default_cli_args(parser)
    add_station_cli_args(parser,
                         help="Die (RIL100-)Codes der Haltestellen auf dem Pfad",
                         required=True,
                         allow_countries=False)
    PathSuggestionConfig.add_cli_args(parser)

    args = parser.parse_args()
    stations = parse_station_args(args, required=True)
    config = PathSuggestionConfig.from_cli_args(args)

    print_path_suggestion(
        station_codes=stations,
        tc_directory=args.tc_directory,
        data_directory=args.data_directory,
        config=config
    )