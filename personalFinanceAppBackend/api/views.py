import json
import os
from datetime import datetime, timedelta
from logging import getLogger

from django.db import IntegrityError
from plaid.api import plaid_api
from plaid.api_client import ApiClient, ApiException
from plaid.configuration import Configuration, Environment
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from rest_framework import generics, status
from rest_framework.decorators import APIView
from rest_framework.response import Response

from .models import Account, Institution, Investment, Item, Transaction
from .serializers import (
    AccountSerializer,
    InstitutionSerializer,
    InvestmentSerializer,
    ItemSerializer,
    TransactionSerializer,
)
from .utils import (
    clean_accounts_data,
    clean_institution_data,
    clean_investment_data,
    clean_item_data,
    clean_transaction_data,
)

if os.getenv("PLAID_ENV") == "production":
    host = Environment.Production
else:
    host = Environment.Sandbox

configuration = Configuration(
    host=host,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
        "plaidVersion": "2020-09-14",
    },
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

logger = getLogger("personal_finance_app")


class PlaidLinkToken(APIView):
    def post(self, request):
        user = request.user
        if "item_id" in request.data and not request.data["item_id"] is None:
            item = Item.objects.get(pk=request.data["item_id"])
            # Update Link Request for existing user
            update_link_request = LinkTokenCreateRequest(
                client_name="G&E Personal Finance",
                country_codes=[CountryCode("US")],
                access_token=item.access_token,
                redirect_uri="http://localhost:3000/",
                language="en",
                webhook="https://webhook.example.com",
                user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
            )
            update_link_response = client.link_token_create(update_link_request)
            return Response(
                update_link_response.to_dict(), status=status.HTTP_201_CREATED
            )

        # Create a link_token for the new user
        request = LinkTokenCreateRequest(
            products=[Products("transactions"), Products("investments")],
            client_name="G&E Personal Finance",
            country_codes=[CountryCode("US")],
            redirect_uri="http://localhost:3000/",
            language="en",
            webhook="https://webhook.example.com",
            user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        )
        response = client.link_token_create(request)
        # Send the data to the client
        return Response(response.to_dict(), status=status.HTTP_201_CREATED)


