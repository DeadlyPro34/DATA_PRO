from .models import Team, TeamMember, DataPoint

def create_team_for_user(user):
    """
    Creates a default team for a user, registers them as admin, and seeds initial data.
    
    # NOTE: This should ideally be handled by a Django post_save signal on the User model
    # to automatically provision a team and seed data upon account creation.
    """
    team = Team.objects.create(name=f"{user.username}'s Team", owner=user)
    TeamMember.objects.create(user=user, team=team, role='admin')
    
    # Seed default datapoints to render stunning reports out-of-the-box
    DataPoint.objects.create(label='Organic Traffic', value=14.2, team=team)
    DataPoint.objects.create(label='Web API', value=28.4, team=team)
    DataPoint.objects.create(label='Social Media', value=8.9, team=team)
    DataPoint.objects.create(label='Manual CSV', value=19.5, team=team)
    DataPoint.objects.create(label='Integrations', value=22.1, team=team)
    return team

def get_or_create_user_team(user):
    """
    Retrieves the team membership for the user. If none exists, provisions a default team.
    """
    membership = TeamMember.objects.filter(user=user).select_related('team').first()
    if not membership:
        team = create_team_for_user(user)
        membership = TeamMember.objects.filter(user=user, team=team).first()
    return membership.team, membership
