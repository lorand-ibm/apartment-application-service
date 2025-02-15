# Generated by Django 3.2.6 on 2021-11-29 09:02

from django.db import migrations


def apply_migration(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.create(name=u"salesperson")


def revert_migration(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.filter(name=u"salesperson").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_set_new_fields_to_null"),
    ]

    operations = [migrations.RunPython(apply_migration, revert_migration)]
