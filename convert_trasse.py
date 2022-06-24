import csv
import json
import sys
import re
import os
from fix_positions import import_locations
from route_data import import_route_data

def convert(trasse: str):
	with open(trasse, encoding="cp1252") as trasse_f:
		trassen_reader = csv.reader(trasse_f, delimiter=';')
		trassen_reader.__next__()
		# Format: (distance from start, full name, RIL100, is stop, route number)
		waypoints = [(float(waypoint[0].replace(',', '.')), waypoint[1], waypoint[2].replace('  ', ' '), 'Kundenhalt' in waypoint[17], int(waypoint[3] if waypoint[3] else '0')) for waypoint in trassen_reader]
	# Split the data into the part relevant for Station.json and Path.json
	waypoints_station = [(waypoint[1], waypoint[2]) for waypoint in waypoints if waypoint[3]]
	waypoints_paths = [(waypoint[0], waypoint[2], waypoint[3], waypoint[4]) for waypoint in waypoints]
	extend_station(waypoints_station)
	extend_path(waypoints_paths)


def group_from_category(station_category: int) -> int:
	if station_category <= 2:
		return 0
	if station_category == 3:
		return 1
	else:
		return 2


# We use this regex to remove extensions like "HO U" -> "HO"
no_extensions_regex = re.compile(r'(\w+)( \w+)?')
def remove_ril_extensions(ril100: str) -> str:
	return no_extensions_regex.match(ril100).group(1)


def get_category_data(category_data: dict[str, int], ril100: str) -> int:
	try:
		return category_data[ril100]
	except KeyError:
		return category_data[remove_ril_extensions(ril100)]


def extend_station(waypoints: list[tuple[str, str, int]]):
	platform_data = import_platform_data()
	position_data = import_locations()
	category_data = import_station_categories()
	stations = [{
		"group": group_from_category(get_category_data(category_data, ril100)),
		"name": name,
		"ril100": ril100,
		"x": position_data[ril100][0] if ril100 in position_data else 424242,
		"y": position_data[ril100][1] if ril100 in position_data else 424242,
		"platformLength": (platform_data[ril100][1] if ril100 in platform_data else 0),
		"platforms": (platform_data[ril100][0] if ril100 in platform_data else 0)
	} for (name, ril100) in waypoints]
	
	with open("Station.json", encoding="utf-8") as station_f:
		data = json.load(station_f)
		stations_list: list = data["data"]
		ril100_list = [station["ril100"] for station in stations_list]
		new_stations = [station for station in stations 
						if station["ril100"] not in ril100_list 
						and remove_ril_extensions(station["ril100"]) not in ril100_list]
		stations_list.extend(new_stations)
	with open("Station.json", "w", encoding="utf-8", newline="\n") as output:
		json.dump(data, output, ensure_ascii=False, indent="\t")


def extend_path(waypoints: list[tuple[float, str, bool, int]]):
	# (RIL100, length, is electrified, category)
	route: list[tuple[str, int, bool, int]] = []
	route_data: dict[int, (bool, int)] = import_route_data()
	# The distance to the next stop (accumulated for all segments without one)
	distance_to_stop = 0
	total_distance = 0
	# The Streckennr. we cover by this segment
	segment_segments = []
	for (km, ril100, is_stop, segment_no) in waypoints:
		# Get the distance of the segment
		segment = km - total_distance
		total_distance = km
		# Regardless of whether it is a stop, we will add it
		distance_to_stop += segment
		if is_stop:
			segment_data = [route_data[segment_no] for segment_no in segment_segments]
			segment_segments = []
			electrified = all((electrified for (electrified, _) in segment_data))
			# We want 2 > 0 > 1.
			# A way to achieve this ordering is to invert the last bit.
			# 2 - 10 -> 11 -> 3
			# 0 - 00 -> 01 -> 1
			# 1 - 01 -> 00 -> 0
			if segment_data:
				route_category = max((category for (_, category) in segment_data), key=lambda cat: cat ^ 1)
			else:
				route_category = 0
			route.append((ril100, int(distance_to_stop), electrified, route_category))
			distance_to_stop = 0
		segment_segments.append(segment_no)
	route_segments = [{
		"start": ril_start,
		"end": ril_end,
		"electrified": electrified,
		"group": category,
		"length": segment_length,
		"twistingFactor": 0
	} for ((ril_start, _, _, _), (ril_end, segment_length, electrified, category)) in zip(route, route[1:])]
	route_entry = {
		"maxSpeed": 0
	}
	# Move shared properties out of the segments
	for (key, value) in route_segments[0].copy().items():
		# We use a placeholder here. We don't want to delete that.
		if key != "twistingFactor":
			if all((segment[key] == value for segment in route_segments)):
				route_entry.update([(key, value)])
				for segment in route_segments:
					segment.pop(key)
	route_entry.update(objects=route_segments)
	
	with open("Path.json", encoding="utf-8") as paths_f:
		data = json.load(paths_f)
		paths_list: list = data["data"]
		paths_list.append(route_entry)
	with open("Path.json", "w", encoding="utf-8", newline="\n") as output:
		json.dump(data, output, ensure_ascii=False, indent="\t")


def import_station_categories() -> dict[str, int]:
	with open("tools/bahnhoefe.csv", encoding="utf-8") as stations_f:
		stations_reader = csv.reader(stations_f, delimiter=';')
		stations_reader.__next__()
		# (RIL100, category)
		stations = dict(((station[5], station[6]) for station in stations_reader))
		return stations
	

def import_platform_data() -> dict[str, tuple[int, int]]:
	with open("tools/bahnsteige.csv", encoding="utf-8") as platform_f:
		platform_reader = csv.reader(platform_f, delimiter=';')
		platform_reader.__next__()
		platforms = [(int(platform[0]), int(float(platform[4].replace(',', '.')))) for platform in platform_reader]
		platform_data = dict()
		for (bf_nr, platform_length) in platforms:
			if bf_nr not in platform_data:
				platform_data[bf_nr] = [0, 0]
			platform_data[bf_nr][0] += 1
			platform_data[bf_nr][1] = max(platform_data[bf_nr][1], platform_length)
		platform_data = ((bf_nr, tuple(data)) for (bf_nr, data) in platform_data.items())

	# Now we need to convert from Bf-Nr to RIL100
	with open("tools/bahnhoefe.csv", encoding="utf-8") as stations_f:
		stations_reader = csv.reader(stations_f, delimiter=';')
		stations_reader.__next__()
		stations = dict(((int(station[3]), station[5]) for station in stations_reader))
	platform_data_ril100 = dict(((stations[bf_nr], platform_info) for (bf_nr, platform_info) in platform_data))
	return platform_data_ril100


if __name__ == '__main__':
	if not os.path.exists("Path.json") and os.path.exists("../Path.json"):
		os.chdir('..')
	try:
		filename = sys.argv[1]
	except KeyError:
		print("Usage: python convert_trasse.py trassenfinder.csv")
		exit()
	convert(filename)
	