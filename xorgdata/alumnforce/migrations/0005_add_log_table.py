# Generated by Django 2.0.10 on 2019-04-15 18:36

from django.db import migrations, models
import xorgdata.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('alumnforce', '0004_add_last_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('export_kind', models.SlugField(choices=[
                    ('groupmembers', 'groupmembers'),
                    ('groups', 'groups'),
                    ('userdegrees', 'userdegrees'),
                    ('userjobs', 'userjobs'),
                    ('users', 'users')])),
                ('is_incremental', models.BooleanField()),
                ('error', models.IntegerField(choices=[
                    (0, 'success'),
                    (1, 'AlumnForce error'),
                    (2, 'X.org error')])),
                ('num_modified', models.IntegerField(blank=True, null=True)),
                ('message', xorgdata.utils.fields.UnboundedCharField(blank=True)),
            ],
        ),
    ]
