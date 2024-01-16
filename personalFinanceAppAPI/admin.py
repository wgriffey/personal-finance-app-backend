from django.contrib import admin
from .models import Account, Investment, Transaction, Item

# Register your models here.


@admin.register(Account)
class AccountModel(admin.ModelAdmin):
    list_filter = ("account_id", "name")
    list_display = (
        "account_id",
        "name",
        "current_balance",
        "available_balance",
        "account_subtype",
        "account_type",
    )


@admin.register(Transaction)
class TransactionModel(admin.ModelAdmin):
    list_filter = ("transaction_id", "account")
    list_display = (
        "transaction_id",
        "amount",
        "account",
        "name",
        "payment_channel",
        "date",
    )


@admin.register(Item)
class ItemModel(admin.ModelAdmin):
    list_filter = ("item_id", "user")
    list_display = ("item_id", "user", "access_token")


@admin.register(Investment)
class InvestmentModel(admin.ModelAdmin):
    list_filter = ("account", "security_name", "price")
    list_display = (
        "account",
        "price",
        "security_name",
        "price_as_of",
        "cost_basis",
        "quantity",
    )
