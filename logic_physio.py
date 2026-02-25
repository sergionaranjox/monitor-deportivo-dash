from dash import Input, Output, State, html, no_update, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from database import db
from logic_pdf import pdf_generator
from logic_export import excel_generator
from datetime import datetime

class physio:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def create_physio_table(self, ex_type, patient_id, limit_hr):
        data = db.get_specific_history(patient_id, ex_type)
        if not data: return dbc.Alert("Sin datos", color="light")
        header = html.Thead(html.Tr([html.Th("Fecha"), html.Th("Tiempo"), html.Th("FC Max"), html.Th("SpO2 Med"), html.Th("Estado")]))
        rows = []
        for row in data:
            max_hr = row[3]
            avg_spo2 = row[5]
            is_hypoxia = avg_spo2 < 90
            is_tachy = max_hr > limit_hr 
            if is_hypoxia: status, row_class = "⚠️ HIPOXIA", "table-info"
            elif is_tachy: status, row_class = "⚠️ TAQUICARDIA", "table-danger"
            else: status, row_class = "Normal", ""
            mins = row[1] // 60
            secs = row[1] % 60
            rows.append(html.Tr([
                html.Td(row[0]), html.Td(f"{mins}m {secs}s"), html.Td(f"{max_hr}"), html.Td(f"{avg_spo2} %"), html.Td(status, className="fw-bold")
            ], className=row_class))
        return dbc.Table([header, html.Tbody(rows)], size="sm", bordered=True, hover=True)

    def start_callbacks(self):
        @self.app.callback(
            Output("fisio-patient-selector", "options"),
            Output("btn-download-excel", "disabled"), # <--- AHORA CONTROLAMOS ESTO AQUÍ
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def load_list(path, session):
            if path == "/app" and session and session.get("role") == "fisio":
                patients_list = db.get_all_patients()
                updated_list = []
                for p in patients_list:
                    status = db.get_last_health_status(p['value'])
                    if status == "danger": label = f"🔴 {p['label']} (RIESGO)"
                    elif status == "ok": label = f"🟢 {p['label']}"
                    else: label = f"⚪ {p['label']}"
                    updated_list.append({"label": label, "value": p['value']})
                
                # Devolvemos la lista Y habilitamos el botón Excel siempre (False = no disabled)
                return updated_list, False 
            return no_update, True

        # --- DESCARGA PDF (INDIVIDUAL) ---
        @self.app.callback(
            Output("download-component", "data"),
            Input("btn-download-report", "n_clicks"),
            State("fisio-patient-selector", "value"),
            prevent_initial_call=True
        )
        def download_report(n_clicks, patient_id):
            if not patient_id: return no_update
            user_info = db.get_user_info(patient_id)
            name = user_info['name'] if user_info and 'name' in user_info else f"Paciente_{patient_id}"
            date_str = datetime.now().strftime("%Y-%m-%d")
            pdf_bytes = pdf_generator.create_report(patient_id)
            return dcc.send_bytes(pdf_bytes, filename=f"Informe_{name}_{date_str}.pdf")

        # --- DESCARGA EXCEL (GLOBAL - TODOS LOS PACIENTES) ---
        @self.app.callback(
            Output("download-excel-component", "data"),
            Input("btn-download-excel", "n_clicks"),
            # Ya no necesitamos el State del selector porque descargamos TODO
            prevent_initial_call=True
        )
        def download_excel(n_clicks):
            date_str = datetime.now().strftime("%Y-%m-%d")
            # Llamamos a la función sin argumentos (o con None)
            excel_bytes = excel_generator.create_excel()
            return dcc.send_bytes(excel_bytes, filename=f"BASE_DE_DATOS_COMPLETA_{date_str}.xlsx")

        # --- VISTAS DEL PACIENTE ---
        @self.app.callback(
            Output("fisio-quest-chart", "figure"),
            Output("fisio-quest-table", "children"),
            Output("fisio-ex-chart", "figure"),
            Output("fisio-ex-table", "children"),
            Output("fisio-scatter-chart", "figure"),
            Output("fisio-patient-info", "children"),
            Output("btn-download-report", "disabled"), # Solo controlamos el botón PDF aquí
            
            Input("fisio-patient-selector", "value")
        )
        def update_patient_view(patient_id):
            if not patient_id:
                empty = go.Figure()
                empty.update_layout(template="plotly_white", xaxis={"visible":False}, yaxis={"visible":False}, annotations=[{"text": "Seleccione Paciente", "showarrow": False}])
                return empty, "", empty, "", empty, "Esperando...", True

            user_info = db.get_user_info(patient_id)
            age = user_info['age'] if user_info and user_info['age'] else 0
            limit_hr = (220 - age) if age > 0 else 170 
            patient_details = f"ID: {patient_id} | Edad: {age if age else 'N/A'} | Límite FC: {limit_hr} bpm"

            # GRÁFICAS (Igual que antes)
            quest_data = db.get_chart_data(patient_id)
            fig_quest = go.Figure()
            if quest_data:
                dates = [x[0] for x in quest_data]
                fig_quest.add_trace(go.Scatter(x=dates, y=[x[1] for x in quest_data], name='Fatiga', line=dict(color='#d62728')))
                fig_quest.add_trace(go.Scatter(x=dates, y=[x[2] for x in quest_data], name='RPE', line=dict(color='#1f77b4', dash='dot')))
                fig_quest.update_layout(template="plotly_white", height=300, margin=dict(l=40,r=20,t=20,b=40), yaxis=dict(range=[0, 11], title="Nivel (0-10)"))
                rows_q = []
                for r in quest_data[-5:]: 
                    is_danger = (r[1] and r[1] >= 8)
                    color_class = "table-danger" if is_danger else ""
                    rows_q.append(html.Tr([html.Td(r[0]), html.Td(f"{r[1]}"), html.Td(r[2])], className=color_class))
                table_quest = dbc.Table([html.Thead(html.Tr([html.Th("Fecha"), html.Th("Fatiga"), html.Th("RPE")])), html.Tbody(rows_q)], size="sm", bordered=True)
            else:
                fig_quest.update_layout(xaxis={"visible":False}, yaxis={"visible":False})
                table_quest = dbc.Alert("Sin datos clínicos.", color="light")

            ex_data = db.get_exercise_history(patient_id)
            fig_ex = go.Figure()
            if ex_data:
                ex_rev = ex_data[::-1]
                dates_ex = [x[0] for x in ex_rev]
                fig_ex.add_trace(go.Bar(x=dates_ex, y=[x[4] for x in ex_rev], name='FC Max', marker_color='#ff9999'))
                fig_ex.add_trace(go.Scatter(x=dates_ex, y=[x[3] for x in ex_rev], name='FC Media', line=dict(color='red')))
                fig_ex.update_layout(template="plotly_white", height=300, margin=dict(l=40,r=20,t=20,b=40))
            else:
                fig_ex.update_layout(xaxis={"visible":False}, yaxis={"visible":False})

            tab_run = self.create_physio_table("run", patient_id, limit_hr)
            tab_bike = self.create_physio_table("bike", patient_id, limit_hr)
            tab_squat = self.create_physio_table("squat", patient_id, limit_hr)
            ex_content = dbc.Tabs([dbc.Tab(tab_run, label="Correr"), dbc.Tab(tab_bike, label="Bici"), dbc.Tab(tab_squat, label="Sentadillas")])

            corr_data = db.get_correlation_data(patient_id)
            fig_scatter = go.Figure()
            if corr_data:
                for ex_type, color in [("run", "orange"), ("bike", "blue"), ("squat", "green")]:
                    points = [p for p in corr_data if p['type'] == ex_type]
                    if points:
                        fig_scatter.add_trace(go.Scatter(x=[p['fatiga'] for p in points], y=[p['hr_max'] for p in points], mode='markers', marker=dict(size=12, color=color), name=ex_type.upper()))
                fig_scatter.update_layout(template="plotly_white", xaxis_title="Fatiga", yaxis_title="FC Max", height=400)
            else:
                fig_scatter.update_layout(xaxis={"visible":False}, yaxis={"visible":False}, annotations=[{"text": "Faltan datos", "showarrow": False}])

            # Habilitamos botón PDF (False), el de Excel ya está habilitado desde el inicio
            return fig_quest, table_quest, fig_ex, ex_content, fig_scatter, patient_details, False