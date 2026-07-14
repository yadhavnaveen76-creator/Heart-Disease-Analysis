import os
import numpy as np
import pandas as pd
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from sqlalchemy import text
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Project modules
from db_config import db_repo
from models import User
from data_pipeline import clean_and_preprocess_csv, calculate_pearson_correlations

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cardiosync_secret_production_key_9482')

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db_repo.find_user_by_id(user_id)

# Simple Logistic Regression model training
model_params = None

def train_ml_model():
    global model_params
    try:
        data_rows = db_repo.get_patients()
        if not data_rows:
            print("Model training skipped: Patient database is empty.")
            model_params = None
            return False
            
        data = []
        for r in data_rows:
            data.append([
                r['age'], r['sex'], r['cp'], r['trestbps'], r['chol'], r['fbs'], r['restecg'], 
                r['thalach'], r['exang'], r['oldpeak'], r['slope'], r['ca'], r['thal'], r['smoking'], r['bmi'], r['target']
            ])
            
        data = np.array(data, dtype=float)
        X = data[:, :-1]
        y = data[:, -1]
        
        # Normalize features
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        std[std == 0] = 1e-8
        
        X_scaled = (X - mean) / std
        X_bias = np.hstack([np.ones((X_scaled.shape[0], 1)), X_scaled])
        
        # Train Logistic Regression
        weights = np.zeros(X_bias.shape[1])
        learning_rate = 0.1
        epochs = 1000
        
        for _ in range(epochs):
            z = np.dot(X_bias, weights)
            h = 1 / (1 + np.exp(-z))
            gradient = np.dot(X_bias.T, (h - y)) / y.size
            weights -= learning_rate * gradient
            
        model_params = {
            'weights': weights.tolist(),
            'mean': mean.tolist(),
            'std': std.tolist()
        }
        print(f"Logistic Regression Model trained successfully on {len(data_rows)} patients!")
        return True
    except Exception as e:
        print(f"Error training model: {e}")
        return False

