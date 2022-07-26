from __future__ import annotations

import logging
import os
from os import PathLike
from os.path import isfile
from typing import List, Tuple, Generator

from structures import DataSet
from structures.country import CodeParser


def check_files(tc_directory: PathLike | str, data_directory: PathLike | str):
    fail: bool = False
    for tc_file in ['Station', 'Path']:
        if not isfile(os.path.join(tc_directory, tc_file) + '.json'):
            logging.error('Konnte Datei nicht finden: {} (in {})'.format(tc_file, tc_directory))
            fail = True
    for data_file in ['bahnhoefe', 'bahnsteige', 'betriebsstellen', 'strecken']:
        if not isfile(os.path.join(data_directory, data_file) + '.csv'):
            logging.error('Konnte Datei nicht finden: {} (in {})'.format(data_file, data_directory))
            fail = True
    if fail:
        exit(1)


def parse_station_input(stations: List[str]) -> Generator[Tuple[str], None, None]:
    current_country = None
    for station in stations:
        station = station.upper()
        equivalent_codes = station.split('=')
        code_parser = CodeParser(equivalent_codes, current_country)
        equivalent_parsed_codes = tuple(iter(code_parser))
        current_country = code_parser.current_country
        if len(equivalent_parsed_codes):
            yield equivalent_parsed_codes


def process_station_input(stations: List[str], dataset: DataSet) -> List[str]:
    parsed_station_codes = parse_station_input(stations)
    station_codes = []
    for equivalent_stations in parsed_station_codes:
        dataset.merge_station(equivalent_stations)
        station_codes.append(equivalent_stations[0])
    return station_codes
