# -*- coding: utf-8 -*-
"""Parse data from AlumnForce CSV exports, in order to import them"""

import csv
import datetime
import os.path
import re
import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail

from xorgdata.alumnforce import models


def bool_or_none(txt):
    if txt == '':
        return None
    elif txt in ('0', '1'):
        return bool(int(txt))
    else:
        raise ValueError("invalid bool value {}".format(repr(txt)))


def int_or_none(txt):
    if txt == '':
        return None
    elif re.match(r'^[0-9]+$', txt):
        return int(txt)
    else:
        raise ValueError("invalid integer value: {}".format(repr(txt)))


def phone_indicator(txt):
    """A phone indicator is a number identifying a country.

    It may start with +, which is why int_or_none is not used.
    """
    if txt == '':
        return None
    elif re.match(r'^\+?[0-9]+$', txt):
        return int(txt)
    else:
        raise ValueError("invalid phone indicator value: {}".format(repr(txt)))


FRENCH_DATE_RE = re.compile(r'(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})$')


def parse_french_date(value):
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
    'Date de naissance': ('birthdate', parse_french_date),
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
    'Date de décès': ('deathdate', parse_french_date),
    'Type d\'utilisateur': ('user_kind', int),
    'Rôles supplémentaires': ('additional_roles', str),  # comma-separated integers
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
    'Date d\'obtention du diplôme': ('diplomation_date', parse_french_date),
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
    'Indicateur téléphone fixe professionnel': ('phone_indicator', phone_indicator),
    'Téléphone fixe professionnel': ('phone_number', str),
    'Indicateur téléphone mobile professionnel': ('mobile_phone_indicator', phone_indicator),
    'Téléphone mobile professionnel': ('mobile_phone_number', str),
    'Fax professionnel': ('fax', str),
    'Email professionnel': ('email', str),
    'Date de début de l\'expérience': ('start_date', parse_french_date),
    'Date de fin de l\'expérience': ('end_date', parse_french_date),
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
KNOWN_EXPORT_KINDS = frozenset(x[0] for x in models.ImportLog.KNOWN_EXPORT_KINDS)


def get_export_kind_from_filename(file_path):
    """Return the kind of a file from its path

    Example of path: downloads/ftp/exportusers-afbo-Polytechnique-X-20190323.csv
    """
    file_name = os.path.basename(file_path)
    match = re.match(r'^export([a-z]+)-afbo[^.]*\.csv$', file_name)
    if match:
        kind = match.group(1)
        if kind not in KNOWN_EXPORT_KINDS:
            raise ValueError("unknown export kind %r" % kind)
        return kind
    return None


def get_export_date_from_filename(file_path):
    """Return the date a file has been exported, from its path

    Example of path: downloads/ftp/exportusers-afbo-Polytechnique-X-20190323.csv
    """
    file_name = os.path.basename(file_path)
    match = re.match(r'.*([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])\.csv$', file_name)
    if match:
        year, month, day = match.groups()
        return datetime.date(year=int(year), month=int(month), day=int(day))
    return None


def compute_current_problem_file_path(kind, id):
    id_str = str(id)
    directory = os.path.join(
        settings.PERSISTENT_DIRECTORY,
        "current_problems_by_id",
        kind)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(
        directory,
        id_str + ".rej"
    )


def compute_problem_archive_file_path(kind, id, csv_file_path, state, account_str, hash):
    id_str = str(id)
    directory = os.path.join(
        settings.PERSISTENT_DIRECTORY,
        "problem_archive",
        kind)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(
        directory,
        "__".join([
            id_str,
            os.path.basename(csv_file_path),
            state,
            account_str,
            hash
        ]) + ".txt"
    )


# The CSV (actually tab-separated) files we receive from Alumnforce sometimes contain malformed
# lines.

# Previously, any malformed line would cause this import to fail with an exception, then the
# whole script to fail the same, no log in https://data.m4x.org/admin/alumnforce/importlog/ .
# Worse, the next run of this script would try the same file again and never advance to the next
# file, effectively blocking the whole import process until a developer fixes this.

