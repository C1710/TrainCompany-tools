from __future__ import annotations

import argparse
import logging
import os
from argparse import ArgumentParser, Namespace
from os import PathLike
from os.path import isfile
from typing import List, Tuple, Generator, Optional

from structures import DataSet
from structures.country import CodeParser, iso_3166_to_country, tld_to_country


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


def parse_station_input(stations: List[str], case_sensitive: bool = False) -> Generator[Tuple[str], None, None]:
    current_country = None
    for station in stations:
        if not case_sensitive:
            station = station.upper()
        # If commas are inserted, e.g., from JSON, ignore them
        station = station.strip(",")
        equivalent_codes = station.split('=')
        code_parser = CodeParser(equivalent_codes, current_country)
        equivalent_parsed_codes = tuple(iter(code_parser))
        current_country = code_parser.current_country
        if len(equivalent_parsed_codes):
            yield equivalent_parsed_codes


def process_station_input(stations: List[str],
                          dataset: DataSet,
                          case_sensitive: bool = False
                          ) -> List[str]:
    parsed_station_codes = parse_station_input(stations, case_sensitive=case_sensitive)
    station_codes = []
    for equivalent_stations in parsed_station_codes:
        dataset.merge_station(equivalent_stations)
        station_codes.append(equivalent_stations[0])
    return station_codes


def add_default_cli_args(parser: ArgumentParser,
                         tc_directory: bool = True,
                         data_directory: bool = True,
                         default_logging_level: int = logging.WARNING):
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    default_tc_directory = os.path.dirname(script_dir)
    default_data_directory = os.path.join(script_dir, 'data')
    if "TRAINCOMPANY_DATA" in os.environ:
        default_tc_directory = os.environ["TRAINCOMPANY_DATA"]
    if "TRAINCOMPANY_TOOLS_DATA" in os.environ:
        default_data_directory = os.environ["TRAINCOMPANY_TOOLS_DATA"]

    if tc_directory:
        parser.add_argument('--tc-directory', '--tc_directory', '--tc-dir', dest='tc_directory', metavar='VERZEICHNIS',
                            type=str,
                            default=default_tc_directory,
                            help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    if data_directory:
        parser.add_argument('--data-directory', '--data_directory', "--data-dir", dest='data_directory',
                            metavar='VERZEICHNIS', type=str,
                            default=default_data_directory,
                            help="Das Verzeichnis, in dem sich die OpenData-Datensätze befinden")
    logging_args = parser.add_mutually_exclusive_group(required=False)
    # https://stackoverflow.com/a/20663028/5070653
    logging_args.add_argument("--log-level", dest="loglevel", default=default_logging_level,
                              help=argparse.SUPPRESS)
    if default_logging_level != logging.INFO:
        logging_args.add_argument("-v", "--verbose", action="store_const", dest="loglevel", const=logging.INFO,
                                  help="Gibt mehr Logging-Informationen aus")
    if default_logging_level != logging.DEBUG:
        logging_args.add_argument("-d", "--debug", action="store_const", dest="loglevel", const=logging.DEBUG,
                                  help="Gibt Debug-Informationen aus")
    if default_logging_level != logging.WARNING:
        logging_args.add_argument("-w", "--warning", action="store_const", dest="loglevel", const=logging.WARNING,
                                  help="Gibt nur Warnungen aus")
    if default_logging_level != logging.ERROR:
        logging_args.add_argument("-e", "--error", "--quiet", action="store_const", dest="loglevel",
                                  const=logging.ERROR,
                                  help="Gibt nur schwerwiegende Fehler aus")


def use_default_cli_args(args: Namespace):
    logging.basicConfig(level=args.loglevel)


def add_station_cli_args(parser: ArgumentParser,
                         help: str = "Die (RIL100-)Codes der betroffenen Haltestellen",
                         help_countries: str = "Die ISO-Kürzel der betroffenen Länder",
                         required: bool = False,
                         allow_unordered: bool = True,
                         allow_multiple_stations: bool = False):
    """Adds CLI arguments for station input. Use parse_station_args later.
    Attributes:
        parser: The ArgumentParser to add the arguments to
        help: The help-string for the stations-option
        help_countries: The help-string for the countries-option
        required: Whether one of the options is required
        allow_unordered: Whether the input methods without an explicit order should be allowed
        allow_multiple_stations: Whether multiple --stations or --countries options should be required
    """
    if not allow_multiple_stations:
        import_strategy = parser.add_mutually_exclusive_group(required=required)
    else:
        import_strategy = parser.add_argument_group("Arten der Stations-Eingabe")
    action = 'store' if not allow_multiple_stations else 'append'

    parser.add_argument('--case-sensitive', action='store_true',
                        help="Berücksichtigt Groß-/Kleinschreibung der Stations-Kürzel")

    import_strategy.add_argument('--stations', metavar='RIL100', type=str, nargs='+', help=help, action=action)
    if allow_unordered:
        import_strategy.add_argument('--countries', type=str, nargs='+', help=help_countries, action=action)


def parse_station_args(args: Namespace,
                       data_set: Optional[DataSet] = None,
                       data_directory: Optional[PathLike | str] = None,
                       inplace: bool = True,
                       required: bool = False) -> List[str] | List[List[str]] | None:
    if required:
        assert args.stations or args.countries, "Es muss mindestens ein --stations oder --countries angegeben werden."
    if not data_set:
        if data_directory:
            data_set = DataSet.load_data(data_directory=data_directory)
        elif args.data_directory:
            data_set = DataSet.load_data(data_directory=args.data_directory)
        else:
            raise ValueError("Missing both data_set and data_directory")
    if 'countries' in args and args.countries:
        countries = args.countries
        if isinstance(countries[0], str):
            # We need to collect the stations of the countries
            station_codes = _parse_countries(countries, data_set)
            if inplace:
                args.station_codes = station_codes
            return station_codes
        elif isinstance(countries[0], list):
            # We have a list of list, i.e., collect the countries for all --countries arguments
            all_station_codes = [_parse_countries(entry, data_set) for entry in countries]
            if inplace:
                args.station_codes = all_station_codes
            return all_station_codes
        else:
            raise TypeError("countries must be a list of strings or lists (of strings), but is list of {}"
                            .format(type(countries[0])))
    if 'stations' in args and args.stations:
        stations = args.stations
        case_sensitive = args.case_sensitive
        if not isinstance(stations[0], list):
            station_codes = process_station_input(stations, dataset=data_set, case_sensitive=case_sensitive)
            if inplace:
                args.station_codes = station_codes
            return station_codes
        elif isinstance(stations[0], list):
            all_station_codes = [process_station_input(entry, dataset=data_set, case_sensitive=case_sensitive) for entry
                                 in stations]
            if inplace:
                args.station_codes = all_station_codes
            return all_station_codes
        else:
            raise TypeError("stations must be a list of strings or lists (of strings), but is list of {}"
                            .format(type(stations[0])))
    else:
        return None


def _parse_countries(countries: List[str], data_set: DataSet) -> List[str]:
    countries = (country.upper() for country in countries)
    countries = [iso_3166_to_country[country] if country in iso_3166_to_country else tld_to_country[country]
                 for country in countries]
    stations = (station for station in data_set.station_data if station.country in countries)
    station_codes = [station.codes[0] for station in stations]
    return station_codes


def format_list_double_quotes(things: List[str]) -> str:
    return "[ {} ]".format(', '.join(("\"{}\"".format(thing) for thing in things)))
