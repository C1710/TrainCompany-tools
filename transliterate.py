import argparse
import re
from enum import Enum
from typing import Dict, Any

import unidecode

from cli_utils import add_default_cli_args, use_default_cli_args
from tc_utils import TcFile


class Transliterable(Enum):
    cyrillic = re.compile(r"[а-яА-Я]")
    greek = re.compile(r"[α-ωΑ-Ω]")


def transliterate(station_json: TcFile, **kwargs):
    for station in station_json.data:
        transliterate_station(station, **kwargs)


def transliterate_station(station: Dict[str, Any], **kwargs):
    if "name" in station:
        name = station["name"]
        for transliterable in Transliterable:
            if transliterable.name not in kwargs or kwargs[transliterable.name]:
                if transliterable.value.search(name):
                    station['name'] = unidecode.unidecode(name)
    if 'objects' in station:
        for sub_station in station['objects']:
            transliterate_station(sub_station)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transliterate certain scripts')
    add_default_cli_args(parser, data_directory=False)
    for transliterable in Transliterable:
        parser.add_argument(f"--no-{transliterable.name}", dest=f"{transliterable.name}", action="store_false",
                            help=f"Transliteriert {transliterable.name} nicht")

    args = parser.parse_args()
    use_default_cli_args(args)

    station_json = TcFile("Station", args.tc_directory)
    transliterate(station_json, **args.__dict__)
    station_json.save_formatted()
