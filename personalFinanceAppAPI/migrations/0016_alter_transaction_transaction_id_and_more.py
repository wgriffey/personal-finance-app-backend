# Generated by Django 4.1.4 on 2023-03-16 23:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("personalFinanceAppAPI", "0015_alter_transaction_transaction_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="transaction_id",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name="transaction",
            unique_together={("account", "transaction_id")},
        ),
    ]
