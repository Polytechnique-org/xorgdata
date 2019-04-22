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