# We want:
# - For clarity, whatever the file content, have a log in https://data.m4x.org/admin/alumnforce/importlog/ .
# - Malformed lines cause explicit log+mail, but do not prevent importing other good lines in the file.
# - For debugging, at any time the set of currently invalid lines (indexed by the first field AF_ID) is accessible (filesystem + mail)
# - To keep sync on, malformed lines do not prevent moving on to the next file when available.
# - When a newer file provides a valid fixed line for any AF_ID, the now obsolete incident is removed from the set of invalid lines.
# - An archive is kept of lines that caused an issue and line that fixed it.

# To properly record the various cases, we need a hash and an id.
# Most fields may end up malformed, so the most reliable ID is the first column: AF_ID.

# We need to detect when things are fixed, and record resolution for archival.
# How do we know things are fixed?

# One valid line for a user in a file is not always enough to consider the ID fixed.
# It is enough in the case of the 'users' kind. In this cas, the ID is the ID of the line.
# Other kind, `userdegrees` and `userjobs` require a "later" logic, which is suitable for all kinds.
# When a user has something changed on their degrees or jobs, all of these have to be transmitted (and they are).
# We can only consider things fixed *for this user* if all lines *of this user* in the same file are parsed okay.
# So, we wait for the whole file to be processed and only then we figure out which users are affected.
# For this reason, load_csv returns a tuple: a parse_report and the value.

