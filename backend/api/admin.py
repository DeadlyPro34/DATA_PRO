from django.contrib import admin
from .models import Dataset, DataRow


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display  = ('name', 'owner', 'file_type', 'status', 'row_count', 'col_count', 'uploaded_at')
    list_filter   = ('status', 'file_type')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('uploaded_at', 'processed_at', 'row_count', 'col_count', 'columns', 'status')


@admin.register(DataRow)
class DataRowAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'row_index')
    list_filter  = ('dataset',)
