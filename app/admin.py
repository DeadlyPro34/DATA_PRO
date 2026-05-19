from django.contrib import admin
from .models import Team, TeamMember, CSVDataset, DataPoint, TeamInvitation, UploadedFile, CleanedDataset, SavedChart

admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(CSVDataset)
admin.site.register(DataPoint)
admin.site.register(TeamInvitation)
admin.site.register(UploadedFile)
admin.site.register(CleanedDataset)
admin.site.register(SavedChart)
