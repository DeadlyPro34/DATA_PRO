from rest_framework import serializers, viewsets
from .models import UploadedFile, CleanedDataset, Team, TeamMembership
from django.db.models import Q

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'

class CleanedDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CleanedDataset
        fields = '__all__'

class UploadedFileViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedFileSerializer

    def get_queryset(self):
        user = self.request.user
        return UploadedFile.objects.filter(
            Q(user=user) | Q(team__teammembership__user=user)
        ).distinct()

class CleanedDatasetViewSet(viewsets.ModelViewSet):
    serializer_class = CleanedDatasetSerializer

    def get_queryset(self):
        user = self.request.user
        return CleanedDataset.objects.filter(
            Q(uploaded_file__user=user) | Q(uploaded_file__team__teammembership__user=user)
        ).distinct()
