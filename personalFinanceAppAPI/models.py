from django.db import models
from authuser.models import User

class Institution(models.Model):
    institution_id = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=200)

class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'institution_id'], name='user_institution_unique_constraint')
        ]

    def __str__(self):
        return self.item_id


class Account(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=100, blank=True)
    available_balance = models.FloatField()
    current_balance = models.FloatField()
    name = models.CharField(max_length=100, blank=True)
    account_type = models.CharField(max_length=100, blank=True)
    account_subtype = models.CharField(max_length=100, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['item_id', 'account_id'], name='item_account_unique_constraint')
        ]

    def __str__(self):
        return self.account_id


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.FloatField()
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)
    payment_channel = models.CharField(max_length=100, blank=True)
    primary_category = models.CharField(max_length=100, blank=True)
    detailed_category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.transaction_id

class Investment(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True)
    security_id = models.CharField(max_length = 100, blank=True)
    security_name = models.CharField(max_length=100, blank=True)
    security_ticker = models.CharField(max_length=20, blank=True)
    price = models.FloatField()
    price_as_of = models.DateField()
    cost_basis = models.FloatField()
    quantity = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account', 'security_id'], name='account_security_unique_constraint')
        ]
        

