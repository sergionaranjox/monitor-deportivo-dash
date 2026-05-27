import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BADGES = [
    {"nombre": "Principiante", "metros": 0,     "icono": "🎿", "color": "secondary"},
    {"nombre": "Iniciado",     "metros": 1000,  "icono": "⛷️", "color": "info"},
    {"nombre": "Aficionado",   "metros": 5000,  "icono": "🏅", "color": "primary"},
    {"nombre": "Competidor",   "metros": 15000, "icono": "🥈", "color": "warning"},
    {"nombre": "Experto",      "metros": 30000, "icono": "🥇", "color": "danger"},
    {"nombre": "Leyenda",      "metros": 75000, "icono": "🏆", "color": "dark"},
]

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
                        metros_descenso INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id))""")

        # Migración: añadir columna si ya existe la tabla sin ella
        try:
            c.execute("ALTER TABLE sesiones_nieve ADD COLUMN metros_descenso INTEGER DEFAULT 0")
            conn.commit()
        except: pass

        try:
            c.execute("ALTER TABLE users ADD COLUMN first_login INTEGER DEFAULT 0")
            conn.commit()
        except: pass

        try:
            c.execute("ALTER TABLE users ADD COLUMN notes TEXT DEFAULT ''")
            conn.commit()
        except: pass

        try:
            pwd = generate_password_hash("1234")
            c.execute("INSERT INTO users (user, pass, role) VALUES (?,?,?)", ("admin", pwd, "fisio"))
            conn.commit()
        except: pass
        conn.close()

    @classmethod
    def is_first_login(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT first_login FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return bool(row and row[0] == 1)

    @classmethod
    def mark_profile_complete(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET first_login=0 WHERE id=?", (user_id,))
        conn.commit()
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
            c.execute("INSERT INTO users (user, pass, role, first_login) VALUES (?,?,?,1)", (user, pwd, role))
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
    def save_exercise(cls, user_id, ex_type, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud=0, metros=0):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO sesiones_nieve
                      (user_id, modalidad, altitud_ejercicio, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, metros_descenso)
                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                      (user_id, ex_type, altitud, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, metros))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(e)
            conn.close()
            return False

    @classmethod
    def get_total_metros(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(metros_descenso), 0) FROM sesiones_nieve WHERE user_id=?", (user_id,))
        total = c.fetchone()[0]
        conn.close()
        return total

    @classmethod
    def get_ranking(cls):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.user, COALESCE(SUM(s.metros_descenso), 0) as total_metros
            FROM users u
            LEFT JOIN sesiones_nieve s ON u.id = s.user_id
            WHERE u.role = 'paciente'
            GROUP BY u.id, u.user
            ORDER BY total_metros DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "metros": r[2]} for r in rows]

    @classmethod
    def get_badge_info(cls, total_metros):
        current = BADGES[0]
        next_badge = None
        for badge in BADGES:
            if total_metros >= badge["metros"]:
                current = badge
            else:
                next_badge = badge
                break
        return current, next_badge

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
    def get_heatmap_data(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT altitud_ejercicio, metros_descenso, max_hr, modalidad
            FROM sesiones_nieve
            WHERE user_id=?
            ORDER BY created_at ASC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"altitud": r[0], "metros": r[1], "max_hr": r[2], "modalidad": r[3]} for r in rows]

    @classmethod
    def get_acwr(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(SUM(metros_descenso), 0)
            FROM sesiones_nieve
            WHERE user_id=? AND date(created_at,'localtime') >= date('now','-7 days')
        """, (user_id,))
        acute = c.fetchone()[0] or 0
        c.execute("""
            SELECT COALESCE(SUM(metros_descenso), 0)
            FROM sesiones_nieve
            WHERE user_id=? AND date(created_at,'localtime') >= date('now','-28 days')
        """, (user_id,))
        chronic_total = c.fetchone()[0] or 0
        conn.close()
        chronic_weekly = chronic_total / 4
        acwr = round(acute / chronic_weekly, 2) if chronic_weekly > 0 else None
        return {"acwr": acwr, "acute": acute, "chronic_weekly": int(chronic_weekly)}

    @classmethod
    def get_weekly_summary(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(SUM(metros_descenso),0), COUNT(*)
            FROM sesiones_nieve
            WHERE user_id=? AND date(created_at,'localtime') >= date('now','-7 days')
        """, (user_id,))
        row = c.fetchone()
        this_m, this_s = row[0] or 0, row[1] or 0
        c.execute("""
            SELECT COALESCE(SUM(metros_descenso),0), COUNT(*)
            FROM sesiones_nieve
            WHERE user_id=?
              AND date(created_at,'localtime') >= date('now','-14 days')
              AND date(created_at,'localtime') <  date('now','-7 days')
        """, (user_id,))
        row = c.fetchone()
        prev_m, prev_s = row[0] or 0, row[1] or 0
        conn.close()
        return {"this_metros": this_m, "this_sessions": this_s,
                "prev_metros": prev_m, "prev_sessions": prev_s}

    @classmethod
    def save_exercise_manual(cls, user_id, ex_type, duration, avg_hr, max_hr, min_hr,
                             avg_spo2, min_spo2, altitud, metros, date_str):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO sesiones_nieve
                      (user_id, modalidad, altitud_ejercicio, duration_sec, avg_hr, max_hr, min_hr,
                       avg_spo2, min_spo2, metros_descenso, created_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (user_id, ex_type, altitud, duration, avg_hr, max_hr, min_hr,
                       avg_spo2, min_spo2, metros, date_str))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(e)
            conn.close()
            return False

    @classmethod
    def get_activity_by_day(cls, user_id, days=90):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT date(created_at, 'localtime'), SUM(metros_descenso), MAX(max_hr), COUNT(*)
            FROM sesiones_nieve
            WHERE user_id=? AND date(created_at, 'localtime') >= date('now', ?)
            GROUP BY date(created_at, 'localtime')
            ORDER BY date(created_at, 'localtime') ASC
        """, (user_id, f'-{days} days'))
        data = c.fetchall()
        conn.close()
        return data

    @classmethod
    def get_monthly_metros(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(SUM(metros_descenso), 0), COUNT(*)
            FROM sesiones_nieve
            WHERE user_id=? AND date(created_at, 'localtime') >= date('now', 'start of month')
        """, (user_id,))
        row = c.fetchone()
        conn.close()
        return (row[0] or 0, row[1] or 0)

    @classmethod
    def save_athlete_note(cls, user_id, note):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET notes=? WHERE id=?", (note, user_id))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def get_athlete_note(cls, user_id):
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT notes FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else ""

    @classmethod
    def get_last_session_days(cls, user_id):
        from datetime import date
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("SELECT date(created_at, 'localtime') FROM sesiones_nieve WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        last_date = date.fromisoformat(row[0])
        return (date.today() - last_date).days

    @classmethod
    def get_acwr_history(cls, user_id, weeks=12):
        from datetime import date, timedelta
        conn = sqlite3.connect(cls.PATH)
        c = conn.cursor()
        c.execute("""
            SELECT date(created_at, 'localtime') as d, SUM(metros_descenso) as m
            FROM sesiones_nieve WHERE user_id=?
            GROUP BY date(created_at, 'localtime')
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        daily = {r[0]: (r[1] or 0) for r in rows}
        today = date.today()
        result = []
        for w in range(weeks - 1, -1, -1):
            week_end = today - timedelta(days=w * 7)
            acute = sum(daily.get((week_end - timedelta(days=d)).isoformat(), 0) for d in range(7))
            chronic_total = sum(daily.get((week_end - timedelta(days=d)).isoformat(), 0) for d in range(28))
            chronic_weekly = chronic_total / 4
            acwr = round(acute / chronic_weekly, 2) if chronic_weekly > 0 else None
            result.append({"week": week_end.isoformat(), "acwr": acwr, "acute": acute})
        return result

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
