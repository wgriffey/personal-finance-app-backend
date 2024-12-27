from rest_framework import serializers

from .models import Account, Institution, Investment, Transaction, Item

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["id", "institution_id", "institution_name"]

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields=["id", "item_id", "institution", "access_token"]
        
    def create(self, validated_data):
        # Retrieve the user from the serializer's context
        user = self.context['user']
        validated_data['user'] = user
        return super().create(validated_data)

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
            "id",
            "account",
            "security_id",
            "security_name",
            "security_ticker",
            "price",
            "price_as_of",
            "cost_basis",
            "quantity",
        ]
