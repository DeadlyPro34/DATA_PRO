# DATA PRO — Full Stack Edition

A robust, full-stack data analytics and visualization platform designed to streamline dataset management, processing, and reporting. DATA PRO allows users to upload Excel or CSV datasets, view and edit records, and instantly generate Pandas-driven automated dashboards and charts — entirely locally, without relying on external AI APIs.

## 👥 Contributors

- **Akhil Biju Varghese** ([@DeadlyPro34](https://github.com/DeadlyPro34))
- **Taksh Patel** ([@Taksh-Patel02](https://github.com/Taksh-Patel02))

---

## 💡 What We Used & Why (Architecture)

This project is built using a modern, decoupled architecture to ensure high performance even when processing heavy datasets.

### Frontend
- **React + Vite**: Chosen for lightning-fast hot reloading and component-based UI development.
- **Vanilla CSS / Custom Styling**: We built a custom glassmorphism design system (lavender/indigo theme) for a premium, lightweight UI without relying heavily on bloated component libraries.
- **ApexCharts**: Used for rendering interactive, responsive charts (Bar, Donut, Area).
- **html2canvas & jsPDF**: Implemented to capture the analytical dashboard and instantly export pixel-perfect PDFs locally.

### Backend
- **Django & Django REST Framework (DRF)**: Serves as the robust backend API. Django handles our models, views, and routing securely.
- **PostgreSQL**: Used as the primary relational database (`Excel_Pro`) to store dataset metadata and user information securely.
- **Pandas & OpenPyXL**: The absolute core of our analytics engine. Instead of using third-party AI APIs, we wrote pure Python/Pandas logic to ingest datasets, clean data, detect column types, and compute KPIs, averages, peaks, and trends locally.
- **Celery & Redis**: Dataset processing can take time. We use Celery as an asynchronous task queue backed by Redis to process heavy Excel files in the background. This ensures the frontend UI never freezes while uploading or indexing data.

---

## ✨ Key Features

- **Dataset Management**: Upload, index, and manage multiple Excel/CSV datasets asynchronously.
- **Spreadsheet Editor**: View, sort, and inline-edit dataset records directly from the browser.
- **Auto Dashboard**: Instantly generate analytical dashboards featuring:
  - Dynamic KPI cards (Sums, Averages, Peaks, Row counts).
  - Categorical distribution (Donut charts) & comparisons (Bar charts).
  - Time-series trend analysis (Area/Line charts).
  - Top 5 ranked performers table.
- **Smart Insights**: Auto-generated text insights analyzing null percentages, variances, and dataset metadata using pure Pandas logic.
- **PDF Export**: One-click PDF export of analytical dashboards.

---

## 🚀 Installation & Setup Guide

Follow these steps exactly to get the project running on your local machine.

### Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.9+**
- **Node.js 18+**
- **PostgreSQL** (Create a database named `Excel_Pro`)
- **Redis Server** (Must be running on `localhost:6379`)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DATA_PRO
```

### 2. Backend Setup (Django)
Open a terminal and navigate to the backend folder:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On Mac/Linux:
python3 -m venv venv
source venv/bin/activate
```

Install the Python dependencies:
```bash
pip install -r requirements.txt
```

Set up your `.env` file in the `backend/` directory:
```env
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=Excel_Pro
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
CORS_ORIGIN=http://localhost:5174
```

Apply database migrations and start the server:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
*The backend API will now be running on `http://localhost:8000`.*

### 3. Start the Background Worker (Celery)
**Open a second terminal window**, navigate to the backend folder, and activate the virtual environment again:
```bash
cd backend
venv\Scripts\activate  # On Windows
```
Start the Celery worker to handle background dataset processing (Use `--pool=solo` on Windows):
```bash
celery -A config worker --loglevel=info --pool=solo
```

### 4. Frontend Setup (React)
**Open a third terminal window** and navigate to the frontend folder:
```bash
cd frontend
```

Install the Node dependencies and start the Vite development server:
```bash
npm install
npm run dev
```
*The React app will typically start on `http://localhost:5173` or `5174`.*

---

## 💻 Usage

1. **Access the App**: Open your browser and go to the frontend URL (e.g., `http://localhost:5174`).
2. **Upload Data**: Navigate to the **Datasets** tab and upload an `.xlsx` or `.csv` file.
3. **Background Processing**: A creative toast notification will appear. Celery will process and index your file in the background without freezing your browser.
4. **View Dashboards**: Navigate to the **Auto Dashboard** tab, select your ready dataset from the dropdown, and instantly view the Pandas-generated analytics.
5. **Export**: Click the **Export PDF** button to download a copy of your dashboard.

---

## 🛠 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/datasets/upload/` | Uploads and queues a dataset for processing via Celery. |
| `GET`  | `/api/datasets/` | Lists all datasets and their processing status. |
| `GET`  | `/api/datasets/<id>/auto_dashboard/` | Returns Pandas-computed KPIs, chart data, and metadata. |
| `GET`  | `/api/datasets/<id>/rows/` | Returns paginated rows for the spreadsheet view. |

---

## 🔮 Future Improvements

- Add support for custom SQL query execution from the frontend.
- Implement user authentication and private workspaces.
- Introduce interactive drill-downs on dashboard charts.
- Expand data cleaning capabilities (handling outliers and imputing missing values directly via the UI).

---

## 📄 License

This project is licensed under the MIT License.
