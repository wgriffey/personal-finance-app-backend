# Generated by Django 4.1.4 on 2023-01-29 03:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0013_alter_investmentholding_security"),
    ]

    operations = [
        migrations.RenameField(
            model_name="investmentholding",
            old_name="security",
            new_name="security_id",
        ),
    ]
