from __future__ import annotations

import collections.abc
from functools import partial
from typing import List
from urllib.parse import urlencode

import geopy
from geopy import Photon
from geopy.geocoders.base import DEFAULT_SENTINEL


class PhotonAdvancedReverse(Photon):
    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=False,
            limit=None,
            radius: int | None = None,
            query_string_filter: str | List[str] | None = None
    ) -> geopy.location.Location | List[geopy.location.Location] | None:
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: Preferred language in which to return results.

        :param int limit: Limit the number of returned results, defaults to no
            limit.

        :param int radius: The radius in km to look around the location

        :param query_string_filter: Filters for the search result(s)

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon,
        }
        if limit:
            params['limit'] = int(limit)
        if exactly_one:
            params['limit'] = 1
        if language:
            params['lang'] = language
        if radius is not None:
            params['radius'] = radius
        if query_string_filter:
            if isinstance(query_string_filter, str):
                params['query_string_filter'] = [query_string_filter]
            elif not isinstance(query_string_filter, collections.abc.Iterable):
                raise ValueError(
                    "query_string_filter must be a string or "
                    "an iterable of strings"
                )
            else:
                params['query_string_filter'] = list(query_string_filter)
        url = "?".join((self.reverse_api, urlencode(params, doseq=True, safe="+")))
        geopy.util.logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)
