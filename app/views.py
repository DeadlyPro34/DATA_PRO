from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Team, TeamMember

@login_required
def dashboard_view(request):
    """
    Renders the main dashboard layout.
    """
    return render(request, 'Layout/index.html')

def login_view(request):
    """
    Handles user login using Django's built-in authentication.
    """
    error = None
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '')

        username = username_input
        # Support email log-in by resolving email to standard username
        if '@' in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                username = user_obj.username
            except User.DoesNotExist:
                pass

        user = authenticate(request, username=username, password=password_input)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid business email or password. Please try again."

    return render(request, 'Login_Signup/login.html', {'error': error})

def signup_view(request):
    """
    Handles user registration, validates uniqueness, creates default Team, and initiates auto-login.
    """
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Input and validation checks
        if not username or not email or not password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "Username already exists."
        elif User.objects.filter(email=email).exists():
            error = "An account with this email address already exists."
        else:
            try:
                # Create the user using Django standard manager
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                
                # Automatically create a new Team
                team = Team.objects.create(name=f"{username}'s Team", owner=user)
                
                # Assign the user as "admin" in TeamMember
                TeamMember.objects.create(user=user, team=team, role='admin')
                
                # Auto log-in after registration
                auth_login(request, user)
                return redirect('dashboard')
            except Exception as e:
                error = f"An error occurred during account creation: {str(e)}"

    return render(request, 'Login_Signup/Sign_up.html', {'error': error})

@login_required
def team_view(request):
    """
    Renders the team directory page with dynamic members list from the database.
    """
    # Fetch current logged-in user's team membership
    membership = TeamMember.objects.filter(user=request.user).first()
    
    if not membership:
        # Fallback: if user doesn't have a team membership (e.g. if created via manage.py createsuperuser),
        # automatically create a team for them.
        team = Team.objects.create(name=f"{request.user.username}'s Team", owner=request.user)
        membership = TeamMember.objects.create(user=request.user, team=team, role='admin')
    else:
        team = membership.team

    # Handle Team operations (adding / removing members)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'invite_member':
            email_input = request.POST.get('email', '').strip()
            role_input = request.POST.get('role', 'member').lower()
            
            if email_input:
                try:
                    invited_user = User.objects.get(email=email_input)
                    # Check if user is already in the team
                    if not TeamMember.objects.filter(team=team, user=invited_user).exists():
                        TeamMember.objects.create(user=invited_user, team=team, role=role_input)
                except User.DoesNotExist:
                    # For interactive demo purposes, if invited email doesn't exist in system yet,
                    # we create a stub user so the member directory grows instantly!
                    username_stub = email_input.split('@')[0]
                    # Ensure username is unique
                    suffix = 1
                    base_username = username_stub
                    while User.objects.filter(username=username_stub).exists():
                        username_stub = f"{base_username}{suffix}"
                        suffix += 1
                    
                    new_user = User.objects.create_user(username=username_stub, email=email_input, password='Password123')
                    TeamMember.objects.create(user=new_user, team=team, role=role_input)
            
        elif action == 'remove_member':
            member_id = request.POST.get('member_id')
            if member_id:
                try:
                    member_to_remove = TeamMember.objects.get(id=member_id, team=team)
                    # Prevent owners from removing themselves
                    if member_to_remove.user != request.user:
                        member_to_remove.delete()
                except TeamMember.DoesNotExist:
                    pass
        
        return redirect('team')

    # Query all members of the user's team
    team_members = TeamMember.objects.filter(team=team).select_related('user')
    
    # Format members matching what template expects
    members = []
    for m in team_members:
        status = 'online' if m.user.is_active else 'offline'
        members.append({
            'id': m.id,
            'username': m.user.username,
            'role': m.role.capitalize(), # 'admin' -> 'Admin', 'member' -> 'Member'
            'status': status,
            'activeNode': 'US-EAST-1' if m.role == 'admin' else 'EU-CENTRAL-1',
            'datasets': 14 if m.role == 'admin' else 8,
            'avatar': None
        })

    # Stub pending invites for dashboard view
    pending_invites = [
        {'id': 101, 'email': 'thomas.shelby@vortex.io', 'role': 'Member', 'status': 'Pending', 'date_sent': '2 hours ago'},
        {'id': 102, 'email': 'aria.montgomery@vortex.io', 'role': 'Admin', 'status': 'Pending', 'date_sent': 'Yesterday'}
    ]

    context = {
        'members': members,
        'pending_invites': pending_invites,
    }
    return render(request, 'Team/index.html', context)

@login_required
def analytics_view(request):
    """
    Renders the analytics page with dynamic labels and values for Chart.js.
    """
    context = {
        'labels': ['Organic', 'Web API', 'Social', 'Manual CSV', 'Integrations'],
        'values': [14.2, 28.4, 8.9, 19.5, 22.1],
    }
    return render(request, 'Analytics/index.html', context)

@login_required
def datasets_view(request):
    """
    Renders the datasets page with dynamic dataset records.
    """
    dataset = [
        {'id': 1, 'label': 'Q4_Marketing_Metrics.csv', 'value': '12,840 rows', 'status': 'Ready', 'last_updated': 'Oct 24, 2023', 'category': 'Financial Data'},
        {'id': 2, 'label': 'User_Behavior_Logs', 'value': '84,201 rows', 'status': 'Processing', 'last_updated': '2 hours ago', 'category': 'User Analytics'},
        {'id': 3, 'label': 'Incomplete_Sales_Data', 'value': '240 rows', 'status': 'Error', 'last_updated': 'Oct 20, 2023', 'category': 'Archive'}
    ]
    
    if request.method == 'POST':
        # Simple POST stub reload
        return redirect('datasets')

    context = {
        'dataset': dataset,
    }
    return render(request, 'Data_Sets/index.html', context)

@login_required
def settings_view(request):
    """
    Renders the account settings page.
    """
    return render(request, 'Settings/index.html')
