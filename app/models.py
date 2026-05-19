import uuid
from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_teams')

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

class CSVDataset(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('deleting', 'Deleting'),
    )
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='csv_datasets')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.team.name} ({self.uploaded_at})"

class DataPoint(models.Model):
    label = models.CharField(max_length=255)
    value = models.FloatField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='datapoints')
    csv_file = models.ForeignKey(CSVDataset, on_delete=models.CASCADE, null=True, blank=True, related_name='datapoints')

    def __str__(self):
        return f"{self.label}: {self.value} ({self.team.name})"

class TeamInvitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
    )
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    email = models.EmailField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.email} to {self.team.name} ({self.status})"


class UploadedFile(models.Model):
    FILE_TYPE_CHOICES = (
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)

    def __str__(self):
        return f"{self.original_filename} - {self.user.username} ({self.status})"


class CleanedDataset(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='cleaned_dataset')
    cleaned_at = models.DateTimeField(auto_now_add=True)
    columns = models.JSONField(default=list)
    rows = models.JSONField(default=list)
    cleaning_log = models.JSONField(default=list)

    def __str__(self):
        return f"Cleaned {self.uploaded_file.original_filename}"


class SavedChart(models.Model):
    CHART_TYPE_CHOICES = (
        ('bar', 'Bar'),
        ('line', 'Line'),
        ('pie', 'Pie'),
        ('scatter', 'Scatter'),
    )
    dataset = models.ForeignKey(CleanedDataset, on_delete=models.CASCADE, related_name='saved_charts')
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES)
    x_axis = models.CharField(max_length=255)
    y_axis = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.chart_type})"
