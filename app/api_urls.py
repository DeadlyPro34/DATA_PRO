from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .api_views import (
    DatasetListView,
    DatasetDetailView,
    DatasetInsightsView,
    DatasetStatsView,
)

api_patterns = [
    # Token auth
    path('token/', obtain_auth_token, name='api_token'),

    # Dataset endpoints
    path('datasets/', DatasetListView.as_view(), name='api_dataset_list'),
    path('datasets/<int:pk>/', DatasetDetailView.as_view(), name='api_dataset_detail'),
    path('datasets/<int:pk>/insights/', DatasetInsightsView.as_view(), name='api_dataset_insights'),
    path('datasets/<int:pk>/stats/', DatasetStatsView.as_view(), name='api_dataset_stats'),
]

urlpatterns = api_patterns
