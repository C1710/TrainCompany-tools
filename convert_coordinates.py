#!/usr/bin/env python

import sys

from geo import Location

if __name__ == '__main__':
    location = Location(
        latitude=float(sys.argv[1].strip(',')),
        longitude=float(sys.argv[2].strip(','))
    )

    print("x: {}\ny: {}".format(*location.to_projection()))
