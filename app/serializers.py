from rest_framework import serializers
from .models import UploadedFile, CleanedDataset


class CleanedDatasetInlineSerializer(serializers.ModelSerializer):
    """Minimal inline serializer — used to pull quality_score into UploadedFileSerializer."""
    class Meta:
        model = CleanedDataset
        fields = ['quality_score']


class UploadedFileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for UploadedFile.
    Includes quality_score from the related CleanedDataset (null when not yet processed).
    """
    quality_score = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            'id',
            'original_filename',
            'file_type',
            'uploaded_at',
            'row_count',
            'column_count',
            'quality_score',
        ]
        read_only_fields = fields

    def get_quality_score(self, obj) -> int | None:
        try:
            return obj.cleaneddataset.quality_score
        except CleanedDataset.DoesNotExist:
            return None


class CleanedDatasetSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for CleanedDataset.
    Exposes the analytical fields needed by external consumers.
    """
    class Meta:
        model = CleanedDataset
        fields = [
            'id',
            'columns',
            'stats',
            'health_report',
            'quality_score',
            'ai_insights',
            'cleaning_log',
        ]
        read_only_fields = fields
