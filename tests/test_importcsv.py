from pathlib import Path
import re

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO


TEST_CSV_FILES = (
    'exportusers-afbo-Polytechnique-X-20010203.csv',
    'exportuserdegrees-afbo-Polytechnique-X-20010203.csv',
    'exportuserjobs-afbo-Polytechnique-X-20010203.csv',
    'exportgroups-afbo-Polytechnique-X-20010203.csv',
    'exportgroupmembers-afbo-Polytechnique-X-20010203.csv',
)


class ImportCsvTests(TestCase):
    """Test importing several CSV files"""
    def setUp(self):
        csv_dirpath = Path(__file__).parent / 'files'
        self.csv_files = [csv_dirpath / file_name for file_name in TEST_CSV_FILES]

    def test_importcsv_verbose(self):
        for file_path in self.csv_files:
            out = StringIO()
            call_command('importcsv', file_path, stdout=out)
            num_error_lines = 0
            for out_line in out.getvalue().splitlines():
                # Remove color escape sequences
                line = out_line.replace('\x1b[32;1m', '').replace('\x1b[0m', '')
                if re.match(r"^Loaded [0-9]+ values from \S+ '.*'$", line):
                    continue
                else:  # pragma: no cover
                    # Display the errors
                    num_error_lines += 1
                    print(out_line)
            self.assertEqual(num_error_lines, 0)

    def test_importcsv_quiet(self):
        for file_path in self.csv_files:
            out = StringIO()
            call_command('importcsv', file_path, stdout=out, verbosity=0)
            self.assertEqual(out.getvalue(), '')
