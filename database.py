import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class db:
    PATH = "users.db"

    @classmethod
    def init(cls):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT UNIQUE,
                    pass TEXT, 
                    role TEXT,
                    age INTEGER,
                    weight REAL,
                    height REAL)""")
        
        # --- MODIFICADO: Añadimos 'altitud' al cuestionario diario ---
        c.execute("""CREATE TABLE IF NOT EXISTS quest (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fatiga INTEGER,
                    rpe INTEGER,
                    sueno REAL,
                    altitud_pernocta INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    FOREIGN KEY(user_id) REFERENCES users(id))""")

        # --- MODIFICADO: Unificamos en una sola tabla 'sesiones_nieve' ---
        c.execute("""CREATE TABLE IF NOT EXISTS sesiones_nieve (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        modalidad TEXT,
                        altitud_ejercicio INTEGER DEFAULT 0,
                        duration_sec INTEGER,
                        avg_hr INTEGER, max_hr INTEGER, min_hr INTEGER,
                        avg_spo2 INTEGER, min_spo2 INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        FOREIGN KEY(user_id) REFERENCES users(id))""")
        
        try:
            pwd = generate_password_hash("1234")
            c.execute("INSERT INTO users (user, pass, role) VALUES (?,?,?)", ("admin", pwd, "fisio"))
            conn.commit()
        except: pass
        conn.close()

    @classmethod
    def update_profile(cls, user_id, age, weight, height):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET age=?, weight=?, height=? WHERE id=?", (age, weight, height, user_id))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def get_user_info(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT user, age, weight, height FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row: 
            return {"name": row[0], "age": row[1], "weight": row[2], "height": row[3]}
        return None

    @classmethod
    def verify(cls, user, password):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT id, pass, role FROM users WHERE user=?", (user,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[1], password):
            return {"id": row[0], "role": row[2]}
        return None

    @classmethod
    def register(cls, user, password, role):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        pwd = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (user, pass, role) VALUES (?,?,?)", (user, pwd, role))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def save_quest(cls, user_id, fatiga, rpe, sueno, altitud=0):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO quest (user_id, fatiga, rpe, sueno, altitud_pernocta) VALUES (?,?,?,?,?)", 
                      (user_id, fatiga, rpe, sueno, altitud))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def get_history(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT datetime(created_at, 'localtime'), fatiga, rpe, sueno, altitud_pernocta FROM quest WHERE user_id=? ORDER BY id DESC LIMIT 5", (user_id,))
        data = c.fetchall()
        conn.close()
        return data

    @classmethod
    def get_chart_data(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT datetime(created_at, 'localtime'), fatiga, rpe FROM quest WHERE user_id=? ORDER BY created_at ASC", (user_id,))
        data = c.fetchall()
        conn.close()
        return data

    # --- MODIFICADO: Guardar ejercicio en la nueva tabla ---
    @classmethod
    def save_exercise(cls, user_id, ex_type, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud=0):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO sesiones_nieve 
                      (user_id, modalidad, altitud_ejercicio, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2) 
                      VALUES (?,?,?,?,?,?,?,?,?)""", 
                      (user_id, ex_type, altitud, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(e)
            conn.close()
            return False

    # --- MODIFICADO: Leer historial específico (ahora filtra por modalidad) ---
    @classmethod
    def get_specific_history(cls, user_id, ex_type):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT datetime(created_at, 'localtime'), duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud_ejercicio 
            FROM sesiones_nieve 
            WHERE user_id=? AND modalidad=?
            ORDER BY created_at DESC
        """, (user_id, ex_type))
        data = c.fetchall()
        conn.close()
        return data

    # --- MODIFICADO: Obtener todo el historial ---
    @classmethod
    def get_exercise_history(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        query = """
            SELECT datetime(created_at, 'localtime'), modalidad, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud_ejercicio 
            FROM sesiones_nieve 
            WHERE user_id=?
            ORDER BY created_at DESC
        """
        c.execute(query, (user_id,))
        data = c.fetchall()
        conn.close()
        return data

    @classmethod
    def get_correlation_data(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT date(created_at, 'localtime'), fatiga FROM quest WHERE user_id=?", (user_id,))
        quest_dict = {row[0]: row[1] for row in c.fetchall()}
        
        correlation_points = []
        c.execute("SELECT date(created_at, 'localtime'), max_hr, modalidad FROM sesiones_nieve WHERE user_id=?", (user_id,))
        ex_rows = c.fetchall()
        for row in ex_rows:
            if row[0] in quest_dict:
                correlation_points.append({
                    "date": row[0], "fatiga": quest_dict[row[0]], "hr_max": row[1], "type": row[2]
                })
        conn.close()
        return correlation_points

    @classmethod
    def get_all_patients(cls):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT id, user FROM users WHERE role != 'fisio'")
        rows = c.fetchall()
        conn.close()
        return [{"label": row[1], "value": row[0]} for row in rows]

    # --- NUEVO SEMÁFORO DE MONTAÑA ---
    @classmethod
    def get_last_health_status(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        
        c.execute("SELECT age FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        age = row[0] if row and row[0] else 0
        limit_hr = (220 - age) if age > 0 else 170

        c.execute("SELECT max_hr, min_spo2 FROM sesiones_nieve WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,))
        data = c.fetchone()
        conn.close()

        if not data:
            return None
        
        max_hr = data[0]
        min_spo2 = data[1]

        # Criterios más estrictos para altitud
        if min_spo2 < 88 or max_hr > limit_hr:
            return "danger"
        elif min_spo2 < 92 or max_hr > (limit_hr * 0.9):
            return "warning"
        
        return "ok"
