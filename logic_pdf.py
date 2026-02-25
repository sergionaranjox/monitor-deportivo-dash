from fpdf import FPDF
import datetime
from database import db

class pdf_generator:
    
    @staticmethod
    def create_report(patient_id):
        # 1. Recuperar datos
        user_info = db.get_user_info(patient_id)
        quest_data = db.get_chart_data(patient_id)
        ex_data = db.get_exercise_history(patient_id) 

        # --- CÁLCULO DEL LÍMITE PERSONALIZADO ---
        age = 0
        limit_hr = 170 # Valor por defecto si no hay edad
        
        if user_info and user_info.get('age'):
            age = user_info['age']
            limit_hr = 220 - age # Fórmula médica

        # 2. Configurar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # --- CABECERA ---
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="MedTrack - Informe Clínico", ln=True, align='C')
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 10, txt=f"Fecha de emisión: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)

        # --- DATOS DEL PACIENTE ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt=f"ID Paciente: {patient_id}", ln=True)
        
        pdf.set_font("Arial", size=11)
        if user_info:
            # Obtenemos nombre si existe, sino ID
            name = user_info.get('user', 'Desconocido') 
            weight = user_info.get('weight', 'N/A')
            height = user_info.get('height', 'N/A')
            
            imc_txt = "N/A"
            if weight != "N/A" and height != "N/A":
                try:
                    imc = float(weight) / ((float(height)/100)**2)
                    imc_txt = f"{imc:.2f}"
                except: pass
                
            pdf.cell(200, 8, txt=f"Paciente: {name}", ln=True)
            pdf.cell(200, 8, txt=f"Edad: {age} anos | Peso: {weight} kg | Altura: {height} cm | IMC: {imc_txt}", ln=True)
            
            # Mostramos en rojo el límite que se va a usar
            pdf.set_text_color(200, 0, 0)
            pdf.cell(200, 8, txt=f"Límite FC Personalizado (220-{age}): {limit_hr} bpm", ln=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(200, 8, txt="Datos de perfil no disponibles.", ln=True)
        
        pdf.ln(5)

        # --- RESUMEN DE ACTIVIDAD (TABLA) ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt="Historial de Sensores (FC y SpO2)", ln=True)
        
        # Cabecera
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(200, 220, 255) 
        pdf.cell(45, 8, "Fecha", 1, 0, 'C', 1)
        pdf.cell(25, 8, "Tipo", 1, 0, 'C', 1)
        pdf.cell(25, 8, "Tiempo", 1, 0, 'C', 1)
        pdf.cell(25, 8, "FC Max", 1, 0, 'C', 1)
        pdf.cell(25, 8, "SpO2 Med", 1, 0, 'C', 1) 
        pdf.cell(40, 8, "Estado", 1, 1, 'C', 1)

        # Filas
        pdf.set_font("Arial", size=10)
        if ex_data:
            for row in ex_data[:18]: 
                # row indices: 0:date, 1:type, 2:dur, 3:avg_hr, 4:max_hr, 5:min_hr, 6:avg_spo2, 7:min_spo2
                fecha = str(row[0])[:16]
                tipo = row[1].upper()
                mins = row[2] // 60
                tiempo = f"{mins} min"
                fc_max = row[4]
                spo2_avg = row[6] # Usamos la Media (índice 6)
                
                # --- AQUÍ ESTABA EL ERROR, AHORA CORREGIDO ---
                estado = "NORMAL"
                if row[7] < 90: # Si mínimo SpO2 < 90
                    estado = "! HIPOXIA"
                elif fc_max > limit_hr: # AHORA USA LA VARIABLE PERSONALIZADA
                    estado = "! TAQUICARDIA" 
                
                pdf.cell(45, 8, fecha, 1)
                pdf.cell(25, 8, tipo, 1)
                pdf.cell(25, 8, tiempo, 1)
                pdf.cell(25, 8, str(fc_max), 1)
                pdf.cell(25, 8, f"{spo2_avg}%", 1)
                pdf.cell(40, 8, estado, 1, 1)
        else:
            pdf.cell(185, 8, "No hay registros de ejercicio.", 1, 1)

        pdf.ln(10)

        # --- RESUMEN CLÍNICO ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt="Últimos Datos Clínicos (Fatiga/Sueño)", ln=True)
        pdf.set_font("Arial", size=10)
        if quest_data:
            last = quest_data[-1]
            pdf.multi_cell(0, 8, txt=f"Último registro ({last[0]}):\nNivel de Fatiga: {last[1]}/10\nEsfuerzo Percibido (RPE): {last[2]}/10")
        else:
            pdf.cell(200, 8, txt="Sin datos de diario.", ln=True)

        return pdf.output(dest='S').encode('latin-1')