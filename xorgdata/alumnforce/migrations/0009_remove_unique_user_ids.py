# Generated by Django 2.0.10 on 2019-04-20 21:31

from django.db import migrations, models
import xorgdata.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('alumnforce', '0008_reorder_kinds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='ax_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='xorg_id',
            field=xorgdata.utils.fields.DottedSlugField(blank=True, max_length=255, null=True),
        ),
    ]