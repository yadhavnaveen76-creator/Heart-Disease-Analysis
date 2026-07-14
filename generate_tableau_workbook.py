import os

TWB_CONTENT = """<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='18.1' vversion='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
  </preferences>
  <datasources>
    <datasource caption='CardioSync Cleaned Dataset' inline='true' name='cleaned_heart_dataset' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='cleaned_heart_dataset' name='cleaned_heart_dataset_leaf'>
            <connection class='textscan' directory='.' filename='cleaned_heart_dataset.csv' separator=',' />
          </named-connection>
        </named-connections>
      </connection>
      
      <!-- Columns Mapping Definitions -->
      <column datatype='integer' name='[id]' role='dimension' type='ordinal' />
      
      <column datatype='integer' name='[age]' role='measure' type='quantitative' caption='Age (Years)'>
        <desc><formatted-text>Patient Age in years</formatted-text></desc>
      </column>
      
      <column datatype='integer' name='[sex]' role='dimension' type='nominal' caption='Biological Sex'>
        <aliases>
          <alias key='0' value='Female' />
          <alias key='1' value='Male' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[cp]' role='dimension' type='nominal' caption='Chest Pain Type'>
        <aliases>
          <alias key='1' value='Typical Angina' />
          <alias key='2' value='Atypical Angina' />
          <alias key='3' value='Non-Anginal' />
          <alias key='4' value='Asymptomatic' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[trestbps]' role='measure' type='quantitative' caption='Resting Blood Pressure' />
      <column datatype='integer' name='[chol]' role='measure' type='quantitative' caption='Serum Cholesterol (mg/dl)' />
      
      <column datatype='integer' name='[fbs]' role='dimension' type='nominal' caption='Fasting Blood Sugar &gt; 120'>
        <aliases>
          <alias key='0' value='False' />
          <alias key='1' value='True' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[restecg]' role='dimension' type='nominal' caption='Resting ECG Result'>
        <aliases>
          <alias key='0' value='Normal' />
          <alias key='1' value='ST-T Wave Abnormality' />
          <alias key='2' value='LV Hypertrophy' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[thalach]' role='measure' type='quantitative' caption='Max Heart Rate' />
      
      <column datatype='integer' name='[exang]' role='dimension' type='nominal' caption='Exercise Induced Angina'>
        <aliases>
          <alias key='0' value='No' />
          <alias key='1' value='Yes' />
        </aliases>
      </column>
      
      <column datatype='real' name='[oldpeak]' role='measure' type='quantitative' caption='ST Depression (Oldpeak)' />
      
      <column datatype='integer' name='[slope]' role='dimension' type='nominal' caption='Peak ST Slope'>
        <aliases>
          <alias key='1' value='Upsloping' />
          <alias key='2' value='Flat' />
          <alias key='3' value='Downsloping' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[ca]' role='dimension' type='ordinal' caption='Vessels Colored (Fluoroscopy)' />
      
      <column datatype='integer' name='[thal]' role='dimension' type='nominal' caption='Thalassemia Status'>
        <aliases>
          <alias key='3' value='Normal' />
          <alias key='6' value='Fixed Defect' />
          <alias key='7' value='Reversible Defect' />
        </aliases>
      </column>
      
      <column datatype='integer' name='[smoking]' role='dimension' type='nominal' caption='Smoking Status'>
        <aliases>
          <alias key='0' value='Non-Smoker' />
          <alias key='1' value='Smoker' />
        </aliases>
      </column>
      
      <column datatype='real' name='[bmi]' role='measure' type='quantitative' caption='Body Mass Index (BMI)' />
      
      <column datatype='integer' name='[target]' role='dimension' type='nominal' caption='Heart Disease Diagnosis'>
        <aliases>
          <alias key='0' value='Normal' />
          <alias key='1' value='Disease Confirmed' />
        </aliases>
      </column>
    </datasource>
  </datasources>
  <worksheets>
  </worksheets>
</workbook>
"""

def generate_tableau_workbook():
    target_file = 'heart_disease_dashboard.twb'
    print(f"Creating Tableau Workbook structure in: {target_file}...")
    
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(TWB_CONTENT.strip())
            
        print("Tableau Workbook generated successfully!")
        print("\\n--- How to use in Tableau ---")
        print(f"1. Generate your preprocessed dataset inside CardioSync ('cleaned_heart_dataset.csv').")
        print(f"2. Move '{target_file}' and 'cleaned_heart_dataset.csv' to the same folder.")
        print(f"3. Double-click '{target_file}' to open it in Tableau Desktop or upload to Tableau Public.")
        print(f"4. Tableau will automatically connect to 'cleaned_heart_dataset.csv' and load all 16 variables (dimensions, measures, and description aliases) pre-configured.")
    except Exception as e:
        print(f"Error writing Tableau workbook: {e}")

if __name__ == '__main__':
    generate_tableau_workbook()
