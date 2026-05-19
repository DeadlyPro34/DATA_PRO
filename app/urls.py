from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('team/', views.team_view, name='team'),
    path('team/accept/<uuid:token>/', views.accept_invite_view, name='accept_invite'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('datasets/', views.datasets_view, name='datasets'),
    path('datasets/status/<int:csv_id>/', views.csv_status_view, name='csv_status'),
    path('settings/', views.settings_view, name='settings'),
]
