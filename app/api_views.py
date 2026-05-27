from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import UploadedFile, CleanedDataset, TeamMembership
from .serializers import UploadedFileSerializer, CleanedDatasetSerializer
from django.db.models import Q


def _user_file_qs(user):
    """Return a queryset of UploadedFiles the user is allowed to see."""
    team_ids = TeamMembership.objects.filter(
        user=user).values_list('team_id', flat=True)
    return UploadedFile.objects.filter(
        Q(user=user) | Q(team_id__in=team_ids)
    ).select_related('cleaneddataset').order_by('-uploaded_at')


class DatasetListView(APIView):
    """
    GET /api/v1/datasets/
    Returns all UploadedFiles belonging to or shared with the authenticated user.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        files = _user_file_qs(request.user)
        serializer = UploadedFileSerializer(files, many=True)
        return Response(serializer.data)


class DatasetDetailView(APIView):
    """
    GET /api/v1/datasets/<id>/
    Returns full UploadedFile details for one dataset owned by / shared with the user.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = _user_file_qs(request.user)
        uploaded_file = get_object_or_404(qs, pk=pk)
        serializer = UploadedFileSerializer(uploaded_file)
        return Response(serializer.data)


class DatasetInsightsView(APIView):
    """
    GET /api/v1/datasets/<id>/insights/
    Returns the AI-generated insights list for a dataset.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = _user_file_qs(request.user)
        uploaded_file = get_object_or_404(qs, pk=pk)
        dataset = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)
        return Response({
            'file_id': pk,
            'filename': str(uploaded_file),
            'ai_insights': dataset.ai_insights,
        })


class DatasetStatsView(APIView):
    """
    GET /api/v1/datasets/<id>/stats/
    Returns the statistical summary (pandas .describe() output) for a dataset.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = _user_file_qs(request.user)
        uploaded_file = get_object_or_404(qs, pk=pk)
        dataset = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)
        return Response({
            'file_id': pk,
            'filename': str(uploaded_file),
            'columns': dataset.columns,
            'stats': dataset.stats,
            'health_report': dataset.health_report,
            'quality_score': dataset.quality_score,
        })
