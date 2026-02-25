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
        
        c.execute("""CREATE TABLE IF NOT EXISTS quest (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fatiga INTEGER,
                    rpe INTEGER,
                    sueno REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    FOREIGN KEY(user_id) REFERENCES users(id))""")

        for table in ["ex_run", "ex_bike", "ex_squat"]:
            c.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
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

    # --- MODIFICADO: AHORA DEVUELVE EL NOMBRE TAMBIÉN ---
    @classmethod
    def get_user_info(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT user, age, weight, height FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row: 
            # row[0] es el nombre
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
    def save_quest(cls, user_id, fatiga, rpe, sueno):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO quest (user_id, fatiga, rpe, sueno) VALUES (?,?,?,?)", (user_id, fatiga, rpe, sueno))
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
        c.execute("SELECT datetime(created_at, 'localtime'), fatiga, rpe, sueno FROM quest WHERE user_id=? ORDER BY id DESC LIMIT 5", (user_id,))
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

    @classmethod
    def save_exercise(cls, user_id, ex_type, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        table_name = {"run": "ex_run", "bike": "ex_bike", "squat": "ex_squat"}.get(ex_type)
        if not table_name: return False
        try:
            c.execute(f"""INSERT INTO {table_name} 
                      (user_id, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2) 
                      VALUES (?,?,?,?,?,?,?)""", 
                      (user_id, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(e)
            conn.close()
            return False

    @classmethod
    def get_specific_history(cls, user_id, ex_type):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        table_name = {"run": "ex_run", "bike": "ex_bike", "squat": "ex_squat"}.get(ex_type)
        if not table_name: return []
        # Índices: 0:fecha, 1:dur, 2:avg_hr, 3:max_hr, 4:min_hr, 5:avg_spo2, 6:min_spo2
        c.execute(f"""
            SELECT datetime(created_at, 'localtime'), duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2 
            FROM {table_name} 
            WHERE user_id=? 
            ORDER BY created_at DESC
        """, (user_id,))
        data = c.fetchall()
        conn.close()
        return data

    @classmethod
    def get_exercise_history(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        # Indices: 0:date, 1:type, 2:dur, 3:avg_hr, 4:max_hr, 5:min_hr, 6:avg_spo2, 7:min_spo2
        query = """
            SELECT datetime(created_at, 'localtime'), 'run', duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2 FROM ex_run WHERE user_id=?
            UNION ALL
            SELECT datetime(created_at, 'localtime'), 'bike', duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2 FROM ex_bike WHERE user_id=?
            UNION ALL
            SELECT datetime(created_at, 'localtime'), 'squat', duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2 FROM ex_squat WHERE user_id=?
            ORDER BY 1 DESC
        """
        c.execute(query, (user_id, user_id, user_id))
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
        tables = ["ex_run", "ex_bike", "ex_squat"]
        for table in tables:
            c.execute(f"SELECT date(created_at, 'localtime'), max_hr FROM {table} WHERE user_id=?", (user_id,))
            ex_rows = c.fetchall()
            for row in ex_rows:
                if row[0] in quest_dict:
                    correlation_points.append({
                        "date": row[0], "fatiga": quest_dict[row[0]], "hr_max": row[1], "type": table.replace("ex_", "")
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
    # --- NUEVO: SEMÁFORO DE RIESGO ---
    @classmethod
    def get_last_health_status(cls, user_id):
        """
        Devuelve el estado del último ejercicio del paciente:
        - 'danger': Si hubo Taquicardia o Hipoxia.
        - 'ok': Si todo fue normal.
        - None: Si no tiene registros.
        """
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        
        # 1. Recuperar Edad para calcular límite
        c.execute("SELECT age FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        age = row[0] if row and row[0] else 0
        limit_hr = (220 - age) if age > 0 else 170

        # 2. Buscar el ÚLTIMO registro de cualquiera de las 3 tablas
        # Usamos UNION ALL y ordenamos por fecha descendente, cogemos solo 1
        query = """
            SELECT max_hr, min_spo2, created_at FROM ex_run WHERE user_id=?
            UNION ALL
            SELECT max_hr, min_spo2, created_at FROM ex_bike WHERE user_id=?
            UNION ALL
            SELECT max_hr, min_spo2, created_at FROM ex_squat WHERE user_id=?
            ORDER BY 3 DESC LIMIT 1
        """
        c.execute(query, (user_id, user_id, user_id))
        data = c.fetchone()
        conn.close()

        if not data:
            return None # Sin datos
        
        max_hr = data[0]
        min_spo2 = data[1]

        # 3. Evaluar Riesgo
        if min_spo2 < 90 or max_hr > limit_hr:
            return "danger"
        
        return "ok"