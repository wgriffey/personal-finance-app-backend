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
    account_id = models.CharField(max_length=100)
    available_balance = models.FloatField()
    current_balance = models.FloatField()
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=100)
    account_subtype = models.CharField(max_length=100)

    def __str__(self):
        return self.account_id


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    amount = models.FloatField()
    date = models.DateField()
    name = models.CharField(max_length=100)
    payment_channel = models.CharField(max_length=100)

    def __str__(self):
        return self.transaction_id

class TransactionCategory(models.Model):
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)

class InvestmentSecurity(models.Model):
    security_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    ticker = models.CharField(max_length=5)

class InvestmentHolding(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    holding_id = models.CharField(max_length=100)
    security_id = models.ForeignKey(InvestmentSecurity, on_delete=models.CASCADE)
    price = models.FloatField()
    price_as_of = models.DateField()
    cost_basis = models.FloatField()
    quantity = models.FloatField()

