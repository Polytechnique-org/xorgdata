# -*- coding: utf-8 -*-
"""Parse data from AlumnForce CSV exports, in order to import them"""

import csv
import datetime
import os.path
import re

from django.core.management.base import BaseCommand, CommandError

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


FRENCH_DATE_RE = re.compile(r'(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})$')


def parse_date(value):
    # Copy from django.utils.dateparse which supports dates in French format
    if not value:
        return None
    match = FRENCH_DATE_RE.match(value)
    if match:
        kw = {k: int(v) for k, v in match.groupdict().items()}
        return datetime.date(**kw)
    raise ValueError("Unknown date format (%r)" % value)


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
ALUMNFORCE_USERDEGREE_FIELDS = {
    'Identifiant AF': ('af_id', int),
    'Identifiant école': ('ax_id', str),
    'Référence du diplôme': ('diploma_reference', str),
    'A obtenu son diplôme ?': ('diplomed', bool_or_none),
    'Date d\'obtention du diplôme': ('diplomation_date', parse_date),
    'Mode de formation': ('domain', str),
    'Cycle': ('name', str),
}
ALUMNFORCE_USERJOB_FIELDS = {
    'Identifiant AF': ('af_id', int),
    'Identifiant école': ('ax_id', str),
    'Titre du poste': ('title', str),
    'Fonction dans l\'entreprise': ('role', str),
    'Nom de l\'entreprise': ('company_name', str),
    'Adresse professionnelle - Ligne 1': ('address_1', str),
    'Adresse professionnelle - Ligne 2': ('address_2', str),
    'Adresse professionnelle - Ligne 3': ('address_3', str),
    'Adresse professionnelle - Ligne 4': ('address_4', str),
    'Adresse professionnelle - Code postal': ('address_postcode', str),
    'Adresse professionnelle - Ville': ('address_city', str),
    'Adresse professionnelle - Pays': ('address_country', str),
    'Indicateur téléphone fixe professionnel': ('phone_indicator', int_or_none),
    'Téléphone fixe professionnel': ('phone_number', str),
    'Indicateur téléphone mobile professionnel': ('mobile_phone_indicator', int_or_none),
    'Téléphone mobile professionnel': ('mobile_phone_number', str),
    'Fax professionnel': ('fax', str),
    'Email professionnel': ('email', str),
    'Date de début de l\'expérience': ('start_date', parse_date),
    'Date de fin de l\'expérience': ('end_date', parse_date),
    'Type de contrat': ('contract_kind', str),
    'Poste actuel ?': ('current', bool_or_none),
    'J\'ai créé cette entreprise ?': ('creator_of_company', bool_or_none),
    'J\'ai repris cette entreprise ?': ('buyer_of_company', bool_or_none),
}
ALUMNFORCE_GROUP_FIELDS = {
    'Identifiant AF': ('af_id', int),
    'Matricule AX': ('ax_id', str),
    'URL du groupe': ('url', str),
    'Nom du groupe': ('name', str),
    'Catégorie du groupe': ('category', str),
}
ALUMNFORCE_GROUPMEMBER_FIELDS = {
    'Identifiant AF utilisateur': ('user_id', int),
    'Matricule AX': ('user_ax_id', str),
    'Identifiant AF groupe': ('group_id', int),
    'Rôle dans le groupe': ('role', str),
}
ALUMNFORCE_GROUPMEMBER_ROLES = {
    'banni': 'banned',
    'désinscrit': 'unsubscribed',
    'invité': 'invited',
    'membre': 'member',
    'modérateur': 'moderator',
    'responsable': 'responsible',
    'sur liste': 'onlist',
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
    match = re.match(r'^export([a-z]+)-afbo[^.]*.csv$', file_name)
    if match:
        kind = match.group(1)
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
                for value in load_csv(file_path, ALUMNFORCE_USERDEGREE_FIELDS):
                    try:
                        account = models.Account.objects.get(af_id=value['af_id'])
                    except models.Account.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            "Unable to find user with AF ID %d (AX ID %r)" % (value['af_id'], value['ax_id'])))
                    else:
                        del value['af_id']
                        del value['ax_id']
                        models.AcademicInformation.objects.update_or_create(account=account, defaults=value)
                self.stdout.write(self.style.SUCCESS("Loaded values from user degrees %r" % file_path))
            elif file_kind == "userjobs":
                for value in load_csv(file_path, ALUMNFORCE_USERJOB_FIELDS):
                    try:
                        account = models.Account.objects.get(af_id=value['af_id'])
                    except models.Account.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            "Unable to find user with AF ID %d (AX ID %r)" % (value['af_id'], value['ax_id'])))
                    else:
                        del value['af_id']
                        del value['ax_id']
                        models.ProfessionnalInformation.objects.update_or_create(account=account, defaults=value)
                self.stdout.write(self.style.SUCCESS("Loaded values from user jobs %r" % file_path))
            elif file_kind == "groups":
                for value in load_csv(file_path, ALUMNFORCE_GROUP_FIELDS):
                    models.Group.objects.update_or_create(af_id=value['af_id'], defaults=value)
                self.stdout.write(self.style.SUCCESS("Loaded values from groups %r" % file_path))
            elif file_kind == "groupmembers":
                for value in load_csv(file_path, ALUMNFORCE_GROUPMEMBER_FIELDS):
                    try:
                        account = models.Account.objects.get(af_id=value['user_id'])
                    except models.Account.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            "Unable to find user with AF ID %d (AX ID %r)" % (value['user_id'], value['user_ax_id'])))
                        continue
                    try:
                        group = models.Group.objects.get(af_id=value['group_id'])
                    except models.Group.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            "Unable to find group with AF ID %d" % value['group_id']))
                        continue
                    try:
                        role = ALUMNFORCE_GROUPMEMBER_ROLES[value['role']]
                    except KeyError:
                        self.stdout.write(self.style.WARNING(
                            "Unable to find group role %r" % value['role']))
                        continue
                    models.GroupMemberhip.objects.update_or_create(
                        account=account,
                        group=group,
                        defaults={'role': role},
                    )
                self.stdout.write(self.style.SUCCESS("Loaded values from group members %r" % file_path))
            else:
                raise CommandError("Unknown kind %r" % file_kind)
