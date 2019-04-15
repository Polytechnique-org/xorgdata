#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
"""Convert a CSV exported from AlumnForce website to JSON format

As the CSV headers are quite verbose, transform them into usable field names.
This makes using tools like jq (commandline JSON processor) very straightforward
(cf. https://stedolan.github.io/jq/ ).

Examples:

* Show the data associated for a user selected by Polytechnique.org ID:

    ./convert_csv_to_json.py -u export-users-20180314-159265.csv | \
        jq '.[] | select(.xorg.login=="nicolas.iooss.2010") | [.id_af, .id_ax, .first_name + " " + .last_name]'

* Who is admin? ("role 3" in the database)

    ./convert_csv_to_json.py -u export-users-20180314-159265.csv | \
        jq '.[] | select(.roles | any(. == "3")) | [.first_name, .last_name, .email]'

* Who has an AlumnForce email?

    ./convert_csv_to_json.py -u export-users-20180314-159265.csv | \
        jq '.[] | select(.email and (.email | any(contains("@alumnforce"))))'
"""
import argparse
import sys

from lib.converters import AlumnForceDataC2J


def main():
    parser = argparse.ArgumentParser(description="Convert AF CSV to JSON")
    parser.add_argument('file', nargs='?',
                        help="CSV file to read (or standard input)")
    parser.add_argument('-k', '--keep-empty', action='store_true',
                        help="keep empty fields instead of dropping them")
    parser.add_argument('-o', '--output', type=str,
                        help="JSON file to write (or standard output)")
    parser.add_argument('-u', '--utf8', action='store_true',
                        help="write unicode strings as UTF-8 instead of escaping characters with \\u")
    args = parser.parse_args()

    if args.file:
        data = AlumnForceDataC2J.import_csv_file(args.file, args.keep_empty)
    else:
        data = AlumnForceDataC2J.import_csv_stream(sys.stdin.buffer, args.keep_empty)

    if args.output and args.output != '-':
        with open(args.output, 'w') as fjson:
            data.json_dump(fjson, indent=2, ensure_ascii=not args.utf8)
    else:
        data.json_dump(sys.stdout, indent=2, ensure_ascii=not args.utf8)


if __name__ == '__main__':
    main()
