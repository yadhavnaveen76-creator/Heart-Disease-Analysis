import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
DB_PATH = os.getenv('DB_PATH', 'heart_disease.db')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '27017' if DB_TYPE == 'mongodb' else '3306')
DB_NAME = os.getenv('DB_NAME', 'heart_disease')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def check_mongodb_driver():
    try:
        import pymongo
        return True
    except ImportError:
        return False

class DatabaseRepository:
    def __init__(self):
        self.mode = 'sql'
        self.mongo_client = None
        self.mongo_db = None
        self.sql_engine = None
        
        # Determine connection parameters
        self.db_type = DB_TYPE
        self.db_host = DB_HOST
        self.db_port = DB_PORT
        self.db_name = DB_NAME
        self.db_user = DB_USER
        self.db_password = DB_PASSWORD
        
        self.connect()

    def connect(self):
        # 1. MongoDB Branch
        if self.db_type == 'mongodb':
            if check_mongodb_driver():
                try:
                    import pymongo
                    # Set a short timeout so fallback executes quickly if server is down
                    conn_str = f"mongodb://{self.db_host}:{self.db_port}/"
                    if self.db_user and self.db_password:
                        # With auth
                        conn_str = f"mongodb://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/"
                        
                    print(f"Connecting to MongoDB at {self.db_host}:{self.db_port}...")
                    client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=2000)
                    # Check connection
                    client.server_info()
                    
                    self.mongo_client = client
                    self.mongo_db = client[self.db_name]
                    self.mode = 'mongodb'
                    print("Successfully connected to MongoDB backend!")
                    return
                except Exception as e:
                    print(f"\n[WARNING] MongoDB connection failed: {e}", file=sys.stderr)
                    print("[FALLBACK] Falling back to SQLite dialect.\n", file=sys.stderr)
            else:
                print("\n[WARNING] 'pymongo' driver not installed. Falling back to SQLite.\n", file=sys.stderr)
        
        # 2. SQL Branch (Default / Fallback)
        self.mode = 'sql'
        db_path = DB_PATH
        uri = f"sqlite:///{db_path}"
        
        # If user explicitly requested MySQL/PostgreSQL in env, configure it
        if self.db_type in ['mysql', 'postgresql']:
            try:
                if self.db_type == 'mysql':
                    import pymysql
                    uri = f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
                else:
                    import psycopg2
                    uri = f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
            except Exception as e:
                print(f"[WARNING] SQL dialect driver failed to load: {e}. Falling back to SQLite.", file=sys.stderr)
                uri = f"sqlite:///{db_path}"
                
        print(f"Connecting to SQL Database: {uri.split('@')[-1] if '@' in uri else uri}...")
        if uri.startswith('sqlite:'):
            self.sql_engine = create_engine(uri, connect_args={"check_same_thread": False})
        else:
            self.sql_engine = create_engine(uri, pool_recycle=3600, pool_pre_ping=True)

    def _get_next_sequence(self, name):
        """Generates sequential integer IDs in MongoDB similar to AUTOINCREMENT"""
        counter = self.mongo_db.counters.find_one_and_update(
            {'_id': name},
            {'$inc': {'sequence_value': 1}},
            upsert=True,
            return_document=True
        )
        return counter['sequence_value']

    def init_db(self):
        """Initialize schema, collections, and build default Admin user"""
        if self.mode == 'mongodb':
            # Create collections if they do not exist
            cols = self.mongo_db.list_collection_names()
            if 'users' not in cols:
                self.mongo_db.create_collection('users')
            if 'patients' not in cols:
                self.mongo_db.create_collection('patients')
            if 'uploaded_datasets' not in cols:
                self.mongo_db.create_collection('uploaded_datasets')
                
            # Create unique indexes
            self.mongo_db.users.create_index('username', unique=True)
            self.mongo_db.patients.create_index('id', unique=True)
            
            # Seed default admin user if not present
            admin = self.mongo_db.users.find_one({'username': 'admin'})
            if not admin:
                from werkzeug.security import generate_password_hash
                pwd_hash = generate_password_hash('admin123')
                uid = self._get_next_sequence('users')
                self.mongo_db.users.insert_one({
                    'id': uid,
                    'username': 'admin',
                    'password_hash': pwd_hash,
                    'role': 'admin'
                })
                print("Default admin created in MongoDB. Username: admin | Password: admin123")
        else:
            # SQL initialization
            from models import Base
            Base.metadata.create_all(self.sql_engine)
            
            # Seed default admin user
            with self.sql_engine.connect() as conn:
                check = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).scalar()
                if check == 0:
                    from werkzeug.security import generate_password_hash
                    pwd_hash = generate_password_hash('admin123')
                    with self.sql_engine.begin() as transaction:
                        transaction.execute(
                            text("INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role)"),
                            {'username': 'admin', 'password_hash': pwd_hash, 'role': 'admin'}
                        )
                    print("Default admin created in SQL. Username: admin | Password: admin123")

    # --- USER METRIC INTERFACES ---
    def find_user(self, username):
        if self.mode == 'mongodb':
            doc = self.mongo_db.users.find_one({'username': username.lower().strip()})
            if doc:
                from models import User
                u = User()
                u.id = doc['id']
                u.username = doc['username']
                u.password_hash = doc['password_hash']
                u.role = doc['role']
                return u
        else:
            with self.sql_engine.connect() as conn:
                r = conn.execute(text("SELECT id, username, password_hash, role FROM users WHERE username = :u"), {'u': username.lower().strip()}).fetchone()
                if r:
                    from models import User
                    u = User()
                    u.id = r[0]
                    u.username = r[1]
                    u.password_hash = r[2]
                    u.role = r[3]
                    return u
        return None

    def find_user_by_id(self, uid):
        if self.mode == 'mongodb':
            doc = self.mongo_db.users.find_one({'id': int(uid)})
            if doc:
                from models import User
                u = User()
                u.id = doc['id']
                u.username = doc['username']
                u.password_hash = doc['password_hash']
                u.role = doc['role']
                return u
        else:
            with self.sql_engine.connect() as conn:
                r = conn.execute(text("SELECT id, username, password_hash, role FROM users WHERE id = :id"), {'id': int(uid)}).fetchone()
                if r:
                    from models import User
                    u = User()
                    u.id = r[0]
                    u.username = r[1]
                    u.password_hash = r[2]
                    u.role = r[3]
                    return u
        return None

    def get_users(self):
        if self.mode == 'mongodb':
            return list(self.mongo_db.users.find({}, {'_id': 0}))
        else:
            with self.sql_engine.connect() as conn:
                result = conn.execute(text("SELECT id, username, role FROM users ORDER BY id ASC"))
                return [{'id': r[0], 'username': r[1], 'role': r[2]} for r in result.fetchall()]

    def create_user(self, username, password_hash, role='user'):
        if self.mode == 'mongodb':
            uid = self._get_next_sequence('users')
            self.mongo_db.users.insert_one({
                'id': uid,
                'username': username.lower().strip(),
                'password_hash': password_hash,
                'role': role
            })
            return uid
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role)"),
                    {'username': username.lower().strip(), 'password_hash': password_hash, 'role': role}
                )
            return True

    def delete_user(self, uid):
        if self.mode == 'mongodb':
            self.mongo_db.users.delete_one({'id': int(uid)})
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(text("DELETE FROM users WHERE id = :id"), {'id': int(uid)})

    # --- PATIENT RECORD INTERFACES ---
    def get_patients_count(self, sex_filter='all', age_min=0, age_max=100):
        if self.mode == 'mongodb':
            query = {'age': {'$gte': int(age_min), '$lte': int(age_max)}}
            if sex_filter == 'male':
                query['sex'] = 1
            elif sex_filter == 'female':
                query['sex'] = 0
            return self.mongo_db.patients.count_documents(query)
        else:
            where = ["age >= :age_min", "age <= :age_max"]
            params = {'age_min': int(age_min), 'age_max': int(age_max)}
            if sex_filter == 'male':
                where.append("sex = 1")
            elif sex_filter == 'female':
                where.append("sex = 0")
            where_str = " WHERE " + " AND ".join(where)
            with self.sql_engine.connect() as conn:
                return conn.execute(text(f"SELECT COUNT(*) FROM patients {where_str}"), params).scalar()

    def get_patients(self, limit=None, offset=0, sex_filter='all', age_min=0, age_max=100):
        if self.mode == 'mongodb':
            query = {'age': {'$gte': int(age_min), '$lte': int(age_max)}}
            if sex_filter == 'male':
                query['sex'] = 1
            elif sex_filter == 'female':
                query['sex'] = 0
                
            cursor = self.mongo_db.patients.find(query, {'_id': 0}).sort('id', -1)
            if offset:
                cursor = cursor.skip(offset)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        else:
            where = ["age >= :age_min", "age <= :age_max"]
            params = {'age_min': int(age_min), 'age_max': int(age_max)}
            if sex_filter == 'male':
                where.append("sex = 1")
            elif sex_filter == 'female':
                where.append("sex = 0")
            
            limit_str = ""
            if limit is not None:
                limit_str = f" LIMIT {int(limit)} OFFSET {int(offset)}"
                
            where_str = " WHERE " + " AND ".join(where)
            with self.sql_engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT id, age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, smoking, bmi, target FROM patients {where_str} ORDER BY id DESC {limit_str}"),
                    params
                )
                rows = result.fetchall()
                
            keys = ['id', 'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'smoking', 'bmi', 'target']
            return [dict(zip(keys, r)) for r in rows]

    def add_patient(self, p):
        if self.mode == 'mongodb':
            pid = self._get_next_sequence('patients')
            p['id'] = pid
            self.mongo_db.patients.insert_one(p)
            return pid
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO patients (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, smoking, bmi, target)
                        VALUES (:age, :sex, :cp, :trestbps, :chol, :fbs, :restecg, :thalach, :exang, :oldpeak, :slope, :ca, :thal, :smoking, :bmi, :target)
                    """),
                    p
                )
            return True

    def bulk_add_patients(self, p_list):
        if not p_list:
            return
        if self.mode == 'mongodb':
            # Reset counters & add sequences
            for p in p_list:
                p['id'] = self._get_next_sequence('patients')
            self.mongo_db.patients.insert_many(p_list)
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO patients (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, smoking, bmi, target)
                        VALUES (:age, :sex, :cp, :trestbps, :chol, :fbs, :restecg, :thalach, :exang, :oldpeak, :slope, :ca, :thal, :smoking, :bmi, :target)
                    """),
                    p_list
                )

    def update_patient(self, pid, p):
        if self.mode == 'mongodb':
            self.mongo_db.patients.update_one({'id': int(pid)}, {'$set': p})
        else:
            p['id'] = int(pid)
            with self.sql_engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE patients SET age=:age, sex=:sex, cp=:cp, trestbps=:trestbps, chol=:chol, fbs=:fbs, 
                        restecg=:restecg, thalach=:thalach, exang=:exang, oldpeak=:oldpeak, slope=:slope, ca=:ca, thal=:thal, 
                        smoking=:smoking, bmi=:bmi, target=:target
                        WHERE id=:id
                    """),
                    p
                )

    def delete_patient(self, pid):
        if self.mode == 'mongodb':
            self.mongo_db.patients.delete_one({'id': int(pid)})
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(text("DELETE FROM patients WHERE id = :id"), {'id': int(pid)})

    def clear_patients(self):
        if self.mode == 'mongodb':
            self.mongo_db.patients.delete_many({})
            # Reset counter
            self.mongo_db.counters.update_one({'_id': 'patients'}, {'$set': {'sequence_value': 0}}, upsert=True)
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(text("DELETE FROM patients"))

    # --- UPLOAD HISTORICAL DATA INTERFACES ---
    def get_datasets(self):
        if self.mode == 'mongodb':
            return list(self.mongo_db.uploaded_datasets.find({}, {'_id': 0}).sort('id', -1))
        else:
            with self.sql_engine.connect() as conn:
                result = conn.execute(text("SELECT id, filename, upload_time, raw_rows, clean_rows, duplicates_removed, missing_filled, uploaded_by FROM uploaded_datasets ORDER BY id DESC"))
                rows = result.fetchall()
            keys = ['id', 'filename', 'upload_time', 'raw_rows', 'clean_rows', 'duplicates_removed', 'missing_filled', 'uploaded_by']
            return [dict(zip(keys, r)) for r in rows]

    def add_dataset(self, d):
        if self.mode == 'mongodb':
            did = self._get_next_sequence('uploaded_datasets')
            d['id'] = did
            self.mongo_db.uploaded_datasets.insert_one(d)
            return did
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO uploaded_datasets (filename, upload_time, raw_rows, clean_rows, duplicates_removed, missing_filled, uploaded_by)
                        VALUES (:filename, :upload_time, :raw_rows, :clean_rows, :duplicates_removed, :missing_filled, :uploaded_by)
                    """),
                    d
                )
            return True

    def delete_dataset(self, did):
        if self.mode == 'mongodb':
            self.mongo_db.uploaded_datasets.delete_one({'id': int(did)})
        else:
            with self.sql_engine.begin() as conn:
                conn.execute(text("DELETE FROM uploaded_datasets WHERE id = :id"), {'id': int(did)})

    # --- SCHEMA EXPOSITIONS (For SQLite Viewer check) ---
    def get_sqlite_schema(self):
        if self.mode == 'mongodb':
            # MongoDB has no relational schema tables, return simulated attributes
            return [
                {'cid': i, 'name': n, 'type': 'INTEGER' if n != 'oldpeak' and n != 'bmi' else 'REAL', 'notnull': 1}
                for i, n in enumerate(['id', 'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'smoking', 'bmi', 'target'])
            ]
        else:
            from sqlalchemy import inspect
            schema = []
            inspector = inspect(self.sql_engine)
            if inspector.has_table('patients'):
                cols = inspector.get_columns('patients')
                for idx, col in enumerate(cols):
                    schema.append({
                        'cid': idx,
                        'name': col['name'],
                        'type': str(col['type']),
                        'notnull': 1 if not col['nullable'] else 0
                    })
            return schema

# Instantiate dynamic repository manager
db_repo = DatabaseRepository()

def get_db_engine():
    """Retained for backward compatibility with old SQLAlchemy script instances"""
    return db_repo.sql_engine
