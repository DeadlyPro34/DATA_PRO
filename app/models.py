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
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='csv_datasets')

    def __str__(self):
        return f"{self.name} - {self.team.name} ({self.uploaded_at})"

class DataPoint(models.Model):
    label = models.CharField(max_length=255)
    value = models.FloatField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='datapoints')
    csv_file = models.ForeignKey(CSVDataset, on_delete=models.CASCADE, null=True, blank=True, related_name='datapoints')

    def __str__(self):
        return f"{self.label}: {self.value} ({self.team.name})"

import uuid

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

