import datetime
from pathlib import Path
import re

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from xorgdata.alumnforce.models import Account


class ImportAllUsersTests(TestCase):
    """Test importing a full dump of the users"""
    def setUp(self):
        csv_dirpath = Path(__file__).parent / 'files'
        self.csv_file = csv_dirpath / 'export-users-20010203-040506.csv'

    @staticmethod
    def count_error_lines_from_stdout(out):
        num_error_lines = 0
        for out_line in out.getvalue().splitlines():
            # Remove color escape sequences
            line = out_line.replace('\x1b[32;1m', '').replace('\x1b[0m', '')
            if re.match(r"^Loaded 2 values from full export '", line):
                continue
            else:  # pragma: no cover
                # Display the errors
                num_error_lines += 1
                print(out_line)
        return num_error_lines

    def test_import_all_users(self):
        out = StringIO()
        call_command('importallusers', self.csv_file, stdout=out)
        self.assertEqual(self.count_error_lines_from_stdout(out), 0)

        # Ensure the loaded data is correct
        user = Account.objects.get(af_id=1)
        self.assertIsNotNone(user)
        self.assertEqual(user.af_id, 1)
        self.assertEqual(user.ax_id, None)
        self.assertEqual(user.first_name, 'admin')
        self.assertEqual(user.last_name, '')
        self.assertEqual(user.common_name, 'alumnforce')
        self.assertEqual(user.civility, '')
        self.assertEqual(user.birthdate, None)
        self.assertEqual(user.address_1, 'appt du Test')
        self.assertEqual(user.address_2, 'rue du Test')
        self.assertEqual(user.address_3, '')
        self.assertEqual(user.address_4, '')
        self.assertEqual(user.address_postcode, '75000')
        self.assertEqual(user.address_city, 'Paris')
        self.assertEqual(user.address_state, '')
        self.assertEqual(user.address_country, 'FR')
        self.assertEqual(user.address_npai, False)
        self.assertEqual(user.phone_personnal, '')
        self.assertEqual(user.phone_mobile, '')
        self.assertEqual(user.email_1, 'noreply@alumnforce.com')
        self.assertEqual(user.email_2, '')
        self.assertEqual(user.nationality, '')
        self.assertEqual(user.nationality_2, '')
        self.assertEqual(user.nationality_3, '')
        self.assertEqual(user.dead, False)
        self.assertEqual(user.deathdate, None)
        self.assertEqual(user.dead_for_france, '')
        self.assertEqual(user.user_kind, 3)
        self.assertEqual(user.additional_roles, '2,3,5')
        self.assertEqual(user.xorg_id, 'admin.alumnforce')
        self.assertEqual(user.school_id, '')
        self.assertEqual(user.admission_path, '')
        self.assertEqual(user.cursus_domain, '')
        self.assertEqual(user.cursus_name, '')
        self.assertEqual(user.corps_current, '')
        self.assertEqual(user.corps_origin, '')
        self.assertEqual(user.corps_grade, '')
        self.assertEqual(user.nickname, 'AlumnForce')
        self.assertEqual(user.sport_section, '')
        self.assertEqual(user.binets, '')
        self.assertEqual(user.mail_reception, '')
        self.assertEqual(user.newsletter_inscriptions, '')
        self.assertEqual(user.profile_picture_url, '')
        self.assertEqual(user.last_update, datetime.date(2001, 2, 3))
        self.assertEqual(user.deleted_since, None)

        user = Account.objects.get(af_id=2)
        self.assertIsNotNone(user)
        self.assertEqual(user.af_id, 2)
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
        self.assertEqual(user.nationality_2, '')
        self.assertEqual(user.nationality_3, '')
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
        self.assertEqual(user.profile_picture_url, '')
        self.assertEqual(user.last_update, datetime.date(2001, 2, 3))
        self.assertEqual(user.deleted_since, None)

    def test_delete_user(self):
        # Create a user which will be destroyed
        account = Account.objects.create(
            af_id=123456,
            user_kind=1,
            last_update=datetime.date(2001, 2, 3))
        self.assertEqual(account.deleted_since, None)

        # Load exported data
        out = StringIO()
        call_command('importallusers', self.csv_file, stdout=out)
        self.assertEqual(self.count_error_lines_from_stdout(out), 0)

        # Check whether the account has been marked as deleted
        account.refresh_from_db()
        self.assertEqual(account.deleted_since, datetime.date(2001, 2, 3))
        self.assertEqual(Account.objects.filter(deleted_since=datetime.date(2001, 2, 3)).count(), 1)
