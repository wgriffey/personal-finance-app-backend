from django.urls import path, include
from .views import UserViewSet, PlaidLinkToken, PublicTokenExchange, AccountListPlaid, AccountListDB, AccountDetailsDB, TransactionListPlaid, TransactionListDB, InvestmentListPlaid, InvestmentListDB
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
    path('api/save_accounts_from_plaid', AccountListPlaid.as_view()),
    path('api/get_accounts', AccountListDB.as_view()),
    path('api/get_account/<int:id>', AccountDetailsDB.as_view()),
    path('api/save_transactions_from_plaid', TransactionListPlaid.as_view()),
    path('api/get_transactions', TransactionListDB.as_view()),
    path('api/save_investments_from_plaid', InvestmentListPlaid.as_view()),
    path('api/get_investments', InvestmentListDB.as_view())

    #paths for class based views
    # path('articles/', ArticleList.as_view()),
    # path('articles/<int:id>/', ArticleDetails.as_view())

    # paths for function based views
    # path('articles/', article_list),
    # path('articles/<int:pk>/', article_details)
]