# Model prediction helper
def predict_heart_disease(features):
    global model_params
    if model_params is None:
        success = train_ml_model()
        if not success or model_params is None:
            return 0.5, "Error: Model not trained"
            
    try:
        weights = np.array(model_params['weights'])
        mean = np.array(model_params['mean'])
        std = np.array(model_params['std'])
        
        features_arr = np.array(features, dtype=float)
        scaled_features = (features_arr - mean) / std
        scaled_with_bias = np.insert(scaled_features, 0, 1.0)
        
        z = np.dot(scaled_with_bias, weights)
        prob = 1 / (1 + np.exp(-z))
        
        return prob, "Success"
    except Exception as e:
        return 0.5, f"Prediction error: {e}"

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        try:
            u = db_repo.find_user(username)
            if u and u.check_password(password):
                login_user(u)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
                        
            flash('Invalid username or password.', 'danger')
        except Exception as e:
            flash(f"Login database error: {e}", 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- CORE PLATFORM ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            age = float(request.form.get('age', 54))
            sex = float(request.form.get('sex', 1))
            cp = float(request.form.get('cp', 1))
            trestbps = float(request.form.get('trestbps', 130))
            chol = float(request.form.get('chol', 240))
            fbs = float(request.form.get('fbs', 0))
            restecg = float(request.form.get('restecg', 0))
            thalach = float(request.form.get('thalach', 150))
            exang = float(request.form.get('exang', 0))
            oldpeak = float(request.form.get('oldpeak', 1.0))
            slope = float(request.form.get('slope', 1))
            ca = float(request.form.get('ca', 0))
            thal = float(request.form.get('thal', 3))
            smoking = float(request.form.get('smoking', 0))
            bmi = float(request.form.get('bmi', 24.5))
            
            features = [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, smoking, bmi]
            prob, msg = predict_heart_disease(features)
            
            risk_pct = round(prob * 100, 1)
            risk_class = "High" if risk_pct >= 60 else ("Medium" if risk_pct >= 30 else "Low")
            
            suggestions = []
            if risk_class == "High":
                suggestions.append("Immediate consultation with a cardiologist is strongly recommended.")
                suggestions.append("Monitor blood pressure and heart rate daily.")
                if smoking == 1:
                    suggestions.append("Smoking cessation is critical to reduce acute arterial risk.")
                if bmi >= 30:
                    suggestions.append("Weight reduction guidelines should be discussed with a nutritionist.")
            elif risk_class == "Medium":
                suggestions.append("Schedule a checkup with your primary physician to discuss risk factors.")
                suggestions.append("Engage in moderate physical activities (e.g., 30 min walking/day).")
            else:
                suggestions.append("Maintain your current healthy lifestyle and balanced diet.")
                suggestions.append("Routine annual wellness checks are sufficient.")
                
            return jsonify({
                'success': True,
                'risk_probability': prob,
                'risk_percentage': risk_pct,
                'risk_classification': risk_class,
                'suggestions': suggestions
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
            
    return render_template('predict.html')

@app.route('/story')
def story():
    return render_template('story.html')

@app.route('/database', methods=['GET', 'POST'])
def database():
    schema = db_repo.get_sqlite_schema()
    query_result = None
    query_error = None
    query_str = "SELECT * FROM patients LIMIT 10"
    
    if request.method == 'POST':
        if db_repo.mode == 'mongodb':
            query_error = "SQL Console queries are deactivated when running under MongoDB backend collections mode."
        else:
            query_str = request.form.get('sql_query', '').strip()
            query_upper = query_str.upper()
            blocked_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'REPLACE', 'TRUNCATE']
            
            if not query_str:
                query_error = "Query cannot be empty."
            elif not query_upper.startswith('SELECT') and not query_upper.startswith('EXPLAIN') and not query_upper.startswith('PRAGMA'):
                query_error = "Security Restriction: Only SELECT (read-only) queries are allowed."
            elif any(k in query_upper for k in blocked_keywords):
                query_error = "Security Restriction: Write operations are not allowed."
            else:
                try:
                    with db_repo.sql_engine.connect() as conn:
                        result = conn.execute(text(query_str))
                        headers = list(result.keys())
                        rows = [list(row) for row in result.fetchall()]
                        
                        query_result = {
                            'headers': headers,
                            'rows': rows,
                            'count': len(rows)
                        }
                except Exception as e:
                    query_error = str(e)
                
    return render_template('database.html', schema=schema, query_str=query_str, query_result=query_result, query_error=query_error)

# --- ADVANCED ANALYTICS ROUTE ---
@app.route('/analytics')
def analytics():
    try:
        data_rows = db_repo.get_patients()
        if not data_rows:
            return render_template('analytics.html', empty=True)
            
        columns = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'smoking', 'bmi', 'target']
        df = pd.DataFrame(data_rows, columns=columns)
        
        correlation_data = calculate_pearson_correlations(df)
        
        summary_stats = {
            'records_count': len(df),
            'avg_age': round(df['age'].mean(), 1),
            'std_age': round(df['age'].std(), 1),
            'avg_chol': round(df['chol'].mean(), 1),
            'std_chol': round(df['chol'].std(), 1),
            'avg_trestbps': round(df['trestbps'].mean(), 1),
            'std_trestbps': round(df['trestbps'].std(), 1),
            'avg_thalach': round(df['thalach'].mean(), 1),
            'std_thalach': round(df['thalach'].std(), 1),
            'avg_bmi': round(df['bmi'].mean(), 1),
            'std_bmi': round(df['bmi'].std(), 1),
            'high_risk_percentage': round((df['target'].sum() / len(df)) * 100, 1),
            'male_percentage': round((df['sex'].sum() / len(df)) * 100, 1),
            'smoker_percentage': round((df['smoking'].sum() / len(df)) * 100, 1)
        }
        
        return render_template('analytics.html', empty=False, stats=summary_stats, correlations=correlation_data)
    except Exception as e:
        print(f"Analytics rendering error: {e}")
        return render_template('analytics.html', empty=True, error=str(e))

# --- DATA CSV UPLOAD ROUTE (Admin Required) ---
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'admin':
        flash('Access restricted to Administrator accounts.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file segment found.'}), 400
            
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
            
        if not uploaded_file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Invalid file type. Only CSV files are supported.'}), 400
            
        try:
            csv_stream = __import__('io').StringIO(uploaded_file.read().decode('utf-8'))
            cleaned_df, cleaning_stats = clean_and_preprocess_csv(csv_stream)
            
            if cleaned_df is None:
                err_msg = cleaning_stats['errors'][0] if cleaning_stats['errors'] else "CSV parsing failed."
                return jsonify({'success': False, 'error': err_msg}), 400
                
            # Clear & bulk insert via repository manager
            db_repo.clear_patients()
            dict_rows = cleaned_df.to_dict(orient='records')
            db_repo.bulk_add_patients(dict_rows)
            
            # Save dataset upload logs
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_repo.add_dataset({
                'filename': uploaded_file.filename,
                'upload_time': timestamp,
                'raw_rows': cleaning_stats['total_rows_raw'],
                'clean_rows': cleaning_stats['rows_cleaned'],
                'duplicates_removed': cleaning_stats['duplicates_removed'],
                'missing_filled': cleaning_stats['missing_values_filled'],
                'uploaded_by': current_user.username
            })
                
            train_ml_model()
            return jsonify({'success': True, 'stats': cleaning_stats})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
            
    return render_template('upload.html')

