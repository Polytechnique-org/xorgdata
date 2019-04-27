import collections
import datetime
from pathlib import Path
import re

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from xorgdata.alumnforce.models import Account


TEST_CSV_FILES = (
    ('users', 'exportusers-afbo-Polytechnique-X-20010203.csv'),
    ('userdegrees', 'exportuserdegrees-afbo-Polytechnique-X-20010203.csv'),
    ('userjobs', 'exportuserjobs-afbo-Polytechnique-X-20010203.csv'),
    ('groups', 'exportgroups-afbo-Polytechnique-X-20010203.csv'),
    ('groupmembers', 'exportgroupmembers-afbo-Polytechnique-X-20010203.csv'),
)


class ImportCsvTests(TestCase):
    """Test importing several CSV files"""
    def setUp(self):
        csv_dirpath = Path(__file__).parent / 'files'
        self.csv_files = collections.OrderedDict((kind, csv_dirpath / file_name) for kind, file_name in TEST_CSV_FILES)

    def test_importcsv_verbose(self):
        for kind, file_path in self.csv_files.items():
            out = StringIO()
            call_command('importcsv', file_path, stdout=out)
            num_error_lines = 0
            for out_line in out.getvalue().splitlines():
                # Remove color escape sequences
                line = out_line.replace('\x1b[32;1m', '').replace('\x1b[0m', '')
                if re.match(r"^Loaded [0-9]+ values from " + kind + " '.*'$", line):
                    continue
                else:  # pragma: no cover
                    # Display the errors
                    num_error_lines += 1
                    print(out_line)
            self.assertEqual(num_error_lines, 0)

    def test_importcsv_quiet(self):
        for file_path in self.csv_files.values():
            out = StringIO()
            call_command('importcsv', file_path, stdout=out, verbosity=0)
            self.assertEqual(out.getvalue(), '')

    def test_importcsv_with_kind(self):
        for kind, file_path in self.csv_files.items():
            out = StringIO()
            call_command('importcsv', '--kind=' + kind, file_path, stdout=out, verbosity=0)
            self.assertEqual(out.getvalue(), '')

    def test_import_csv_user(self):
        # Ensure that the test user did not exist beforehand, in the test database
        self.assertEqual(Account.objects.filter(xorg_id='louis.vaneau.1829').count(), 0)
        self.assertEqual(Account.objects.filter(af_id=1).count(), 0)

        # Import the test user and test the result
        call_command('importcsv', self.csv_files['users'], verbosity=0)
        user = Account.objects.get(af_id=1)
        self.assertIsNotNone(user)
        self.assertEqual(user.af_id, 1)
        self.assertEqual(user.ax_id, '18290001')
        self.assertEqual(user.first_name, 'Louis')
        self.assertEqual(user.last_name, 'Vaneau')
        self.assertEqual(user.common_name, 'Vaneau')
        self.assertEqual(user.civility, 'M')
        self.assertEqual(user.birthdate, datetime.date(1811, 3, 27))
        self.assertEqual(user.address_1, 'rue de Babylone')
        self.assertEqual(user.address_2, '')
        self.assertEqual(user.address_3, '')
        self.assertEqual(user.address_4, '')
        self.assertEqual(user.address_postcode, '75007')
        self.assertEqual(user.address_city, 'PARIS')
        self.assertEqual(user.address_state, '')
        self.assertEqual(user.address_country, 'FR')
        self.assertEqual(user.address_npai, False)
        self.assertEqual(user.phone_personnal, '06 00 00 00 00')
        self.assertEqual(user.phone_mobile, '06 00 00 00 00')
        self.assertEqual(user.email_1, 'louis.vaneau.1829@polytechnique.org')
        self.assertEqual(user.email_2, 'louis.vaneau.1829+ax@polytechnique.org')
        self.assertEqual(user.nationality, 'France')
        self.assertEqual(user.nationality_2, 'Non renseigné')  # TODO: make empty
        self.assertEqual(user.nationality_3, 'Non renseigné')
        self.assertEqual(user.dead, True)
        self.assertEqual(user.deathdate, datetime.date(1830, 7, 29))
        self.assertEqual(user.dead_for_france, '')
        self.assertEqual(user.user_kind, 1)
        self.assertEqual(user.additional_roles, '')
        self.assertEqual(user.xorg_id, 'louis.vaneau.1829')
        self.assertEqual(user.school_id, '18290001')
        self.assertEqual(user.admission_path, '')
        self.assertEqual(user.cursus_domain, '')
        self.assertEqual(user.cursus_name, '')
        self.assertEqual(user.corps_current, 'Aucun (anc. démissionnaire)')
        self.assertEqual(user.corps_origin, '')
        self.assertEqual(user.corps_grade, 'Aucun')
        self.assertEqual(user.nickname, '')
        self.assertEqual(user.sport_section, 'Escrime')
        self.assertEqual(user.binets, 'Binet Escrime')
        self.assertEqual(user.mail_reception, '')
        self.assertEqual(user.newsletter_inscriptions, 'Lettre mensuelle de Polytechnique.org,Lettre de la communauté')
        self.assertEqual(user.profile_picture_url, '/medias/profile/42.jpeg')
        self.assertEqual(user.last_update, datetime.date(2001, 2, 3))
