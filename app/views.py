from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User

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
    Renders the signup page.
    """
    error = None
    if request.method == 'POST':
        # Simple POST stub signup redirection to login
        return redirect('login')
    return render(request, 'Login_Signup/Sign_up.html', {'error': error})

def team_view(request):
    """
    Renders the team directory page with dynamic members list.
    """
    members = [
        {'id': 1, 'username': 'Sarah Connor', 'role': 'Admin', 'status': 'online', 'activeNode': 'US-EAST-1', 'datasets': 14, 'avatar': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=256&auto=format&fit=crop'},
        {'id': 2, 'username': 'Marcus Aure', 'role': 'Member', 'status': 'online', 'activeNode': 'EU-CENTRAL-1', 'datasets': 22, 'avatar': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=256&auto=format&fit=crop'},
        {'id': 3, 'username': 'Emily Watson', 'role': 'Admin', 'status': 'online', 'activeNode': 'AP-SOUTH-1', 'datasets': 8, 'avatar': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop'},
        {'id': 4, 'username': 'David Miller', 'role': 'Member', 'status': 'offline', 'activeNode': 'Inert', 'datasets': 5, 'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=256&auto=format&fit=crop'},
        {'id': 5, 'username': 'Elena Rostova', 'role': 'Member', 'status': 'online', 'activeNode': 'US-WEST-2', 'datasets': 19, 'avatar': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=256&auto=format&fit=crop'}
    ]
    pending_invites = [
        {'id': 101, 'email': 'thomas.shelby@vortex.io', 'role': 'Member', 'status': 'Pending', 'date_sent': '2 hours ago'},
        {'id': 102, 'email': 'aria.montgomery@vortex.io', 'role': 'Admin', 'status': 'Pending', 'date_sent': 'Yesterday'}
    ]
    
    if request.method == 'POST':
        # Simple POST stub reload
        return redirect('team')

    context = {
        'members': members,
        'pending_invites': pending_invites,
    }
    return render(request, 'Team/index.html', context)

def analytics_view(request):
    """
    Renders the analytics page with dynamic labels and values for Chart.js.
    """
    context = {
        'labels': ['Organic', 'Web API', 'Social', 'Manual CSV', 'Integrations'],
        'values': [14.2, 28.4, 8.9, 19.5, 22.1],
    }
    return render(request, 'Analytics/index.html', context)

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

def settings_view(request):
    """
    Renders the account settings page.
    """
    return render(request, 'Settings/index.html')
