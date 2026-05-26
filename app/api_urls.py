from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views
from .api_views import UploadedFileViewSet, CleanedDatasetViewSet

router = DefaultRouter()
router.register(r'datasets', CleanedDatasetViewSet, basename='dataset')
router.register(r'files', UploadedFileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', auth_views.obtain_auth_token, name='api_token_auth'),
]
