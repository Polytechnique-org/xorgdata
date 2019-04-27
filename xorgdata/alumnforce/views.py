import re

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

from xorgdata.alumnforce import models


class SummaryView(TemplateView):
    template_name = 'xorgdata/summary.html'

    def last_logs_by_kind(self):
        """Get the last logs from the database, for each defined kind"""
        last_logs = []
        for kind, _kind_name in models.ImportLog.KNOWN_EXPORT_KINDS:
            qs = models.ImportLog.objects.filter(export_kind=kind).order_by('-date', '-is_incremental')
            try:
                last_logs.append(qs[:1].get())
            except models.ImportLog.DoesNotExist:
                pass
        return last_logs


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
            account_issues.append("Invalid additional roles value: {}".format(repr(account.additional_roles)))
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
        return account_issues

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issues = []
        for account in models.Account.objects.filter(deleted_since=None):
            account_issues = self.find_issues(account)
            if account_issues:
                issues.append({
                    'account': account,
                    'issues': account_issues,
                })
        context['issues'] = issues
        return context
