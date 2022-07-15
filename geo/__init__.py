from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import geopy.distance
import pyproj

crs_wg84 = pyproj.CRS('WGS84')
crs_proj = pyproj.CRS('epsg:3035')
transformer = pyproj.Transformer.from_crs(crs_wg84, crs_proj)
transformer_reverse = pyproj.Transformer.from_crs(crs_proj, crs_wg84)
projection = pyproj.Proj('epsg:3035')

origin_x_tc: float = 6.482451
origin_y_tc: float = 51.766433
scale_x_tc: float = 625.0 / (11.082989 - origin_x_tc)
scale_y_tc: float = 385.0 / (49.445616 - origin_y_tc)


@dataclass(frozen=True)
class Location:
    __slots__ = 'latitude', 'longitude'
    latitude: float
    longitude: float

    def convert_to_tc(self) -> Tuple[int, int]:
        x = int((self.longitude - origin_x_tc) * scale_x_tc)
        y = int((self.latitude - origin_y_tc) * scale_y_tc)
        return x, y

    @staticmethod
    def from_tc(x: int | float, y: int | float) -> Location:
        if isinstance(x, float) and isinstance(y, float):
            location = Location(
                longitude=x,
                latitude=y
            )
        else:
            longitude = (x / scale_x_tc) + origin_x_tc
            latitude = (y / scale_y_tc) + origin_y_tc
            if x == 0:
                assert abs(longitude - origin_x_tc) < 0.002, abs(longitude - origin_x_tc)
            if y == 0:
                assert abs(latitude - origin_y_tc) < 0.002, abs(latitude - origin_y_tc)
            if x == 625:
                assert abs(longitude - location_nn.longitude) < 0.002, abs(longitude - location_nn.longitude)
            if y == 385:
                assert abs(latitude - location_nn.latitude) < 0.002, abs(latitude - location_nn.latitude)
            location = Location(
                latitude=latitude,
                longitude=longitude
            )
        return location

    @staticmethod
    def from_projection(x: int, y: int, version: int = 1) -> Location:
        if version == 0:
            return Location.from_tc(x, y)
        if version == 1:
            longitude, latitude = projection(x, y, inverse=True)
        elif version == 2:
            longitude, latitude = transformer_reverse.transform(x, y)
        return Location(
            latitude=latitude,
            longitude=longitude
        )

    def to_projection(self, version: int = 1) -> Tuple[int, int]:
        if version == 1:
            x, y = projection(longitude=self.longitude, latitude=self.latitude, errcheck=True)
        elif version == 2:
            x, y = transformer.transform(longitude=self.longitude, latitude=self.latitude, errcheck=True)
        x -= x_kdn
        y -= y_ha
        # Note that we negate y here, as we want y to face southwards
        return int(x * scale_x_laea), int(-y * scale_y_laea)

    def distance(self, other: Location) -> int:
        return geopy.distance.geodesic(
            (self.latitude, self.longitude),
            (other.latitude, other.longitude)
        ).kilometers

    def __hash__(self):
        return ('location', self.latitude, self.longitude).__hash__()


location_kdn = Location(
    latitude=50.809494066048444,
    longitude=6.48224930984118
)
location_nn = Location(
    latitude=49.444986777895615,
    longitude=11.082370202236625
)
location_ha = Location(
    latitude=51.76666898080754,
    longitude=8.943182001417538
)

x_kdn, y_kdn = projection(longitude=location_kdn.longitude, latitude=location_kdn.latitude)
x_nn, y_nn = projection(longitude=location_nn.longitude, latitude=location_nn.latitude)
x_ha, y_ha = projection(longitude=location_ha.longitude, latitude=location_ha.latitude)
x_distance_laea_kdn_nn = x_nn - x_kdn
y_distance_laea_ha_nn = abs(y_nn - y_ha)
scale_x_laea = 625.0 / x_distance_laea_kdn_nn
scale_y_laea = 385.0 / y_distance_laea_ha_nn
