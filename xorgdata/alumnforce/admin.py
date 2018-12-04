# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.contrib import admin

from . import models

@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ['hrid', 'main_email', 'fullname', 'preferred_name']

    list_display = ['af_id', 'ax_id', 'xorg_id', 'first_name', 'last_name']
    ordering = ('-ax_id', 'xorg_id', 'af_id')
