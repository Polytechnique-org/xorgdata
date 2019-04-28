# -*- coding: utf-8 -*-
"""Import data from a full export from AlumnForce website"""
import datetime
import os.path
import re

from django.core.management.base import BaseCommand, CommandError

from xorgdata.alumnforce import models
from xorgdata.alumnforce.full_export.lib.converters import AlumnForceDataC2J

from .importcsv import parse_french_date


def get_export_date_from_filename(file_path):
    """Return the date a file has been exported from the website, from its path

    Example of path: export-users-20190204-133700.csv
    """
    file_name = os.path.basename(file_path)
    match = re.match(r'.*-([0-9]{4})([0-9]{2})([0-9]{2})-[0-9]{6}\.csv$', file_name)
    if match:
        year, month, day = match.groups()
        return datetime.date(year=int(year), month=int(month), day=int(day))
    return None


class Command(BaseCommand):
    help = "Import data from a full export of users from AlumnForce database"

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str,
                            help="path to CSV file to load")
        parser.add_argument('--date', type=str,
                            help="date associate with the export (by default: use the file name)")

    def handle(self, *args, **options):
        file_path = options['csvfile']
        if options['date']:
            file_date = datetime.datetime.strptime(options['date'], '%Y-%m-%d').date()
            # Compare with a potential file date
            maybe_file_date = get_export_date_from_filename(file_path)
            if maybe_file_date and maybe_file_date != file_date:
                self.stdout.write(self.style.WARNING(
                    "Forcing date %s that mismatches with file date %s" %
                    (file_date, maybe_file_date)))
        else:
            file_date = get_export_date_from_filename(file_path)
            if not file_date:
                raise CommandError("Unable to find a date in file path %r" % file_path)

        # Track users in order to find out those which have been deleted
        deleted_account_ids = set(account.af_id for account in models.Account.objects.filter(deleted_since=None))

        # Import the file as a JSON structure
        json_obj = AlumnForceDataC2J.import_csv_file(file_path, keep_empty=True)
        for user_data in json_obj.content:
            # Prepare a dict for insertion into the Django database
            af_id = int(user_data['id_af'])
            fields = {
                'ax_id': user_data['id_ax'] or None,
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'common_name': user_data['usage_name'],
                'civility': user_data['civility'],
                'birthdate': parse_french_date(user_data['birth_date']),
                'address_1': user_data['personal']['address']['line_1'],
                'address_2': user_data['personal']['address']['line_2'],
                'address_3': user_data['personal']['address']['line_3'],
                'address_4': user_data['personal']['address']['line_4'],
                'address_postcode': user_data['personal']['address']['code'],
                'address_city': user_data['personal']['address']['city'],
                'address_state': user_data['personal']['address']['state'],
                'address_country': user_data['personal']['address']['country'],
                'address_npai': user_data['personal']['address']['bounced'],
                'phone_personnal': user_data['personal']['fix_phone'],
                'phone_mobile': user_data['personal']['cell_phone'],
                'email_1': user_data['email']['personal_1'],
                'email_2': user_data['email']['personal_2'],
                'nationality': user_data['nationality'],
                'nationality_2': user_data['nationality_2'],
                'nationality_3': user_data['nationality_3'],
                'dead': user_data['is_dead'],
                'deathdate': parse_french_date(user_data['death_date']),
                'dead_for_france': user_data['dead_for_france'],
                'user_kind': user_data['user_kind'],
                'additional_roles': '',
                'xorg_id': user_data['xorg']['login'] or None,
                'school_id': user_data['school']['id'],
                'admission_path': user_data['school']['input'],
                'cursus_domain': user_data['school']['domain'],
                'cursus_name': user_data['school']['name'],
                'corps_current': user_data['corps']['current'],
                'corps_origin': user_data['corps']['original'],
                'corps_grade': user_data['corps']['grade'],
                'nickname': user_data['nickname'],
                'sport_section': user_data['school']['sport'],
                'binets': ','.join(user_data['school']['binets'] or []),
                'mail_reception': user_data['has_postal_mail'],
                'newsletter_inscriptions': ','.join(user_data['newsletters'] or []),
                'last_update': file_date,
                'deleted_since': None,
            }
            if fields['civility'] == 'M.':
                # Normalize civility, in order to share the same format as incremental exports
                fields['civility'] = 'M'
            if fields['school_id'] == '0':
                # Normalize school ID
                fields['school_id'] = ''

            for key in ('nationality', 'nationality_2', 'nationality_3'):
                # Make an unfilled field blank
                if fields[key] == 'Non renseigné':
                    fields[key] = ''

            if user_data['roles']:
                # Format the additional roles as a list of integers
                fields['additional_roles'] = ','.join(user_data['roles'])
            models.Account.objects.update_or_create(af_id=af_id, defaults=fields)
            if af_id in deleted_account_ids:
                deleted_account_ids.remove(af_id)

        num_users = len(json_obj.content)
        message = "Loaded {} values from full export {}".format(num_users, repr(file_path))

        if deleted_account_ids:
            message += " ({} deleted users)".format(len(deleted_account_ids))
            for account in models.Account.objects.filter(af_id__in=deleted_account_ids):
                account.deleted_since = file_date
                account.save()

        self.stdout.write(self.style.SUCCESS(message))
        models.ImportLog.objects.create(
            date=file_date,
            export_kind='users',
            is_incremental=False,
            error=models.ImportLog.SUCCESS,
            num_modified=num_users,
            message=message,
        )
