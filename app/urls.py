from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    
    # Modular Dataset Pages
    path('dataset/<int:file_id>/lab/', views.cleaning_lab, name='cleaning_lab'),
    path('dataset/<int:file_id>/explorer/', views.data_explorer, name='data_explorer'),
    path('dataset/<int:file_id>/analytics/', views.analytics_studio, name='analytics_studio'),
    path('dataset/<int:file_id>/insights/', views.ai_insights_page, name='ai_insights_page'),
    path('dataset/<int:file_id>/exports/', views.exports_page, name='exports_page'),
    
    # API endpoints
    path('dataset/<int:file_id>/reclean/', views.reclean_dataset, name='reclean_dataset'),
    path('dataset/<int:file_id>/delete/', views.delete_dataset, name='delete_dataset'),
    path('dataset/<int:file_id>/chart-data/', views.chart_data, name='chart_data'),
    path('dataset/<int:file_id>/advanced-stats/', views.advanced_stats, name='advanced_stats'),
    path('dataset/<int:file_id>/chat/', views.ai_chat_api, name='ai_chat_api'),
    
    path('register/', views.register, name='register'),
    path('dataset/<int:file_id>/profiler/', views.data_profiler, name='data_profiler'),
]
