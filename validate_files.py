from __future__ import annotations

import argparse
import logging
import os

from cli_utils import check_files, add_default_cli_args
from validation import validate

if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    parser = argparse.ArgumentParser(description='Test')
    add_default_cli_args(parser)
    parser.add_argument('--limit', type=int, default=700,
                        help="Die maximal zulässige Problempunktzahl (sollte <10000 liegen)")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    issues = validate(args.tc_directory, args.data_directory)

    logging.info("Score: {} (kleiner ist besser)".format(issues))

    if issues > args.limit:
        raise AssertionError(issues)


