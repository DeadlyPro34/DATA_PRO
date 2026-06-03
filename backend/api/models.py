from django.db import models
from django.contrib.auth.models import User
import os


def upload_to(instance, filename):
    return f'uploads/{instance.owner.id}/{filename}'


class Dataset(models.Model):
    """One uploaded file = one Dataset."""

    STATUS_PENDING    = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_READY      = 'ready'
    STATUS_ERROR      = 'error'

    STATUS_CHOICES = [
        (STATUS_PENDING,    'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_READY,      'Ready'),
        (STATUS_ERROR,      'Error'),
    ]

    owner         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name          = models.CharField(max_length=255)           # custom name or original filename
    original_name = models.CharField(max_length=255)           # raw filename from upload
    file          = models.FileField(upload_to=upload_to)
    file_type     = models.CharField(max_length=10)            # xlsx | xls | xlsm | json
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, default='')
    row_count     = models.IntegerField(default=0)
    col_count     = models.IntegerField(default=0)
    columns       = models.JSONField(default=list)             # list of column header strings
    uploaded_at   = models.DateTimeField(auto_now_add=True)
    processed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.name} ({self.owner.username})'

    @property
    def file_size_mb(self):
        try:
            return round(self.file.size / 1024 / 1024, 2)
        except Exception:
            return 0


class DataRow(models.Model):
    """One spreadsheet row stored as JSON."""

    dataset   = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='rows')
    row_index = models.IntegerField()         # 0-based, excluding header
    data      = models.JSONField()            # {"col_name": value, ...}

    class Meta:
        ordering  = ['row_index']
        # Fast lookup by dataset + page
        indexes = [
            models.Index(fields=['dataset', 'row_index']),
        ]

    def __str__(self):
        return f'Row {self.row_index} of {self.dataset.name}'
