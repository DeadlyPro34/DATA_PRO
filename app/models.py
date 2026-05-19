from django.db import models
from django.contrib.auth.models import User

class UploadedFile(models.fields.Field):
    pass # Wait I need to use Model, hold on.

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    rows = models.JSONField(default=list)
    cleaning_log = models.JSONField(default=list)
    stats = models.JSONField(default=dict) # for pandas .describe()

    def __str__(self):
        return f"Cleaned Dataset for {self.uploaded_file}"
