from django.urls import path, include
from .views import UserViewSet, PlaidLinkToken, PublicTokenExchange, GetAccountsPlaid, GetAccountsDB, GetTransactionsPlaid, GetTransactionsDB, GetInvestmentsPlaid, GetInvestmentsDB
from rest_framework.routers import DefaultRouter

## View imports depending on method
## article_list, article_details ArticleList, ArticleDetails, ArticleViewSet

router = DefaultRouter()
# router.register(r'articles', ArticleViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/create_link_token/', PlaidLinkToken.as_view()),
    path('api/set_access_token/', PublicTokenExchange.as_view()),
    path('api/get_accounts_from_plaid', GetAccountsPlaid.as_view()),
    path('api/get_accounts_from_db', GetAccountsDB.as_view()),
    path('api/get_transactions_from_plaid', GetTransactionsPlaid.as_view()),
    path('api/get_transactions_from_db', GetTransactionsDB.as_view()),
    path('api/get_investments_from_plaid', GetInvestmentsPlaid.as_view()),
    path('api/get_investments_from_db', GetInvestmentsDB.as_view())

    #paths for class based views
    # path('articles/', ArticleList.as_view()),
    # path('articles/<int:id>/', ArticleDetails.as_view())

    # paths for function based views
    # path('articles/', article_list),
    # path('articles/<int:pk>/', article_details)
]
