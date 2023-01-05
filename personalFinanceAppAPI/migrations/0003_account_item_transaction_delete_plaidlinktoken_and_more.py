# Generated by Django 4.1.4 on 2022-12-28 00:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('personalFinanceAppAPI', '0002_plaidlinktoken_delete_article'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.CharField(max_length=100)),
                ('available_balance', models.FloatField()),
                ('current_balace', models.FloatField()),
                ('name', models.CharField(max_length=100)),
                ('account_type', models.CharField(max_length=100)),
                ('account_subtype', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_id', models.CharField(max_length=100)),
                ('access_token', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100)),
                ('amount', models.FloatField()),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=100)),
                ('payment_channel', models.CharField(max_length=100)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personalFinanceAppAPI.account')),
            ],
        ),
        migrations.DeleteModel(
            name='PlaidLinkToken',
        ),
        migrations.AddField(
            model_name='account',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personalFinanceAppAPI.item'),
        ),
    ]
