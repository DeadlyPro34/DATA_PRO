from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamMembership(models.Model):
    ROLES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10) # csv, excel, json
    uploaded_at = models.DateTimeField(auto_now_add=True)
    custom_name = models.CharField(max_length=255, blank=True)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.custom_name or self.original_filename

class CleanedDataset(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE)
    cleaned_at = models.DateTimeField(auto_now_add=True)
    columns = models.JSONField(default=list)
    rows = models.JSONField(default=list, null=True, blank=True)
    parquet_path = models.CharField(max_length=512, blank=True, null=True)
    cleaning_log = models.JSONField(default=list)
    stats = models.JSONField(default=dict) # for pandas .describe()
    raw_snapshot = models.JSONField(default=list)      # first 200 rows pre-cleaning
    raw_columns = models.JSONField(default=list)       # original column names
    health_report = models.JSONField(default=dict)     # data health scan results
    quality_score = models.IntegerField(default=100)   # 0-100 quality score
    cleaning_actions = models.JSONField(default=list)  # structured cleaning actions
    before_after = models.JSONField(default=dict)      # before vs after stats
    ai_insights = models.JSONField(default=list)       # AI-generated insights
    cell_annotations = models.JSONField(default=dict)  # cell-level issue markers
    cleaning_options = models.JSONField(default=dict)  # user-selected cleaning toggles
    pipeline_history = models.JSONField(default=list)  # History of applied pipelines for undo

    def __str__(self):
        return f"Cleaned Dataset for {self.uploaded_file}"

class SavedPipeline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    operations = models.JSONField(default=list) # List of dicts with operation config
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
