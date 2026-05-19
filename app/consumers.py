from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Sum, Avg, Max, Min
from .models import TeamMember, DataPoint
import json

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Fetch the user's team
        self.team = await self.get_user_team()
        if not self.team:
            await self.close()
            return

        self.team_id = self.team.id
        self.group_name = f"team_{self.team_id}"

        # Join team group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial data
        await self.send_dashboard_data()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            if message_type == 'refresh':
                await self.send_dashboard_data()
        except Exception:
            pass

    async def dashboard_update(self, event):
        # Broadcast team update to client
        await self.send(text_data=json.dumps(event['payload']))

    async def send_dashboard_data(self):
        payload = await self.get_dashboard_payload()
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def get_user_team(self):
        membership = TeamMember.objects.filter(user=self.user).select_related('team').first()
        return membership.team if membership else None

    @database_sync_to_async
    def get_dashboard_payload(self):
        stats = DataPoint.objects.filter(team=self.team).aggregate(
            total=Sum('value'),
            average=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value')
        )
        
        datapoints = DataPoint.objects.filter(team=self.team).order_by('id')
        labels = [dp.label for dp in datapoints]
        values = [dp.value for dp in datapoints]

        return {
            'total': round(stats['total'] or 0.0, 2),
            'average': round(stats['average'] or 0.0, 2),
            'max_value': round(stats['max_value'] or 0.0, 2),
            'min_value': round(stats['min_value'] or 0.0, 2),
            'labels': labels,
            'values': values
        }
