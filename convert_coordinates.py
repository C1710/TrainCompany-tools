import sys

from structures.station import Location

if __name__ == '__main__':
    location = Location(
        latitude=float(sys.argv[1]),
        longitude=float(sys.argv[2])
    )

    print("x: {}\ny: {}".format(*location.convert_to_tc()))
