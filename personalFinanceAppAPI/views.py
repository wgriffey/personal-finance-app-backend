from datetime import datetime, timedelta
from django.db import IntegrityError
from django.shortcuts import render, HttpResponse, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate
from authuser.models import User
from rest_framework import status, generics, mixins, viewsets
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, permission_classes, authentication_classes, APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import Token
from rest_framework.permissions import IsAuthenticated
from .models import Investment, Item, Account, Transaction
from .serializers import InvestmentSerializer, UserSerializer, AccountSerializer, TransactionSerializer
from .permissions import IsCreationOrIsAuthenticated
from .utils import clean_accounts_data, clean_investment_data, clean_transaction_data
from plaid import Configuration, Environment, ApiClient, ApiException
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv('./env/.env.sandbox')

host = Environment.Sandbox

access_token = None

item_id = None

configuration = Configuration(
    host=host,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
        'plaidVersion': '2020-09-14'
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = (TokenAuthentication,)

class PlaidLinkToken(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        # Create a link_token for the given user
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="G&E Personal Finance",
            country_codes=[CountryCode('US')],
            redirect_uri='http://localhost:3000/',
            language='en',
            webhook='https://webhook.example.com',
            user=LinkTokenCreateRequestUser(
                client_user_id=str(user.id)
            )
        )
        response = client.link_token_create(request)
        # Send the data to the client
        return Response(response.to_dict(), status=status.HTTP_201_CREATED)

class PublicTokenExchange(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        public_token = request.data['public_token']
        
        tokenRequest = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        
        tokenResponse = client.item_public_token_exchange(tokenRequest)
        
        access_token = tokenResponse['access_token']
        item_id = tokenResponse['item_id']

        # Get Institution ID That Item ID Relates To
        itemRequest = ItemGetRequest(
            access_token=access_token
        )

        itemResponse = client.item_get(itemRequest)

        institution_id = itemResponse['item']['institution_id']

        if Item.objects.filter(user=user, item_id=item_id, access_token=access_token, institution_id=institution_id):
            return Response("Item for Institution Exists for User", status=status.HTTP_409_CONFLICT)
        
        # Save Item to Database
        try:
            item = Item.objects.create(user = user, item_id = item_id, access_token = access_token, institution_id = institution_id)
            item.save()
        except Exception as e:
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response('Item and Access Token Generated User Access to Institution', status = status.HTTP_201_CREATED)
    
class AccountListPlaid(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):        
        items = Item.objects.filter(user=request.user)
        accounts_dict = {}
        
        # Get All Accounts For User
        for item in items:
            access_token = item.access_token
        
            try:
                accounts_request = AccountsGetRequest(
                    access_token=access_token
                )
                accounts_response = client.accounts_get(accounts_request)
                print('INITIAL ACCOUNTS DATA: ' + str(accounts_response))
            except ApiException as e:
                response = JSONParser(e.body)
                return JsonResponse({'error': {'status_code': e.status, 'display_message':
                                response['error_message'], 'error_code': response['error_code'], 'error_type': response['error_type']}})

            # Clean the Account Data
            accounts = clean_accounts_data(item.pk, accounts_response['accounts']) 
            
            # Skip Existing Accounts
            if Account.objects.filter(item_id=item.id):
                continue

            try:
                # Save Account Data to DB
                serializer = AccountSerializer(data=accounts, many=True)         
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except IntegrityError as e:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            accounts_dict[item.institution_id] = serializer.data

        if not accounts_dict:
            return Response("No New Accounts to Save From Plaid", status=status.HTTP_409_CONFLICT)
        
        return Response(accounts_dict, status = status.HTTP_200_OK) 

class AccountListDB(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user = request.user)

        accounts = []

        for item in items:
            dbAccounts = Account.objects.filter(item_id=item.id)
            serializer = AccountSerializer(dbAccounts, many=True)
            for acc in serializer.data:
                accounts.append(acc)

        return Response(accounts, status=status.HTTP_200_OK)

class AccountDetailsDB(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, id):
        try:
            account = Account.objects.get(id=id)
            serializer = AccountSerializer(account)
        except:
            return Response('Account Not Found', status=status.HTTP_404_NOT_FOUND)  
        return Response(serializer.data, status=status.HTTP_200_OK)        


class TransactionListPlaid(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request):
        items = Item.objects.filter(user=request.user)
        transactions_dict = {}

        for item in items:
            access_token = item.access_token

            start_date = (datetime.now() - timedelta(days=30)).date()
            end_date = datetime.now().date()

            if ('start_date' in request.data and request.data['start_date'] is not None) and ('end_date' in request.data and request.data['end_date'] is not None):
                start_date = request.data['start_date']
                end_date = request.data['end_date']
            
            transaction_request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )

            response = client.transactions_get(transaction_request)

            ## Clean the Transaction Data
            transactions = clean_transaction_data(response['transactions'])

            ## Skip Existing Transactions
            transaction_ids = [tran['transaction_id'] for tran in transactions]
            if Transaction.objects.filter(transaction_id__in=transaction_ids):
                continue

            try:
                serializer = TransactionSerializer(data=transactions, many=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except IntegrityError as e:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            transactions_dict[item.institution_id] = serializer.data

        if not transactions_dict:
            return Response("No New Transactions to Save From Plaid", status=status.HTTP_409_CONFLICT)
            
        return Response(transactions_dict, status= status.HTTP_200_OK)

class TransactionListDB(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user = request.user)
        transactions = []
        for item in items:
            dbAccounts = Account.objects.filter(item_id=item.id)

            account_id_list = [acc.id for acc in dbAccounts]
        
            dbTransactions = Transaction.objects.filter(account__in=account_id_list)
            serializer = TransactionSerializer(dbTransactions, many=True)
            for tran in serializer.data:
                transactions.append(tran)

        return Response(transactions, status=status.HTTP_200_OK)
    
class InvestmentListPlaid(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        items = Item.objects.filter(user=request.user)
        investment_data_dict = {}

        for item in items:

            access_token = item.access_token
        
            investment_request = InvestmentsHoldingsGetRequest(
                access_token=access_token,
            )

            response = client.investments_holdings_get(investment_request)

            ## Clean Investment Data
            investment_data = clean_investment_data(response['holdings'], response['securities'])

            #Skip Existing Investment Accounts
            dbAccounts = Account.objects.filter(item_id=item.id)
            account_id_list = [acc.id for acc in dbAccounts]
            account_security_found = False
            
            for investment in investment_data:
                if Investment.objects.filter(account_id__in=account_id_list, security_id=investment['security_id']):
                    account_security_found = True
            
            if account_security_found:
                continue

            try:
                investment_serializer = InvestmentSerializer(data=investment_data, many=True)         
                investment_serializer.is_valid(raise_exception=True)
                investment_serializer.save()
            except IntegrityError as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            
            investment_data_dict[item.institution_id] = investment_serializer.data
        
        if not investment_data_dict:
            return Response("No New Investment Accounts to Save From Plaid", status=status.HTTP_409_CONFLICT)

        return Response(investment_data_dict, status= status.HTTP_200_OK)
    
class InvestmentListDB(APIView):
    permission_classes = [IsCreationOrIsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        items = Item.objects.filter(user = request.user)
        investments = []

        for item in items:
            dbAccounts = Account.objects.filter(item_id=item.id)

            account_id_list = [acc.id for acc in dbAccounts]

            dbInvestments = Investment.objects.filter(account__in=account_id_list)
            serializer = InvestmentSerializer(dbInvestments, many=True)

            for inv in serializer.data:
                investments.append(inv)
            
        return Response(investments, status=status.HTTP_200_OK)

'''
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

'''

#GenericViewSets with mixins
'''
class ArticleViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
'''

#ViewSets
'''
class ArticleViewSet(viewsets.ViewSet):
    def list(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        queryset = Article.objects.all()
        article = get_object_or_404(queryset, pk=pk)
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    def update(self, request, pk=None):
        article = Article.objects.get(pk=pk)

        serializer = ArticleSerializer(article, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        article = Article.objects.get(pk=pk)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

'''

#GenericAPIView with Mixins
'''
class ArticleList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get(self, request):
        return self.list(request)

    def post(self, request):
        return self.create(request)   

class ArticleDetails(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    lookup_field = 'id'

    def get(self, request, id):
        return self.retrieve(request, id=id)

    def put(self, request, id):
        return self.update(request, id=id)

    def delete(self, request, id):
        self.destroy(request, id=id)
'''       

# APIViews
'''
class ArticleList(APIView):
    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ArticleSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ArticleDetails(APIView):

    def get_object(self, id):
        try:
            return Article.objects.get(id=id)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)    

    def get(self, request, id):
        article = self.get_object(id)
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    def put(self, request, id):
        article = self.get_object(id)
        serializer = ArticleSerializer(article, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        article = self.get_object(id)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  

'''          

# Function Based Views
'''
@api_view(['GET', 'POST'])
def article_list(request):
    #get all articles
    if request.method == 'GET':
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ArticleSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def article_details(request, pk):
    try:
        article = Article.objects.get(pk=pk)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ArticleSerializer(article, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)   

'''

        
