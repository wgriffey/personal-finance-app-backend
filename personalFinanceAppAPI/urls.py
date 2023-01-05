from django.urls import path, include
from .views import UserViewSet, create_plaid_link_token, exchange_public_token, get_accounts_from_plaid, get_accounts_from_db, get_transactions_from_plaid
from rest_framework.routers import DefaultRouter

## View imports depending on method
## article_list, article_details ArticleList, ArticleDetails, ArticleViewSet

router = DefaultRouter()
# router.register(r'articles', ArticleViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/create_link_token/', create_plaid_link_token),
    path('api/set_access_token/', exchange_public_token),
    path('api/get_accounts_from_plaid', get_accounts_from_plaid),
    path('api/get_accounts_from_db', get_accounts_from_db),
    path('api/get_transactions_from_plaid', get_transactions_from_plaid)




    #paths for class based views
    # path('articles/', ArticleList.as_view()),
    # path('articles/<int:id>/', ArticleDetails.as_view())

    # paths for function based views
    # path('articles/', article_list),
    # path('articles/<int:pk>/', article_details)
]
