from __future__ import annotations
import code

import os.path
from dataclasses import dataclass
from typing import List, Tuple

from structures.route import Track, Path, merge_tracks
from structures.station import Station, merge_stations, assert_unique_first_code, merge_stations_on_first_code, \
    CodeTuple, Location


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
        from importers.db_betriebsstellenverzeichnis import DbBetriebsstellenverzeichnisImporter
        from importers.fr_platforms import FrPlatformsImporter
        from importers.fr_stations import FrStationsImporter
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

        stations_fr = FrStationsImporter().import_data(os.path.join(data_directory, 'fr_stations.csv'))
        stations_fr = merge_stations_on_first_code(stations_fr)
        # Manual stations
        stations_fr.append(Station(
            name="Baudrecourt",
            number=hash('Baudrecourt'),
            codes=CodeTuple("🇫🇷BDC"),
            kind='abzw'
        ))
        stations_fr.append(Station(
            name="Pasilly à Aisy",
            number=hash("Pasilly à Aisy"),
            codes=CodeTuple("🇫🇷PAI"),
            location=Location(
                latitude=47.68882057293988,
                longitude=4.075627659435932
            ),
            kind='abzw'
        ))
        stations_fr.append(Station(
            name="Moisenay (Crisenoy)",
            number=hash("LGV Interconnexion Est -> Sud-Est"),
            codes=CodeTuple("🇫🇷MOIS"),
            location=Location(
                latitude=48.576961786948054, 
                longitude=2.74276121315047
            ),
            kind='abzw'
        ))
        stations_fr.append(Station(
            name="Jablines/Messy",
            number=hash("Warum muss das alles so kompliziert sein?!"),
            codes=CodeTuple("🇫🇷JAB"),
            location=Location(
                latitude=48.94902574095624, 
                longitude=2.7114885647354288
            ),
            kind='abzw'
        ))
        stations_fr.append(Station(
            name="Vémars",
            number=hash("Vemars"),
            codes=CodeTuple("🇫🇷VEMARS"),
            location=Location(
                latitude=49.055763434522255, 
                longitude=2.5651358332731578
            ),
            kind='abzw'
        ))
        stations_fr.append(Station(
            name="Eurotunnel UK-Terminal",
            number=hash("EUROTUNNEL!!!!"),
            codes=CodeTuple("🇬🇧ETUK"),
            location=Location(
                latitude=51.09612758903609, 
                longitude=1.139774590509386
            )
        ))
        stations_fr.append(Station(
            name="Montanay",
            number=hash("FR:Montanay"),
            codes=CodeTuple("🇫🇷MONT"),
            location=Location(
                latitude=45.8892271474285, 
                longitude=4.877505944798289
            ),
            kind='abzw'
        ))
        stations_fr.append(abzw_fr("Grenay", "GRNY", 45.649041949201745, 5.081229404359257))
        stations_fr.append(abzw_fr("Bollène", "BLLN", 44.30218827489829, 4.7017237487605215))

        platforms_fr = FrPlatformsImporter(stations_fr).import_data(os.path.join(data_directory, 'fr_platforms.csv'))
        add_platforms_to_stations(stations_fr, platforms_fr)

        # passenger_stations_ch = ChBahnhofsbenutzerImporter().import_data(os.path.join(data_directory, 'sbb_bahnhofsbenutzer.csv'))
        # add_passengers_to_stations_ch(stations_ch, passenger_stations_ch)

        stations = merge_stations(stations, stations_ch, 'name')
        stations = merge_stations(stations, stations_fr, 'name')

        return stations


def abzw_fr(name: str, code: str, latitude: float, longitude: float) -> Station:
    return Station(
        name=name,
        number=hash("FRANKREICH:{}".format(name)),
        codes=CodeTuple("🇫🇷" + code.upper()),
        location=Location(
            latitude=latitude,
            longitude=longitude
        ),
        kind='abzw'
    )
