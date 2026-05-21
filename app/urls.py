from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('dataset/<int:file_id>/', views.dataset_view, name='dataset_view'),
    path('dataset/<int:file_id>/delete/', views.delete_dataset, name='delete_dataset'),
    path('dataset/<int:file_id>/chart-data/', views.chart_data, name='chart_data'),
    path('dataset/<int:file_id>/advanced-stats/', views.advanced_stats, name='advanced_stats'),
    path('register/', views.register, name='register'),
]
