from authuser.models import User
from rest_framework import serializers
from rest_framework.authtoken.views import Token
from .models import Account, Transaction, Investment, Institution

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

        extra_kwargs = {'password': {
            'write_only': True,
            'required': True
        }}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password', None)
            instance.set_password(password)
        return super().update(instance, validated_data)
    
class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['institution_id', 'institution_name']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['item', 'account_id','available_balance', 'current_balance', 'name', 'account_type', 'account_subtype']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['account', 'transaction_id' ,'amount', 'date', 'name', 'payment_channel', 'primary_category', 'detailed_category']

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = ['account', 'security_id', 'security_name', 'security_ticker', 'price', 'price_as_of', 'cost_basis', 'quantity']
