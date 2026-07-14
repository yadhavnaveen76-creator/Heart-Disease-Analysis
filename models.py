from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), default='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    age = Column(Integer, nullable=False)
    sex = Column(Integer, nullable=False)
    cp = Column(Integer, nullable=False)
    trestbps = Column(Integer, nullable=False)
    chol = Column(Integer, nullable=False)
    fbs = Column(Integer, nullable=False)
    restecg = Column(Integer, nullable=False)
    thalach = Column(Integer, nullable=False)
    exang = Column(Integer, nullable=False)
    oldpeak = Column(Float, nullable=False)
    slope = Column(Integer, nullable=False)
    ca = Column(Integer, nullable=False)
    thal = Column(Integer, nullable=False)
    smoking = Column(Integer, default=0, nullable=False)
    bmi = Column(Float, default=24.5, nullable=False)
    target = Column(Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'age': self.age,
            'sex': self.sex,
            'cp': self.cp,
            'trestbps': self.trestbps,
            'chol': self.chol,
            'fbs': self.fbs,
            'restecg': self.restecg,
            'thalach': self.thalach,
            'exang': self.exang,
            'oldpeak': self.oldpeak,
            'slope': self.slope,
            'ca': self.ca,
            'thal': self.thal,
            'smoking': self.smoking,
            'bmi': self.bmi,
            'target': self.target
        }
        
    def __repr__(self):
        return f'<Patient ID={self.id} Age={self.age} Target={self.target}>'

class UploadedDataset(Base):
    __tablename__ = 'uploaded_datasets'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    upload_time = Column(String(64), nullable=False)
    raw_rows = Column(Integer, nullable=False)
    clean_rows = Column(Integer, nullable=False)
    duplicates_removed = Column(Integer, nullable=False)
    missing_filled = Column(Integer, nullable=False)
    uploaded_by = Column(String(64), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_time': self.upload_time,
            'raw_rows': self.raw_rows,
            'clean_rows': self.clean_rows,
            'duplicates_removed': self.duplicates_removed,
            'missing_filled': self.missing_filled,
            'uploaded_by': self.uploaded_by
        }
        
    def __repr__(self):
        return f'<UploadedDataset File={self.filename} Date={self.upload_time}>'
