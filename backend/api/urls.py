from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path('auth/register/',  views.RegisterView.as_view(), name='register'),
    path('auth/login/',     TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/',   TokenRefreshView.as_view(),    name='token_refresh'),
    path('auth/me/',        views.me_view,                 name='me'),

    # ── Dataset CRUD ──────────────────────────────────────────────────────
    path('datasets/',                     views.dataset_list,   name='dataset_list'),
    path('datasets/upload/',              views.dataset_upload, name='dataset_upload'),
    path('datasets/<int:pk>/',            views.dataset_detail, name='dataset_detail'),
    path('datasets/<int:pk>/delete/',     views.dataset_delete, name='dataset_delete'),
    path('datasets/<int:pk>/rows/',       views.dataset_rows,   name='dataset_rows'),

    # ── NEW: Cell / Row / Column Operations ───────────────────────────────
    path('datasets/<int:pk>/update_cell/',                    views.update_cell,    name='update_cell'),
    path('datasets/<int:pk>/add_row/',                        views.add_row,        name='add_row'),
    path('datasets/<int:pk>/delete_row/<int:row_index>/',     views.delete_row,     name='delete_row'),
    path('datasets/<int:pk>/add_column/',                     views.add_column,     name='add_column'),

    # ── NEW: Excel Functions ──────────────────────────────────────────────
    path('datasets/<int:pk>/function/',   views.apply_function, name='apply_function'),

    # ── NEW: AI Pandas ────────────────────────────────────────────────────
    path('datasets/<int:pk>/ai_pandas/',  views.ai_pandas,      name='ai_pandas'),

    # ── NEW: Auto Dashboard (pure Pandas, no AI API) ──────────────────────
    path('datasets/<int:pk>/auto_dashboard/', views.auto_dashboard, name='auto_dashboard'),
]
