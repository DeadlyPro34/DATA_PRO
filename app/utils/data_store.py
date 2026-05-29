"""
data_store.py — re-export shim for DATA_PRO
============================================

parquet_helpers.py is the single source of truth for DataFrame
persistence. This module re-exports its public API so that any
existing code that imports from data_store continues to work
without modification.
"""

from app.utils.parquet_helpers import (
    save_dataframe_to_parquet,
    get_dataframe,
)

__all__ = ['save_dataframe_to_parquet', 'get_dataframe']
