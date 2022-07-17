from __future__ import annotations

import argparse
import logging
import os

from cli_utils import check_files
from validation import validate

if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Test')
    parser.add_argument('--tc_directory', dest='tc_directory', metavar='VERZEICHNIS', type=str, default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data_directory', dest='data_directory', metavar='VERZEICHNIS', type=str, default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    parser.add_argument('--limit', type=int, default=700,
                        help="Die maximal zulässige Problempunktzahl (sollte <10000 liegen)")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    issues = validate(args.tc_directory, args.data_directory)

    logging.info("Score: {} (kleiner ist besser)".format(issues))

    if issues > args.limit:
        raise AssertionError(issues)