# --- ADMIN PANEL WORKSPACE: PATIENTS CRUD ---
@app.route('/admin/patients')
@login_required
def admin_patients():
    if current_user.role != 'admin':
        flash('Access restricted to Administrator accounts.', 'danger')
        return redirect(url_for('index'))
        
    page = int(request.args.get('page', 1))
    per_page = 15
    offset = (page - 1) * per_page
    
    try:
        total = db_repo.get_patients_count()
        patients = db_repo.get_patients(limit=per_page, offset=offset)
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('admin_patients.html', patients=patients, page=page, total_pages=total_pages, total_records=total)
    except Exception as e:
        flash(f"Error fetching patients records: {e}", 'danger')
        return redirect(url_for('index'))

@app.route('/admin/patients/add', methods=['POST'])
@login_required
def add_patient():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        p_dict = {
            'age': int(request.form.get('age')),
            'sex': int(request.form.get('sex')),
            'cp': int(request.form.get('cp')),
            'trestbps': int(request.form.get('trestbps')),
            'chol': int(request.form.get('chol')),
            'fbs': int(request.form.get('fbs')),
            'restecg': int(request.form.get('restecg')),
            'thalach': int(request.form.get('thalach')),
            'exang': int(request.form.get('exang')),
            'oldpeak': float(request.form.get('oldpeak')),
            'slope': int(request.form.get('slope')),
            'ca': int(request.form.get('ca')),
            'thal': int(request.form.get('thal')),
            'smoking': int(request.form.get('smoking', 0)),
            'bmi': float(request.form.get('bmi', 24.5)),
            'target': int(request.form.get('target'))
        }
        
        db_repo.add_patient(p_dict)
        train_ml_model()
        flash('Patient record added successfully!', 'success')
    except Exception as e:
        flash(f"Error adding patient: {e}", 'danger')
        
    return redirect(url_for('admin_patients'))

