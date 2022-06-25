import csv
import json
import os
import plot


def import_locations() -> dict[str, (int, int)]:
	"""
	Imports location data for (almost) all stations in Germany.
	returns: a dict from RIL100-string to location (in the TC coordinate system)
	"""
	with open("tools/haltestellen.CSV", encoding="utf-8") as haltestellen_f:
		haltestellen_reader = csv.reader(haltestellen_f, delimiter=";")
		haltestellen_reader.__next__()
		positions = ((station[1], float(station[5].replace(',', '.')), float(station[6].replace(',', '.'))) for station in haltestellen_reader)
		# Some entries have multiple RIL100 in one line
		positions = ([(ril100, lon, lat) for ril100 in ril100s.split(',')] for (ril100s, lon, lat) in positions)
		positions = ((ril100.replace('  ', ' '), lon, lat) for entries in positions for (ril100, lon, lat) in entries)
		origin_x: float = 6.482451
		origin_y: float = 51.766433
		scale_x: float = 625.0 / (11.082989 - origin_x)
		scale_y: float = 385.0 / (49.445616 - origin_y)
		positions_tc = dict(((ril100, (int((lon - origin_x) * scale_x), int((lat - origin_y) * scale_y))) for (ril100, lon, lat) in positions))
		return positions_tc


def fix_locations():
	"""
	Moves all stations to their "real" location, 
	with the exception of stations with their RIL100 code starting with 'K', 'F', 'R', 'S', or 'T'.
	This does _not_ affect newly added stations.
	"""
	positions_tc = import_locations()
	with open("Station.json", encoding="utf-8") as station_f:
		data = json.load(station_f)
		station_list: list[dict] = data["data"]
		for station in station_list:
			try:
				if station['ril100'][0] not in ["K", "F", "R", "S", "T"]:
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
	fix_locations()
