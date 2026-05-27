"""
migrate_to_postgres.py
======================
One-shot script to migrate DATA_PRO from SQLite to PostgreSQL.

Steps it performs automatically:
  1. Dumps all data from SQLite → data_backup.json
  2. Creates the PostgreSQL database 'data_pro' (if it doesn't exist)
  3. Runs Django migrations on PostgreSQL
  4. Loads the dumped data into PostgreSQL

Run this ONCE from the project root:
    python migrate_to_postgres.py

Requirements:
  - PostgreSQL is installed and running
  - psycopg2-binary is installed  (pip install psycopg2-binary)
  - Your .env file has DB_USER and DB_PASSWORD set correctly
"""

import os
import sys
import subprocess
import django

# ── 0. Load .env so os.environ has DB_* values ──────────────────────────────
from pathlib import Path

env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())

DB_NAME     = os.environ.get('DB_NAME', 'data_pro')
DB_USER     = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST     = os.environ.get('DB_HOST', 'localhost')
DB_PORT     = os.environ.get('DB_PORT', '5432')

BACKUP_FILE = 'data_backup.json'

print("\n" + "="*60)
print("   DATA_PRO  →  SQLite to PostgreSQL Migration")
print("="*60 + "\n")

# ── 1. Temporarily point Django at SQLite to export data ─────────────────────
print("STEP 1: Exporting data from SQLite …")

os.environ['DJANGO_SETTINGS_MODULE'] = 'data_pro_project.settings'

# Patch settings in-memory: use SQLite for the export only
import importlib
import data_pro_project.settings as _settings_mod

_orig_db = _settings_mod.DATABASES.copy()
_settings_mod.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(Path(__file__).parent / 'db.sqlite3'),
    }
}

django.setup()
from django.core import management
from io import StringIO

buf = StringIO()
try:
    management.call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '--exclude=contenttypes',
        '--exclude=auth.permission',
        '--indent=2',
        stdout=buf,
    )
    data_json = buf.getvalue()
    if not data_json.strip():
        print("  ⚠  SQLite database appears to be empty — nothing to export.")
        data_json = '[]'
    with open(BACKUP_FILE, 'w', encoding='utf-8') as fp:
        fp.write(data_json)
    print(f"  ✅  Data exported to {BACKUP_FILE}")
except Exception as exc:
    print(f"  ❌  Export failed: {exc}")
    sys.exit(1)

# ── 2. Create the PostgreSQL database if it doesn't exist ────────────────────
print(f"\nSTEP 2: Creating PostgreSQL database '{DB_NAME}' …")
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone():
        print(f"  ℹ  Database '{DB_NAME}' already exists — skipping creation.")
    else:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"  ✅  Database '{DB_NAME}' created.")

    cur.close()
    conn.close()
except Exception as exc:
    print(f"  ❌  Could not connect to PostgreSQL: {exc}")
    print("  Make sure PostgreSQL is running and DB_USER / DB_PASSWORD are correct in .env")
    sys.exit(1)

# ── 3. Switch Django back to PostgreSQL and run migrations ───────────────────
print("\nSTEP 3: Running Django migrations on PostgreSQL …")
_settings_mod.DATABASES = _orig_db   # restore PostgreSQL config

# We need to re-initialise Django connections
from django.db import connections
connections.close_all()

try:
    management.call_command('migrate', '--run-syncdb', verbosity=1)
    print("  ✅  Migrations complete.")
except Exception as exc:
    print(f"  ❌  Migration failed: {exc}")
    sys.exit(1)

# ── 4. Load the exported data into PostgreSQL ────────────────────────────────
print(f"\nSTEP 4: Loading data from {BACKUP_FILE} into PostgreSQL …")
try:
    management.call_command(
        'loaddata',
        BACKUP_FILE,
        verbosity=1,
    )
    print("  ✅  Data loaded successfully.")
except Exception as exc:
    print(f"  ❌  loaddata failed: {exc}")
    print("  The database was created and migrated — your backup is at data_backup.json")
    print("  You can retry with:  python manage.py loaddata data_backup.json")
    sys.exit(1)

print("\n" + "="*60)
print("  ✅  MIGRATION COMPLETE!")
print(f"  Your data is now in PostgreSQL database: {DB_NAME}")
print(f"  Backup saved at: {BACKUP_FILE}  (keep this safe!)")
print("="*60 + "\n")
