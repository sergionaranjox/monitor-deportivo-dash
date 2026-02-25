from dash import Input, Output, State, html, no_update, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import math
import random
from database import db

class simulation:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def start_callbacks(self):
        @self.app.callback(
            Output("clock-interval", "disabled"),
            Output("clock-interval", "n_intervals"),
            Output("btn-start-ex", "children"),
            Output("btn-start-ex", "color"),
            Output("is-running-store", "data"),
            Output("save-confirmation-msg", "children"),
            Output("locked-ex-store", "data"),
            
            Input("btn-start-ex", "n_clicks"),
            Input("ex-type", "value"),
            
            State("is-running-store", "data"),
            State("clock-interval", "n_intervals"),
            State("user_storage", "data"),
            State("locked-ex-store", "data"), 
            prevent_initial_call=True
        )
        def master_control(n_clicks, ex_input_value, is_running, n_intervals, session, locked_ex):
            
            ctx = callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            should_save = False
            if trigger_id == "btn-start-ex" and is_running: should_save = True
            elif trigger_id == "ex-type" and is_running: should_save = True

            if should_save:
                duration_sec = int(n_intervals * 0.5) if n_intervals else 0
                exercise_to_save = locked_ex if locked_ex else ex_input_value

                if session and session.get("id"):
                    user_id = session.get("id")
                    
                    user_info = db.get_user_info(user_id)
                    age = user_info["age"] if user_info and user_info["age"] else 0
                    limit_hr = (220 - age) if age > 0 else 170

                    if duration_sec > 0:
                        # Simulamos datos Cardiacos
                        if exercise_to_save == "run": base_hr = random.randint(140, 160)
                        elif exercise_to_save == "bike": base_hr = random.randint(120, 140)
                        else: base_hr = random.randint(100, 125)

                        sim_avg_hr = base_hr
                        sim_max_hr = base_hr + random.randint(10, 25)
                        sim_min_hr = base_hr - random.randint(10, 20)

                        # Simulamos datos SpO2
                        sim_avg_spo2 = random.randint(95, 99)
                        sim_min_spo2 = sim_avg_spo2 - random.randint(0, 7) 

                        if db.save_exercise(user_id, exercise_to_save, duration_sec, sim_avg_hr, sim_max_hr, sim_min_hr, sim_avg_spo2, sim_min_spo2):
                            mins = duration_sec // 60
                            secs = duration_sec % 60
                            
                            # Prioridad de Alertas
                            if sim_min_spo2 < 90:
                                color = "info"
                                head = f"⚠️ ALERTA: HIPOXIA ({sim_min_spo2}%)"
                                rec = "Nivel de oxígeno bajo."
                            elif sim_max_hr > limit_hr:
                                color = "danger"
                                head = f"⚠️ ALERTA CARDIACA (>{limit_hr} bpm)"
                                rec = "Frecuencia muy alta."
                            else:
                                color = "success"
                                head = "✅ Ejercicio Guardado"
                                rec = "Parámetros normales."

                            msg = dbc.Alert([
                                html.H5(head, className="alert-heading"),
                                html.P(f"Actividad: {exercise_to_save.upper()} | Tiempo: {mins}m {secs}s"),
                                html.Hr(),
                                html.B(f"❤️ Max: {sim_max_hr} | 🫁 SpO2 Min: {sim_min_spo2}%"),
                                html.P(rec, className="mb-0 small")
                            ], color=color, duration=8000)
                        else:
                            msg = dbc.Alert("Error BD", color="danger")
                    else:
                        msg = dbc.Alert("Tiempo muy corto", color="warning", duration=3000)

                return True, 0, "INICIAR SESIÓN", "success", False, msg, None

            if trigger_id == "btn-start-ex" and not is_running:
                return False, no_update, "DETENER SESIÓN", "danger", True, "", ex_input_value

            if trigger_id == "ex-type" and not is_running:
                return True, 0, "INICIAR SESIÓN", "success", False, "", None

            return no_update, no_update, no_update, no_update, no_update, no_update, no_update

        @self.app.callback(
            Output("timer-display", "children"),
            Output("ecg-graph", "figure"),
            Input("clock-interval", "n_intervals"),
            State("is-running-store", "data")
        )
        def update_display(n, is_running):
            if n is None or n == 0:
                fig = go.Figure()
                fig.update_layout(paper_bgcolor="black", plot_bgcolor="black", xaxis={"visible":False}, yaxis={"visible":False}, margin=dict(l=0,r=0,t=0,b=0))
                return "00:00", fig

            seconds_total = int(n * 0.5)
            time_str = f"{seconds_total//60:02d}:{seconds_total%60:02d}"

            x_vals = list(range(60))
            y_vals = []
            for x in x_vals:
                t = x + (n * 5)
                val = math.sin(t * 0.2) * 0.2
                if t % 15 < 2: val += 2.5
                elif t % 15 < 4: val -= 1.0
                val += random.uniform(-0.1, 0.1)
                y_vals.append(val)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', line=dict(color='#00ff00', width=2), fill='tozeroy'))
            fig.update_layout(paper_bgcolor="black", plot_bgcolor="black", xaxis={"visible":False, "range":[0,60]}, yaxis={"visible":False, "range":[-2,3]}, margin=dict(l=0,r=0,t=10,b=10), showlegend=False)
            return time_str, fig