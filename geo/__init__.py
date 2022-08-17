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
transformer_robinson = pyproj.Transformer.from_crs(crs_wgs84, crs_robinson)
projection = pyproj.Proj('epsg:3035')


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

    @classmethod
    def from_projection(cls, x: int, y: int, version: int = default_projection_version) -> Location:
        if version == 0:
            return Location.from_tc(x, y)
        if version == 1:
            return cls.from_projection_with_fun(
                projection_fun=lambda lon, lat: projection(longitude=lon, latitude=lat, errcheck=True),
                projection_fun_reverse=lambda x, y: projection(x, y, inverse=True, errcheck=True),
                x=x, y=y)
        elif version == 2:
            return cls.from_projection_with_fun(
                projection_fun=lambda lon, lat: transformer.transform(xx=lon, yy=lat, errcheck=True),
                projection_fun_reverse=lambda x, y: transformer.transform(xx=x, yy=y,
                                                                          direction=TransformDirection.INVERSE,
                                                                          errcheck=True),
                x=x, y=y)
        elif version == 3:
            # There seems to be a bug in the robinson transformer that longitude and latitude are swapped
            return cls.from_projection_with_fun(
                projection_fun=lambda lon, lat: transformer_robinson.transform(xx=lat, yy=lon, errcheck=True),
                projection_fun_reverse=lambda x, y: transformer_robinson.transform(xx=y, yy=x,
                                                                                   direction=TransformDirection.INVERSE,
                                                                                   errcheck=True),
                x=x, y=y)

    @classmethod
    def from_projection_with_fun(cls, projection_fun: Callable[[float, float], Tuple[float, float]],
                                 projection_fun_reverse: Callable[[float, float], Tuple[float, float]],
                                 x: float, y: float) -> Location:
        origin_x, origin_y, scale_x, scale_y = get_origin_scale(projection_fun)
        x /= scale_x
        y = -y / scale_y
        x += origin_x
        y += origin_y
        longitude, latitude = projection_fun_reverse(x, y)

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

        return cls(
            longitude=longitude,
            latitude=latitude
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
                return self.to_projection_with_fun(
                    lambda lon, lat: projection(longitude=lon, latitude=lat, errcheck=True))
            elif version == 2:
                return self.to_projection_with_fun(
                    lambda lon, lat: transformer.transform(xx=lon, yy=lat, errcheck=True))
            elif version == 3:
                # There seems to be a bug in the robinson transformer that longitude and latitude are swapped
                return self.to_projection_with_fun(
                    lambda lon, lat: transformer_robinson.transform(xx=lat, yy=lon, errcheck=True))
            else:
                raise ValueError("Projection version is not supported")

    def to_projection_with_fun(self, projection_fun: Callable[[float, float], Tuple[float, float]]) -> Tuple[int, int]:
        x, y = projection_fun(self.longitude, self.latitude)
        origin_x, origin_y, scale_x, scale_y = get_origin_scale(projection_fun)
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
origin_x_tc: float = location_kdn.longitude

location_ha = Location(
    latitude=51.76666898080754,
    longitude=8.943182001417538
)
origin_y_tc: float = location_ha.latitude

location_nn = Location(
    latitude=49.444986777895615,
    longitude=11.082370202236625
)
scale_x_tc: float = 625.0 / (location_nn.longitude - location_kdn.longitude)
scale_y_tc: float = 385.0 / (location_nn.latitude - location_ha.latitude)


@lru_cache
def get_origin_scale(projection_fun: Callable[[float, float], Tuple[float, float]]) -> Tuple[
    float, float, float, float]:
    """returns: origin_x, origin_y, scale_x, scale_y"""
    x_kdn, y_kdn = projection_fun(location_kdn.longitude, location_kdn.latitude)
    x_nn, y_nn = projection_fun(location_nn.longitude, location_nn.latitude)
    x_ha, y_ha = projection_fun(location_ha.longitude, location_ha.latitude)
    x_distance_kdn_nn = abs(x_nn - x_kdn)
    y_distance_ha_nn = abs(y_nn - y_ha)
    scale_x = 625.0 / x_distance_kdn_nn
    scale_y = 385.0 / y_distance_ha_nn
    return x_kdn, y_ha, scale_x, scale_y
