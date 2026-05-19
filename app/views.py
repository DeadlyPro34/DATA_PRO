from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, TeamMember, DataPoint, TeamInvitation
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
    Renders the main dashboard layout with dataset insights.
    """
    # Fetch current logged-in user's team membership
    membership = TeamMember.objects.filter(user=request.user).first()
    if not membership:
        team = create_team_for_user(request.user)
    else:
        team = membership.team

    # Calculate dataset statistics for the team
    from django.db.models import Sum, Avg, Max, Min
    stats = DataPoint.objects.filter(team=team).aggregate(
        total=Sum('value'),
        average=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value')
    )

    context = {
        'total': round(stats['total'] or 0.0, 2),
        'average': round(stats['average'] or 0.0, 2),
        'max_value': round(stats['max_value'] or 0.0, 2),
        'min_value': round(stats['min_value'] or 0.0, 2),
    }
    return render(request, 'Layout/index.html', context)

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
            # Check for invitation token in session
            invite_token = request.session.pop('invite_token', None)
            if invite_token:
                return redirect('accept_invite', token=invite_token)
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
                # Check for invitation token in session
                invite_token = request.session.pop('invite_token', None)
                if invite_token:
                    return redirect('accept_invite', token=invite_token)
                return redirect('dashboard')
            except Exception as e:
                error = f"An error occurred during account creation: {str(e)}"

    return render(request, 'Login_Signup/Sign_up.html', {'error': error})

@login_required
def team_view(request):
    """
    Renders the team directory page with dynamic members list and invitation outbox.
    """
    # Fetch current logged-in user's team membership
    membership = TeamMember.objects.filter(user=request.user).first()
    
    if not membership:
        team = create_team_for_user(request.user)
    else:
        team = membership.team

    # Security check: Determine if current user is admin/owner
    is_admin = (membership and membership.role == 'admin') or (team.owner == request.user)

    # Handle Team operations (adding / removing members, revoking invites)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'invite_member':
            if not is_admin:
                messages.error(request, "Only team admins can invite new members.")
            else:
                email_input = request.POST.get('email', '').strip()
                role_input = request.POST.get('role', 'member').lower()
                if role_input not in ['admin', 'member']:
                    role_input = 'member'
                
                if email_input:
                    # Check if user is already a member
                    already_member = TeamMember.objects.filter(team=team, user__email=email_input).exists()
                    if already_member:
                        messages.error(request, f"User with email '{email_input}' is already in this team.")
                    else:
                        # Check if a pending invite exists
                        existing_invite = TeamInvitation.objects.filter(team=team, email=email_input, status='pending').first()
                        if existing_invite:
                            messages.info(request, f"A pending invitation for '{email_input}' already exists.")
                        else:
                            invitation = TeamInvitation.objects.create(
                                email=email_input,
                                team=team,
                                role=role_input,
                                status='pending'
                            )
                            accept_url = request.build_absolute_uri(f"/team/accept/{invitation.token}/")
                            messages.success(request, f"Invitation created for {email_input}! Link: {accept_url}")
            
        elif action == 'remove_member':
            # Only admin can remove members
            if not is_admin:
                messages.error(request, "Only team admins can remove members.")
            else:
                member_id = request.POST.get('member_id')
                if member_id:
                    try:
                        member_to_remove = TeamMember.objects.get(id=member_id, team=team)
                        # Prevent owners from removing themselves
                        if member_to_remove.user != request.user:
                            member_to_remove.delete()
                            messages.success(request, f"Removed member '{member_to_remove.user.username}' from the team.")
                        else:
                            messages.error(request, "You cannot remove yourself from your owned team.")
                    except TeamMember.DoesNotExist:
                        pass
        
        elif action == 'cancel_invite':
            if not is_admin:
                messages.error(request, "Only team admins can revoke invitations.")
            else:
                invite_id = request.POST.get('invite_id')
                if invite_id:
                    try:
                        TeamInvitation.objects.get(id=invite_id, team=team, status='pending').delete()
                        messages.success(request, "Invitation revoked.")
                    except TeamInvitation.DoesNotExist:
                        pass
        
        return redirect('team')

    # Query all members of the user's team
    team_members = TeamMember.objects.filter(team=team).select_related('user')
    
    members = []
    for m in team_members:
        status = 'online' if m.user.is_active else 'offline'
        members.append({
            'id': m.id,
            'username': m.user.username,
            'role': m.role.capitalize(),
            'status': status,
            'activeNode': 'US-EAST-1' if m.role == 'admin' else 'EU-CENTRAL-1',
            'datasets': DataPoint.objects.filter(team=team).count(),
            'avatar': None
        })

    # Query real pending invitations
    pending_invites = TeamInvitation.objects.filter(team=team, status='pending').order_by('-created_at')

    context = {
        'members': members,
        'pending_invites': pending_invites,
        'is_admin': is_admin,
    }
    return render(request, 'Team/index.html', context)


def accept_invite_view(request, token):
    """
    Validates the invitation token and joins the user to the team.
    """
    try:
        invitation = TeamInvitation.objects.get(token=token, status='pending')
    except (TeamInvitation.DoesNotExist, ValueError):
        messages.error(request, "Invalid or expired invitation token.")
        return redirect('dashboard')

    # If user is not logged in, save invite token in session and redirect to login
    if not request.user.is_authenticated:
        request.session['invite_token'] = str(token)
        messages.info(request, "Please log in or sign up to accept the invitation.")
        return redirect('login')

    # Guard against user joining their own team or duplicate memberships
    already_member = TeamMember.objects.filter(team=invitation.team, user=request.user).exists()
    if already_member:
        invitation.status = 'accepted'
        invitation.save()
        messages.info(request, f"You are already a member of team '{invitation.team.name}'.")
        return redirect('dashboard')

    # Create new TeamMember record
    TeamMember.objects.create(
        user=request.user,
        team=invitation.team,
        role=invitation.role
    )
    
    # Mark invite as accepted
    invitation.status = 'accepted'
    invitation.save()

    messages.success(request, f"Successfully joined team '{invitation.team.name}' as {invitation.role.capitalize()}!")
    return redirect('dashboard')

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
        is_admin = True
    else:
        team = membership.team
        is_admin = (membership.role == 'admin') or (team.owner == request.user)

    # Form Submission Handling
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_dataset':
            label = request.POST.get('label', '').strip()
            value_str = request.POST.get('value', '').strip()
            
            # Remove invalid values (non-numeric): strip commas, text, and symbols
            cleaned_val = ''.join(c for c in value_str if c.isdigit() or c == '.')
            if not cleaned_val:
                messages.error(request, "Invalid value. Value must contain numeric digits.")
            elif label:
                try:
                    value = float(cleaned_val)
                    DataPoint.objects.create(label=label, value=value, team=team)
                    messages.success(request, f"Successfully created data entry '{label}' with cleaned value {value}.")
                except ValueError:
                    messages.error(request, "Failed to parse value. Please enter a valid number.")
                
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
                    skipped_count = 0
                    for row in csv_data:
                        if not row:
                            continue
                        
                        label = row[0].strip()
                        if not label:
                            continue
                        
                        if len(row) > 1:
                            val_str = row[1].strip()
                            # Clean value: strip commas, symbols, text, and convert safely to float
                            cleaned_val = ''.join(c for c in val_str if c.isdigit() or c == '.')
                            if cleaned_val:
                                try:
                                    value = float(cleaned_val)
                                    DataPoint.objects.create(label=label, value=value, team=team)
                                    count += 1
                                except ValueError:
                                    skipped_count += 1
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    
                    if count > 0:
                        messages.success(request, f"Successfully imported {count} data entries from {csv_file.name}.")
                    if skipped_count > 0:
                        messages.warning(request, f"Skipped {skipped_count} row(s) containing invalid or non-numeric values.")
                except Exception as e:
                    messages.error(request, f"Error parsing CSV: {str(e)}")

        elif action == 'delete_dataset':
            if not is_admin:
                messages.error(request, "Only team admins can delete data.")
            else:
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

    # Sort data in view: order_by('value') or order_by('-value') based on query param (?sort=asc / ?sort=desc)
    sort_param = request.GET.get('sort', '').lower()
    if sort_param == 'asc':
        dataset = dataset.order_by('value')
    elif sort_param == 'desc':
        dataset = dataset.order_by('-value')
    else:
        dataset = dataset.order_by('-id')

    context = {
        'dataset': dataset,
        'is_admin': is_admin,
    }
    return render(request, 'Data_Sets/index.html', context)

@login_required
def settings_view(request):
    """
    Renders the account settings page.
    """
    return render(request, 'Settings/index.html')
