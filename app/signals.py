from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Avg, Max, Min
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import DataPoint

def broadcast_team_update(team):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    # Calculate new stats
    stats = DataPoint.objects.filter(team=team).aggregate(
        total=Sum('value'),
        average=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value')
    )

    # Fetch datapoints sorted by ID
    datapoints = DataPoint.objects.filter(team=team).order_by('id')
    labels = [dp.label for dp in datapoints]
    values = [dp.value for dp in datapoints]

    payload = {
        'total': round(stats['total'] or 0.0, 2),
        'average': round(stats['average'] or 0.0, 2),
        'max_value': round(stats['max_value'] or 0.0, 2),
        'min_value': round(stats['min_value'] or 0.0, 2),
        'labels': labels,
        'values': values
    }

    # Group name based on team_id
    group_name = f"team_{team.id}"

    # Broadcast to the team group
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'dashboard_update',
                'payload': payload
            }
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to broadcast dashboard update via WebSockets: {e}")

@receiver(post_save, sender=DataPoint)
def datapoint_saved(sender, instance, **kwargs):
    broadcast_team_update(instance.team)

@receiver(post_delete, sender=DataPoint)
def datapoint_deleted(sender, instance, **kwargs):
    broadcast_team_update(instance.team)
