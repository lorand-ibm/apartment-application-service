# Generated by Django 3.2.11 on 2022-02-11 09:18

from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    Customer = apps.get_model("customer", "Customer")
    # make sure there are no existing Customers because adding primary_profile field for
    # them would fail
    Customer.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0017_add_salesperson_group"),
        ("customer", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customer",
            name="profiles",
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AddField(
            model_name="customer",
            name="primary_profile",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="customers_where_primary",
                to="users.profile",
                verbose_name="primary profile",
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="secondary_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="customers_where_secondary",
                to="users.profile",
                verbose_name="secondary profile",
            ),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                fields=("primary_profile", "secondary_profile"),
                name="customer_primary_profile_secondary_profile_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                condition=models.Q(("secondary_profile__isnull", True)),
                fields=("primary_profile",),
                name="customer_sole_primary_profile_unique",
            ),
        ),
    ]
