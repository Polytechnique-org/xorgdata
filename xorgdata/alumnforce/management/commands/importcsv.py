# -*- coding: utf-8 -*-
"""Parse data from AlumnForce CSV exports, in order to import them"""

import csv
import os.path
import re

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from xorgdata.alumnforce import models


def bool_or_none(txt):
    if txt == '':
        return None
    else:
        return bool(int(txt))


def int_or_none(txt):
    if txt == '':
        return None
    else:
        return int(txt)


# Mapping from CSV columns to database fields
ALUMNFORCE_USER_FIELDS = {
    'Identifiant AF': ('af_id', int),
    'Identifiant école': ('ax_id', str),
    'Prénom': ('first_name', str),
    'Nom d\'état civil': ('last_name', str),
    'Nom d\'usage': ('common_name', str),
    'Civilité': ('civility', str),
    'Date de naissance': ('birthdate', parse_date),
    'Adresse personnelle - Ligne 1': ('address_1', str),
    'Adresse personnelle - Ligne 2': ('address_2', str),
    'Adresse personnelle - Ligne 3': ('address_3', str),
    'Adresse personnelle - Ligne 4': ('address_4', str),
    'Adresse personnelle - Code Postal': ('address_postcode', str),
    'Adresse personnelle - Ville': ('address_city', str),
    'Adresse personnelle - État': ('address_state', str),
    'Adresse personnelle - Pays': ('address_country', str),
    'NPAI': ('address_npai', bool_or_none),
    'Téléphone fixe personnel': ('phone_personnal', str),
    'Téléphone mobile personnel': ('phone_mobile', str),
    'Email personnel 1': ('email_1', str),
    'Email personnel 2': ('email_2', str),
    'Nationalité': ('nationality', str),
    'Décédé': ('dead', bool_or_none),
    'Date de décès': ('deathdate', parse_date),
    'Type d\'utilisateur': ('user_kind', int),
    'Rôles supplémentaires': ('additional_roles', int_or_none),
    'Login X.org': ('xorg_id', str),
    'Matricule école': ('school_id', str),
    'Voie d\'entrée': ('admission_path', str),
    'Domaine du cursus': ('cursus_domain', str),
    'Intitulé du cursus': ('cursus_name', str),
    'Corps actuel': ('corps_current', str),
    'Corps d\'origine': ('corps_origin', str),
    'Grade': ('corps_grade', str),
    'Surnom': ('nickname', str),
    'Seconde nationalité': ('nationality_2', str),
    'Troisième nationalité': ('nationality_3', str),
    'Mort pour la france': ('dead_for_france', str),
    'Sections sportive à l’X': ('sport_section', str),
    'Ex-binets': ('binets', str),
    'Réception courrier': ('mail_reception', str),
    'Inscription aux newsletters': ('newsletter_inscriptions', str),
    'URL de la photo de profil': ('profile_picture_url', str),
}


# Kind of export file
KNOWN_EXPORT_KINDS = frozenset((
    'groupmembers',
    'groups',
    'userdegrees',
    'userjobs',
    'users',
))


def get_export_kind_from_filename(file_path):
    """Return the kind of a file from its path

    Example of path: downloads/ftp/exportusers-afbo-Polytechnique-X-20190323.csv
    """
    file_name = os.path.basename(file_path)
    matches = re.match(r'^export([a-z]+)-afbo[^.]*.csv$', file_name)
    if matches is not None:
        kind = matches.group(1)
        if kind not in KNOWN_EXPORT_KINDS:
            raise ValueError("unknown export kind %r" % kind)
        return kind
    return None


def load_csv(csv_file_path, fields):
    with open(csv_file_path, 'r', encoding='utf-8') as csv_stream:
        reader = csv.reader(csv_stream, delimiter='\t', quotechar='"', escapechar='\\', strict=True)
        header_row = []
        convertions = []
        for row in reader:
            if reader.line_num == 1:
                # Parse the header line
                for col_name in row:
                    # Use the `fields` translation if it is known, otherwise the column name
                    header_row.append(fields.get(col_name, col_name)[0])
                    convertions.append(fields.get(col_name, col_name)[1])

                # Sanity check
                assert len(set(header_row)) == len(header_row), \
                    "There are columns which are not unique in {}".format(csv_file_path)
                continue

            assert len(row) == len(header_row), \
                "The CSV line {} has a different length from the header".format(reader.line_num)
            # convert the values as appropriate
            row = [conv(val) for (val, conv) in zip(row, convertions)]
            yield dict(zip(header_row, row))


class Command(BaseCommand):
    help = "Import a CSV file with accounts data into the database"

    def add_arguments(self, parser):
        parser.add_argument('-k', '--kind', type=str, choices=KNOWN_EXPORT_KINDS,
                            help="Kind of csv filed to load")
        parser.add_argument('csvfile', nargs='+', type=str,
                            help="path to CSV file to load")

    def handle(self, *args, **options):
        for file_path in options['csvfile']:
            try:
                file_kind = get_export_kind_from_filename(file_path)
            except ValueError as exc:
                # Forward the exception if there is no default value
                if not options['kind']:
                    raise CommandError(str(exc))
                file_kind = None

            if not file_kind:
                if not options['kind']:
                    raise CommandError(
                        "Unable to find the kind of %r, use --kind option" % file_path)
                file_kind = options['kind']
            elif options['kind'] and file_kind != options['kind']:
                raise CommandError(
                    "Incompatible kind for file %r: %r != %r" % (
                        file_path, file_kind, options['kind']))

            if file_kind == "users":
                for value in load_csv(file_path, ALUMNFORCE_USER_FIELDS):
                        models.Account.objects.update_or_create(af_id=value['af_id'], defaults=value)
                self.stdout.write(self.style.SUCCESS("Loaded values from users %r" % file_path))
            elif file_kind == "userdegrees":
                pass
            elif file_kind == "userjobs":
                pass
            elif file_kind == "groups":
                pass
            elif file_kind == "groupmembers":
                pass
            else:
                raise CommandError("Unknown kind %r" % file_kind)
