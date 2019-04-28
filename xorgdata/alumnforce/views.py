import re

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.views.generic import TemplateView

from xorgdata.alumnforce import models


class SummaryView(TemplateView):
    template_name = 'xorgdata/summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        """Get the last logs from the database, for each defined kind"""
        last_logs = []
        for kind, _kind_name in models.ImportLog.KNOWN_EXPORT_KINDS:
            qs = models.ImportLog.objects.filter(export_kind=kind).order_by('-date', '-is_incremental')
            try:
                last_logs.append(qs[:1].get())
            except models.ImportLog.DoesNotExist:
                pass
        context['last_logs_by_kind'] = last_logs
        return context


class IssuesView(UserPassesTestMixin, TemplateView):
    template_name = 'xorgdata/issues.html'

    def test_func(self):
        """Restrict this view to the superuser"""
        return self.request.user.is_superuser

    def find_issues(self, account):
        """Find issues in an account"""
        account_issues = []

        if account.civility not in ('', 'Mme', 'M'):
            account_issues.append("Unknown civility {}".format(repr(account.civility)))

        if account.user_kind not in models.Account.KINDS:
            account_issues.append("Unknown account kind {}".format(account.user_kind))

        try:
            account_roles = account.get_additional_roles()
        except ValueError:
            account_issues.append("Invalid additional roles value {}".format(repr(account.additional_roles)))
        else:
            for role in account_roles:
                if role not in models.Account.ROLES:
                    account_issues.append("Unknown account role {}".format(role))

        if account.xorg_id:
            # Verify the format of X.org ID
            if re.search(r'[^a-z0-9.-]', account.xorg_id):
                account_issues.append("Invalid X.org ID: {}".format(repr(account.xorg_id)))
        else:
            # Check whether the user should have a X.org ID
            if account.user_kind == models.Account.KIND_GRADUATED:
                account_issues.append("Missing X.org ID for graduated")
            elif account.user_kind == models.Account.KIND_STUDENT:
                account_issues.append("Missing X.org ID for student")

        # Verify email addresses against a simple regular expression
        email_regexp = re.compile(r'^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+$')
        if account.email_1 and not email_regexp.match(account.email_1):
            account_issues.append("Invalid email address 1 {}".format(repr(account.email_1)))
        if account.email_2 and not email_regexp.match(account.email_2):
            account_issues.append("Invalid email address 2 {}".format(repr(account.email_2)))
        return account_issues

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Find accounts with duplicate IDs
        duplicated_ax_id = {
            row['ax_id']: row['count']
            for row in models.Account.objects
            .filter(deleted_since=None)
            .exclude(ax_id=None)
            .values('ax_id')
            .annotate(count=Count('af_id'))
            .filter(count__gt=1)
        }
        duplicated_xorg_id = {
            row['xorg_id']: row['count']
            for row in models.Account.objects
            .filter(deleted_since=None)
            .exclude(xorg_id=None)
            .values('xorg_id')
            .annotate(count=Count('af_id'))
            .filter(count__gt=1)
        }
        duplicated_school_id = {
            row['school_id']: row['count']
            for row in models.Account.objects
            .filter(deleted_since=None)
            .exclude(school_id='')
            .values('school_id')
            .annotate(count=Count('af_id'))
            .filter(count__gt=1)
        }

        issues = []
        for account in models.Account.objects.filter(deleted_since=None):
            account_issues = self.find_issues(account)
            dup_count = duplicated_ax_id.get(account.ax_id)
            if dup_count is not None:
                account_issues.append("Duplicated AX ID {}, shared with {} accounts".format(
                    repr(account.ax_id), dup_count))

            dup_count = duplicated_xorg_id.get(account.xorg_id)
            if dup_count is not None:
                account_issues.append("Duplicated X.org ID {}, shared with {} accounts".format(
                    repr(account.xorg_id), dup_count))

            dup_count = duplicated_school_id.get(account.school_id)
            if dup_count is not None:
                account_issues.append("Duplicated school ID {}, shared with {} accounts".format(
                    repr(account.school_id), dup_count))

            if account_issues:
                issues.append({
                    'account': account,
                    'issues': account_issues,
                })
        context['issues'] = issues
        return context
