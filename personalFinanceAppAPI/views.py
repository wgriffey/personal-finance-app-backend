from datetime import datetime, timedelta
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
from .models import InvestmentHolding, InvestmentSecurity, Item, Account, Transaction
from .serializers import InvestmentHoldingSerializer, InvestmentSecuritySerializer, UserSerializer, AccountSerializer, TransactionSerializer
from .permissions import IsCreationOrIsAuthenticated
from .utils import clean_accounts_data, clean_investment_data, clean_transaction_data, remove_duplicate_accounts, remove_duplicate_holdings, remove_duplicate_securities, remove_duplicate_transactions, remove_duplicate_user_items
from plaid import Configuration, Environment, ApiClient, ApiException
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
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

## Create Plaid Link Token
@api_view(['POST'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
@ensure_csrf_cookie
def create_plaid_link_token(request):
    user = request.user
    client_user_id = str(user.id)

    # Create a link_token for the given user
    request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="G&E Personal Finance",
        country_codes=[CountryCode('US')],
        redirect_uri='http://localhost:3000/',
        language='en',
        webhook='https://webhook.example.com',
        user=LinkTokenCreateRequestUser(
            client_user_id=client_user_id
        )
    )
    response = client.link_token_create(request)
    # Send the data to the client
    return JsonResponse(response.to_dict())

## Exchange Public Token for Access Token
@api_view(['POST'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
@ensure_csrf_cookie
def exchange_public_token(request):
    global access_token
    global item_id

    user = request.user

    ## Remove Existing Item For User So that Updated Item is Added
    remove_duplicate_user_items(user = user)

    public_token = request.data['public_token']
    request = ItemPublicTokenExchangeRequest(
      public_token=public_token
    )
    response = client.item_public_token_exchange(request)
    
    access_token = response['access_token']
    item_id = response['item_id']
    
    # Save Item to Database
    item = Item.objects.create(user = user, item_id = item_id, access_token = access_token)
    item.save()
    
    data = {
        "access_token": access_token,
        "item_id": item_id
    }

    print('Access Token and Item ID' + str(data))

    return JsonResponse(data, status = status.HTTP_201_CREATED)

## Get Accounts From Plaid API and Save to DB
@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_accounts_from_plaid(request):
    global access_token
    
    item = Item.objects.filter(user=request.user)
    access_token = item[0].access_token

    print(f'Item: {item} Access Token: {access_token}')
    
    try:
        request = AccountsGetRequest(
            access_token=access_token
        )
        accounts_response = client.accounts_get(request)
        print('INITIAL ACCOUNTS DATA: ' + str(accounts_response))

        # Clean the Account Data and Save to DB
        accounts = clean_accounts_data(item[0].pk, accounts_response['accounts']) 
        
        # Save Account Data to DB
        serializer = AccountSerializer(data=accounts, many=True)

        # Ensure that there aren't duplicate accounts
        remove_duplicate_accounts(accounts=accounts)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status = status.HTTP_200_OK)    


    except ApiException as e:
        response = JSONParser(e.body)
        return JsonResponse({'error': {'status_code': e.status, 'display_message':
                        response['error_message'], 'error_code': response['error_code'], 'error_type': response['error_type']}})

## Get Accounts From DB
@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_accounts_from_db(request):
    
    item = Item.objects.filter(user = request.user)

    dbAccounts = Account.objects.filter(item_id=item[0].id)

    accounts = list(dbAccounts.values())

    print(f'ACCOUNTS: {accounts}')

    return Response(accounts, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_transactions_from_plaid(request):
    item = Item.objects.filter(user=request.user)
    access_token = item[0].access_token

    start_date = (datetime.now() - timedelta(days=30)).date()
    end_date = datetime.now().date()

    if ('start_date' in request.data and request.data['start_date'] is not None) and ('end_date' in request.data and request.data['end_date'] is not None):
        start_date = request.data['start_date']
        end_date = request.data['end_date']
    
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions()
    )

    response = client.transactions_get(request)

    print('TRANSACTIONS: ' + str(response))

    transactions = clean_transaction_data(response['transactions'])
                
    serializer = TransactionSerializer(data=transactions, many=True)

    remove_duplicate_transactions(transactions)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status= status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_transactions_from_db(request):
    item = Item.objects.filter(user = request.user)

    dbAccounts = Account.objects.filter(item_id=item[0].id)

    account_id_list = []
    for acc in dbAccounts:
        account_id_list.append(acc.pk)
    
    transactions = Transaction.objects.filter(account__in=account_id_list)
    transactions_list = list(transactions.values())

    return Response(transactions_list, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_investments_from_plaid(request):
    item = Item.objects.filter(user=request.user)
    access_token = item[0].access_token
    
    request = InvestmentsHoldingsGetRequest(
        access_token=access_token,
    )

    response = client.investments_holdings_get(request)

    investment_holdings, investment_securities = clean_investment_data(response['holdings'], response['securities'])

    holdings_serializer = InvestmentHoldingSerializer(data=investment_holdings, many=True)         
    securities_serializer = InvestmentSecuritySerializer(data=investment_securities, many=True)

    remove_duplicate_securities(investment_securities)
    remove_duplicate_holdings(investment_holdings)

    securities_serializer.is_valid(raise_exception=True)
    securities_serializer.save()

    holdings_serializer.is_valid(raise_exception=True)
    holdings_serializer.save()

    return Response([holdings_serializer.data, securities_serializer.data], status= status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsCreationOrIsAuthenticated])
def get_investments_from_db(request):
    item = Item.objects.filter(user = request.user)

    dbAccounts = Account.objects.filter(item_id=item[0].id)

    account_id_list = []
    for acc in dbAccounts:
        account_id_list.append(acc.pk)
    
    investment_holdings = InvestmentHolding.objects.filter(account__in=account_id_list)
    holdings_list = list(investment_holdings.values())

    holdings_security_ids = []
    for holding in holdings_list:
        holdings_security_ids.append(holding['security_id'])
    
    investment_securities = InvestmentSecurity.objects.filter(security_id__in=holdings_security_ids)
    securities_list = list(investment_securities.values())

    return Response([holdings_list, securities_list], status=status.HTTP_200_OK)

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

        
