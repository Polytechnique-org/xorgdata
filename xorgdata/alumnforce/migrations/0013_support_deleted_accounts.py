# Generated by Django 2.2 on 2019-04-27 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alumnforce', '0012_fix_membership_typo'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='deleted_since',
            field=models.DateField(blank=True, null=True),
        ),
    ]