from dash import Input, Output, State, html, no_update, dcc, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from collections import defaultdict
import random
from database import db
from logic_pdf import pdf_generator
from logic_export import excel_generator
from datetime import datetime

_RESORTS = [
    {"name": "Sierra Nevada",   "lat": 37.097, "lon": -3.394, "alt_min":  900, "alt_max": 3300},
    {"name": "Formigal",        "lat": 42.780, "lon": -0.383, "alt_min": 1500, "alt_max": 2250},
    {"name": "Baqueira-Beret",  "lat": 42.690, "lon":  0.969, "alt_min": 1500, "alt_max": 2610},
    {"name": "La Molina",       "lat": 42.344, "lon":  1.940, "alt_min": 1700, "alt_max": 2445},
    {"name": "Candanchú",       "lat": 42.786, "lon": -0.513, "alt_min": 1500, "alt_max": 2400},
    {"name": "Grandvalira",     "lat": 42.543, "lon":  1.712, "alt_min": 1710, "alt_max": 2640},
    {"name": "Masella",         "lat": 42.350, "lon":  1.917, "alt_min": 1600, "alt_max": 2535},
    {"name": "Cerler",          "lat": 42.604, "lon":  0.496, "alt_min": 1500, "alt_max": 2630},
    {"name": "Val d'Isère",     "lat": 45.449, "lon":  6.981, "alt_min": 1850, "alt_max": 3456},
    {"name": "Courchevel",      "lat": 45.418, "lon":  6.636, "alt_min": 1300, "alt_max": 3230},
    {"name": "Verbier",         "lat": 46.096, "lon":  7.227, "alt_min": 1500, "alt_max": 3330},
    {"name": "Zermatt",         "lat": 46.021, "lon":  7.749, "alt_min": 1620, "alt_max": 3883},
    {"name": "Kitzbühel",       "lat": 47.446, "lon": 12.390, "alt_min":  800, "alt_max": 2000},
    {"name": "St. Moritz",      "lat": 46.498, "lon":  9.840, "alt_min": 1800, "alt_max": 3303},
]


