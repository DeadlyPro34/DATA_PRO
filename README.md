# DATA_PRO

DATA_PRO is a full-stack Django web application for intelligent data ingestion, automated cleaning, AI-powered analysis, and interactive visualization. Upload a CSV, Excel, or JSON file — and get a cleaned, profiled, AI-summarized dataset with charts and export options, all processed automatically in the background.

---

## ✨ Features

- **User Authentication** — Secure login, signup, and per-user workspaces.
- **Dataset Management** — Upload, manage, re-clean, and delete datasets.
- **Automated Data Cleaning** — Removes duplicates, normalizes headers, trims whitespace, drops empty rows/columns, coerces numeric types. Up to 5,000 rows processed per file.
- **AI Insights** — OpenAI-powered summaries and health reports generated automatically for every dataset.
- **Parquet Storage** — Cleaned DataFrames are stored as efficient columnar Parquet files instead of bloating the database with raw row data.
- **Interactive Chart Builder** — Bar, Line, and other chart types with customizable X/Y axes.
- **Data Preview** — View raw and cleaned tabular data side by side in the browser.
- **Cleaning Log & Health Report** — Full audit trail of every cleaning action applied.
- **Export Center** — Export cleaned data, summaries, and cleaning logs as **PDF** or **Excel**.
- **REST API** — DRF-powered API with Token & Session authentication for programmatic access.
- **Auto-Ingestion Pipeline** — Drop files into `watched_inbox/` and Celery Beat auto-processes them every 5 minutes.
- **Team & Membership Model** — Multi-user team support with role-based membership.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5+ / Django REST Framework |
| **Database** | PostgreSQL 18 (via `psycopg2-binary`) |
| **Background Tasks** | Celery 5 + Redis (Worker + Beat scheduler) |
| **Data Processing** | Pandas, NumPy, OpenPyXL |
| **Columnar Storage** | PyArrow (Parquet files) |
| **AI Integration** | OpenAI API |
| **PDF Generation** | WeasyPrint |
| **Frontend** | Vanilla HTML / CSS / JavaScript |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd DATA_PRO
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac / Linux:
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install & configure PostgreSQL

- **Windows:** Download from https://www.postgresql.org/download/windows/ (use the EDB installer, include pgAdmin).
- **Mac:** `brew install postgresql@18 && brew services start postgresql@18`
- **Linux:** `sudo apt install postgresql && sudo systemctl start postgresql`

#### Add PostgreSQL `bin/` to your PATH (Windows only)
If `psql` isn't found on the command line, run this once in PowerShell:
```powershell
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("Path", $currentPath + ";C:\Program Files\PostgreSQL\18\bin", [System.EnvironmentVariableTarget]::User)
```
Then open a **new terminal** for the change to take effect.

#### Create the database and user
Open **pgAdmin** or run `psql -U postgres` and execute:
```sql
CREATE DATABASE data_pro;
CREATE USER data_pro_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE data_pro TO data_pro_user;
```
> You can also connect as the default `postgres` superuser — just set `DB_USER=postgres` in `.env`.

### 5. Create your `.env` file
Create a file named `.env` in the project root (`DATA_PRO/`) with the following content:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
DB_NAME=data_pro
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# OpenAI (optional — leave blank to disable AI insights)
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. Install Redis

| OS | Command |
|---|---|
| **Windows** | Download [Redis .msi installer](https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.msi) — runs as a background service automatically |
| **Mac** | `brew install redis && brew services start redis` |
| **Linux** | `sudo apt install redis-server && sudo systemctl start redis` |

### 7. Apply migrations & create superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 🚀 Running the Application

Open **4 separate terminals**, activate `venv` in each, and run:

**Terminal 1 — Django Web Server**
```bash
python manage.py runserver
```

**Terminal 2 — Redis Server** *(skip if already running as a service)*
```bash
redis-server
```

**Terminal 3 — Celery Worker** *(processes uploaded files in the background)*
```bash
python -m celery -A data_pro_project worker --loglevel=info --pool=solo
```

**Terminal 4 — Celery Beat** *(scheduler + auto-ingestion every 5 minutes)*
```bash
python -m celery -A data_pro_project beat --loglevel=info
```

Access the app at **http://127.0.0.1:8000**

---

## 📥 Auto-Ingestion Pipeline (Watched Inbox)

Once Celery Beat is running, a `watched_inbox/` folder is automatically created in the project root.

1. Drop any `.csv`, `.xlsx`, `.xls`, `.xlsm`, or `.json` file into `watched_inbox/`.
2. Celery Beat scans it **every 5 minutes** via the `scan_watched_inbox` task.
3. Each file is ingested, registered as an `UploadedFile`, queued for background cleaning & profiling, then removed from the inbox.

---

## 🗄️ Database Shell

To open an interactive PostgreSQL shell connected to `data_pro`:
```bash
python manage.py dbshell
```

Useful psql commands:

| Command | Description |
|---|---|
| `\dt` | List all tables |
| `\d tablename` | Describe a table |
| `\l` | List all databases |
| `\du` | List all users/roles |
| `\q` | Quit |

---

## 📤 Exporting Reports

From the **Export Center** in the UI you can download:
- ✅ Cleaned dataset as **Excel** (`.xlsx`)
- ✅ Cleaning log + health report as **PDF**
- ✅ AI insights summary

---

## 📁 Project Structure

```
DATA_PRO/
├── app/
│   ├── models.py          # Team, UploadedFile, CleanedDataset, SavedPipeline
│   ├── tasks.py           # Celery tasks: process_uploaded_file_task, scan_watched_inbox
│   ├── views.py           # All page views
│   ├── api_views.py       # REST API endpoints
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # URL routing
│   └── utils/
│       ├── parquet_helpers.py   # Single source of truth for Parquet I/O
│       ├── data_store.py        # Re-export shim → parquet_helpers
│       ├── file_parser.py       # CSV / Excel / JSON parser
│       ├── data_cleaner.py      # Automated cleaning logic
│       └── ai_insights.py       # OpenAI insights builder
├── data_pro_project/
│   ├── settings.py        # PostgreSQL + Celery + env-based config
│   ├── celery.py          # Celery app definition
│   └── urls.py
├── watched_inbox/         # Drop files here for auto-ingestion
├── media/
│   └── parquet_data/      # Cleaned DataFrames stored as .parquet files
├── .env                   # Environment variables (not committed to git)
├── requirements.txt
└── manage.py
```

---

## 🔒 Security Notes

- `.env` is listed in `.gitignore` — **never commit it**.
- Set `DEBUG=False` and a strong `SECRET_KEY` before deploying to production.
- Restrict `ALLOWED_HOSTS` to your domain in production.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
