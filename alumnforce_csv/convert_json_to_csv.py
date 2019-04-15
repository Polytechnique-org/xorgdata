#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
"""Convert a JSON file to a CSV file to be imported on AlumnForce website

This is the reciprocal of convert_csv_to_json.py.
"""
import argparse
import csv
import json
import sys

from csv_format import ALUMNFORCE_FIELDS


JSON_TO_CSV_FIELDS = dict((x[1], (x[0], x[2], i)) for i, x in enumerate(ALUMNFORCE_FIELDS))
assert len(ALUMNFORCE_FIELDS) == len(JSON_TO_CSV_FIELDS)


class AlumnForceDataJ2C(object):
    """Data extracted from a JSON to produce data importted on AlumnForce website"""
    def __init__(self):
        self.fields = set()
        # content is a list of dicts "json field"->value
        self.content = []

    @classmethod
    def import_json_file(cls, json_file_path):
        """Create AlumnForce data from a JSON file"""
        with open(json_file_path, 'r') as json_stream:
            return cls.import_json_stream(json_stream)

    @classmethod
    def import_json_stream(cls, json_file):
        """Create AlumnForce data from a JSON stream"""
        data = cls()
        for record in json.load(json_file):
            flat_record = data.flatten_json_fields(record)
            for record_val in flat_record:
                if record_val[0] not in data.fields:
                    data.fields.add(record_val[0])
            data.content.append(dict(flat_record))
        return data

    @classmethod
    def flatten_json_fields(cls, json_record, prefixkey=None):
        result = []
        for key, value in json_record.items():
            fullkey = (prefixkey + key) if prefixkey else key
            field_properties = JSON_TO_CSV_FIELDS.get(fullkey)
            if field_properties is not None:
                if field_properties[1] is not None:
                    # Encode the JSON value to CSV
                    value = field_properties[1].encode(value)
                result.append((fullkey, value))
            elif isinstance(value, dict):
                # sub-dict
                result += cls.flatten_json_fields(value, fullkey + '.')
            else:
                raise ValueError("Unknown json field %r" % fullkey)
        return result

    def csv_dump(self, csv_file, **kwargs):
        """Dump all the CSV data"""
        # Sort the fields by their rank in ALUMNFORCE_FIELDS
        columns = sorted(self.fields, key=lambda f: JSON_TO_CSV_FIELDS[f][2])
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', escapechar='\\', quoting=csv.QUOTE_MINIMAL)
        writer.writerow((JSON_TO_CSV_FIELDS[f][0] for f in columns))
        for row in self.content:
            writer.writerow(row.get(f) for f in columns)


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
