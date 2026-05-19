from django.test import TestCase, Client
from django.contrib.auth.models import User
from app.models import Team, TeamMember, DataPoint, TeamInvitation
import io

class DatasetSystemTest(TestCase):
    def setUp(self):
        # Create standard test client
        self.client = Client()
        
        # Register a test user
        signup_data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }
        self.client.post('/signup/', signup_data, follow=True)
        self.user = User.objects.get(username='test_user')
        self.membership = TeamMember.objects.get(user=self.user)
        self.team = self.membership.team

    def test_csv_upload_and_cleaning(self):
        # Prepare CSV content with mixed alphanumeric values (commas, spaces, text)
        csv_content = (
            "Mobile App,35.6\n"
            "Desktop Site,48.2\n"
            "Referrals,12.8\n"
            "Partner Network,18.9\n"
            "Email Campaigns,24.5\n"
            "Invalid Row,not-numeric-at-all\n"
        )
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'marketing_data.csv'
        
        post_data = {
            'action': 'upload_csv',
            'csv_file': csv_file
        }
        
        response = self.client.post('/datasets/', post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify 5 valid data points were created (ignoring the 5 default seeds and the 1 invalid row)
        new_datapoints = DataPoint.objects.filter(team=self.team).exclude(
            label__in=['Organic Traffic', 'Web API', 'Social Media', 'Manual CSV', 'Integrations']
        )
        self.assertEqual(new_datapoints.count(), 5)
        
        # Verify cleaning: commas, spaces, and text removed, converted to float
        mobile_dp = new_datapoints.get(label='Mobile App')
        self.assertEqual(mobile_dp.value, 35.6)
        
        # Verify the invalid row was skipped
        self.assertFalse(new_datapoints.filter(label='Invalid Row').exists())

    def test_sorting_functionality(self):
        # Upload a few datapoints with known values
        DataPoint.objects.create(label='Point A', value=100.5, team=self.team)
        DataPoint.objects.create(label='Point B', value=10.2, team=self.team)
        DataPoint.objects.create(label='Point C', value=50.9, team=self.team)
        
        # 1. Test Ascending Sort (?sort=asc)
        response_asc = self.client.get('/datasets/?sort=asc')
        self.assertEqual(response_asc.status_code, 200)
        dataset_asc = list(response_asc.context['dataset'])
        values_asc = [d.value for d in dataset_asc]
        self.assertEqual(values_asc, sorted(values_asc))
        
        # 2. Test Descending Sort (?sort=desc)
        response_desc = self.client.get('/datasets/?sort=desc')
        self.assertEqual(response_desc.status_code, 200)
        dataset_desc = list(response_desc.context['dataset'])
        values_desc = [d.value for d in dataset_desc]
        self.assertEqual(values_desc, sorted(values_desc, reverse=True))

    def test_manual_entry_cleaning_and_validation(self):
        # Test valid manual entry
        valid_data = {
            'action': 'add_dataset',
            'label': 'Manual Valid',
            'value': '12,345.67 units'
        }
        response = self.client.post('/datasets/', valid_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        dp = DataPoint.objects.get(label='Manual Valid')
        self.assertEqual(dp.value, 12345.67)
        
        # Test completely invalid manual entry
        invalid_data = {
            'action': 'add_dataset',
            'label': 'Manual Invalid',
            'value': 'no-digits-here'
        }
        response_invalid = self.client.post('/datasets/', invalid_data, follow=True)
        self.assertEqual(response_invalid.status_code, 200)
        
        # Should not create datapoint
        self.assertFalse(DataPoint.objects.filter(label='Manual Invalid').exists())

    def test_dashboard_insights_calculations(self):
        # Seed additional datapoints with specific values
        DataPoint.objects.create(label='Insight A', value=10.0, team=self.team)
        DataPoint.objects.create(label='Insight B', value=20.0, team=self.team)
        DataPoint.objects.create(label='Insight C', value=30.0, team=self.team)
        
        response = self.client.get('/') # Renders dashboard_view
        self.assertEqual(response.status_code, 200)
        
        # Seed totals: (14.2, 28.4, 8.9, 19.5, 22.1) + (10.0, 20.0, 30.0) = 153.1
        # Seed count: 8 items
        # Average: 153.1 / 8 = 19.1375 -> 19.14 rounded
        # Max: 30.0
        # Min: 8.9
        self.assertEqual(response.context['total'], 153.1)
        self.assertEqual(response.context['average'], 19.14)
        self.assertEqual(response.context['max_value'], 30.0)
        self.assertEqual(response.context['min_value'], 8.9)

    def test_invite_member_flow(self):
        # 1. Admin invites standard email
        invite_data = {
            'action': 'invite_member',
            'email': 'invitee@vortex.io',
            'role': 'member'
        }
        # Client currently authenticated as admin 'test_user'
        response = self.client.post('/team/', invite_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify invitation created in database
        invite = TeamInvitation.objects.get(email='invitee@vortex.io', team=self.team)
        self.assertEqual(invite.status, 'pending')
        self.assertEqual(invite.role, 'member')

    def test_accept_invite_flow(self):
        # 1. Create a pending invite record
        invitation = TeamInvitation.objects.create(
            email='accept_test@vortex.io',
            team=self.team,
            role='member',
            status='pending'
        )
        
        # 2. Click acceptance link logged out
        self.client.logout()
        response_logout = self.client.get(f'/team/accept/{invitation.token}/')
        # Should redirect to login and set session variable
        self.assertRedirects(response_logout, '/login/')
        self.assertEqual(self.client.session.get('invite_token'), str(invitation.token))
        
        # 3. Log in as a new user to accept the invite
        new_user = User.objects.create_user(username='new_member', email='accept_test@vortex.io', password='Password123')
        login_data = {
            'username': 'new_member',
            'password': 'Password123'
        }
        # Simulate session variables being persisted by making client login and redirecting
        session = self.client.session
        session['invite_token'] = str(invitation.token)
        session.save()
        
        response_login = self.client.post('/login/', login_data)
        # Should redirect to accept invite view
        self.assertRedirects(response_login, f'/team/accept/{invitation.token}/', target_status_code=302)
        
        # 4. Visit the accept URL (with user logged in)
        response_accept = self.client.get(f'/team/accept/{invitation.token}/')
        # Should redirect to dashboard
        self.assertRedirects(response_accept, '/')
        
        # 5. Verify TeamMember record created
        self.assertTrue(TeamMember.objects.filter(team=self.team, user=new_user, role='member').exists())
        
        # 6. Verify invitation status accepted
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'accepted')

    def test_revoke_invite_flow(self):
        # 1. Create a pending invite record
        invitation = TeamInvitation.objects.create(
            email='revoke_test@vortex.io',
            team=self.team,
            role='member',
            status='pending'
        )
        
        # 2. Revoke invitation
        post_data = {
            'action': 'cancel_invite',
            'invite_id': invitation.id
        }
        response = self.client.post('/team/', post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # 3. Verify invitation record is deleted
        self.assertFalse(TeamInvitation.objects.filter(id=invitation.id).exists())
