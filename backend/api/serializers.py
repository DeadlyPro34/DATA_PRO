from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Dataset, DataRow


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, label='Confirm password')

    class Meta:
        model  = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'username', 'email')


# ── Dataset ───────────────────────────────────────────────────────────────────

class DatasetSerializer(serializers.ModelSerializer):
    owner      = serializers.StringRelatedField(read_only=True)
    file_size  = serializers.SerializerMethodField()

    class Meta:
        model  = Dataset
        fields = (
            'id', 'name', 'original_name', 'file_type',
            'status', 'error_message',
            'row_count', 'col_count', 'columns',
            'uploaded_at', 'processed_at',
            'owner', 'file_size',
        )
        read_only_fields = (
            'id', 'status', 'row_count', 'col_count', 'columns',
            'uploaded_at', 'processed_at', 'owner', 'file_size',
        )

    def get_file_size(self, obj):
        return obj.file_size_mb


class DatasetUploadSerializer(serializers.Serializer):
    """Used only for the upload endpoint — accepts the raw file."""
    file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_file(self, f):
        from django.conf import settings
        ext = f.name.rsplit('.', 1)[-1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f'File type .{ext} not supported. '
                f'Allowed: {", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)}'
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if f.size > max_bytes:
            raise serializers.ValidationError(
                f'File too large ({round(f.size/1024/1024, 1)} MB). '
                f'Max: {settings.MAX_UPLOAD_SIZE_MB} MB.'
            )
        return f


# ── DataRow ───────────────────────────────────────────────────────────────────

class DataRowSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DataRow
        fields = ('row_index', 'data')
