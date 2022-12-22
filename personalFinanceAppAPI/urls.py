from django.urls import path, include
from .views import ArticleViewSet, UserViewSet
from rest_framework.routers import DefaultRouter

## View imports depending on method
## article_list, article_details ArticleList, ArticleDetails

router = DefaultRouter()
router.register(r'articles', ArticleViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),

    #paths for class based views
    # path('articles/', ArticleList.as_view()),
    # path('articles/<int:id>/', ArticleDetails.as_view())

    # paths for function based views
    # path('articles/', article_list),
    # path('articles/<int:pk>/', article_details)
]
