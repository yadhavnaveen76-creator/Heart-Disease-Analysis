# CardioSync - Heart Disease Analysis Platform

CardioSync is a premium, full-stack medical informatics web application designed to analyze cardiovascular clinical data, identify critical cardiac risk parameters, and evaluate patient health anomalies. The system features a responsive analytics interface built with Python Flask, SQLAlchemy, SQLite, HTML5, CSS3, JavaScript, Bootstrap 5, ApexCharts, and Tableau.

---

## Key Features

1. **Secure Admin Authentication**: Simple login session management (via Flask-Login) guarding administrative endpoints. Default developer credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
2. **Seeding & Cleaning Data Pipeline**: Administrators can drag-and-drop a CSV dataset (e.g. Kaggle `heart.csv` or UCI `processed.cleveland.data`). The pipeline normalizes headers, drops duplicates, imputes missing cells, clips outliers, commits records to SQLite, and immediately triggers ML retraining.
3. **Interactive Local Dashboard**: Custom interactive charts using ApexCharts (Age Prevalence, Chest Pain type risk, Max HR scatter, Cholesterol categories) connected directly to SQL aggregate query parameters.
4. **Tableau Integration**: Dedicated container supporting Tableau Public dashboards, allowing analysts to configure, save, and embed their own custom Tableau worksheets.
5. **Advanced Analytics**: Pearson Correlation Heatmaps ($r$) mapping parameter associations alongside complete dataset summary metrics (means, standard deviations, distributions).
6. **Self-Contained Prediction Engine**: A Logistic Regression classifier built from scratch using NumPy that updates its weights dynamically when a new dataset is uploaded.
7. **Read-Only SQL Console**: Full SQL console that lets analysts run custom queries with automatic checks to prevent modifying statements.

---

## Folder Structure

```text
c:\medical naveen\
├── app.py                 # Flask server controller and API routes
├── models.py              # User (Auth) and Patient SQLAlchemy tables schema
├── db_config.py           # Database config with self-healing driver fallback
├── data_pipeline.py       # Data cleaning, imputation, and Pearson correlations
├── requirements.txt       # Python dependencies list
├── setup_db.py            # CLI database seeding script
├── README.md              # Project documentation
├── static/
│   ├── css/
│   │   └── styles.css     # Unified CSS variables and custom components
│   └── js/
│       └── main.js        # Theme toggles and narrative slide slideshow
└── templates/
    ├── base.html          # Responsive Bootstrap master template
    ├── index.html         # Overview landing page with scenarios
    ├── login.html         # Administrator credentials card
    ├── upload.html        # CSV upload dropzone and cleaning summary
    ├── dashboard.html     # ApexCharts grid and Tableau embed controls
    ├── analytics.html     # Pearson heatmap and statistical stats
    └── database.html      # Schema list and SQL console query runner
```

---

## Data Dictionary (Patient Schema)

| Variable | Description | Value Map |
| :--- | :--- | :--- |
| **id** | Primary key identifier | Sequential Integer |
| **age** | Patient age in years | Integer (29 to 77) |
| **sex** | Biological sex | `0` = Female, `1` = Male |
| **cp** | Chest pain type classification | `1` = Typical Angina, `2` = Atypical Angina, `3` = Non-Anginal, `4` = Asymptomatic |
| **trestbps** | Resting blood pressure | Integer mm Hg (on hospital admission) |
| **chol** | Serum cholesterol | Integer mg/dl |
| **fbs** | Fasting blood sugar > 120 mg/dl | `0` = False, `1` = True |
| **restecg** | Resting electrocardiographic results | `0` = Normal, `1` = ST-T Wave Abnormality, `2` = LV Hypertrophy |
| **thalach** | Maximum heart rate achieved | Integer bpm |
| **exang** | Exercise-induced angina | `0` = No, `1` = Yes |
| **oldpeak** | ST depression induced by exercise | Float (0.0 to 6.2) |
| **slope** | Slope of peak exercise ST segment | `1` = Upsloping, `2` = Flat, `3` = Downsloping |
| **ca** | Number of major vessels colored | Integer (0 to 3) by fluoroscopy |
| **thal** | Thalassemia types | `3` = Normal, `6` = Fixed Defect, `7` = Reversible Defect |
| **target** | Angiographic disease presence | `0` = Normal, `1` = Heart Disease Confirmed |

---

## Installation & Setup

### Prerequisites
Make sure **Python 3** is installed and in your environment PATH.

### 1. Configure the Environment
Initialize local configurations by editing the `.env` file in the project root:
```env
DB_TYPE=sqlite
DB_PATH=heart_disease.db
PORT=5000
```
*(If you want to connect to MySQL/PostgreSQL, install the drivers like `pymysql`/`psycopg2` and update the parameters in `.env` accordingly).*

### 2. Seed the Database
Run the CLI setup script to create database tables and seed the initial dataset:
```bash
py setup_db.py
```

### 3. Run the Platform
Start the Flask local development server:
```bash
py app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**
"# Heart-Disease-Analysis" 
"# Heart-Disease-Analysis" 