class PublicTokenExchange(APIView):
    def post(self, request):
        user = request.user
        institution_id = request.data["institution_data"]["institution_id"]
        institution_name = request.data["institution_data"]["name"]
        public_token = request.data["public_token"]

        token_request = ItemPublicTokenExchangeRequest(public_token=public_token)

        if Item.objects.filter(user=user, institution__institution_id=institution_id):
            return Response(
                "Item for Institution Exists for User", status=status.HTTP_409_CONFLICT
            )

        try:
            token_response = client.item_public_token_exchange(token_request)
        except ApiException as e:
            response = json.loads(e.body)

            return Response(
                {
                    "error": {
                        "status_code": e.status,
                        "display_message": response["error_message"],
                        "error_code": response["error_code"],
                        "error_type": response["error_type"],
                    }
                }
            )

        item_id = token_response["item_id"]
        access_token = token_response["access_token"]

        # Save New Institutions to DB
        if Institution.objects.filter(institution_id=institution_id):
            pass
        else:
            try:
                institution = clean_institution_data(institution_id, institution_name)

                institution_serializer = InstitutionSerializer(data=institution)
                institution_serializer.is_valid(raise_exception=True)
                institution_serializer.save()
            except Exception as e:
                return Response(
                    data={"message": "Failed to Save Institution", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            institution = Institution.objects.get(institution_id=institution_id)
            item = clean_item_data(item_id, access_token, institution.pk)

            item_serializer = ItemSerializer(data=item, context={"user": user})
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()
        except Exception as e:
            return Response(
                data={"message": "Failed to Save Item", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            "Item and Access Token Generated for User Access to Institution",
            status=status.HTTP_201_CREATED,
        )


class InstitutionDetailsDB(APIView):
    def get(self, request, account_id):
        account = Account.objects.get(pk=account_id)

        item = Item.objects.get(item=account.item)

        institution = Institution.objects.get(institution=item.institution)

        institution_serializer = InstitutionSerializer(institution)

        return Response(institution_serializer.data, status=status.HTTP_200_OK)


class AccountListPlaid(APIView):
    def post(self, request):
        items = Item.objects.filter(user=request.user)
        accounts_saved_list = []
        accounts_dict = {}

        # Get All Accounts For User
        for item in items:
            access_token = item.access_token

            try:
                accounts_request = AccountsGetRequest(access_token=access_token)
                accounts_response = client.accounts_get(accounts_request)
            except ApiException as e:
                response = json.loads(e.body)

                return Response(
                    {
                        "error": {
                            "status_code": e.status,
                            "display_message": response["error_message"],
                            "error_code": response["error_code"],
                            "error_type": response["error_type"],
                        }
                    }
                )

            # Clean the Account Data
            accounts = clean_accounts_data(item.pk, accounts_response["accounts"])

            # Skip Existing Accounts and Save New Accounts
            for acc in accounts:
                if Account.objects.filter(
                    item=acc["item"], account_id=acc["account_id"]
                ):
                    continue
                else:
                    try:
                        # Save Account Data to DB
                        account_serializer = AccountSerializer(data=acc)
                        account_serializer.is_valid(raise_exception=True)
                        account_serializer.save()
                    except IntegrityError as e:
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

                accounts_saved_list.append(account_serializer.data)
            if len(accounts_saved_list) != 0:
                accounts_dict[item.institution_id] = accounts_saved_list

        if not accounts_dict:
            return Response(
                "No New Accounts to Save From Plaid", status=status.HTTP_200_OK
            )

        return Response(accounts_dict, status=status.HTTP_201_CREATED)


class AccountListDB(APIView):
    def get(self, request):
        items = Item.objects.filter(user=request.user)
        accounts = []

        for item in items:
            db_accounts = Account.objects.filter(item=item.pk)
            account_serializer = AccountSerializer(db_accounts, many=True)
            for acc in account_serializer.data:
                accounts.append(acc)

        return Response(accounts, status=status.HTTP_200_OK)


class AccountDetailsDB(APIView):
    def get(self, request, pk):
        try:
            account = Account.objects.get(pk=pk)
            account_serializer = AccountSerializer(account)
        except Account.DoesNotExist:
            return Response("Account Not Found", status=status.HTTP_404_NOT_FOUND)
        except Account.MultipleObjectsReturned:
            return Response(
                "Multiple Accounts Returned", status=status.HTTP_409_CONFLICT
            )
        return Response(account_serializer.data, status=status.HTTP_200_OK)


class TransactionListPlaid(APIView):
    def post(self, request):
        items = Item.objects.filter(user=request.user)
        transactions_saved_list = []
        transactions_dict = {}

        for item in items:
            access_token = item.access_token

            start_date = (datetime.now() - timedelta(days=720)).date()
            end_date = datetime.now().date()

            if (
                "start_date" in request.data and request.data["start_date"] is not None
            ) and ("end_date" in request.data and request.data["end_date"] is not None):
                start_date = request.data["start_date"]
                end_date = request.data["end_date"]

            transaction_request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )

            response = client.transactions_get(transaction_request)

            ## Clean the Transaction Data
            transactions = clean_transaction_data(response["transactions"])

            for tran in transactions:
                # Skip existing transactions and save new transactions
                if Transaction.objects.filter(transaction_id=tran["transaction_id"]):
                    continue
                else:
                    try:
                        transaction_serializer = TransactionSerializer(data=tran)
                        transaction_serializer.is_valid(raise_exception=True)
                        transaction_serializer.save()
                    except IntegrityError as e:
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

                    transactions_saved_list.append(transaction_serializer.data)
            if len(transactions_saved_list) != 0:
                transactions_dict[item.institution.pk] = transactions_saved_list

        if not transactions_dict:
            return Response(
                "No New Transactions to Save From Plaid",
                status=status.HTTP_200_OK,
            )

        return Response(transactions_dict, status=status.HTTP_201_CREATED)


class TransactionListDB(APIView):
    def get(self, request):
        items = Item.objects.filter(user=request.user)
        start_date = request.query_params.get(
            "start_date",
        )
        end_date = request.query_params.get("end_date", datetime.now().date())
        if start_date == "undefined" or end_date == "undefined":
            start_date = (datetime.now() - timedelta(days=720)).date()
            end_date = datetime.now().date()
        transactions = []
        for item in items:
            db_accounts = Account.objects.filter(item=item)

            account_id_list = [acc.pk for acc in db_accounts]

            db_transactions = Transaction.objects.filter(
                account__in=account_id_list, date__range=(start_date, end_date)
            ).order_by("-date")
            transaction_serializer = TransactionSerializer(db_transactions, many=True)
            for tran in transaction_serializer.data:
                transactions.append(tran)

        return Response(
            transactions,
            status=status.HTTP_200_OK,
        )


class TransactionDetailsDB(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class InvestmentListPlaid(APIView):
    def post(self, request):
        items = Item.objects.filter(user=request.user)
        investments_saved_list = []
        investments_dict = {}

        for item in items:
            access_token = item.access_token

            investment_request = InvestmentsHoldingsGetRequest(
                access_token=access_token,
            )

            response = client.investments_holdings_get(investment_request)

            ## Clean Investment Data
            investment_data = clean_investment_data(
                response["holdings"], response["securities"]
            )

            # Skip Existing Investments for an Account and Save New Investments for an Account
            for investment in investment_data:
                if Investment.objects.filter(
                    account=investment["account"],
                    security_id=investment["security_id"],
                ):
                    continue
                else:
                    try:
                        investment_serializer = InvestmentSerializer(data=investment)
                        investment_serializer.is_valid(raise_exception=True)
                        investment_serializer.save()
                    except IntegrityError as e:
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

                    investments_saved_list.append(investment_serializer.data)
            if len(investments_saved_list) != 0:
                investments_dict[item.institution_id] = investments_saved_list

        if not investments_dict:
            return Response(
                "No New Investment Accounts to Save From Plaid",
                status=status.HTTP_200_OK,
            )

        return Response(investments_dict, status=status.HTTP_201_CREATED)


class InvestmentListDB(APIView):

    def get(self, request):
        items = Item.objects.filter(user=request.user)
        investments = []

        for item in items:
            db_accounts = Account.objects.filter(item=item)

            account_id_list = [acc.pk for acc in db_accounts]

            db_investments = Investment.objects.filter(account__in=account_id_list)
            investment_serializer = InvestmentSerializer(db_investments, many=True)

            for inv in investment_serializer.data:
                investments.append(inv)

        return Response(investments, status=status.HTTP_200_OK)
