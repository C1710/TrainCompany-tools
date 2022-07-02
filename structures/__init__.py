from __future__ import annotations

import logging
import os.path
from dataclasses import dataclass
from typing import List

from importers.db_betriebsstellenverzeichnis import DbBetriebsstellenverzeichnisImporter
from structures.route import Track, Path, merge_tracks
from structures.station import Station, merge_stations, assert_unique_first_code, merge_stations_on_first_code


@dataclass
class DataSet:
    station_data: List[Station]
    path_data: List[Path]

    @staticmethod
    def load_data(
            data_directory: str = 'data'
    ) -> DataSet:
        from importers.db_strecken import DbStreckenImporter

        stations = DataSet.load_station_data(data_directory)
        tracks = DbStreckenImporter().import_data(os.path.join(data_directory, "strecken.csv"))
        paths = merge_tracks(tracks)

        return DataSet(
            stations,
            paths
        )

    @staticmethod
    def load_station_data(data_directory: str = 'data') -> List[Station]:
        from importers.ch_bahnhofsbenutzer import ChBahnhofsbenutzerImporter, add_passengers_to_stations_ch
        from importers.ch_betriebsstellen import ChBetriebsstellenImporter
        from importers.ch_platforms import ChPlatformsImporter
        from importers.db_bahnhoefe import DbBahnhoefeImporter
        from importers.db_bahnsteige import DbBahnsteigeImporter, add_platforms_to_stations
        from importers.db_betriebsstellen import DbBetriebsstellenImporter

        stations = DbBetriebsstellenverzeichnisImporter().import_data(os.path.join(data_directory, "betriebsstellen_verzeichnis.csv"))

        assert_unique_first_code(stations)

        stations_with_location = DbBetriebsstellenImporter().import_data(os.path.join(data_directory, "betriebsstellen.csv"))
        stations_with_location = merge_stations_on_first_code(stations_with_location)
        stations = merge_stations(stations, stations_with_location, on="codes")

        assert_unique_first_code(stations)

        passenger_stations = DbBahnhoefeImporter().import_data(os.path.join(data_directory, "bahnhoefe.csv"))
        stations = merge_stations(stations, passenger_stations, on="codes")

        assert_unique_first_code(stations)

        platforms = DbBahnsteigeImporter().import_data(os.path.join(data_directory, "bahnsteige.csv"))
        add_platforms_to_stations(stations, platforms)

        stations_ch = ChBetriebsstellenImporter().import_data(os.path.join(data_directory, "sbb_didok.csv"))

        platforms_ch = ChPlatformsImporter().import_data(os.path.join(data_directory, "sbb_platforms.csv"))
        add_platforms_to_stations(stations_ch, platforms_ch)

        # passenger_stations_ch = ChBahnhofsbenutzerImporter().import_data(os.path.join(data_directory, 'sbb_bahnhofsbenutzer.csv'))
        # add_passengers_to_stations_ch(stations_ch, passenger_stations_ch)

        stations = merge_stations(stations, stations_ch, 'name')

        return stations
