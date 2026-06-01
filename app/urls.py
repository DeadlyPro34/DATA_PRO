from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    
    # Modular Dataset Pages
    path('dataset/<int:file_id>/lab/', views.cleaning_lab, name='cleaning_lab'),
    path('dataset/<int:file_id>/cleaning-center/', views.cleaning_center_view, name='cleaning_center'),
    path('dataset/<int:file_id>/explorer/', views.data_explorer, name='data_explorer'),
    path('dataset/<int:file_id>/analytics/', views.analytics_studio, name='analytics_studio'),
    path('dataset/<int:file_id>/insights/', views.ai_insights_page, name='ai_insights_page'),
    path('dataset/<int:file_id>/exports/', views.exports_page, name='exports_page'),
    path('dataset/<int:file_id>/export/excel/', views.export_excel, name='export_excel'),
    path('dataset/<int:file_id>/export/pdf/', views.export_pdf, name='export_pdf'),
    
    # API endpoints
    path('dataset/<int:file_id>/reclean/', views.reclean_dataset, name='reclean_dataset'),
    path('dataset/<int:file_id>/delete/', views.delete_dataset, name='delete_dataset'),
    path('dataset/<int:file_id>/chart-data/', views.chart_data, name='chart_data'),
    path('dataset/<int:file_id>/advanced-stats/', views.advanced_stats, name='advanced_stats'),
    path('dataset/<int:file_id>/rows/', views.dataset_rows_api, name='dataset_rows_api'),
    path('dataset/<int:file_id>/chart-suggestions/', views.chart_suggestions, name='chart_suggestions'),
    path('dataset/<int:file_id>/api/preview-cleaning/', views.api_preview_cleaning, name='api_preview_cleaning'),
    path('dataset/<int:file_id>/api/apply-cleaning/', views.api_apply_cleaning, name='api_apply_cleaning'),
    
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/invite/', views.invite_member, name='invite_member'),
    path('teams/<int:team_id>/settings/', views.team_settings, name='team_settings'),
    
    path('register/', views.register, name='register'),
    path('dataset/<int:file_id>/profiler/', views.data_profiler, name='data_profiler'),
    path('dataset/<int:file_id>/sheets/', views.sheet_viewer, name='sheet_viewer'),
]