def _assign_resort(altitud: int, rng: random.Random) -> dict:
    matching = [r for r in _RESORTS if r["alt_min"] <= altitud <= r["alt_max"]]
    if not matching:
        matching = sorted(_RESORTS, key=lambda r: abs((r["alt_min"] + r["alt_max"]) / 2 - altitud))[:3]
    return rng.choice(matching)

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
            Output("btn-download-excel", "disabled"),
            Output("fisio-overview", "children"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def load_list(path, session):
            if path == "/app" and session and session.get("role") == "fisio":
                patients_list = db.get_all_patients()
                updated_list  = []
                overview_rows = []
                medals = ["🥇", "🥈", "🥉"]

                ranking = db.get_ranking()
                rank_map = {r["id"]: i for i, r in enumerate(ranking)}

                alert_items = []
                for p in patients_list:
                    pid    = p['value']
                    status = db.get_last_health_status(pid)
                    total  = db.get_total_metros(pid)
                    badge, _ = db.get_badge_info(total)
                    acwr_data = db.get_acwr(pid)
                    acwr      = acwr_data["acwr"]

                    hist      = db.get_history(pid)
                    last_fatiga = hist[0][1] if hist else None
                    days_since  = db.get_last_session_days(pid)

                    if acwr is not None and acwr > 1.5 and last_fatiga is not None and last_fatiga >= 8:
                        alert_items.append(
                            dbc.Alert([
                                html.Span("🚨 ", style={"fontSize": "1.1rem"}),
                                html.Strong(f"{p['label']}"),
                                f" — ACWR crítico ({acwr}) con fatiga alta ({last_fatiga}/10). "
                                "Riesgo de lesión elevado. Reducir carga inmediatamente.",
                            ], color="danger", className="mb-2 py-2 small")
                        )
                    if days_since is None or days_since >= 7:
                        days_txt = f"hace {days_since} días" if days_since is not None else "nunca"
                        alert_items.append(
                            dbc.Alert([
                                html.Span("⚠️ ", style={"fontSize": "1.1rem"}),
                                html.Strong(f"{p['label']}"),
                                f" — Sin sesión en los últimos 7 días (última: {days_txt}). "
                                "Posible abandono o lesión.",
                            ], color="warning", className="mb-2 py-2 small")
                        )

                    if status == "danger":
                        semaforo, dd_label = "🔴", f"🔴 {p['label']} (RIESGO)"
                        row_class = "table-danger"
                    elif status == "warning":
                        semaforo, dd_label = "🟡", f"🟡 {p['label']}"
                        row_class = "table-warning"
                    elif status == "ok":
                        semaforo, dd_label = "🟢", f"🟢 {p['label']}"
                        row_class = ""
                    else:
                        semaforo, dd_label = "⚪", f"⚪ {p['label']}"
                        row_class = ""

                    if acwr is None:
                        acwr_cell = html.Td("—", className="text-center text-muted small")
                    elif acwr > 1.5:
                        acwr_cell = html.Td(dbc.Badge(str(acwr), color="danger"),
                                            className="text-center")
                    elif acwr > 1.3:
                        acwr_cell = html.Td(dbc.Badge(str(acwr), color="warning"),
                                            className="text-center")
                    elif acwr >= 0.8:
                        acwr_cell = html.Td(dbc.Badge(str(acwr), color="success"),
                                            className="text-center")
                    else:
                        acwr_cell = html.Td(dbc.Badge(str(acwr), color="info"),
                                            className="text-center")

                    updated_list.append({"label": dd_label, "value": pid})

                    pos = rank_map.get(pid, len(ranking))
                    pos_icon = medals[pos] if pos < 3 else f"#{pos+1}"
                    overview_rows.append(html.Tr([
                        html.Td(pos_icon, className="text-center fw-bold"),
                        html.Td(p['label'], className="fw-bold"),
                        html.Td(semaforo, className="text-center fs-5"),
                        acwr_cell,
                        html.Td(f"{badge['icono']} {badge['nombre']}"),
                        html.Td(f"{total:,} m", className="text-end fw-bold"),
                    ], className=row_class))

                alerts_section = html.Div(alert_items) if alert_items else html.Div()

                if overview_rows:
                    header = html.Thead(html.Tr([
                        html.Th("#", className="text-center"),
                        html.Th("Atleta"),
                        html.Th("Estado", className="text-center"),
                        html.Th("ACWR", className="text-center"),
                        html.Th("Insignia"),
                        html.Th("Metros", className="text-end"),
                    ]))
                    overview_table = dbc.Table(
                        [header, html.Tbody(overview_rows)],
                        hover=True, bordered=False, striped=True, size="sm", className="mb-0"
                    )
                else:
                    overview_table = dbc.Alert("No hay atletas registrados aún.", color="light")

                overview = html.Div([alerts_section, overview_table])
                return updated_list, False, overview

            return no_update, True, no_update

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
                ex_rev   = ex_data[::-1]
                dates_ex = [x[0] for x in ex_rev]
                fig_ex.add_trace(go.Bar(
                    x=dates_ex, y=[x[4] for x in ex_rev],
                    name='FC Max', marker_color='#fca5a5', yaxis='y1'
                ))
                fig_ex.add_trace(go.Scatter(
                    x=dates_ex, y=[x[3] for x in ex_rev],
                    name='FC Media', line=dict(color='#dc2626', dash='dot'), yaxis='y1'
                ))
                fig_ex.add_trace(go.Scatter(
                    x=dates_ex, y=[x[7] for x in ex_rev],
                    name='SpO2 Min %', line=dict(color='#0ea5e9', width=2),
                    mode='lines+markers', marker=dict(size=6), yaxis='y2'
                ))
                fig_ex.update_layout(
                    template="plotly_white", height=300,
                    margin=dict(l=40, r=50, t=20, b=40),
                    yaxis=dict(title="FC (bpm)", side="left"),
                    yaxis2=dict(title="SpO2 %", overlaying="y", side="right",
                                range=[80, 100], showgrid=False),
                    legend=dict(orientation="h", y=1.08),
                )
            else:
                fig_ex.update_layout(xaxis={"visible":False}, yaxis={"visible":False})

            tab_esqui = self.create_physio_table("esqui", patient_id, limit_hr)
            tab_snow  = self.create_physio_table("snowboard", patient_id, limit_hr)
            ex_content = dbc.Tabs([dbc.Tab(tab_esqui, label="⛷️ Esquí Alpino"), dbc.Tab(tab_snow, label="🏂 Snowboard")])

            corr_data = db.get_correlation_data(patient_id)
            fig_scatter = go.Figure()
            if corr_data:
                for ex_type, color, label in [("esqui", "#0ea5e9", "⛷️ Esquí"), ("snowboard", "#f97316", "🏂 Snowboard")]:
                    points = [p for p in corr_data if p['type'] == ex_type]
                    if points:
                        fig_scatter.add_trace(go.Scatter(x=[p['fatiga'] for p in points], y=[p['hr_max'] for p in points], mode='markers', marker=dict(size=13, color=color, line=dict(width=1, color='white')), name=label))
                fig_scatter.update_layout(template="plotly_white", xaxis_title="Fatiga", yaxis_title="FC Max", height=400)
            else:
                fig_scatter.update_layout(xaxis={"visible":False}, yaxis={"visible":False}, annotations=[{"text": "Faltan datos", "showarrow": False}])

            # Habilitamos botón PDF (False), el de Excel ya está habilitado desde el inicio
            return fig_quest, table_quest, fig_ex, ex_content, fig_scatter, patient_details, False

        # --- NOTAS DEL ENTRENADOR ---
        @self.app.callback(
            Output("physio-note-input", "value"),
            Output("physio-note-msg",   "children"),
            Input("fisio-patient-selector",  "value"),
            Input("btn-save-physio-note",    "n_clicks"),
            State("physio-note-input", "value"),
            prevent_initial_call=False,
        )
        def manage_physio_notes(patient_id, n_save, note_text):
            ctx     = callback_context
            trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

            if trigger == "btn-save-physio-note":
                if not patient_id:
                    return no_update, dbc.Alert("Selecciona un atleta primero", color="warning",
                                                duration=3000)
                db.save_athlete_note(patient_id, note_text or "")
                return no_update, dbc.Alert("✅ Nota guardada", color="success", duration=3000)

            if not patient_id:
                return "", ""
            return db.get_athlete_note(patient_id), ""

        # --- MAPA DE CALOR GEOGRÁFICO ---
        @self.app.callback(
            Output("fisio-heatmap", "figure"),
            Input("fisio-patient-selector", "value")
        )
        def update_heatmap(patient_id):
            def empty_map(msg):
                fig = go.Figure()
                fig.update_layout(
                    mapbox=dict(style="open-street-map", center=dict(lat=43, lon=2), zoom=4),
                    margin=dict(l=0, r=0, t=0, b=0), height=480,
                    annotations=[{"text": msg, "showarrow": False,
                                  "xref": "paper", "yref": "paper", "x": 0.5, "y": 0.5,
                                  "font": {"size": 16, "color": "gray"}}]
                )
                return fig

            if not patient_id:
                return empty_map("Seleccione un atleta")

            sessions = db.get_heatmap_data(patient_id)
            if not sessions:
                return empty_map("Sin sesiones registradas")

            density_lats, density_lons, density_z = [], [], []
            resort_agg = defaultdict(lambda: {
                "sessions": 0, "metros": 0, "max_hr_sum": 0,
                "esqui": 0, "snow": 0, "lat": 0.0, "lon": 0.0
            })

            for i, s in enumerate(sessions):
                rng    = random.Random(f"{patient_id}-{i}")
                resort = _assign_resort(s["altitud"], rng)
                name   = resort["name"]

                density_lats.append(resort["lat"])
                density_lons.append(resort["lon"])
                density_z.append(max(1, s["metros"]) * max(1, s["max_hr"]) / 100)

                resort_agg[name]["sessions"] += 1
                resort_agg[name]["metros"]   += s["metros"]
                resort_agg[name]["max_hr_sum"] += s["max_hr"]
                resort_agg[name]["lat"] = resort["lat"]
                resort_agg[name]["lon"] = resort["lon"]
                if s["modalidad"] == "esqui":
                    resort_agg[name]["esqui"] += 1
                else:
                    resort_agg[name]["snow"] += 1

            fig = go.Figure()

            fig.add_trace(go.Densitymapbox(
                lat=density_lats, lon=density_lons, z=density_z,
                radius=40, colorscale="YlOrRd", showscale=False,
                hoverinfo="skip", name="Intensidad",
            ))

            for name, d in resort_agg.items():
                avg_hr = d["max_hr_sum"] / d["sessions"]
                size   = max(14, min(42, d["metros"] // 400 + 12))
                fig.add_trace(go.Scattermapbox(
                    lat=[d["lat"]], lon=[d["lon"]],
                    mode="markers+text",
                    marker=dict(size=size, color="white", opacity=0.88),
                    text=[name], textposition="top right",
                    textfont=dict(size=11, color="white"),
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        f"Sesiones: {d['sessions']}  (⛷️ {d['esqui']} · 🏂 {d['snow']})<br>"
                        f"Metros:  {d['metros']:,} m<br>"
                        f"FC Max media: {avg_hr:.0f} bpm"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                ))

            lats = [d["lat"] for d in resort_agg.values()]
            lons = [d["lon"] for d in resort_agg.values()]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            zoom = 4 if len(resort_agg) > 3 else 6

            fig.update_layout(
                mapbox=dict(style="open-street-map",
                            center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
                margin=dict(l=0, r=0, t=0, b=0),
                height=480,
                showlegend=False,
            )
            return fig