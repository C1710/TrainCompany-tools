from __future__ import annotations
import os.path
from dataclasses import dataclass
from typing import List

from tools.importers.db_bahnhoefe import DbBahnhoefeImporter, add_hp_information_to_stations
from tools.importers.db_bahnsteige import DbBahnsteigeImporter, add_platforms_to_stations
from tools.importers.db_betriebsstellen import DbBetriebsstellenImporter
from tools.importers.db_strecken import DbStreckenImporter
from tools.structures.route import Track
from tools.structures.station import Station


@dataclass
class DataSet:
    station_data: List[Station]
    track_data: List[Track]

    @staticmethod
    def load_data(
            data_directory: str = 'data'
    ) -> DataSet:
        stations = DbBetriebsstellenImporter().import_data(os.path.join(data_directory, "betriebsstellen.csv"))

        passenger_stations = DbBahnhoefeImporter().import_data(os.path.join(data_directory, "bahnhoefe.csv"))
        add_hp_information_to_stations(stations, passenger_stations)

        platforms = DbBahnsteigeImporter().import_data(os.path.join(data_directory, "bahnteige.csv"))
        add_platforms_to_stations(stations, platforms)

        tracks = DbStreckenImporter().import_data(os.path.join(data_directory, "strecken.csv"))

        return DataSet(
            stations,
            tracks
        )
