from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Tuple

import geopy.distance
import pyproj
from pyproj.enums import TransformDirection

default_projection_version = 1

crs_wgs84 = pyproj.CRS('WGS84')
crs_proj = pyproj.CRS('epsg:3035')
crs_robinson = pyproj.CRS('esri:54030')
transformer = pyproj.Transformer.from_crs(crs_wgs84, crs_proj)
transformer_reverse = pyproj.Transformer.from_crs(crs_proj, crs_wgs84)
transformer_robinson = pyproj.Transformer.from_crs(crs_wgs84, crs_robinson)
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

    def to_tc(self) -> Tuple[int, int]:
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
            location = Location(
                latitude=latitude,
                longitude=longitude
            )
        return location

    @staticmethod
    def from_projection(x: int, y: int, version: int = default_projection_version) -> Location:
        if version == 0:
            return Location.from_tc(x, y)
        if version == 1:
            origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                lambda lon, lat: projection(longitude=lon, latitude=lat, errcheck=True))
            y = -y
            x /= scale_x
            y /= scale_y
            x += origin_x
            y += origin_y
            longitude, latitude = projection(x, y, inverse=True)
        elif version == 2:
            origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                lambda lon, lat: transformer.transform(xx=lon, yy=lat, errcheck=True))
            y = -y
            x /= scale_x
            y /= scale_y
            x += origin_x
            y += origin_y
            longitude, latitude = transformer_reverse.transform(x, y)
        elif version == 3:
            origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                lambda lon, lat: transformer.transform(yy=lon, xx=lat, errcheck=True))
            y = -y
            x /= scale_x
            y /= scale_y
            x += origin_x
            y += origin_y
            longitude, latitude = transformer_robinson.transform(x, y, direction=TransformDirection.INVERSE)
        if abs(x - 0) < 2:
            assert abs(longitude - origin_x_tc) < 0.002, abs(longitude - origin_x_tc)
        if abs(y - 0) < 2:
            assert abs(latitude - origin_y_tc) < 0.002, abs(latitude - origin_y_tc)
        if abs(x - 625) < 2:
            assert abs(longitude - location_nn.longitude) < 0.002, abs(longitude - location_nn.longitude)
        if abs(y - 385) < 2:
            assert abs(latitude - location_nn.latitude) < 0.002, abs(latitude - location_nn.latitude)
        assert -180.0 <= longitude <= 180.0
        assert -90.0 <= latitude <= 90.0
        return Location(
            latitude=latitude,
            longitude=longitude
        )

    def to_projection(self, version: int = default_projection_version) -> Tuple[int, int]:
        assert -180.0 <= self.longitude <= 180.0
        assert -90.0 <= self.latitude <= 90.0
        if version == -1:
            return int(self.longitude), int(self.latitude)
        elif version == 0:
            return self.to_tc()
        else:
            if version == 1:
                x, y = projection(longitude=self.longitude, latitude=self.latitude, errcheck=True)
                origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                    lambda lon, lat: projection(longitude=lon, latitude=lat, errcheck=True))
            elif version == 2:
                x, y = transformer.transform(xx=self.longitude, yy=self.latitude, errcheck=True)
                origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                    lambda lon, lat: transformer.transform(xx=lon, yy=lat, errcheck=True))
            elif version == 3:
                try:
                    x, y = transformer_robinson.transform(yy=self.longitude, xx=self.latitude, errcheck=True)
                except Exception as e:
                    print(self.longitude, self.latitude)
                    raise e
                origin_x, origin_y, scale_x, scale_y = get_origin_scale(
                    lambda lon, lat: transformer_robinson.transform(yy=lon, xx=lat, errcheck=True))
            else:
                raise ValueError("Projection version is not supported")
            x -= origin_x
            y -= origin_y
            # Note that we negate y here, as we want y to face southwards
            return int(x * scale_x), int(-y * scale_y)

    def distance(self, other: Location) -> int:
        return geopy.distance.geodesic(
            (self.latitude, self.longitude),
            (other.latitude, other.longitude)
        ).kilometers

    def distance_float(self, other: Location) -> float:
        return geopy.distance.geodesic(
            (self.latitude, self.longitude),
            (other.latitude, other.longitude)
        ).meters / 1000

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


@lru_cache
def get_origin_scale(projection_fun: Callable[[float, float], Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """returns: origin_x, origin_y, scale_x, scale_y"""
    x_kdn, y_kdn = projection_fun(location_kdn.longitude, location_kdn.latitude)
    x_nn, y_nn = projection_fun(location_nn.longitude, location_nn.latitude)
    x_ha, y_ha = projection_fun(location_ha.longitude, location_ha.latitude)
    x_distance_kdn_nn = abs(x_nn - x_kdn)
    y_distance_ha_nn = abs(y_nn - y_ha)
    scale_x = 625.0 / x_distance_kdn_nn
    scale_y = 385.0 / y_distance_ha_nn
    return x_kdn, y_ha, scale_x, scale_y
