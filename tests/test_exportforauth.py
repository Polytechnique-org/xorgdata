import json

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from .test_importcsv import TEST_CSV_PATHS
from xorgdata.alumnforce.models import Account


class ExportForAuthTests(TestCase):

    def test_exportforauth(self):
        # Start by populating the database
        for file_path in TEST_CSV_PATHS.values():
            call_command('importcsv', file_path, verbosity=0)

        # Export the database
        out = StringIO()
        call_command('exportforauth', stdout=out)
        exported_data = json.loads(out.getvalue())
        self.assertEqual(exported_data, [
            {
                'xorg_id': 'louis.vaneau.1829',
                'af_id': 1,
                'ax_contributor': False,
                'axjr_subscribed': False,
                'last_updated': '2001-02-03',
            }
        ])

        # Change the role of the user and verify that it gets propagated in the export
        account = Account.objects.get(af_id=1)
        account.additional_roles = '2,5'  # graduated, contributor
        account.save()
        out = StringIO()
        call_command('exportforauth', stdout=out)
        exported_data = json.loads(out.getvalue())
        self.assertEqual(exported_data[0]['af_id'], 1)
        self.assertEqual(exported_data[0]['ax_contributor'], True)
        self.assertEqual(exported_data[0]['axjr_subscribed'], False)

        account.additional_roles = '5,7,17'  # contributor, student, subscribed
        account.save()
        out = StringIO()
        call_command('exportforauth', stdout=out)
        exported_data = json.loads(out.getvalue())
        self.assertEqual(exported_data[0]['af_id'], 1)
        self.assertEqual(exported_data[0]['ax_contributor'], True)
        self.assertEqual(exported_data[0]['axjr_subscribed'], True)
