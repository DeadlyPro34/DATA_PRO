# DATA PRO

A full-stack data analytics and visualization platform designed to streamline dataset management, processing, and reporting. DATA PRO allows users to upload Excel or CSV datasets, view and edit records, and instantly generate Pandas-driven automated dashboards and charts without relying on external AI APIs.

## Description

DATA PRO solves the problem of manual data exploration by providing an automated, out-of-the-box analytical dashboard for any uploaded tabular dataset. It is built for data analysts, business users, and developers who need a fast, local, and secure way to inspect data, compute KPIs, and visualize trends over time without complex BI tool setups.

## Features

- **Dataset Management**: Upload, index, and manage multiple Excel/CSV datasets.
- **Spreadsheet Editor**: View, sort, and edit dataset records directly from the browser.
- **Auto Dashboard**: Instantly generate analytical dashboards featuring:
  - Dynamic KPI cards (Sums, Averages, Peaks, Row/Column counts).
  - Categorical distribution (Donut charts) & comparisons (Bar charts).
  - Time-series trend analysis (Area/Line charts).
  - Top 5 ranked performers tables.
- **Smart Insights**: Auto-generated text insights analyzing null percentages, variances, and dataset metadata using pure Pandas logic.
- **PDF Export**: One-click, pixel-perfect PDF export of analytical dashboards.
- **Background Processing**: Asynchronous dataset indexing and processing using Celery and Redis to handle large files seamlessly.

## Tech Stack

- **Frontend**: React (Vite), Vanilla CSS, ApexCharts (Visualizations), html2canvas & jsPDF (Exporting), Lucide React (Icons).
- **Backend**: Django, Django REST Framework (DRF), Celery, Redis, Pandas, OpenPyXL.
- **Database**: PostgreSQL.

## Project Structure

```text
DATA_PRO/
├── backend/                  # Django backend API
│   ├── api/                  # Core application logic & Pandas processing
│   ├── config/               # Django project settings & routing
│   ├── media/                # Uploaded datasets storage
│   ├── manage.py             # Django execution script
│   └── .env                  # Backend environment variables
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/       # UI components (AutoDashboard, etc.)
│   │   ├── api.js            # Axios client for backend communication
│   │   ├── App.jsx           # Main application routing and state
│   │   └── index.css         # Global design tokens and styles
│   └── package.json          # Frontend dependencies
├── run_backend.bat           # Convenience script for Windows backend execution
└── run_frontend.bat          # Convenience script for Windows frontend execution
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL
- Redis Server (Running on localhost:6379)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DATA_PRO
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Start the Django server
python manage.py runserver
```

### 3. Background Worker (Celery)
In a new terminal window, start the Celery worker to process dataset uploads:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
celery -A config worker --loglevel=info --pool=solo
```

### 4. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Open the application in your browser (typically `http://localhost:5173` or `5174`).
2. Navigate to the **Datasets** tab and upload an Excel or CSV file.
3. Wait for the Celery background worker to index the file (indicated by the progress toast).
4. Navigate to the **Auto Dashboard** tab, select your dataset from the dropdown, and instantly view the generated analytics.
5. Click **Export PDF** to save the dashboard locally.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/datasets/upload/` | Uploads and queues a dataset for processing. |
| `GET`  | `/api/datasets/` | Lists all datasets and their processing status. |
| `GET`  | `/api/datasets/<id>/auto_dashboard/` | Returns Pandas-computed KPIs, chart data, and metadata. |
| `GET`  | `/api/datasets/<id>/rows/` | Returns paginated rows for the spreadsheet view. |

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=Excel_Pro
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
CORS_ORIGIN=http://localhost:5174
```

## Future Improvements

- Add support for custom SQL query execution from the frontend.
- Implement user authentication and private workspaces.
- Introduce interactive drill-downs on dashboard charts.
- Expand data cleaning capabilities (handling outliers and imputing missing values directly via the UI).

## License

This project is licensed under the MIT License.
