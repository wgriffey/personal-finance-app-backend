# Generated by Django 4.1.4 on 2023-01-29 03:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("personalFinanceAppAPI", "0010_remove_investmentholding_holding_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="investmentsecurity",
            name="ticker",
            field=models.CharField(max_length=20),
        ),
    ]
