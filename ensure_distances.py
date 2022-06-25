from collections import OrderedDict
import numpy
import scipy.spatial


def convert_to_list(stations: list[dict]) -> tuple[list[str], numpy.ndarray]:
	"""
	Converts stations with all their attributes to a sorted list of 2D-points
	and a sorted list/mapping from index to RIL100
	"""
	stations: OrderedDict[str, tuple[int, int]] = OrderedDict(((
		station['ril100'],
		(station['x'], station['y'])) for station in stations))
	ril100: list[str] = list(stations.keys())
	points: list[tuple[int, int]] = list(stations.values())
	points_array = numpy.array(points, dtype=float)

	return ril100, points_array


def convert_to_dict(ril100: list[str], points: numpy.ndarray) -> dict[str, tuple[int, int]]:
	"""Converts back from two ordered lists to one dict"""
	points = list(map(tuple, points))
	return dict(zip(ril100, points))


def apply_new_coordinates(new_coordinates: dict[str, tuple[int, int]], stations: list[dict]):
	"""Changes the coordinates of each station according to the newly supplied ones"""
	for station in stations:
		(x_new, y_new) = new_coordinates[station['ril100']]
		station['x'] = int(x_new)
		station['y'] = int(y_new)


def space(points: numpy.ndarray, distance: int):
	# based on https://stackoverflow.com/a/54048062
	length = len(points)
	for i in range(0, 700):
		distance_matrix = scipy.spatial.distance.pdist(points)
		if min(distance_matrix) >= distance:
			return
		directions = numpy.zeros(shape=points.shape, dtype=float)
		for (a, point_a) in enumerate(points):
			for (b, point_b) in enumerate(points[a+1:]):
				# https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html#scipy.spatial.distance.pdist
				vector = point_b - point_a
				norm = numpy.linalg.norm(vector)
				if norm == 0 or norm == numpy.nan:
					raise ZeroDivisionError("{} and {} are identical.".format(point_a, point_b))
				vector /= norm
				# Point B is moved in the vector direction, Point A in the other direction
				if norm <= distance * 2:
					directions[b] += (vector / (norm**2)) * distance / 20
					directions[a] -= (vector / (norm**2)) * distance / 20
		for (index, (point, displacement)) in enumerate(zip(points, directions)):
			displacement_norm = numpy.linalg.norm(displacement)
			if displacement_norm > distance / 2:
				displacement *= (distance / 2) / displacement_norm
			points[index] = point + displacement
	if min(distance_matrix) < distance:
		print("Minimum distance is still too low:", min(distance_matrix))
