# -*- coding:UTF-8 -*-
import collections
import csv
import json

from .csv_format import ALUMNFORCE_FIELDS


CSV_TO_JSON_FIELDS = dict((x[0], (x[1], x[2])) for x in ALUMNFORCE_FIELDS)
assert len(ALUMNFORCE_FIELDS) == len(CSV_TO_JSON_FIELDS)

JSON_TO_CSV_FIELDS = dict((x[1], (x[0], x[2], i)) for i, x in enumerate(ALUMNFORCE_FIELDS))
assert len(ALUMNFORCE_FIELDS) == len(JSON_TO_CSV_FIELDS)


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
                except ValueError:
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
