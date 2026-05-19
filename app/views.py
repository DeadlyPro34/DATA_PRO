from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, TeamMember, DataPoint
import csv
import io

def create_team_for_user(user):
    """
    Creates a default team for a user, registers them as admin, and seeds initial data.
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
                
                # Provision team & seed datasets
                create_team_for_user(user)
                
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
        team = create_team_for_user(request.user)
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
    Renders the analytics page with dynamic labels and values from the user's team dataset for Chart.js.
    """
    # Fetch current logged-in user's team membership
    membership = TeamMember.objects.filter(user=request.user).first()
    if not membership:
        team = create_team_for_user(request.user)
    else:
        team = membership.team

    # Fetch dataset records scoped strictly to the current team
    datapoints = DataPoint.objects.filter(team=team)
    
    # Extract labels and values
    labels = [d.label for d in datapoints]
    values = [d.value for d in datapoints]

    context = {
        'labels': labels,
        'values': values,
    }
    return render(request, 'Analytics/index.html', context)

@login_required
def datasets_view(request):
    """
    Renders the datasets page with dynamic dataset records belonging to the user's team.
    """
    # Fetch current logged-in user's team membership
    membership = TeamMember.objects.filter(user=request.user).first()
    if not membership:
        team = create_team_for_user(request.user)
    else:
        team = membership.team

    # Form Submission Handling
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_dataset':
            label = request.POST.get('label', '').strip()
            value_str = request.POST.get('value', '').strip()
            
            # Safe parsing of numeric values (e.g., "12,840 rows" -> 12840.0)
            cleaned_val = ''.join(c for c in value_str if c.isdigit() or c == '.')
            try:
                value = float(cleaned_val)
            except ValueError:
                value = 0.0
            
            if label:
                DataPoint.objects.create(label=label, value=value, team=team)
                messages.success(request, f"Successfully created data entry '{label}'.")
                
        elif action == 'upload_csv':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, "No file uploaded.")
            elif not csv_file.name.endswith('.csv'):
                messages.error(request, "Invalid file format. Please upload a valid CSV file.")
            else:
                try:
                    file_data = csv_file.read().decode('utf-8')
                    csv_data = csv.reader(io.StringIO(file_data))
                    
                    count = 0
                    for row in csv_data:
                        if not row:
                            continue
                        
                        label = row[0].strip()
                        if not label:
                            continue
                        
                        value = 0.0
                        if len(row) > 1:
                            val_str = row[1].strip()
                            cleaned_val = ''.join(c for c in val_str if c.isdigit() or c == '.')
                            try:
                                value = float(cleaned_val)
                            except ValueError:
                                value = 0.0
                                
                        DataPoint.objects.create(label=label, value=value, team=team)
                        count += 1
                    
                    messages.success(request, f"Successfully imported {count} data entries from {csv_file.name}.")
                except Exception as e:
                    messages.error(request, f"Error parsing CSV: {str(e)}")

        elif action == 'delete_dataset':
            dataset_id = request.POST.get('dataset_id')
            if dataset_id:
                try:
                    # Guarantee isolation: only allow deleting points within the user's team
                    DataPoint.objects.get(id=dataset_id, team=team).delete()
                    messages.success(request, "Data entry deleted.")
                except DataPoint.DoesNotExist:
                    pass
                    
        return redirect('datasets')

    # Fetch dataset records scoped strictly to the current team
    dataset = DataPoint.objects.filter(team=team)

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
