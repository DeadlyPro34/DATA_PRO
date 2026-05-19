from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, TeamMember, DataPoint, TeamInvitation, CSVDataset, UploadedFile, CleanedDataset, SavedChart, TeamActivity
from .services import create_team_for_user, get_or_create_user_team
import csv
import io

@login_required
def dashboard_view(request):
    """
    Renders the main dashboard layout with dataset insights.
    """
    team, membership = get_or_create_user_team(request.user)

    # Calculate dataset statistics for the team
    from django.db.models import Sum, Avg, Max, Min
    stats = DataPoint.objects.filter(team=team).aggregate(
        total=Sum('value'),
        average=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value')
    )

    # Get recent team activities
    activities = TeamActivity.get_recent_activities(team)

    context = {
        'total': round(stats['total'] or 0.0, 2),
        'average': round(stats['average'] or 0.0, 2),
        'max_value': round(stats['max_value'] or 0.0, 2),
        'min_value': round(stats['min_value'] or 0.0, 2),
        'recent_activities': activities[:3],
        'all_activities': activities,
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

def logout_view(request):
    """
    Logs out the user and redirects to the login page.
    """
    auth_logout(request)
    return redirect('login')

@login_required
def team_view(request):
    """
    Renders the team directory page with dynamic members list and invitation outbox.
    """
    team, membership = get_or_create_user_team(request.user)

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
                            messages.success(request, f"Invitation created for {email_input}. Please share the link with them directly.")
                            request.session['new_invite_url'] = accept_url
            
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
    
    # Calculate dataset count once outside the loop to optimize database access (N+1 query fix)
    datasets_count = DataPoint.objects.filter(team=team).count()
    
    members = []
    for m in team_members:
        status = 'online' if m.user.is_active else 'offline'
        members.append({
            'id': m.id,
            'username': m.user.username,
            'role': m.role.capitalize(),
            'status': status,
            'activeNode': 'US-EAST-1' if m.role == 'admin' else 'EU-CENTRAL-1',
            'datasets': datasets_count,
            'avatar': None
        })

    # Query real pending invitations
    pending_invites = TeamInvitation.objects.filter(team=team, status='pending').order_by('-created_at')

    # Retrieve the new invite URL if it exists
    new_invite_url = request.session.pop('new_invite_url', None)

    context = {
        'members': members,
        'pending_invites': pending_invites,
        'is_admin': is_admin,
        'new_invite_url': new_invite_url,
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
    
    # Log team join activity
    TeamActivity.objects.create(
        team=invitation.team,
        user=request.user,
        activity_type='join',
        description="Welcome aboard! 👋",
        status_color='indigo'
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
    team, membership = get_or_create_user_team(request.user)

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
    team, membership = get_or_create_user_team(request.user)
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
                    TeamActivity.objects.create(
                        team=team,
                        user=request.user,
                        activity_type='upload',
                        description=f"Manually added '{label}' ({value})",
                        status_color='emerald'
                    )
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
                    file_data_str = csv_file.read().decode('utf-8')
                    csv_dataset = CSVDataset.objects.create(
                        name=csv_file.name,
                        team=team,
                        status='pending'
                    )
                    TeamActivity.objects.create(
                        team=team,
                        user=request.user,
                        activity_type='upload',
                        description=csv_file.name,
                        status_color='emerald'
                    )
                    from .tasks import process_csv_upload
                    process_csv_upload.delay(csv_dataset.id, file_data_str, team.id)
                    messages.success(request, f"File '{csv_file.name}' uploaded successfully! Processing in the background...")
                    return redirect(f"/datasets/?source={csv_dataset.id}")
                except Exception as e:
                    messages.error(request, f"Error launching background task: {str(e)}")

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

        elif action == 'delete_csv':
            if not is_admin:
                messages.error(request, "Only team admins can delete CSV datasets.")
            else:
                csv_id = request.POST.get('csv_id')
                if csv_id:
                    try:
                        csv_dataset = CSVDataset.objects.get(id=csv_id, team=team)
                        csv_dataset.status = 'deleting'
                        csv_dataset.save()
                        
                        TeamActivity.objects.create(
                            team=team,
                            user=request.user,
                            activity_type='custom',
                            description=f"Deleted CSV dataset '{csv_dataset.name}'",
                            status_color='amber'
                        )
                        
                        from .tasks import process_csv_delete
                        process_csv_delete.delay(csv_id, team.id)
                        
                        messages.success(request, "CSV dataset deletion started in the background.")
                        
                        # If the deleted dataset is currently selected, redirect to default manual view
                        if request.GET.get('source') == str(csv_id):
                            return redirect('datasets')
                    except CSVDataset.DoesNotExist:
                        pass

        elif action == 'clear_data':
            if not is_admin:
                messages.error(request, "Only team admins can clear all data.")
            else:
                dp_count = DataPoint.objects.filter(team=team).delete()[0]
                CSVDataset.objects.filter(team=team).delete()
                
                TeamActivity.objects.create(
                    team=team,
                    user=request.user,
                    activity_type='custom',
                    description="Cleared all team data",
                    status_color='amber'
                )
                
                from .signals import broadcast_team_update
                broadcast_team_update(team)
                
                messages.success(request, f"All team data cleared successfully ({dp_count} data points removed).")
                    
        query_params = request.GET.urlencode()
        if query_params:
            return redirect(f"/datasets/?{query_params}")
        return redirect('datasets')

    # Fetch dataset records scoped strictly to the current team
    csv_files = CSVDataset.objects.filter(team=team).exclude(status='deleting').order_by('-uploaded_at')
    selected_source = request.GET.get('source', 'manual')
    selected_csv = None
    
    if selected_source == 'manual':
        dataset = DataPoint.objects.filter(team=team, csv_file__isnull=True)
    else:
        try:
            selected_csv = CSVDataset.objects.get(id=selected_source, team=team)
            dataset = DataPoint.objects.filter(team=team, csv_file=selected_csv)
        except (CSVDataset.DoesNotExist, ValueError):
            dataset = DataPoint.objects.filter(team=team, csv_file__isnull=True)
            selected_source = 'manual'

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
        'csv_files': csv_files,
        'selected_source': selected_source,
        'selected_csv': selected_csv,
    }
    return render(request, 'Data_Sets/index.html', context)

@login_required
def settings_view(request):
    """
    Renders the account settings page.
    """
    # TODO: implement account settings (change password, update profile)
    return render(request, 'Settings/index.html')

from django.http import JsonResponse

@login_required
def csv_status_view(request, csv_id):
    team, membership = get_or_create_user_team(request.user)
    try:
        csv_dataset = CSVDataset.objects.get(id=csv_id, team=team)
        return JsonResponse({
            'status': csv_dataset.status,
            'imported_count': csv_dataset.imported_count,
            'skipped_count': csv_dataset.skipped_count,
        })
    except CSVDataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found'}, status=404)


@login_required
def upload_view(request):
    """
    Handles CSV, Excel, and JSON file uploads. Dispatches parsing/cleaning
    to a background Celery task and renders the status polling page.
    """
    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        if not file_obj:
            messages.error(request, "No file uploaded.")
            return redirect('upload')
            
        filename = file_obj.name.lower()
        if filename.endswith('.csv'):
            file_type = 'csv'
        elif filename.endswith(('.xls', '.xlsx')):
            file_type = 'excel'
        elif filename.endswith('.json'):
            file_type = 'json'
        else:
            messages.error(request, "Unsupported file format. Please upload CSV, Excel, or JSON.")
            return redirect('upload')
            
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            file=file_obj,
            original_filename=file_obj.name,
            file_type=file_type,
            status='pending'
        )
        
        # Dispatch background Celery task
        from .tasks import process_uploaded_file
        process_uploaded_file.delay(uploaded_file.id)
        
        return redirect(f"/upload/?file_id={uploaded_file.id}")
        
    file_id = request.GET.get('file_id')
    context = {
        'file_id': file_id
    }
    return render(request, 'Data_Sets/upload.html', context)


@login_required
def file_status_view(request, file_id):
    """
    JSON endpoint that returns status, row_count, column_count, and ai_summary
    for an uploaded file, scoped to the logged-in user.
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
        return JsonResponse({
            'status': uploaded_file.status,
            'row_count': uploaded_file.row_count,
            'column_count': uploaded_file.column_count,
            'ai_summary': uploaded_file.ai_summary,
        })
    except UploadedFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)


@login_required
def dataset_view(request, file_id):
    """
    Displays the cleaned dataset, along with dynamic Chart.js options,
    the cleaning execution log, and the AI-generated dataset summary.
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
        cleaned_dataset = CleanedDataset.objects.get(uploaded_file=uploaded_file)
    except (UploadedFile.DoesNotExist, CleanedDataset.DoesNotExist):
        messages.error(request, "Dataset not found or is still being processed.")
        return redirect('upload')
        
    context = {
        'uploaded_file': uploaded_file,
        'dataset': cleaned_dataset,
        'columns': cleaned_dataset.columns,
        'rows': cleaned_dataset.rows,
        'cleaning_log': cleaned_dataset.cleaning_log,
    }
    return render(request, 'Data_Sets/dataset.html', context)


@login_required
def save_chart_view(request, file_id):
    """
    API endpoint to save a customized Chart.js setup for a dataset.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
        
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
        cleaned_dataset = CleanedDataset.objects.get(uploaded_file=uploaded_file)
    except (UploadedFile.DoesNotExist, CleanedDataset.DoesNotExist):
        return JsonResponse({'error': 'Dataset not found'}, status=404)
        
    import json
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
    except Exception:
        data = request.POST
        
    chart_type = data.get('chart_type')
    x_axis = data.get('x_axis')
    y_axis = data.get('y_axis')
    title = data.get('title')
    
    if not all([chart_type, x_axis, y_axis, title]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
        
    try:
        saved_chart = SavedChart.objects.create(
            dataset=cleaned_dataset,
            chart_type=chart_type.lower(),
            x_axis=x_axis,
            y_axis=y_axis,
            title=title
        )
        return JsonResponse({'success': True, 'chart_id': saved_chart.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def charts_gallery_view(request):
    """
    Lists all saved charts and handles deletion requests.
    """
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        chart_id = request.POST.get('chart_id')
        if chart_id:
            try:
                chart = SavedChart.objects.get(id=chart_id, dataset__uploaded_file__user=request.user)
                chart.delete()
                messages.success(request, "Chart deleted successfully.")
            except SavedChart.DoesNotExist:
                messages.error(request, "Chart not found.")
        return redirect('charts_gallery')
        
    charts = SavedChart.objects.filter(dataset__uploaded_file__user=request.user).select_related('dataset', 'dataset__uploaded_file')
    
    # Serialize preview rows for Chart.js rendering on client side
    import json
    preview_data = []
    for chart in charts:
        # Limit rows to first 40 records to keep preview lightweight
        preview_data.append({
            'id': chart.id,
            'chart_type': chart.chart_type,
            'x_axis': chart.x_axis,
            'y_axis': chart.y_axis,
            'rows': chart.dataset.rows[:40]
        })
        
    context = {
        'charts': charts,
        'chart_data_json': json.dumps(preview_data),
    }
    return render(request, 'Data_Sets/charts_gallery.html', context)
