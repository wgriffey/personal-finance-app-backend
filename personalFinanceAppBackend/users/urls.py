from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
)

urlpatterns = [
    path("", include("djoser.urls")),
    re_path(
        r"^auth/o/(?P<provider>\S+)/$",
        CustomProviderAuthView.as_view(),
        name="provider-auth",
    ),
    path("auth/jwt/create/", CustomTokenObtainPairView.as_view()),
    path("auth/jwt/refresh/", CustomTokenRefreshView.as_view()),
    path("auth/jwt/verify/", CustomTokenVerifyView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
]
