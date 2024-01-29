# Generated by Django 4.1.4 on 2022-12-30 22:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_rename_current_balace_account_current_balance"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvestmentSecurity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("security_id", models.CharField(max_length=100)),
                ("name", models.CharField(max_length=100)),
                ("ticker", models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name="InvestmentHolding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("holding_id", models.CharField(max_length=100)),
                ("price", models.FloatField()),
                ("price_as_of", models.DateField()),
                ("cost_basis", models.FloatField()),
                ("quantity", models.FloatField()),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="api.account",
                    ),
                ),
                (
                    "security_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="api.investmentsecurity",
                    ),
                ),
            ],
        ),
    ]