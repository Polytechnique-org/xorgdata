# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3
from django.contrib import admin
from django.db.models import Count, Q
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


class GroupMembershipInline(admin.TabularInline):
    model = models.GroupMembership
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
    search_fields = ('ax_id', 'xorg_id', 'first_name', 'last_name', 'common_name')
    list_display = ('af_id', 'ax_id', 'xorg_id', 'first_name', 'last_name', 'deleted_since')
    list_display_links = ('af_id', 'ax_id', 'xorg_id', 'first_name', 'last_name')
    readonly_fields = ('kind_desc', 'roles_desc', 'alumnforce_profile_url')
    ordering = ('-ax_id', 'xorg_id', 'af_id')

    inlines = [
        AcademicInformationInline,
        ProfessionnalInformationInline,
        GroupMembershipInline,
    ]

    def kind_desc(self, obj):
        """Get the description of account kind"""
        return "{} [{}]".format(models.Account.KINDS.get(obj.user_kind, '?'), obj.user_kind)
    kind_desc.short_description = _("Account kind")

    def roles_desc(self, obj):
        """Get the description of account additional roles"""
        return ', '.join("{} [{}]".format(models.Account.ROLES.get(r, '?'), r) for r in obj.get_additional_roles())
    roles_desc.short_description = _("Additional roles")

    def alumnforce_profile_url(self, obj):
        return format_html('<a href="{}">{}</a>', obj.alumnforce_profile_url, obj.alumnforce_profile_url)


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ('af_id', 'name', 'category')
    list_display = ('af_id', 'ax_id', 'name', 'count_members', 'category', 'url')
    list_display_links = ('af_id', 'ax_id', 'name')
    readonly_fields = ('url_link', )
    ordering = ('name', 'af_id')
    inlines = [
        GroupMembershipInline,
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _members_count=Count("memberships",
                                 filter=Q(memberships__role__in=models.GroupMembership.IN_GROUP_ROLES),
                                 distinct=True),
        )
        return queryset

    def count_members(self, obj):
        return obj._members_count
    count_members.short_description = _("members")

    def url_link(self, obj):
        return format_html('<a href="{0}">{0}</a>', obj.url)
    url_link.short_description = _("URL link")


@admin.register(models.ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'export_kind', 'is_incremental', 'error', 'num_modified', 'message')
    ordering = ('-date', 'export_kind')


@admin.register(models.ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'export_kind', 'error', 'num_items', 'message')
    ordering = ('-date', 'export_kind')
