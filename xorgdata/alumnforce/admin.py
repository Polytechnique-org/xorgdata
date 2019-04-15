# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from . import models


class AcademicInformationInline(admin.StackedInline):
    model = models.AcademicInformation
    extra = 0


class ProfessionnalInformationInline(admin.StackedInline):
    model = models.ProfessionnalInformation
    extra = 0


class GroupMemberhipInline(admin.TabularInline):
    model = models.GroupMemberhip
    extra = 0
    readonly_fields = ('link_account', 'link_group')
    fields = ('link_account', 'link_group', 'role')

    def link_account(self, obj):
        obj_url = reverse(
            'admin:%s_%s_change' % (obj.account._meta.app_label, obj.account._meta.model_name),
            args=(obj.account.af_id, ))
        return format_html('<a href="{}">{}</a>', obj_url, obj.account)
    link_account.short_description = _("account")

    def link_group(self, obj):
        obj_url = reverse(
            'admin:%s_%s_change' % (obj.group._meta.app_label, obj.group._meta.model_name),
            args=(obj.group.af_id, ))
        return format_html('<a href="{}">{}</a>', obj_url, obj.group)
    link_group.short_description = _("group")


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ('hrid', 'main_email', 'fullname', 'preferred_name')
    list_display = ('af_id', 'ax_id', 'xorg_id', 'first_name', 'last_name')
    list_display_links = ('af_id', 'ax_id', 'xorg_id', 'first_name', 'last_name')
    ordering = ('-ax_id', 'xorg_id', 'af_id')

    inlines = [
        AcademicInformationInline,
        ProfessionnalInformationInline,
        GroupMemberhipInline,
    ]


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ('af_id', 'name', 'category')
    list_display = ('af_id', 'ax_id', 'name', 'category', 'url')
    list_display_links = ('af_id', 'ax_id', 'name')
    ordering = ('name', 'af_id')
    inlines = [
        GroupMemberhipInline,
    ]


@admin.register(models.ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'export_kind', 'is_incremental', 'error', 'num_modified', 'message')
