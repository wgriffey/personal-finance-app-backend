from rest_framework import serializers

from .models import Account, Institution, Investment, Transaction


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["institution_id", "institution_name"]


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "item",
            "account_id",
            "available_balance",
            "current_balance",
            "name",
            "account_type",
            "account_subtype",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "transaction_id",
            "amount",
            "date",
            "name",
            "payment_channel",
            "primary_category",
            "detailed_category",
        ]


class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = [
            "account",
            "security_id",
            "security_name",
            "security_ticker",
            "price",
            "price_as_of",
            "cost_basis",
            "quantity",
        ]
