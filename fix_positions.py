from __future__ import annotations
import csv
import json
import os
import sys
from functools import lru_cache
from typing import Optional, List, Tuple, Dict
import plot


@lru_cache
def import_betriebsstellen_data() -> List[Tuple[str, int, int, float, float]]:
	with open("tools/betriebsstellen_open_data.csv", encoding="cp852") as betriebsstellen_f:
		reader = csv.reader(betriebsstellen_f, delimiter=',')
		reader.__next__()
		# RIL100, Strecke_nr, KM, longitude, latitude
		data = [(
			station[6],
			int(station[0]),
			int(station[2]),
			# Longitude and latitude couldn't get this large, so it is okay to use as a placeholder
			float(station[10] if station[10] else 424242),
			float(station[9] if station[9] else 424242)
		) for station in reader]
	return data


@lru_cache
def betriebsstellen_as_dict() -> Dict[str, (int, int, float, float)]:
	data = import_betriebsstellen_data()
	data = ((ril100, (strecken_nr, km, longitude, latitude)) for (ril100, strecken_nr, km, longitude, latitude) in data)
	return dict(data)


@lru_cache
def import_locations() -> Dict[str, (int, int)]:
	"""
	Imports location data for (almost) all stations in Germany.
	returns: a dict from RIL100-string to location (in the TC coordinate system)
	"""
	betriebsstellen_data = import_betriebsstellen_data()
	return dict(((ril100, transform_coordinates(lon, lat)) for (ril100, _, _, lon, lat) in betriebsstellen_data))


origin_x: float = 6.482451
origin_y: float = 51.766433
scale_x: float = 625.0 / (11.082989 - origin_x)
scale_y: float = 385.0 / (49.445616 - origin_y)


def transform_coordinates(longitude: float, latitude: float) -> Tuple[int, int]:
	if longitude < 424242 and latitude < 424242:
		return int((longitude - origin_x) * scale_x), int((latitude - origin_y) * scale_y)
	else:
		# We don't have coordinates here
		return 424242, 424242


def fix_locations(stations: Optional[List[str]] = None):
	"""
	Moves all stations to their "real" location,
	with the exception of stations with their RIL100 code starting with 'K', 'F', 'R', 'S', or 'T'.
	This does _not_ affect newly added stations.
	"""
	positions_tc = import_locations()
	with open("Station.json", encoding="utf-8") as station_f:
		data = json.load(station_f)
		station_list: List[dict] = data["data"]
		for station in station_list:
			try:
				if not stations:
					if station['ril100'][0] not in ["K", "F", "R", "S", "T"]:
						station['x'], station['y'] = positions_tc[station["ril100"]]
				else:
					if station['ril100'].lower() in stations:
						station['x'], station['y'] = positions_tc[station["ril100"]]
			except KeyError:
				print("Konnte Position von {} nicht bestimmen.".format(station['ril100']))
	# Spacing is disabled
	# mapping, points = ensure_distances.convert_to_list(station_list)
	# points = [(point[0], point[1]) for point in points]
	# points = fast_spacing.space(points, 15)
	# points = numpy.array(points)
	# new_coordinates = ensure_distances.convert_to_dict(mapping, points)
	# ensure_distances.apply_new_coordinates(new_coordinates, station_list)
	with open("Station.json", 'w', encoding='utf-8', newline='\n') as output:
		json.dump(data, output, ensure_ascii=False, indent='\t')
	plot.plot_map()


if __name__ == '__main__':
	if not os.path.exists("Station.json") and os.path.exists("../Station.json"):
		os.chdir('..')
	if len(sys.argv) >= 2:
		stations = [ril100.lower() for ril100 in sys.argv[1:]]
		fix_locations(stations)
	else:
		fix_locations()
