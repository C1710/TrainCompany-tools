#!/usr/bin/env python

from __future__ import annotations

import argparse
import logging

from cli_utils import check_files, add_default_cli_args, use_default_cli_args
from validation import validate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test')
    add_default_cli_args(parser, default_logging_level=logging.INFO)
    parser.add_argument('--limit', type=int, default=700,
                        help="Die maximal zulässige Problempunktzahl (sollte <10000 liegen)")
    parser.add_argument('--experimental', nargs='?', choices=["false", "enforce", "warn"],
                        default="false",
                        const="enforce",
                        type=str,
                        help="Führt auch noch nicht ganz stabile Checks durch.\n"
                             "Bei warn wird der Issue-Score nicht erhöht")
    args = parser.parse_args()
    use_default_cli_args(args)

    check_files(args.tc_directory, args.data_directory)

    issues = validate(args.tc_directory, args.data_directory, experimental=args.experimental)

    logging.info("Score: {} (kleiner ist besser)".format(issues))

    if issues > args.limit:
        raise AssertionError(issues)