@app.route('/admin/patients/edit/<int:pid>', methods=['POST'])
@login_required
def edit_patient(pid):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        p_dict = {
            'age': int(request.form.get('age')),
            'sex': int(request.form.get('sex')),
            'cp': int(request.form.get('cp')),
            'trestbps': int(request.form.get('trestbps')),
            'chol': int(request.form.get('chol')),
            'fbs': int(request.form.get('fbs')),
            'restecg': int(request.form.get('restecg')),
            'thalach': int(request.form.get('thalach')),
            'exang': int(request.form.get('exang')),
            'oldpeak': float(request.form.get('oldpeak')),
            'slope': int(request.form.get('slope')),
            'ca': int(request.form.get('ca')),
            'thal': int(request.form.get('thal')),
            'smoking': int(request.form.get('smoking', 0)),
            'bmi': float(request.form.get('bmi', 24.5)),
            'target': int(request.form.get('target'))
        }
        
        db_repo.update_patient(pid, p_dict)
        train_ml_model()
        flash('Patient record updated successfully!', 'success')
    except Exception as e:
        flash(f"Error updating patient record: {e}", 'danger')
        
    return redirect(url_for('admin_patients'))

@app.route('/admin/patients/delete/<int:pid>', methods=['POST'])
@login_required
def delete_patient(pid):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        db_repo.delete_patient(pid)
        train_ml_model()
        flash('Patient record deleted successfully.', 'success')
    except Exception as e:
        flash(f"Error deleting patient record: {e}", 'danger')
        
    return redirect(url_for('admin_patients'))

# --- ADMIN PANEL: USERS CRUD ---
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access restricted to Administrator accounts.', 'danger')
        return redirect(url_for('index'))
        
    try:
        users = db_repo.get_users()
        return render_template('admin_users.html', users=users)
    except Exception as e:
        flash(f"Error loading users: {e}", 'danger')
        return redirect(url_for('index'))

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'user')
    
    if not username or not password:
        flash('Username and Password fields are required.', 'danger')
        return redirect(url_for('admin_users'))
        
    try:
        check = db_repo.find_user(username)
        if check:
            flash(f"Username '{username}' is already taken.", 'danger')
            return redirect(url_for('admin_users'))
                
        u = User(username=username, role=role)
        u.set_password(password)
        db_repo.create_user(u.username, u.password_hash, u.role)
        flash(f"User account '{username}' registered successfully.", 'success')
    except Exception as e:
        flash(f"Error creating user account: {e}", 'danger')
        
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:uid>', methods=['POST'])
@login_required
def delete_user(uid):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    if uid == current_user.id:
        flash('Security Alert: You cannot delete your own logged-in session account.', 'danger')
        return redirect(url_for('admin_users'))
        
    try:
        db_repo.delete_user(uid)
        flash('User account deleted successfully.', 'success')
    except Exception as e:
        flash(f"Error deleting user account: {e}", 'danger')
        
    return redirect(url_for('admin_users'))

# --- ADMIN PANEL: DATASET LOGS ---
@app.route('/admin/datasets')
@login_required
def admin_datasets():
    if current_user.role != 'admin':
        flash('Access restricted to Administrator accounts.', 'danger')
        return redirect(url_for('index'))
        
    try:
        datasets = db_repo.get_datasets()
        return render_template('admin_datasets.html', datasets=datasets)
    except Exception as e:
        flash(f"Error loading dataset logs: {e}", 'danger')
        return redirect(url_for('index'))

@app.route('/admin/datasets/delete/<int:did>', methods=['POST'])
@login_required
def delete_dataset_log(did):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        db_repo.delete_dataset(did)
        flash('Dataset upload log entry removed from history.', 'success')
    except Exception as e:
        flash(f"Error removing log entry: {e}", 'danger')
        
    return redirect(url_for('admin_datasets'))

