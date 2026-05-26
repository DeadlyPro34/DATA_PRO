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

To run DATA_PRO with its background workers and schedulers, you need to open **3 separate terminal windows**. Make sure your virtual environment (`venv\Scripts\activate`) is activated in all of them!

**Terminal 1: Start the Django Web Server**
```cmd
python manage.py runserver
```

**Terminal 2: Start the Celery Worker (Background tasks)**
```cmd
python -m celery -A data_pro_project worker --pool=solo -l INFO
```

**Terminal 3: Start Celery Beat (Scheduled tasks / Folder Watcher)**
```cmd
python -m celery -A data_pro_project beat -l INFO
```

Access the application at `http://127.0.0.1:8000`.

## Exporting Reports
You can export cleaned data, summaries, and cleaning logs into **PDF** and **Excel** formats using the Export Center in the UI. Ensure `reportlab` and `openpyxl` are installed via `requirements.txt`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
