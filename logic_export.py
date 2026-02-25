import pandas as pd
import io
from database import db

class excel_generator:
    
    @staticmethod
    def create_excel(patient_id=None): 
        # NOTA: Ignoramos patient_id para exportar TODO, 
        # pero mantenemos el argumento para no romper compatibilidad si se llamara con él.
        
        # 1. Obtener lista de todos los pacientes
        all_patients = db.get_all_patients() # Devuelve lista de dicts [{'label': 'Nombre', 'value': ID}, ...]
        
        # Listas maestras para acumular datos de TODOS
        master_profiles = []
        master_quests = []
        master_exercises = []

        # 2. Recorrer paciente por paciente
        for p in all_patients:
            p_id = p['value']
            p_name = p['label']
            
            # --- A) PERFIL ---
            info = db.get_user_info(p_id)
            if info:
                # Calcular IMC y Límite FC
                try:
                    weight = float(info['weight'])
                    height = float(info['height'])
                    age = int(info['age'])
                    imc = round(weight / ((height/100)**2), 2)
                    limit_hr = (220 - age) if age > 0 else 170
                except:
                    imc = "Error"
                    limit_hr = 170

                # Añadir a la lista maestra
                master_profiles.append({
                    "ID Paciente": p_id,
                    "Nombre": info['name'],
                    "Edad": info['age'],
                    "Peso (kg)": info['weight'],
                    "Altura (cm)": info['height'],
                    "IMC": imc,
                    "Límite FC Personal": limit_hr
                })
            
            # --- B) DIARIO CLÍNICO ---
            quest_data = db.get_chart_data(p_id)
            if quest_data:
                for row in quest_data:
                    master_quests.append({
                        "ID Paciente": p_id,
                        "Nombre": p_name,
                        "Fecha": row[0],
                        "Fatiga (0-10)": row[1],
                        "RPE (0-10)": row[2]
                    })

            # --- C) EJERCICIOS (Con lógica de alertas) ---
            ex_data = db.get_exercise_history(p_id)
            if ex_data:
                # Recalculamos límite por seguridad si no se hizo arriba
                age_ex = info['age'] if info and info['age'] else 0
                limit_hr_ex = (220 - age_ex) if age_ex > 0 else 170

                for row in ex_data:
                    # row indices: 0:date, 1:type, 2:dur, 3:avg_hr, 4:max_hr, 5:min_hr, 6:avg_spo2, 7:min_spo2
                    max_hr = row[4]
                    min_spo2 = row[7]
                    
                    # Lógica de Estado
                    estado = "NORMAL"
                    if min_spo2 < 90: estado = "⚠️ HIPOXIA"
                    elif max_hr > limit_hr_ex: estado = "⚠️ TAQUICARDIA"

                    master_exercises.append({
                        "ID Paciente": p_id,
                        "Nombre": p_name,
                        "Fecha": row[0],
                        "Actividad": row[1].upper(),
                        "Duración (min)": round(row[2]/60, 2),
                        "FC Máx": max_hr,
                        "SpO2 Mín": min_spo2,
                        "Estado": estado,
                        "FC Media": row[3],
                        "SpO2 Media": row[6]
                    })

        # 3. Crear DataFrames Globales
        df_profiles = pd.DataFrame(master_profiles)
        df_quests = pd.DataFrame(master_quests)
        df_exercises = pd.DataFrame(master_exercises)

        # Ordenar columnas si hay datos (para que ID y Nombre salgan primero)
        if not df_exercises.empty:
            cols = ["ID Paciente", "Nombre", "Fecha", "Actividad", "Estado", "Duración (min)", "FC Máx", "SpO2 Mín", "FC Media", "SpO2 Media"]
            df_exercises = df_exercises[cols]

        # 4. Guardar en Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Si los dataframes están vacíos, creamos una hoja vacía con mensaje
            if df_profiles.empty: 
                pd.DataFrame(["No hay pacientes"]).to_excel(writer, sheet_name='Perfiles')
            else:
                df_profiles.to_excel(writer, sheet_name='Perfiles Global', index=False)
            
            if df_exercises.empty:
                pd.DataFrame(["No hay ejercicios"]).to_excel(writer, sheet_name='Ejercicios')
            else:
                df_exercises.to_excel(writer, sheet_name='Ejercicios Global', index=False)

            if df_quests.empty:
                pd.DataFrame(["No hay diarios"]).to_excel(writer, sheet_name='Diarios')
            else:
                df_quests.to_excel(writer, sheet_name='Diarios Global', index=False)
        
        return output.getvalue()