# --- EXPORT CLEANED CSV API ---
@app.route('/api/export')
@login_required
def api_export():
    if current_user.role != 'admin':
        flash('Access restricted to Administrator accounts.', 'danger')
        return redirect(url_for('index'))
    try:
        data_rows = db_repo.get_patients()
        if not data_rows:
            flash("Export skipped: The database table is empty.", "warning")
            return redirect(url_for('upload'))
            
        columns = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'smoking', 'bmi', 'target']
        df = pd.DataFrame(data_rows, columns=columns)
        
        from data_pipeline import export_preprocessed_dataframe
        preprocessed_df = export_preprocessed_dataframe(df)
        
        csv_buffer = __import__('io').StringIO()
        preprocessed_df.to_csv(csv_buffer, index=False)
        csv_output = csv_buffer.getvalue()
        
        from flask import Response
        return Response(
            csv_output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=cleaned_heart_dataset.csv"}
        )
    except Exception as e:
        flash(f"Error exporting dataset: {e}", "danger")
        return redirect(url_for('upload'))

@app.route('/api/patients')
@login_required
def api_patients():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        patients = db_repo.get_patients()
        return jsonify({'success': True, 'patients': patients})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- LOCAL DATA API ---
@app.route('/api/data')
def api_data():
    age_min = int(request.args.get('age_min', 0))
    age_max = int(request.args.get('age_max', 100))
    sex_filter = request.args.get('sex', 'all')
    
    try:
        filtered_patients = db_repo.get_patients(sex_filter=sex_filter, age_min=age_min, age_max=age_max)
        total_records = len(filtered_patients)
        
        if total_records == 0:
            return jsonify({
                'kpis': {'total': 0, 'disease_pct': 0, 'avg_chol': 0, 'avg_thalach': 0, 'avg_bmi': 0, 'smoker_pct': 0},
                'charts': {}
            })
            
        disease_count = sum(1 for p in filtered_patients if p['target'] == 1)
        disease_pct = round((disease_count / total_records) * 100, 1)
        
        avg_chol = round(sum(p['chol'] for p in filtered_patients) / total_records, 1)
        avg_thalach = round(sum(p['thalach'] for p in filtered_patients) / total_records, 1)
        avg_bmi = round(sum(p['bmi'] for p in filtered_patients) / total_records, 1)
        
        smokers_count = sum(1 for p in filtered_patients if p['smoking'] == 1)
        smoker_pct = round((smokers_count / total_records) * 100, 1)
        
        # Gender Groups Count & Risk
        gender_groups = {'Male': {'normal': 0, 'disease': 0}, 'Female': {'normal': 0, 'disease': 0}}
        for p in filtered_patients:
            label = 'Male' if p['sex'] == 1 else 'Female'
            if p['target'] == 1:
                gender_groups[label]['disease'] += 1
            else:
                gender_groups[label]['normal'] += 1

        # Age Groups
        age_groups = {
            '<40': {'total': 0, 'disease': 0},
            '40-49': {'total': 0, 'disease': 0},
            '50-59': {'total': 0, 'disease': 0},
            '60-69': {'total': 0, 'disease': 0},
            '70+': {'total': 0, 'disease': 0}
        }
        for p in filtered_patients:
            age = p['age']
            if age < 40: grp = '<40'
            elif age < 50: grp = '40-49'
            elif age < 60: grp = '50-59'
            elif age < 70: grp = '60-69'
            else: grp = '70+'
            age_groups[grp]['total'] += 1
            if p['target'] == 1:
                age_groups[grp]['disease'] += 1
                
        # Chest pain types
        cp_types = {
            'Typical Angina': {'normal': 0, 'disease': 0},
            'Atypical Angina': {'normal': 0, 'disease': 0},
            'Non-Anginal': {'normal': 0, 'disease': 0},
            'Asymptomatic': {'normal': 0, 'disease': 0}
        }
        cp_map = {1: 'Typical Angina', 2: 'Atypical Angina', 3: 'Non-Anginal', 4: 'Asymptomatic'}
        for p in filtered_patients:
            cp_name = cp_map.get(p['cp'], 'Unknown')
            if cp_name in cp_types:
                if p['target'] == 1:
                    cp_types[cp_name]['disease'] += 1
                else:
                    cp_types[cp_name]['normal'] += 1
                
        # Scatter heart rate
        scatter_data = [{'x': p['age'], 'y': p['thalach'], 'target': p['target']} for p in filtered_patients]
        
        # Cholesterol
        chol_groups = {
            'Desirable (<200)': {'total': 0, 'disease': 0},
            'Borderline (200-239)': {'total': 0, 'disease': 0},
            'High (>=240)': {'total': 0, 'disease': 0}
        }
        for p in filtered_patients:
            c = p['chol']
            if c < 200: grp = 'Desirable (<200)'
            elif c < 240: grp = 'Borderline (200-239)'
            else: grp = 'High (>=240)'
            chol_groups[grp]['total'] += 1
            if p['target'] == 1:
                chol_groups[grp]['disease'] += 1
                
        # Blood Pressure Line distribution
        bp_groups = {
            'Normal (<120)': {'total': 0, 'disease': 0},
            'Pre-HTN (120-139)': {'total': 0, 'disease': 0},
            'Stage 1 (140-159)': {'total': 0, 'disease': 0},
            'Stage 2 (>=160)': {'total': 0, 'disease': 0}
        }
        for p in filtered_patients:
            bp = p['trestbps']
            if bp < 120: grp = 'Normal (<120)'
            elif bp < 140: grp = 'Pre-HTN (120-139)'
            elif bp < 160: grp = 'Stage 1 (140-159)'
            else: grp = 'Stage 2 (>=160)'
            bp_groups[grp]['total'] += 1
            if p['target'] == 1:
                bp_groups[grp]['disease'] += 1

        # Smoking Groups
        smoking_groups = {
            'Non-Smoker': {'normal': 0, 'disease': 0},
            'Smoker': {'normal': 0, 'disease': 0}
        }
        for p in filtered_patients:
            label = 'Smoker' if p['smoking'] == 1 else 'Non-Smoker'
            if p['target'] == 1:
                smoking_groups[label]['disease'] += 1
            else:
                smoking_groups[label]['normal'] += 1

        # BMI Groups
        bmi_groups = {
            'Normal (<25.0)': {'total': 0, 'disease': 0},
            'Overweight (25.0-29.9)': {'total': 0, 'disease': 0},
            'Obese (>=30.0)': {'total': 0, 'disease': 0}
        }
        for p in filtered_patients:
            bmi = p['bmi']
            if bmi < 25.0: grp = 'Normal (<25.0)'
            elif bmi < 30.0: grp = 'Overweight (25.0-29.9)'
            else: grp = 'Obese (>=30.0)'
            bmi_groups[grp]['total'] += 1
            if p['target'] == 1:
                bmi_groups[grp]['disease'] += 1

        # Exercise Angina
        angina_groups = {
            'No ExAng': {'normal': 0, 'disease': 0},
            'Yes ExAng': {'normal': 0, 'disease': 0}
        }
        for p in filtered_patients:
            label = 'Yes ExAng' if p['exang'] == 1 else 'No ExAng'
            if p['target'] == 1:
                angina_groups[label]['disease'] += 1
            else:
                angina_groups[label]['normal'] += 1

        return jsonify({
            'kpis': {
                'total': total_records,
                'disease_pct': disease_pct,
                'avg_chol': avg_chol,
                'avg_thalach': avg_thalach,
                'avg_bmi': avg_bmi,
                'smoker_pct': smoker_pct
            },
            'charts': {
                'age_groups': age_groups,
                'gender_groups': gender_groups,
                'chest_pain': cp_types,
                'scatter': scatter_data,
                'cholesterol': chol_groups,
                'blood_pressure': bp_groups,
                'smoking_groups': smoking_groups,
                'bmi_groups': bmi_groups,
                'angina_groups': angina_groups
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    try:
        count = db_repo.get_patients_count()
        return jsonify({
            'status': 'healthy',
            'database_mode': db_repo.mode,
            'database_records': count,
            'model_trained': model_params is not None
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize schema indices and seeder accounts
    db_repo.init_db()
    train_ml_model()
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
