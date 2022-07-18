import json
from sys import argv
import os
from typing import Optional


def shift(x: int, y: int, scale_x: Optional[float], scale_y: Optional[float]):
    """Takes all stations and shifts their x and y-coordinates by the specified amount."""
    with open("Station.json", encoding="utf-8") as stations_file:
        data = json.load(stations_file)
        stations_list = data["data"]
        for station in stations_list:
            station['x'] += x
            station['y'] += y
            if scale_x and scale_y:
                station['x'] = int(station['x'] * scale_x)
                station['y'] = int(station['y'] * scale_y)
    with open("Station.json", "w", encoding="utf-8", newline='\n') as output:
        # Preserve Unicode and formatting
        json.dump(data, output, ensure_ascii=False, indent="\t")


if __name__ == '__main__':
    if not os.path.exists("Path.json") and os.path.exists("../Path.json"):
        os.chdir('..')
    try:
        x = int(argv[1])
        y = int(argv[2])
        if len(argv) == 5:
            scale_x = float(argv[3])
            scale_y = float(argv[4])
        else:
            scale_x = scale_y = None
        shift(x, y, scale_x, scale_y)
    except KeyError:
        print("Usage: python shift_station_coordinates.py x-offset y-offset")
