"""
tasks.py — Celery background tasks for DataPro.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_dataset(self, dataset_id: int):
    """
    Background task: parse the uploaded file and bulk-insert rows.

    Steps
    -----
    1. Load Dataset from DB
    2. Mark status = processing
    3. Parse file with file_parser.parse_file()
    4. Bulk-create DataRow objects (batched to avoid memory spikes)
    5. Update Dataset: columns, row_count, col_count, status = ready
    6. On any error: status = error, save error_message
    """
    from .models import Dataset, DataRow
    from .file_parser import parse_file

    BATCH_SIZE = 500   # rows per bulk_create call

    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        logger.error("process_dataset: Dataset %s not found", dataset_id)
        return

    dataset.status = Dataset.STATUS_PROCESSING
    dataset.error_message = ''
    dataset.save(update_fields=['status', 'error_message'])
    logger.info("Processing dataset %s (%s)", dataset_id, dataset.original_name)

    try:
        # ── Parse ─────────────────────────────────────────────────────────
        columns, rows = parse_file(dataset.file.path)
        logger.info("Parsed %d rows × %d cols", len(rows), len(columns))

        # ── Clear old rows (re-processing case) ───────────────────────────
        DataRow.objects.filter(dataset=dataset).delete()

        # ── Bulk insert in batches ────────────────────────────────────────
        total = len(rows)
        for start in range(0, total, BATCH_SIZE):
            batch = rows[start:start + BATCH_SIZE]
            DataRow.objects.bulk_create([
                DataRow(dataset=dataset, row_index=start + i, data=row)
                for i, row in enumerate(batch)
            ])
            logger.debug("Inserted rows %d–%d / %d", start, start + len(batch), total)

        # ── Update dataset metadata ────────────────────────────────────────
        dataset.columns      = columns
        dataset.row_count    = total
        dataset.col_count    = len(columns)
        dataset.status       = Dataset.STATUS_READY
        dataset.processed_at = timezone.now()
        dataset.save(update_fields=[
            'columns', 'row_count', 'col_count', 'status', 'processed_at'
        ])
        logger.info("Dataset %s ready — %d rows", dataset_id, total)

    except Exception as exc:
        logger.exception("Error processing dataset %s: %s", dataset_id, exc)
        dataset.status        = Dataset.STATUS_ERROR
        dataset.error_message = str(exc)
        dataset.save(update_fields=['status', 'error_message'])
        # Retry up to max_retries
        raise self.retry(exc=exc)
