from dash import Input, Output, State, html, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from database import db

class patient:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def create_table(self, ex_type, user_id, age_limit):
        data = db.get_specific_history(user_id, ex_type)
        if not data: return dbc.Alert(f"Sin registros de {ex_type}.", color="light")
        header = html.Thead(html.Tr([html.Th("Estado"), html.Th("Fecha"), html.Th("Tiempo"), html.Th("FC Max"), html.Th("SpO2 Min")]))
        rows = []
        for row in data:
            max_hr, min_spo2 = row[3], row[6]
            if min_spo2 < 90: status, row_class = "⚠️ HIPOXIA", "table-info"
            elif max_hr > age_limit: status, row_class = "⚠️ CARDIACO", "table-danger"
            else: status, row_class = "✅ OK", ""
            mins, secs = row[1] // 60, row[1] % 60
            rows.append(html.Tr([
                html.Td(status, className="fw-bold"), html.Td(row[0]), html.Td(f"{mins}m {secs}s"), html.Td(f"{max_hr} bpm"), html.Td(f"{min_spo2} %"),
            ], className=row_class))
        return dbc.Table([header, html.Tbody(rows)], hover=True, bordered=True, size="sm")

    def start_callbacks(self):
        
        # --- 1. MODAL INTELIGENTE (SOLO SALTA SI INTENTAS USAR HERRAMIENTAS) ---
        @self.app.callback(
            Output("modal-missing-profile", "is_open"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def check_missing_profile(path, session):
            # Solo chequeamos si intenta entrar en Monitor o Historial
            if path in ["/app/monitor", "/app/history"] and session and session.get("id"):
                info = db.get_user_info(session.get("id"))
                # Si falta algún dato vital, saltamos la alerta
                if info and (not info["age"] or not info["weight"] or not info["height"]): return True
                if not info: return True
            return False

        # --- 2. HISTORIAL ---
        @self.app.callback(
            Output("out-quest", "children"),
            Output("table-container", "children"),
            Output("patient-chart", "figure"),
            Output("exercises-table-container", "children"),
            Output("exercises-chart", "figure"),
            Input("btn-send-quest", "n_clicks"),
            Input("url", "pathname"),
            State("q-fatiga", "value"),
            State("q-rpe", "value"),
            State("q-sueno", "value"),
            State("user_storage", "data")
        )
        def update_history_view(n_clicks, pathname, fatiga, rpe, sueno, session):
            if pathname != "/app/history": return no_update, no_update, no_update, no_update, no_update
            if not session or not session.get("id"): return dbc.Alert("Error"), "", go.Figure(), "", go.Figure()

            user_id = session.get("id")
            msg, ctx, trigger_id = "", callback_context, None
            if ctx.triggered: trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if trigger_id == "btn-send-quest":
                if sueno is None: msg = dbc.Alert("Introduce horas de sueño", color="warning")
                elif float(sueno) < 0: msg = dbc.Alert("⚠️ No puedes dormir tiempo negativo", color="danger")
                else:
                    db.save_quest(user_id, fatiga, rpe, sueno)
                    msg = dbc.Alert("✅ Guardado", color="success")

            hist = db.get_history(user_id)
            rows = []
            if hist:
                for r in hist:
                    style = {"color": "red"} if (r[1]>=8) else {}
                    rows.append(html.Tr([html.Td(r[0]), html.Td(r[1], style=style), html.Td(r[2]), html.Td(r[3])]))
            table_diary = dbc.Table([html.Thead(html.Tr([html.Th("F"), html.Th("Fat"), html.Th("RPE"), html.Th("S")])), html.Tbody(rows)], size="sm", bordered=True)
            
            c_data = db.get_chart_data(user_id)
            fig_d = go.Figure()
            if c_data:
                dates = [x[0] for x in c_data]
                fig_d.add_trace(go.Scatter(x=dates, y=[x[1] for x in c_data], name='Fatiga'))
                fig_d.update_layout(template="plotly_white", margin=dict(l=20,r=20,t=20,b=20), height=300, autosize=False, yaxis=dict(range=[0, 11], title="Nivel"))
            else:
                fig_d.update_layout(template="plotly_white", xaxis={"visible":False}, yaxis={"visible":False})

            user_info = db.get_user_info(user_id)
            age = user_info["age"] if user_info and user_info["age"] else 0
            limit_hr = (220 - age) if age > 0 else 170

            t_run = self.create_table("run", user_id, limit_hr)
            t_bike = self.create_table("bike", user_id, limit_hr)
            t_squat = self.create_table("squat", user_id, limit_hr)
            tabs_ex = dbc.Tabs([dbc.Tab(t_run, label="Correr"), dbc.Tab(t_bike, label="Bici"), dbc.Tab(t_squat, label="Sentadilla")])
            
            fig_ex = go.Figure()
            fig_ex.update_layout(template="plotly_white", xaxis={"visible":False}, yaxis={"visible":False})

            return msg, table_diary, fig_d, tabs_ex, fig_ex

        # --- 3. PERFIL ---
        @self.app.callback(
            Output("out-profile", "children"),
            Output("profile-summary", "children"),
            Output("prof-age", "value"),
            Output("prof-weight", "value"),
            Output("prof-height", "value"),
            Input("btn-save-profile", "n_clicks"),
            Input("url", "pathname"),
            State("prof-age", "value"),
            State("prof-weight", "value"),
            State("prof-height", "value"),
            State("user_storage", "data")
        )
        def update_profile_view(n_clicks, pathname, age, weight, height, session):
            if pathname != "/app/profile": return no_update, no_update, no_update, no_update, no_update
            if not session or not session.get("id"): return "", "", "", "", ""
            user_id = session.get("id")
            ctx, trigger_id = callback_context, None
            if ctx.triggered: trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            msg = ""
            
            if trigger_id == "btn-save-profile":
                if age and weight and height:
                    if float(age)<=0 or float(weight)<=0 or float(height)<=0: msg=dbc.Alert("Valores positivos por favor", color="warning")
                    elif db.update_profile(user_id, age, weight, height): msg = dbc.Alert("✅ Guardado", color="success")
                    else: msg = dbc.Alert("Error", color="danger")
                else: msg = dbc.Alert("Rellena todo", color="warning")

            user_info = db.get_user_info(user_id)
            val_age = user_info["age"] if user_info else ""
            val_w = user_info["weight"] if user_info else ""
            val_h = user_info["height"] if user_info else ""
            if val_age: fc_text = f"{220-val_age} bpm"
            else: fc_text = "Pendiente"
            imc_text = "--"
            if val_w and val_h:
                imc = val_w / ((val_h/100)**2)
                imc_text = f"{imc:.2f}"
            summary = [html.H4(f"IMC: {imc_text}", className="text-center"), html.Hr(), html.H4(f"FC Max: {fc_text}", className="text-center text-danger")]
            return msg, summary, val_age, val_w, val_h