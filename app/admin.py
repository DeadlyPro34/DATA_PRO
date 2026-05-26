from django.contrib import admin

# Register your models here.
from .models import Team, TeamMembership, UploadedFile, CleanedDataset

class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    inlines = [TeamMembershipInline]

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'team')

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'team', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'team')

@admin.register(CleanedDataset)
class CleanedDatasetAdmin(admin.ModelAdmin):
    list_display = ('uploaded_file', 'cleaned_at')