def load_csv(kind, csv_file_path, fields):
    with open(csv_file_path, 'r', encoding='utf-8') as line_stream:
        all_lines = line_stream.readlines()

        reader = csv.reader(all_lines, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\', strict=True)
        header_row = []
        conversions = []
        for row in reader:
            if reader.line_num == 1:
                # Parse the header line
                for col_name in row:
                    # Use the `fields` translation if it is known, otherwise the column name
                    header_row.append(fields.get(col_name, col_name)[0])
                    conversions.append(fields.get(col_name, col_name)[1])

                # Sanity check
                assert len(set(header_row)) == len(header_row), \
                    "There are columns which are not unique in {}".format(csv_file_path)
                continue

            # Reader.line_num is indeed what we need, not a record count,
            # cf. https://docs.python.org/3/library/csv.html#csv.csvreader.line_num .
            # Also reader provides 1-based line number, other need zero-based, so subtract one.
            csv_raw_line_num = reader.line_num - 1
            csv_raw_line = all_lines[csv_raw_line_num]
            line_hash = hashlib.sha256(csv_raw_line.encode('utf-8')).hexdigest()

            account_label_for_filename = "unknown"
            problems = []
            af_id = None,
            parse_report = {
                "problems": problems,
                "af_id": af_id,
                "path": os.path.basename(csv_file_path),
                "header": header_row,
                "line_num": csv_raw_line_num,
                "line_hash": line_hash,
                "line": csv_raw_line,
                "line_tabs": csv_raw_line.replace('\t', '<TAB>'),
            }
            value = None
            try:
                assert len(row) == len(header_row), \
                    f"Line has {len(row)} items but the header has {len(header_row)} items."
                # convert the values as appropriate
                row = [conv(val) for (val, conv) in zip(row, conversions)]
                value = dict(zip(header_row, row))
                # first item in row is in all cases the AF_ID of an involved user, check this in ALUMNFORCE_*_FIELDS
                af_id = row[0]

            except (AssertionError, ValueError, KeyError) as exc:
                problems.append(exc)

                # There was a problem handling this line.
                # Time to extract what we can from the line.

                try:
                    # The pattern is to update the parse_report record with the most relevant message in case the next step fails.
                    # If we're interrupted at any point below, the error record will just
                    # remain with the last information.
                    failure = "cannot extract AF_ID"
                    if '\t' not in csv_raw_line:
                        failure = "no tab character"
                        raise Exception("No tab character")
                    # Alumnforce IDs are currently 5 figures, using 9 leave some room.
                    af_id_str = csv_raw_line.split('\t')[0][0:9]
                    af_id = int(af_id_str)

                except Exception as exc2:
                    problems.append(failure)
                    problems.append(exc2)

            parse_report['af_id'] = af_id
            yield (parse_report, value)


class Command(BaseCommand):
    help = "Import a CSV file with accounts data into the database"

    def add_arguments(self, parser):
        parser.add_argument('-k', '--kind', type=str, choices=KNOWN_EXPORT_KINDS,
                            help="Kind of csv filed to load")
        parser.add_argument('csvfile', nargs='+', type=str,
                            help="path to CSV file to load")

    def log_success(self, file_date, file_kind, num_values, file_path, facts):
        """Log a successful import"""
        message = "Loaded {} values from {} {}.".format(num_values, file_kind, repr(file_path))
        for fact in facts:
            message += f" {fact}."
        if self.verbosity:
            self.stdout.write(self.style.SUCCESS(message))
        models.ImportLog.objects.create(
            date=file_date,
            export_kind=file_kind,
            is_incremental=True,
            error=models.ImportLog.SUCCESS,
            num_modified=num_values,
            message=message,
        )

    def log_warning(self, file_date, file_kind, message):
        """Log a warning while processing an import"""
        if self.verbosity:
            self.stdout.write(self.style.WARNING(message))
        models.ImportLog.objects.create(
            date=file_date,
            export_kind=file_kind,
            is_incremental=True,
            error=models.ImportLog.XORG_ERROR,
            message=message,
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        timestamp_start = datetime.datetime.utcnow()

        kinds_involved_in_imported_files = set()
        parse_reports_by_kind = {}

        report_by_file_then_user = []
        problem_changes_all_files = {}
        resolved_to_be_also_in_report = []

        for file_path in options['csvfile']:
            file_date = get_export_date_from_filename(file_path)
            if not file_date:
                raise CommandError("Unable to find a date in file path %r" % file_path)

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

            kinds_involved_in_imported_files.add(file_kind)
            parse_reports_this_kind = []
            parse_reports_by_kind[file_kind] = parse_reports_this_kind

            if file_kind == "users":
                num_values = 0
                for (parse_report, value) in load_csv(file_kind, file_path, ALUMNFORCE_USER_FIELDS):
                    parse_reports_this_kind.append(parse_report)
                    if not value:
                        continue
                    value['last_update'] = file_date
                    value['deleted_since'] = None
                    for key in ('nationality', 'nationality_2', 'nationality_3'):
                        # Make an unfilled field blank
                        if value[key] == 'Non renseigné':
                            value[key] = ''
                    if value['school_id'] == '0':
                        value['school_id'] = ''
                    if value['xorg_id'] == '':
                        value['xorg_id'] = None
                    if value['profile_picture_url'].startswith('/'):
                        value['profile_picture_url'] = 'https://ax.polytechnique.org' + value['profile_picture_url']
                    models.Account.objects.update_or_create(af_id=value['af_id'], defaults=value)
                    num_values += 1
            elif file_kind == "userdegrees":
                num_values = 0
                seen_accounts = {}
                for (parse_report, value) in load_csv(file_kind, file_path, ALUMNFORCE_USERDEGREE_FIELDS):
                    parse_reports_this_kind.append(parse_report)
                    if not value:
                        continue
                    account = seen_accounts.get(value['af_id'])
                    if account is None:
                        try:
                            account = models.Account.objects.get(af_id=value['af_id'])
                        except models.Account.DoesNotExist:
                            self.log_warning(
                                file_date, file_kind,
                                "Unable to find user with AF ID {} (AX ID {})".format(
                                    value['af_id'], repr(value['ax_id'])
                                ))
                            continue
                        seen_accounts[value['af_id']] = account
                        # Remove previous degrees when an account is seen for the first time
                        account.degrees.all().delete()
                    # Insert a degree
                    del value['af_id']
                    del value['ax_id']
                    value['last_update'] = file_date
                    account.degrees.create(**value)
                    num_values += 1
            elif file_kind == "userjobs":
                num_values = 0
                seen_accounts = {}
                for (parse_report, value) in load_csv(file_kind, file_path, ALUMNFORCE_USERJOB_FIELDS):
                    parse_reports_this_kind.append(parse_report)
                    if not value:
                        continue
                    account = seen_accounts.get(value['af_id'])
                    if account is None:
                        try:
                            account = models.Account.objects.get(af_id=value['af_id'])
                        except models.Account.DoesNotExist:
                            self.log_warning(
                                file_date, file_kind,
                                "Unable to find user with AF ID {} (AX ID {})".format(
                                    value['af_id'], repr(value['ax_id'])
                                ))
                            continue
                        seen_accounts[value['af_id']] = account
                        # Remove previous jobs when an account is seen for the first time
                        account.jobs.all().delete()
                    # Insert a job
                    del value['af_id']
                    del value['ax_id']
                    value['last_update'] = file_date
                    account.jobs.create(**value)
                    num_values += 1
            elif file_kind == "groups":
                num_values = 0
                for (parse_report, value) in load_csv(file_kind, file_path, ALUMNFORCE_GROUP_FIELDS):
                    parse_reports_this_kind.append(parse_report)
                    if not value:
                        continue
                    value['last_update'] = file_date
                    models.Group.objects.update_or_create(af_id=value['af_id'], defaults=value)
                    num_values += 1
            elif file_kind == "groupmembers":
                num_values = 0
                for (parse_report, value) in load_csv(file_kind, file_path, ALUMNFORCE_GROUPMEMBER_FIELDS):
                    parse_reports_this_kind.append(parse_report)
                    if not value:
                        continue

                    try:
                        account = models.Account.objects.get(af_id=value['user_id'])
                    except models.Account.DoesNotExist:
                        self.log_warning(
                            file_date, file_kind,
                            "Unable to find user with AF ID {} (AX ID {})".format(
                                value['user_id'], repr(value['user_ax_id'])
                            ))
                        continue
                    try:
                        group = models.Group.objects.get(af_id=value['group_id'])
                    except models.Group.DoesNotExist:
                        self.log_warning(
                            file_date, file_kind,
                            "Unable to find group with AF ID {}".format(
                                value['group_id']
                            ))
                        continue
                    try:
                        role = ALUMNFORCE_GROUPMEMBER_ROLES[value['role']]
                    except KeyError:
                        self.log_warning(
                            file_date, file_kind,
                            "Unable to find group role {}".format(repr(value['role']))
                        )
                        continue
                    models.GroupMembership.objects.update_or_create(
                        account=account,
                        group=group,
                        defaults={'role': role, 'last_update': file_date},
                    )
                    num_values += 1
            else:
                raise CommandError("Unknown kind %r" % file_kind)

            # Here we have finished loaded all lines of one csv file.
            # Time to update the filesystem-based report.

            # Extract af_id that have problems and gather the matching parse reports

            reports_by_afid = {}
            for parse_report in parse_reports_this_kind:
                reports_by_afid.setdefault(parse_report['af_id'], []).append(parse_report)

            # Update records

            problem_changes_this_file = {}

            # These are not all users, only users referred to by imported data.
            for (af_id, reports) in reports_by_afid.items():
                try:
                    account = models.Account.objects.get(af_id=af_id)
                    account_label_for_filename = account.xorg_id
                    account_label_for_content = repr(account.xorg_id)
                except models.Account.DoesNotExist:
                    account_label_for_filename = "unknown"
                    account_label_for_content = f"pas de compte pour af_id={af_id}"

                current_problem_file_path = compute_current_problem_file_path(file_kind, af_id)
                user_was_affected = os.path.exists(current_problem_file_path)

                user_reports_with_problem = [r for r in reports if r["problems"]]

                user_is_affected = len(user_reports_with_problem) > 0
                # any(report["problems"] for report in reports)

                case_number = (user_was_affected << 1) | user_is_affected

                # will allow to summarize affected users and changes
                problem_changes_this_file.setdefault(case_number, []).append(account_label_for_content)
                problem_changes_all_files.setdefault(case_number, []).append(account_label_for_content)

                if user_is_affected:
                    print(
                        f"Recording current problem on user {account_label_for_content} with kind {file_kind}: {current_problem_file_path}")
                    with open(current_problem_file_path, "a") as rej_file:
                        rej_file.write(
                            f"### Soucis de type {file_kind} concernant le compte {account_label_for_content}\n\n")
                        for report in user_reports_with_problem:
                            rej_file.write(
                                "------------------------------------------------------------------------\n"
                                + "\n".join("{:<10}: {}".format(k, v) for k, v in report.items())
                                + "------------------------------------------------------------------------\n")
                else:
                    if user_was_affected:
                        print(f"Deleting rejection file: {current_problem_file_path}")
                        try:
                            os.remove(current_problem_file_path)
                        except OSError:
                            pass

                problem_archive_file_marker = [None, "problem_new", "resolved", "problem_still"][case_number]

                if problem_archive_file_marker:
                    lines_to_log = user_reports_with_problem
                    if problem_archive_file_marker == "resolved":
                        # When an issue arises, we know which line(s) is/are bad.
                        # When the issue is solved, by definition we only have good lines (at least 1,
                        # on kind "user", there is only one line, but on "jobs" there are typically several).
                        # For archival we need all those lines. Each will land in a separate file, by line hash.
                        lines_to_log = reports
                    for report in lines_to_log:
                        problem_archive_file_path = compute_problem_archive_file_path(
                            file_kind, af_id, file_path, problem_archive_file_marker,
                            account_label_for_filename, report["line_hash"])
                        print(f"Recording to problem archive: {problem_archive_file_path}")
                        if problem_archive_file_marker == "resolved":
                            resolved_to_be_also_in_report.append(
                                (account_label_for_filename, problem_archive_file_path))
                        with open(problem_archive_file_path, "w") as rej_file:
                            rej_file.write(
                                "\n------------------------------------------------------------------------\n"
                                + "\n".join("{:<10}: {}".format(k, v) for k, v in report.items())
                                + "\n------------------------------------------------------------------------\n")

            # Here finished importing and processing one file, now reporting

            facts_for_django_logs = []

            for case_number in range(4):
                users_in_this_case = problem_changes_this_file.get(case_number)
                # print (f"For case {case_number} users: {users_in_this_case}")
                if users_in_this_case:
                    case = ["ras", "nouveau souci", "souci résolu",
                            "souci répété"][case_number]
                    if case_number == 0:
                        pass
                        # report_by_file_then_user.append(f"  {case} pour {len(users_in_this_case)} utilisateur(s):")
                    else:
                        for user in users_in_this_case:
                            facts_for_django_logs.append(f"{case} pour {user}")
                            report_by_file_then_user.append(f"{os.path.basename(file_path)} : {case} pour {user}")

            self.log_success(file_date, file_kind, num_values, os.path.basename(file_path), facts_for_django_logs)
            # Here finished importing, processing and reporting one file

        # Here finished importing and processing all files.
        # We can now prepare a global report.

        # TODO we should catch any exception here (else some case will cause no report again).

        import_report_lines = []

        import_report_lines += [
            "",
            "## De quoi s'agit-il ?",
            "",
            "Ce message est envoyé par le sous-système qui importe les dernières données d'annuaires depuis l'AX.",
            "",
            "## Résumé du traitement",
            ""
        ]

        # import_report_lines += [f"Nombre de fichiers à importer : {len(options['csvfile'])}, liste ci-dessous:", ""]
        import_report_lines += ["Importé " + os.path.basename(n) for n in options['csvfile']]
        # import_report_lines += [f"Nombre de fichiers à importer : {len(options['csvfile'])}."]

        import_report_lines += report_by_file_then_user

        import_report_lines += [
            "", "## Synthèse des utilisateurs affectés par des soucis", "",
            "Cette section ne se limite pas aux nouveautés de la dernière importation.",
            "Elle considère tous les incidents non encore résolus.", "",
            "Les erreurs de données manifestes (exemple : tabulation dans un champ, année sur 3 chiffres)",
            "sont à corriger dans la base en amont. Alors l'entrée correspondante disparaîtra à la prochaine importation.",
            "",]

        from pathlib import Path
        rejects_directory = Path(settings.PERSISTENT_DIRECTORY) / "current_problems_by_id"

        active_rejections = []
        for subdir_name in kinds_involved_in_imported_files:
            subdir = rejects_directory / subdir_name
            if not subdir.is_dir():
                continue
            for file in subdir.iterdir():
                if file.is_file():
                    active_rejections.append((subdir.name, file.name, file))

        if not active_rejections:
            import_report_lines.append("**** Aucun incident en cours ! ****")
        else:
            import_report_lines += [
                f"* souci sur les données {kind} pour l'af_id {name.split('.')[0]}"
                for (kind, name, fullpath) in active_rejections
            ]

            import_report_lines.append("\n## Détails des utilisateurs affectés")

            for (kind, name, rejfile) in active_rejections:
                with rejfile.open() as f:
                    import_report_lines.append("\n" + "".join(f.readlines()))

        if resolved_to_be_also_in_report:
            import_report_lines += [
                "", "## Détails des cas résolus", "",
                "Certaines tables peuvent avoir plusieurs lignes par utilisateur (typiquement userjobs).",
                "Le cas est résolu quand toutes les lignes sont valides.",
                "Par simplicité on montre ici toutes les lignes qui concernent l'utilisateur.", ""
            ]

            for (account_label_for_filename, resolved_file_path) in resolved_to_be_also_in_report:
                import_report_lines.append(f"Camarade {account_label_for_filename}")
                import_report_lines.append(f"Fichier {resolved_file_path}")
                with open(resolved_file_path, 'r', encoding='utf-8') as f:
                    import_report_lines.append("".join(f.readlines()))

        # All report info is gathered. Assemble that into an e-mail body.

        overall_report_text = "\n".join(import_report_lines) + "\n"

        human_labels_for_cases = [None, "nouveau(x)", "résolu(s)", "répété(s)"]

        set_of_affected_user_changes = [f"{human_labels_for_cases[case]} pour {len(affected_users)} camarade(s)"
                                        for (case, affected_users) in problem_changes_all_files.items() if case != 0
                                        ]

        set_of_affected_user_changes_text = ", ".join(
            set_of_affected_user_changes) if set_of_affected_user_changes else "aucun changement"

        one_line_subject = f"Souci(s) d'importation : {set_of_affected_user_changes_text}, bilan {len(active_rejections)}"

        worth_an_email = bool(set_of_affected_user_changes) or bool(active_rejections)

        report_as_text = '\n'.join([
            "------------------------------------------------------------------------",
            "Vaut un e-mail ? " + ["non", "oui"][worth_an_email],
            "------------------------------------------------------------------------",
            one_line_subject,
            "------------------------------------------------------------------------",
            overall_report_text
        ])

        timestamp_start_str = timestamp_start.strftime("%Yy%mm%dd-%Hh%Mm%S.%fs")

        report_file_name = timestamp_start_str

        if len(options['csvfile']) == 1:
            report_file_name += "_for_file_" + os.path.basename(options['csvfile'][0])

        report_file_name += ".report.txt"

        directory = os.path.join(
            settings.PERSISTENT_DIRECTORY,
            timestamp_start.strftime("reports/%Y")
        )
        os.makedirs(directory, exist_ok=True)

        report_full_path = os.path.join(directory, report_file_name)

        print("saving report to " + report_full_path)

        with open(report_full_path, "a") as report_file:
            report_file.write(report_as_text)

        if worth_an_email:
            send_mail(
                settings.EMAIL_SUBJECT_PREFIX + one_line_subject,
                overall_report_text,
                None,
                settings.REPORT_RECIPIENTS
            )
