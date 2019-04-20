# -*- coding: utf-8 -*-
import collections
import datetime
import ftplib
from pathlib import Path
import re

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from xorgdata.alumnforce import models


def get_last_update_by_kind():
    """Retrieve from the database the last date the data has been updated and
    whether it was incremental
    """
    last_update_dates = collections.OrderedDict()
    for kind, _kind_name in models.ImportLog.KNOWN_EXPORT_KINDS:
        qs = models.ImportLog.objects.filter(export_kind=kind).order_by('-date', '-is_incremental')
        try:
            last_obj = qs[:1].get()
        except models.ImportLog.DoesNotExist:
            last_update_dates[kind] = None
        else:
            last_update_dates[kind] = (last_obj.date, last_obj.is_incremental)
    return last_update_dates


class FtpConnection:
    """FTP connection to AlumnForce's FTP server"""
    def __init__(self):
        # Connect to the FTPS server
        self.ftps = ftplib.FTP_TLS(settings.ALUMNFORCE_FTP_HOST)
        self.ftps.login(settings.ALUMNFORCE_FTP_USER, settings.ALUMNFORCE_FTP_PASSWORD)
        self.ftps.prot_p()
        if settings.ALUMNFORCE_FTP_REMOTE_DIRECTORY:
            self.ftps.cwd(settings.ALUMNFORCE_FTP_REMOTE_DIRECTORY)

        # List the available files by kind->date->(is_ok, filename)
        self.ftp_files = {kind: {} for kind, _kind_name in models.ImportLog.KNOWN_EXPORT_KINDS}
        self.ftps.dir(self._dir_callback)

    def _dir_callback(self, line):
        """Callback for a dir command of a FTP client"""
        matches = re.match(r'.* (export([a-z]+)-afbo-Polytechnique-X-([0-9]{4}[0-9]{2}[0-9]{2})\.csv(\.error)?)$', line)
        if not matches:
            # Ignore unknown files
            return
        filename, kind, date, error = matches.groups()
        if kind not in self.ftp_files:
            print("Warning: unknown kind {} for file {}".format(repr(kind), repr(filename)))
            return
        if date in self.ftp_files[kind]:
            # If there is a .error file, overwrite the entry. Otherwise, skip it
            if not error:
                return

        self.ftp_files[kind][date] = (filename, not error)

    def download_file(self, filename, out_path):
        """Download a file to the given output path"""
        with open(out_path, 'wb') as fout:
            self.ftps.retrbinary('RETR ' + filename, fout.write)


class Command(BaseCommand):
    help = "Synchronise with AlumnForce's FTP server"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--dryrun', action='store_true',
                            help="show the files that would be applied, without updating anything")
        parser.add_argument('--verbose', action='store_true',
                            help="show what is done")

    def handle(self, *args, **options):
        last_update_dates = get_last_update_by_kind()

        is_dryrun = options['dryrun']
        if is_dryrun:
            self.stdout.write("Dry-run mode, nothing will be committed")

        if not settings.ALUMNFORCE_FTP_USER:
            raise CommandError("XORGDATA_ALUMNFORCE_FTP_USER is not defined")
        if not settings.ALUMNFORCE_FTP_PASSWORD:
            raise CommandError("XORGDATA_ALUMNFORCE_FTP_PASSWORD is not defined")

        # Connect to the FTPS server
        conn = FtpConnection()
        if options['verbose']:
            self.stdout.write(self.style.SUCCESS("Connected to ftps://{}".format(settings.ALUMNFORCE_FTP_HOST)))

        download_dir_path = Path(settings.ALUMNFORCE_FTP_LOCAL_DIRECTORY)
        if not is_dryrun:
            download_dir_path.mkdir(exist_ok=True)

        # Check for updates, for each kind
        for kind, lastup_data in last_update_dates.items():
            if lastup_data is None:
                last_update_date = None
                last_was_incremental = None
            else:
                last_update_date = lastup_data[0].strftime('%Y%m%d')
                last_was_incremental = lastup_data[1]

            # Apply all possible files, sorting them by date
            for date_str, filename_expok in sorted(conn.ftp_files[kind].items()):
                filename, is_export_ok = filename_expok
                if date_str < last_update_date:
                    continue
                # Allow an incremental update to occur after a full export has
                # been imported for a given date, but do not apply the same
                # incremental update twice.
                if date_str == last_update_date and last_was_incremental:
                    continue

                file_date = datetime.date(year=int(date_str[:4]), month=int(date_str[4:6]), day=int(date_str[6:]))

                # If there was an error, log it and continue
                if not is_export_ok:
                    self.stdout.write(self.style.WARNING("AlumnForce export error found: {}".format(repr(filename))))
                    if not is_dryrun:
                        models.ImportLog.objects.create(
                            date=file_date,
                            export_kind=kind,
                            is_incremental=True,
                            error=models.ImportLog.ALUMNFORCE_ERROR,
                            message="error file found: {}".format(repr(filename)),
                        )
                    continue

                if is_dryrun:
                    self.stdout.write(self.style.SUCCESS("(not) applying file {}".format(repr(filename))))
                    continue

                if options['verbose']:
                    self.stdout.write(self.style.SUCCESS("Downloading {}".format(filename)))

                if not re.match(r'^[-0-9A-Za-z]+\.csv$', filename):
                    raise CommandError("Unexpected bad filename {}".format(repr(filename)))

                dl_filepath = download_dir_path / filename
                conn.download_file(filename, dl_filepath)

                if options['verbose']:
                    self.stdout.write(self.style.SUCCESS("Applying {}".format(dl_filepath)))
                    call_command('importcsv', dl_filepath, kind=kind)
                else:
                    call_command('importcsv', dl_filepath, kind=kind, verbosity=0)

                dl_filepath.unlink()
