import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from xorgdata.alumnforce import models


class Command(BaseCommand):
    help = "Export data which is used by X.org authentication project"

    def add_arguments(self, parser):
        parser.add_argument('--push', action='store_true',
                            help="push the exported data to {}".format(settings.XORGAUTH_HOST))

    def handle(self, *args, **options):
        # Avoid duplicated X.org login in the exported data
        duplicated_xorg_id = (
            models.Account.objects
            .filter(deleted_since=None)
            .exclude(xorg_id=None)
            .values('xorg_id')
            .annotate(count=Count('af_id'))
            .values('xorg_id')
            .filter(count__gt=1)
        )

        # Export all accounts that have not been deleted and that have a X.org login
        accounts_qs = (
            models.Account.objects
            .filter(deleted_since=None)
            .exclude(xorg_id=None, xorg_id__in=duplicated_xorg_id)
        )

        def export_account(account):
            roles = account.get_additional_roles()
            return {
                'xorg_id': account.xorg_id,
                'af_id': account.af_id,
                'ax_contributor': models.Account.ROLE_CONTRIBUTOR in roles,
                'axjr_subscribed': models.Account.ROLE_SUBSCRIBED in roles,
                'last_updated': account.last_update.strftime('%Y-%m-%d')
            }

        exported_data = [export_account(account) for account in accounts_qs]

        if not options['push']:
            # Show the exported data, without exporting it
            self.stdout.write(json.dumps(exported_data))
            return

        if not settings.XORGAUTH_PASSWORD:
            raise CommandError("Unable to push: XORGDATA_XORGAUTH_PASSWORD is not defined")
        # TODO Implement Xorgdata API...
