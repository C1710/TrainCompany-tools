from __future__ import annotations
import csv
import re
from typing import Tuple, Dict


def import_route_data() -> Dict[int, Tuple[bool, int]]:
    with open("tools/Strecken.MID", encoding="cp1252") as routes_f:
        route_reader = csv.reader(routes_f, delimiter=',')
        # (route ID, (electrification, Haupt/Nebenbahn))
        routes = dict(
            ((int(route[1]), (route[8] != "nicht elektrifiziert", convert_haupt_nebenbahn(route[8], route[13]))) for
             route in route_reader))
    return routes


speed_re = re.compile(r"(ab (\d+) )?bis (\d+) km/h")


def extract_speed(speed_str: str) -> Tuple[int, int]:
    match = speed_re.search(speed_str)
    if match is not None:
        v_from = match.group(2)
        v_to = int(match.group(3))
        if v_from is None:
            v_from = 0
        else:
            v_from = int(v_from)
        return (v_from, v_to)
    return (0, 0)


def convert_haupt_nebenbahn(speed: str, category: str) -> int:
    if category == "Nebenbahn":
        return 1
    elif category == "Hauptbahn":
        if extract_speed(speed)[1] >= 250:
            return 2
        else:
            return 0
