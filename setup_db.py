import os
import urllib.request
import csv
import random

# Project modules
from db_config import db_repo

CSV_URL = 'https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data'

def generate_synthetic_data(num_records=303):
    print("Generating high-fidelity synthetic heart disease dataset with Smoking & BMI...")
    random.seed(42)
    data = []
    for i in range(num_records):
        age = int(random.normalvariate(54, 9.0))
        age = max(29, min(77, age))
        sex = 1 if random.random() < 0.68 else 0
        cp = random.choices([1, 2, 3, 4], weights=[0.08, 0.16, 0.28, 0.48])[0]
        trestbps = int(random.normalvariate(131, 17.0))
        trestbps = max(94, min(200, trestbps))
        chol = int(random.normalvariate(246, 51.0))
        chol = max(126, min(564, chol))
        fbs = 1 if random.random() < 0.15 else 0
        restecg = random.choices([0, 1, 2], weights=[0.49, 0.02, 0.49])[0]
        thalach_base = 220 - age
        thalach = int(random.normalvariate(thalach_base - 15, 18))
        thalach = max(71, min(202, thalach))
        exang_prob = 0.1 + (0.01 * (age - 30)) + (0.3 if cp == 4 else 0.0)
        exang = 1 if random.random() < max(0.05, min(0.9, exang_prob)) else 0
        oldpeak = round(max(0.0, random.expovariate(1.0)), 1)
        if oldpeak > 6.2:
            oldpeak = 6.2
        slope = random.choices([1, 2, 3], weights=[0.47, 0.46, 0.07])[0]
        ca = random.choices([0, 1, 2, 3], weights=[0.58, 0.22, 0.13, 0.07])[0]
        thal = random.choices([3, 6, 7], weights=[0.55, 0.06, 0.39])[0]
        
        # New parameters: Smoking & BMI
        smoking = 1 if random.random() < 0.35 else 0
        bmi = round(random.normalvariate(26.8, 4.4), 1)
        bmi = max(16.0, min(48.0, bmi))
        
        # Risk score target map
        risk_score = -5.0
        risk_score += 0.04 * age
        risk_score += 0.8 * sex
        risk_score += 1.2 * (1 if cp == 4 else 0)
        risk_score += 0.01 * (trestbps - 120)
        risk_score += 0.005 * (chol - 200)
        risk_score += 1.0 * fbs
        risk_score += 0.5 * restecg
        risk_score -= 0.03 * (thalach - 150)
        risk_score += 1.5 * exang
        risk_score += 0.8 * oldpeak
        risk_score += 0.6 * slope
        risk_score += 1.0 * ca
        risk_score += 1.0 * (1 if thal == 7 else 0)
        risk_score += 1.0 * smoking
        risk_score += 0.15 * (bmi - 24.0)
        
        # Sigmoid
        prob = 1 / (1 + __import__('math').exp(-risk_score))
        target = 1 if random.random() < prob else 0
        
        data.append({
            'age': age, 'sex': sex, 'cp': cp, 'trestbps': trestbps, 'chol': chol,
            'fbs': fbs, 'restecg': restecg, 'thalach': thalach, 'exang': exang, 'oldpeak': oldpeak,
            'slope': slope, 'ca': ca, 'thal': thal, 'smoking': smoking, 'bmi': bmi, 'target': target
        })
    return data

def setup_database():
    print("Setting up CardioSync Database via Repository Interface...")
    db_repo.init_db()
    
    count = db_repo.get_patients_count()
    if count > 0:
        print(f"Database already seeded with {count} patient records. Seeding skipped.")
        return

    # Download or generate patient data
    dict_rows = []
    try:
        print(f"Attempting to download Cleveland Heart Disease Dataset from {CSV_URL}...")
        req = urllib.request.Request(CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            csv_content = response.read().decode('utf-8')
            reader = csv.reader(csv_content.splitlines())
            
            random.seed(42)
            for row in reader:
                if not row or len(row) < 14:
                    continue
                parsed_row = []
                for val in row[:14]:
                    val = val.strip()
                    if val == '?':
                        parsed_row.append(None)
                    else:
                        parsed_row.append(float(val))
                
                # Clean missing fields
                if parsed_row[11] is None: parsed_row[11] = 0.0 # ca
                if parsed_row[12] is None: parsed_row[12] = 3.0 # thal
                
                # Binarize target
                target = 1 if parsed_row[13] > 0 else 0
                
                # Generate missing parameters smoking & bmi for Cleveland rows
                smoking = 1 if random.random() < 0.32 else 0
                bmi = round(random.normalvariate(26.2, 4.3), 1)
                bmi = max(15.5, min(47.5, bmi))
                
                dict_rows.append({
                    'age': int(parsed_row[0]), 'sex': int(parsed_row[1]), 'cp': int(parsed_row[2]), 
                    'trestbps': int(parsed_row[3]), 'chol': int(parsed_row[4]), 'fbs': int(parsed_row[5]), 
                    'restecg': int(parsed_row[6]), 'thalach': int(parsed_row[7]), 'exang': int(parsed_row[8]), 
                    'oldpeak': float(parsed_row[9]), 'slope': int(parsed_row[10]), 'ca': int(parsed_row[11]), 
                    'thal': int(parsed_row[12]), 'smoking': smoking, 'bmi': bmi, 'target': target
                })
        
        print(f"Successfully downloaded and loaded {len(dict_rows)} patient rows.")
            
    except Exception as e:
        print(f"Network download or CSV parsing failed: {e}")
        dict_rows = generate_synthetic_data()

    # Bulk insert patient rows
    db_repo.bulk_add_patients(dict_rows)
    print(f"Seeded {len(dict_rows)} patient records into database.")
    
    # Verification query
    total = db_repo.get_patients_count()
    print(f"\n--- Seeding Verification ---")
    print(f"Active Connection Mode: {db_repo.mode.upper()}")
    print(f"Total Patient Records: {total}")
    
    patients = db_repo.get_patients()
    if patients:
        ages = [p['age'] for p in patients]
        bmis = [p['bmi'] for p in patients]
        smokers = [p['smoking'] for p in patients]
        targets = [p['target'] for p in patients]
        
        avg_age = sum(ages) / len(ages)
        avg_bmi = sum(bmis) / len(bmis)
        smoker_pct = (sum(smokers) / len(smokers)) * 100
        disease_pct = (sum(targets) / len(targets)) * 100
        
        print(f"Age stats: Avg={avg_age:.2f}, Min={min(ages)}, Max={max(ages)}")
        print(f"Added parameters: Avg BMI={avg_bmi:.1f}, Smoker Rate={smoker_pct:.1f}%")
        print(f"Heart Disease Confirmed Rate: {disease_pct:.1f}%")

if __name__ == '__main__':
    setup_database()
