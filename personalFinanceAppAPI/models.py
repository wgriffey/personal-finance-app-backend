from django.db import models
from authuser.models import User


# Create your models here.

# class Article(models.Model):
#     title = models.CharField(max_length=100)
#     description = models.TextField()

#     def __str__(self) -> str:
#         return super().__str__()

class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)

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

    def __str__(self):
        return self.account_id


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    amount = models.FloatField()
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)
    payment_channel = models.CharField(max_length=100, blank=True)
    primary_category = models.CharField(max_length=100, blank=True)
    detailed_category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.transaction_id

class InvestmentSecurity(models.Model):
    security_id = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    ticker = models.CharField(max_length=20, blank=True)

class InvestmentHolding(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True)
    security_id = models.CharField(max_length = 100, blank=True)
    price = models.FloatField()
    price_as_of = models.DateField()
    cost_basis = models.FloatField()
    quantity = models.FloatField()

