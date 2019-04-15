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
import collections
import csv
import json
import sys

from csv_format import ALUMNFORCE_FIELDS


CSV_TO_JSON_FIELDS = dict((x[0], (x[1], x[2])) for x in ALUMNFORCE_FIELDS)
assert len(ALUMNFORCE_FIELDS) == len(CSV_TO_JSON_FIELDS)


class AlumnForceDataC2J(object):
    """Data extracted from AlumnForce website"""
    def __init__(self):
        self.fields = None
        self.content = []

    @classmethod
    def import_csv_file(cls, csv_file_path, keep_empty=False):
        """Create AlumnForce data from a CSV file"""
        with open(csv_file_path, 'r', encoding='iso-8859-15') as csv_stream:
            return cls.import_csv_stream(csv_stream, keep_empty)

    @classmethod
    def import_csv_stream(cls, csv_file, keep_empty=False):
        """Create AlumnForce data from a CSV stream"""
        data = cls()
        reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar='\\', strict=True)
        for row in reader:
            if reader.line_num == 1:
                data.set_fields_from_csv(row)
                continue
            data.content.append(data.decode_csv_row(row, keep_empty))
        return data

    def set_fields_from_csv(self, csv_header):
        """Define the data fields from the given CSV header"""
        self.fields = collections.OrderedDict()
        for csv_field_name in csv_header:
            if csv_field_name not in CSV_TO_JSON_FIELDS:
                raise ValueError("Unknown CSV field %r" % csv_field_name)
            field_name, field_type = CSV_TO_JSON_FIELDS[csv_field_name]
            if field_name in self.fields:
                raise ValueError("Duplicate field %r (for %r)" % (field_name, csv_field_name))
            self.fields[field_name] = field_type

    def decode_csv_row(self, csv_row, keep_empty):
        """Decode a row of the CSV file"""
        if len(csv_row) != len(self.fields):
            raise ValueError(
                "CSV row of length %d not the length of fields (%d): %r" % (
                    len(csv_row), len(self.fields), csv_row))

        data_row = collections.OrderedDict()
        for field_name_type, value in zip(self.fields.items(), csv_row):
            field_name, field_type = field_name_type
            if not keep_empty and value == '':
                continue

            # Convert the value to the field type
            if field_type is None:
                pass
            else:
                try:
                    value = field_type.decode(value)
                except ValueError as exc:
                    raise ValueError("Incompatible value for field %r (%r): %r" % (field_name, field_type, value))

            # Decode name parts
            data_directory = data_row
            while '.' in field_name:
                dir_name, field_name = field_name.split('.', 1)
                if dir_name not in data_directory:
                    data_directory[dir_name] = collections.OrderedDict()
                data_directory = data_directory[dir_name]
            data_directory[field_name] = value
        return data_row

    def json_dump(self, fp, **kwargs):
        """Dump all the JSON data"""
        json.dump(self.content, fp, **kwargs)


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
