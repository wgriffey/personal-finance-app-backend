import json
import os
from datetime import datetime, timedelta

from django.db import IntegrityError
from dotenv import load_dotenv
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
from rest_framework import generics, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Account, Institution, Investment, Item, Transaction
from .serializers import (
    AccountSerializer,
    InstitutionSerializer,
    InvestmentSerializer,
    TransactionSerializer,
)
from .utils import clean_accounts_data, clean_investment_data, clean_transaction_data

load_dotenv("./env/.env.sandbox")

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


class PlaidLinkToken(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

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
            return Response(update_link_response.to_dict(), status=status.HTTP_201_CREATED)

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
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user
        public_token = request.data["publicToken"]

        token_request = ItemPublicTokenExchangeRequest(public_token=public_token)

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

        access_token = token_response["access_token"]
        item_id = token_response["item_id"]

        # Get Institution ID That Item ID Relates To
        item_request = ItemGetRequest(access_token=access_token)

        item_response = client.item_get(item_request)

        institution_id = item_response["item"]["institution_id"]

        institution_request = InstitutionsGetByIdRequest(
            institution_id=institution_id, country_codes=[CountryCode("US")]
        )

        institution_response = client.institutions_get_by_id(institution_request)

        # Save New Institutions to DB
        if Institution.objects.filter(institution_id=institution_id):
            pass
        else:
            try:
                institution = Institution.objects.create(
                    institution_id=institution_id,
                    institution_name=institution_response["institution"]["name"],
                )
                institution.save()
            except Exception as e:
                return Response(
                    data={"message": "Failed to Save Institution", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        institution_pk = Institution.objects.get(institution_id=institution_id).pk

        if Item.objects.filter(user=user, institution_id=institution_pk):
            return Response("Item for Institution Exists for User", status=status.HTTP_409_CONFLICT)

        # Save Item to Database
        try:
            item = Item.objects.create(
                user=user,
                item_id=item_id,
                access_token=access_token,
                institution_id=institution_pk,
            )
            item.save()
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
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, account_id):
        account = Account.objects.get(id=account_id)

        item = Item.objects.get(id=account.item.pk)

        institution = Institution.objects.get(id=item.institution_id)

        institution_serializer = InstitutionSerializer(institution)

        return Response(institution_serializer.data, status=status.HTTP_200_OK)


class AccountListPlaid(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

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
                if Account.objects.filter(item_id=acc["item"], account_id=acc["account_id"]):
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
            return Response("No New Accounts to Save From Plaid", status=status.HTTP_409_CONFLICT)

        return Response(accounts_dict, status=status.HTTP_201_CREATED)


class AccountListDB(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user=request.user)

        accounts = []

        for item in items:
            db_accounts = Account.objects.filter(item_id=item.id)
            account_serializer = AccountSerializer(db_accounts, many=True)
            for acc in account_serializer.data:
                accounts.append(acc)

        return Response(accounts, status=status.HTTP_200_OK)


class AccountDetailsDB(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, id):
        try:
            account = Account.objects.get(id=id)
            account_serializer = AccountSerializer(account)
        except:
            return Response("Account Not Found", status=status.HTTP_404_NOT_FOUND)
        return Response(account_serializer.data, status=status.HTTP_200_OK)


class TransactionListPlaid(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        items = Item.objects.filter(user=request.user)
        transactions_saved_list = []
        transactions_dict = {}

        for item in items:
            access_token = item.access_token

            start_date = (datetime.now() - timedelta(days=720)).date()
            end_date = datetime.now().date()

            if ("start_date" in request.data and request.data["start_date"] is not None) and (
                "end_date" in request.data and request.data["end_date"] is not None
            ):
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
                transactions_dict[item.institution_id] = transactions_saved_list

        if not transactions_dict:
            return Response(
                "No New Transactions to Save From Plaid",
                status=status.HTTP_409_CONFLICT,
            )

        return Response(transactions_dict, status=status.HTTP_201_CREATED)


class TransactionListDB(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user=request.user)
        start_date = request.query_params.get(
            "start_date",
        )
        end_date = request.query_params.get("end_date", datetime.now().date())
        if start_date == "undefined" or end_date == "undefined":
            start_date = (datetime.now() - timedelta(days=720)).date()
            end_date = datetime.now().date()
        print(f"Start: {start_date} End: {end_date}")
        transactions = []
        for item in items:
            db_accounts = Account.objects.filter(item_id=item.id)

            account_id_list = [acc.id for acc in db_accounts]

            db_transactions = Transaction.objects.filter(
                account__in=account_id_list, date__range=(start_date, end_date)
            )
            transaction_serializer = TransactionSerializer(db_transactions, many=True)
            for tran in transaction_serializer.data:
                transactions.append(tran)

        return Response(
            sorted(transactions, key=lambda t: t["date"], reverse=True),
            status=status.HTTP_200_OK,
        )


class TransactionDetailsDB(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class InvestmentListPlaid(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

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
            investment_data = clean_investment_data(response["holdings"], response["securities"])

            # Skip Existing Investments for an Account and Save New Investments for an Account
            for investment in investment_data:
                if Investment.objects.filter(
                    account_id=investment["account"],
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
                status=status.HTTP_409_CONFLICT,
            )

        return Response(investments_dict, status=status.HTTP_201_CREATED)


class InvestmentListDB(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user=request.user)
        investments = []

        for item in items:
            db_accounts = Account.objects.filter(item_id=item.id)

            account_id_list = [acc.id for acc in db_accounts]

            db_investments = Investment.objects.filter(account__in=account_id_list)
            investment_serializer = InvestmentSerializer(db_investments, many=True)

            for inv in investment_serializer.data:
                investments.append(inv)

        return Response(investments, status=status.HTTP_200_OK)
