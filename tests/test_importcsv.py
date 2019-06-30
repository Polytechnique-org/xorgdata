import collections
import datetime
from pathlib import Path
import re

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from xorgdata.alumnforce.models import Account, Group, ImportLog


TEST_CSV_FILES = (
    ('users', 'exportusers-afbo-Polytechnique-X-20010203.csv'),
    ('userdegrees', 'exportuserdegrees-afbo-Polytechnique-X-20010203.csv'),
    ('userjobs', 'exportuserjobs-afbo-Polytechnique-X-20010203.csv'),
    ('groups', 'exportgroups-afbo-Polytechnique-X-20010203.csv'),
    ('groupmembers', 'exportgroupmembers-afbo-Polytechnique-X-20010203.csv'),
)
TEST_CSV_PATHS = collections.OrderedDict(
    (kind, Path(__file__).parent / 'files' / file_name)
    for kind, file_name in TEST_CSV_FILES
)


class ImportCsvTests(TestCase):
    """Test importing several CSV files"""
    def test_importcsv_verbose(self):
        for kind, file_path in TEST_CSV_PATHS.items():
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

            # Ensure the import is logged correctly
            import_log = ImportLog.objects.get(export_kind=kind)
            self.assertEqual(import_log.date, datetime.date(2001, 2, 3))
            self.assertEqual(import_log.export_kind, kind)
            self.assertEqual(import_log.is_incremental, True)
            self.assertEqual(import_log.error, ImportLog.SUCCESS)
            self.assertGreater(import_log.num_modified, 0)
            self.assertNotEqual(import_log.message, '')

    def test_importcsv_quiet(self):
        for file_path in TEST_CSV_PATHS.values():
            out = StringIO()
            call_command('importcsv', file_path, stdout=out, verbosity=0)
            self.assertEqual(out.getvalue(), '')

    def test_importcsv_with_kind(self):
        for kind, file_path in TEST_CSV_PATHS.items():
            out = StringIO()
            call_command('importcsv', '--kind=' + kind, file_path, stdout=out, verbosity=0)
            self.assertEqual(out.getvalue(), '')

            # Ensure the import is logged correctly
            import_log = ImportLog.objects.get(export_kind=kind)
            self.assertEqual(import_log.date, datetime.date(2001, 2, 3))
            self.assertEqual(import_log.export_kind, kind)
            self.assertEqual(import_log.is_incremental, True)
            self.assertEqual(import_log.error, ImportLog.SUCCESS)
            self.assertGreater(import_log.num_modified, 0)
            self.assertNotEqual(import_log.message, '')

    def test_import_csv_user(self):
        # Ensure that the test user did not exist beforehand, in the test database
        self.assertEqual(Account.objects.filter(xorg_id='louis.vaneau.1829').count(), 0)
        self.assertEqual(Account.objects.filter(af_id=1).count(), 0)

        # Import the test user and test the result
        call_command('importcsv', TEST_CSV_PATHS['users'], verbosity=0)
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
        self.assertEqual(user.profile_picture_url, 'https://ax.polytechnique.org/medias/profile/42.jpeg')
        self.assertEqual(user.last_update, datetime.date(2001, 2, 3))
        self.assertEqual(user.deleted_since, None)

        # Import its studies and test the result
        self.assertEqual(user.degrees.count(), 0)
        call_command('importcsv', TEST_CSV_PATHS['userdegrees'], verbosity=0)
        user.refresh_from_db()
        self.assertEqual(user.degrees.count(), 1)
        user_degree = user.degrees.all()[0]
        self.assertEqual(user_degree.account, user)
        self.assertEqual(user_degree.diploma_reference, '1')
        self.assertEqual(user_degree.diplomed, True)
        self.assertEqual(user_degree.diplomation_date, datetime.date(1829, 1, 1))
        self.assertEqual(user_degree.cycle, '')
        self.assertEqual(user_degree.domain, '')
        self.assertEqual(user_degree.name, 'Ingénieur')
        self.assertEqual(user_degree.last_update, datetime.date(2001, 2, 3))

        # Import its jobs and test the result
        self.assertEqual(user.jobs.count(), 0)
        call_command('importcsv', TEST_CSV_PATHS['userjobs'], verbosity=0)
        user.refresh_from_db()
        self.assertEqual(user.jobs.count(), 2)
        user_job = user.jobs.all()[0]
        self.assertEqual(user_job.account, user)
        self.assertEqual(user_job.title, 'Emploi numéro 1')
        self.assertEqual(user_job.role, 'Fonction 1')
        self.assertEqual(user_job.company_name, 'Une Entreprise Exemplaire')
        self.assertEqual(user_job.address_1, 'rue Quelconque')
        self.assertEqual(user_job.address_2, '')
        self.assertEqual(user_job.address_3, '')
        self.assertEqual(user_job.address_4, '')
        self.assertEqual(user_job.address_postcode, '75000')
        self.assertEqual(user_job.address_city, 'Paris')
        self.assertEqual(user_job.address_country, 'FR')
        self.assertEqual(user_job.phone_indicator, None)
        self.assertEqual(user_job.phone_number, '01 00 00 00 00')
        self.assertEqual(user_job.mobile_phone_indicator, None)
        self.assertEqual(user_job.mobile_phone_number, '06 00 00 00 00')
        self.assertEqual(user_job.fax, '')
        self.assertEqual(user_job.email, 'louis.vaneau@example.org')
        self.assertEqual(user_job.start_date, datetime.date(1820, 1, 1))
        self.assertEqual(user_job.end_date, datetime.date(1821, 1, 1))
        self.assertEqual(user_job.contract_kind, 'CDI')
        self.assertEqual(user_job.current, True)
        self.assertEqual(user_job.creator_of_company, False)
        self.assertEqual(user_job.buyer_of_company, False)
        self.assertEqual(user_job.last_update, datetime.date(2001, 2, 3))

        user_job = user.jobs.all()[1]
        self.assertEqual(user_job.account, user)
        self.assertEqual(user_job.title, 'Emploi numéro 2')
        self.assertEqual(user_job.role, 'Fonction 2')
        self.assertEqual(user_job.company_name, 'Une Seconde Entreprise Exemplaire')
        self.assertEqual(user_job.address_1, 'avenue Quelconque')
        self.assertEqual(user_job.address_2, '')
        self.assertEqual(user_job.address_3, '')
        self.assertEqual(user_job.address_4, '')
        self.assertEqual(user_job.address_postcode, '75000')
        self.assertEqual(user_job.address_city, 'Paris')
        self.assertEqual(user_job.address_country, 'FR')
        self.assertEqual(user_job.phone_indicator, 33)
        self.assertEqual(user_job.phone_number, '01 00 00 00 00')
        self.assertEqual(user_job.mobile_phone_indicator, 33)
        self.assertEqual(user_job.mobile_phone_number, '06 00 00 00 00')
        self.assertEqual(user_job.fax, '')
        self.assertEqual(user_job.email, 'louis.vaneau@example.net')
        self.assertEqual(user_job.start_date, datetime.date(1819, 1, 1))
        self.assertEqual(user_job.end_date, datetime.date(1820, 1, 1))
        self.assertEqual(user_job.contract_kind, 'CDI')
        self.assertEqual(user_job.current, False)
        self.assertEqual(user_job.creator_of_company, False)
        self.assertEqual(user_job.buyer_of_company, False)
        self.assertEqual(user_job.last_update, datetime.date(2001, 2, 3))

    def test_import_csv_group(self):
        # Ensure that the test user and group did not exist beforehand, in the test database
        self.assertEqual(Account.objects.filter(xorg_id='louis.vaneau.1829').count(), 0)
        self.assertEqual(Account.objects.filter(af_id=1).count(), 0)
        self.assertEqual(Group.objects.filter(af_id=1).count(), 0)
        call_command('importcsv', TEST_CSV_PATHS['users'], verbosity=0)
        call_command('importcsv', TEST_CSV_PATHS['groups'], verbosity=0)
        user = Account.objects.get(af_id=1)
        self.assertIsNotNone(user)
        group = Group.objects.get(af_id=1)
        self.assertIsNotNone(group)
        self.assertEqual(group.af_id, 1)
        self.assertEqual(group.ax_id, 'AF_1')
        self.assertEqual(group.url, 'https://ax.polytechnique.org/group/GroupeUnit%C3%A9/1')
        self.assertEqual(group.name, 'Groupe Unité')
        self.assertEqual(group.category, 'Acteurs de la communauté')
        self.assertEqual(group.last_update, datetime.date(2001, 2, 3))

        # Import group memberships
        self.assertEqual(user.group_memberships.count(), 0)
        self.assertEqual(group.memberships.count(), 0)
        call_command('importcsv', TEST_CSV_PATHS['groupmembers'], verbosity=0)
        self.assertEqual(user.group_memberships.count(), 2)
        self.assertEqual(group.memberships.count(), 1)

        membership = user.group_memberships.get(group=group)
        self.assertEqual(membership.account, user)
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.role, 'member')
        self.assertEqual(membership.last_update, datetime.date(2001, 2, 3))
