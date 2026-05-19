from django.test import TestCase, Client
from django.contrib.auth.models import User
from app.models import Team, TeamMember, DataPoint
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
