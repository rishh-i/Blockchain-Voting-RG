import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class DataBaseManager:
    # uses SQLite and handles all database operations
    def __init__(self, db_path="voting_system.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """
        Create database tables if they don't exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Elections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS elections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')

            # Candidates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    party TEXT,
                    description TEXT,
                    election_id INTEGER,
                    FOREIGN KEY (election_id) REFERENCES elections (id)
                )
            ''')

            conn.commit()

    def create_user(self, username, password, email, is_admin=False):
        """
        Create new user account
        Returns user ID if successful, None if username/email already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                password_hash = generate_password_hash(password)

                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, email, is_admin))

                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def authenticate_user(self, username, password):
        """
        Authenticate user login
        Returns user data if successful, None if failed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, email, is_admin
                FROM users WHERE username = ?
            ''', (username,))

            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[3],
                    'is_admin': user[4]
                }
            return None

    def create_election(self, title, description, start_date, end_date, created_by):
        """
        Create new election
        Returns election ID if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO elections (title, description, start_date, end_date, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, start_date, end_date, created_by))

            return cursor.lastrowid

    def get_elections(self):
        """
        Get all elections
        Returns list of election dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, description, start_date, end_date, is_active
                FROM elections ORDER BY created_at DESC
            ''')

            elections = []
            for row in cursor.fetchall():
                elections.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'start_date': row[3],
                    'end_date': row[4],
                    'is_active': row[5]
                })
            return elections

    def add_candidate(self, name, party, description, election_id):
        """
        Add candidate to election
        Returns candidate ID if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO candidates (name, party, description, election_id)
                VALUES (?, ?, ?, ?)
            ''', (name, party, description, election_id))

            return cursor.lastrowid

    def get_candidates(self, election_id):
        """
        Get all candidates for specific election
        Returns list of candidate dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, party, description
                FROM candidates WHERE election_id = ?
            ''', (election_id,))

            candidates = []
            for row in cursor.fetchall():
                candidates.append({
                    'id': row[0],
                    'name': row[1],
                    'party': row[2],
                    'description': row[3]
                })
            return candidates
