#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
"""Convert a JSON file to a CSV file to be imported on AlumnForce website

This is the reciprocal of convert_csv_to_json.py.
"""
import argparse
import sys

from lib.converters import AlumnForceDataJ2C


def main():
    parser = argparse.ArgumentParser(description="Convert AF CSV to JSON")
    parser.add_argument('file', nargs='?',
                        help="JSON file to read (or standard input)")
    parser.add_argument('-o', '--output', type=str,
                        help="CSV file to write (or standard output)")
    args = parser.parse_args()

    if args.file:
        data = AlumnForceDataJ2C.import_json_file(args.file)
    else:
        data = AlumnForceDataJ2C.import_json_stream(sys.stdin)

    if args.output and args.output != '-':
        with open(args.output, 'w') as fcsv:
            data.csv_dump(fcsv)
    else:
        data.csv_dump(sys.stdout)


if __name__ == '__main__':
    main()
