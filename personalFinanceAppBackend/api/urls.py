from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountDetailsDB,
    AccountListDB,
    AccountListPlaid,
    InstitutionDetailsDB,
    InvestmentListDB,
    InvestmentListPlaid,
    PlaidLinkToken,
    PublicTokenExchange,
    TransactionDetailsDB,
    TransactionListDB,
    TransactionListPlaid,
)

urlpatterns = [
    path("api/create_link_token/", PlaidLinkToken.as_view()),
    path("api/set_access_token/", PublicTokenExchange.as_view()),
    path(
        "api/get_institution_by_account_id/<int:account_id>",
        InstitutionDetailsDB.as_view(),
    ),
    path("api/save_accounts_from_plaid", AccountListPlaid.as_view()),
    path("api/get_accounts", AccountListDB.as_view()),
    path("api/get_account/<int:id>", AccountDetailsDB.as_view()),
    path("api/save_transactions_from_plaid", TransactionListPlaid.as_view()),
    path("api/get_transactions", TransactionListDB.as_view()),
    path("api/transaction/<int:pk>", TransactionDetailsDB.as_view()),
    path("api/save_investments_from_plaid", InvestmentListPlaid.as_view()),
    path("api/get_investments", InvestmentListDB.as_view()),
]
