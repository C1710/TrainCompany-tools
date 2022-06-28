from __future__ import annotations

import logging
import os
from os import PathLike
from os.path import isfile


def check_files(tc_directory: PathLike | str, data_directory: PathLike | str):
    fail: bool = False
    for tc_file in ['Station', 'Path']:
        if not isfile(os.path.join(tc_directory, tc_file) + '.json'):
            logging.error('Konnte Datei nicht finden: {} (in {})'.format(tc_file, tc_directory))
            fail = True
    for data_file in ['bahnhoefe', 'bahnsteige', 'betriebsstellen', 'strecken']:
        if not isfile(os.path.join(data_directory, data_file) + '.csv'):
            logging.error('Konnte Datei nicht finden: {} (in {})'.format(data_file, data_directory))
            fail = True
    if fail:
        exit(1)
