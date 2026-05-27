# Data Pro

Data Pro is a Django-based web application that allows users to securely upload datasets (CSV/Excel), view raw data, check data cleaning logs, and interactively build charts for data visualization.

## Features
- **User Authentication**: Secure login and signup.
- **Dataset Management**: Upload, manage, and delete datasets securely in your workspace.
- **Data Visualization**: Interactive chart builder (e.g., Bar Charts) with customizable X and Y axes.
- **Data Preview**: View raw tabular data seamlessly within the application.
- **Data Cleaning Log**: Keep track of applied data cleaning and transformation steps.

## Screenshots

### Login Page
![Login](screenshots/login.png)

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Interactive Chart Builder
![Chart Builder](screenshots/chart_builder.png)

*(Note: Please save the screenshots you provided into the `screenshots` folder and name them `login.png`, `dashboard.png`, and `chart_builder.png` so they show up here.)*

## Tech Stack
- **Backend**: Django (Python)
- **Background Processing**: Celery & Redis
- **Data Processing**: Pandas, OpenPyXL
- **PDF Generation**: reportlab
- **Frontend**: HTML, CSS, JavaScript (Vanilla CSS/Modern UI)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DATA_PRO
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Redis:**
   - **Windows:** Download and install the [Redis .msi installer](https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.msi). It runs automatically as a background service.
   - **Mac:** `brew install redis` and run `brew services start redis`
   - **Linux:** `sudo apt install redis-server` and run `sudo systemctl start redis`

5. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

## Running the Application

To run DATA_PRO with its full automated background processing stack (including the auto-ingestion folder watcher), you need to open **4 separate terminal windows**. Make sure your virtual environment (`venv\Scripts\activate`) is activated in all of them (except Redis if running via WSL/System).

**Terminal 1: Start the Django Web Server**
```bash
python manage.py runserver
```

**Terminal 2: Start the Redis Server**
*(If Redis is not already running as a background service)*
```bash
redis-server
```

**Terminal 3: Start the Celery Worker (Background tasks)**
```bash
python -m celery -A data_pro_project worker --loglevel=info --pool=solo
```

**Terminal 4: Start Celery Beat (Scheduler & Auto-Ingestion)**
```bash
python -m celery -A data_pro_project beat --loglevel=info
```

Access the application at `http://127.0.0.1:8000`.

## Auto-Ingestion Pipeline (Watched Inbox)
DATA_PRO includes an automated file ingestion system. 
Once Celery Beat is running (Terminal 4), a folder named `watched_inbox/` will be automatically created in your project root. 
1. Simply drop any `.csv`, `.xlsx`, or `.json` file into the `watched_inbox/` folder.
2. Celery Beat scans this folder **every 5 minutes**.
3. It automatically ingests new files, queues them for background data profiling, and then removes the original file from the inbox once queued.


## Exporting Reports
You can export cleaned data, summaries, and cleaning logs into **PDF** and **Excel** formats using the Export Center in the UI. Ensure `reportlab` and `openpyxl` are installed via `requirements.txt`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
