# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3
import re

from django.core.validators import RegexValidator
from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _


class UnboundedCharField(models.TextField):
    """Unlimited text, on a single line.
    Shows an ``<input type="text">`` in HTML but is stored as a TEXT
    column in Postgres (like ``TextField``).
    Like the standard :class:`~django.db.models.fields.CharField` widget,
    a ``select`` widget is automatically used if the field defines ``choices``.
    """
    def __init__(self, *args, **kwargs):
        if kwargs.get('unique'):
            raise ValueError("UnboundedCharField can not be 'unique' as this is not supported by MySQL")
        return super(UnboundedCharField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['widget'] = None if self.choices else forms.TextInput
        return super(UnboundedCharField, self).formfield(**kwargs)


validate_dotted_slug = RegexValidator(
    re.compile(r'^[-a-zA-Z0-9_.]+\Z'),
    _("Enter a valid 'slug' consisting of letters, numbers, underscores, dots or hyphens."),
    'invalid'
)


class DottedSlugField(models.CharField):
    """Slug field which allows dot"""
    default_validators = [validate_dotted_slug]
