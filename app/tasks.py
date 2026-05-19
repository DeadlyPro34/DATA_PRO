import csv
import io
from celery import shared_task
from django.db import transaction
from .models import CSVDataset, DataPoint, Team
from .signals import broadcast_team_update

@shared_task
def process_csv_upload(csv_dataset_id, file_data_str, team_id):
    try:
        csv_dataset = CSVDataset.objects.get(id=csv_dataset_id)
        team = Team.objects.get(id=team_id)
    except (CSVDataset.DoesNotExist, Team.DoesNotExist):
        return "Dataset or Team not found"

    csv_dataset.status = 'processing'
    csv_dataset.save()

    try:
        csv_data = csv.reader(io.StringIO(file_data_str))
        datapoints_to_create = []
        imported_count = 0
        skipped_count = 0

        for row in csv_data:
            if not row:
                continue

            label = row[0].strip()
            if not label:
                continue

            if len(row) > 1:
                val_str = row[1].strip()
                # Remove common numeric formatting characters like commas
                cleaned_val = ''.join(c for c in val_str if c.isdigit() or c == '.')
                if cleaned_val:
                    try:
                        value = float(cleaned_val)
                        datapoints_to_create.append(DataPoint(
                            label=label,
                            value=value,
                            team=team,
                            csv_file=csv_dataset
                        ))
                        imported_count += 1
                    except ValueError:
                        skipped_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1

            # Save in chunks of 500
            if len(datapoints_to_create) >= 500:
                with transaction.atomic():
                    DataPoint.objects.bulk_create(datapoints_to_create)
                datapoints_to_create = []

        if datapoints_to_create:
            with transaction.atomic():
                DataPoint.objects.bulk_create(datapoints_to_create)

        csv_dataset.imported_count = imported_count
        csv_dataset.skipped_count = skipped_count
        csv_dataset.status = 'done'
        csv_dataset.save()

        # Trigger real-time WebSocket dashboard/analytics updates
        broadcast_team_update(team)

        return f"Completed: {imported_count} imported, {skipped_count} skipped"
    except Exception as e:
        csv_dataset.status = 'failed'
        csv_dataset.save()
        return f"Failed: {str(e)}"


@shared_task
def process_csv_delete(csv_id, team_id):
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return "Team not found"

    try:
        # Perform optimized direct bulk deletion of children to avoid Django's cascade overhead in Python
        DataPoint.objects.filter(csv_file_id=csv_id).delete()
        # Delete the dataset object itself
        CSVDataset.objects.filter(id=csv_id, team=team).delete()

        # Trigger WebSocket update to refresh UI stats and charts for all connected team members
        broadcast_team_update(team)
        return f"Successfully deleted CSV {csv_id} and all related records."
    except Exception as e:
        return f"Failed to delete CSV {csv_id}: {str(e)}"
