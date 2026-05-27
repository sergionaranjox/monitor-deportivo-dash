from dash import Input, Output, State, html, dcc, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import db, BADGES
from physiological_model import get_spo2_range
from logic_pdf import pdf_generator

class athlete:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def create_table(self, ex_type, user_id, age_limit):
        data = db.get_specific_history(user_id, ex_type)
        if not data: return dbc.Alert(f"Sin registros de {ex_type}.", color="light")
        
        # --- AÑADIDO: Columna Altitud en la tabla ---
        header = html.Thead(html.Tr([html.Th("Estado"), html.Th("Fecha"), html.Th("Altitud"), html.Th("Tiempo"), html.Th("FC Max"), html.Th("SpO2 Min")]))
        rows = []
        for row in data:
            # Índices: 0:fecha, 1:dur, 2:avg_hr, 3:max_hr, 4:min_hr, 5:avg_spo2, 6:min_spo2, 7:altitud_ejercicio
            max_hr, min_spo2, altitud = row[3], row[6], row[7]
            
            if min_spo2 < 90: status, row_class = "⚠️ HIPOXIA", "table-info"
            elif max_hr > age_limit: status, row_class = "⚠️ CARDIACO", "table-danger"
            else: status, row_class = "✅ OK", ""
            
            mins, secs = row[1] // 60, row[1] % 60
            rows.append(html.Tr([
                html.Td(status, className="fw-bold"), 
                html.Td(row[0]), 
                html.Td(f"{altitud}m"), # Mostramos la altitud
                html.Td(f"{mins}m {secs}s"), 
                html.Td(f"{max_hr} bpm"), 
                html.Td(f"{min_spo2} %"),
            ], className=row_class))
        return dbc.Table([header, html.Tbody(rows)], hover=True, bordered=True, size="sm")

    def start_callbacks(self):
        
        # 0. HOME DASHBOARD
        @self.app.callback(
            Output("home-stats-row", "children"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def update_home_stats(pathname, session):
            if pathname != "/app":
                return no_update
            if not session or not session.get("id"):
                return ""

            user_id = session.get("id")

            # Semáforo de última sesión
            status = db.get_last_health_status(user_id)
            if status == "danger":
                s_icon, s_text, s_color = "🚨", "Riesgo detectado", "danger"
            elif status == "warning":
                s_icon, s_text, s_color = "⚠️", "Atención", "warning"
            elif status == "ok":
                s_icon, s_text, s_color = "✅", "Todo bien", "success"
            else:
                s_icon, s_text, s_color = "🏔️", "Sin sesiones aún", "secondary"

            # Insignia y progreso
            total = db.get_total_metros(user_id)
            current_badge, next_badge = db.get_badge_info(total)
            if next_badge:
                pct = int((total - current_badge["metros"]) / (next_badge["metros"] - current_badge["metros"]) * 100)
                badge_extra = dbc.Progress(value=pct, color=next_badge["color"],
                                           style={"height": "7px"}, className="mt-2")
            else:
                badge_extra = html.P("🏆 ¡Nivel máximo!", className="small text-warning fw-bold mb-0 mt-1")

            # Última fatiga registrada
            hist = db.get_history(user_id)
            if hist:
                fatiga_val = hist[0][1]
                f_color = "danger" if fatiga_val >= 8 else ("warning" if fatiga_val >= 6 else "success")
                fatiga_body = [
                    html.H3(f"{fatiga_val}/10", className=f"fw-bold text-{f_color} mb-0"),
                    html.P("fatiga muscular · última entrada", className="small text-muted mb-0"),
                ]
            else:
                fatiga_body = [html.P("Sin entradas en el diario", className="small text-muted mb-0 mt-1")]

            # Objetivo mensual de metros
            monthly_goal = 10000
            monthly_metros, monthly_sessions = db.get_monthly_metros(user_id)
            pct_monthly = min(100, int(monthly_metros / monthly_goal * 100))
            month_color = "success" if pct_monthly >= 100 else ("warning" if pct_monthly >= 50 else "info")
            monthly_body = [
                html.H3(f"{monthly_metros:,}m", className="fw-bold mb-0",
                        style={"color": "var(--accent-dark)"}),
                html.P(f"{monthly_sessions} sesiones · meta {monthly_goal:,}m",
                       className="small text-muted mb-1"),
                dbc.Progress(value=pct_monthly, color=month_color,
                             style={"height": "6px"}, className="mt-1"),
            ]

            def stat_card(icon, label, body_content, color=None, outline=False):
                return dbc.Card([
                    dbc.CardBody([
                        html.Div(icon, style={"fontSize": "2rem", "lineHeight": "1"}),
                        html.P(label, className="small text-muted mb-1 mt-1"),
                        *body_content,
                    ], className="text-center py-2")
                ], className="border-0 shadow-sm h-100",
                   color=color, outline=outline)

            return dbc.Row([
                dbc.Col(stat_card(s_icon, "Última Sesión",
                                  [html.H6(s_text, className="fw-bold mb-0")],
                                  color=s_color, outline=True),
                        width=12, sm=6, lg=3, className="mb-3"),
                dbc.Col(stat_card(current_badge["icono"], "Mi Insignia",
                                  [html.H6(current_badge["nombre"], className="fw-bold mb-0"),
                                   badge_extra]),
                        width=12, sm=6, lg=3, className="mb-3"),
                dbc.Col(stat_card("😴", "Fatiga Muscular", fatiga_body),
                        width=12, sm=6, lg=3, className="mb-3"),
                dbc.Col(stat_card("🎯", "Objetivo Mensual", monthly_body),
                        width=12, sm=6, lg=3, className="mb-3"),
            ], justify="center", className="mb-2")

        # 0b. SECCIÓN ACWR + RESUMEN SEMANAL
        @self.app.callback(
            Output("home-acwr-section", "children"),
            Input("url", "pathname"),
            State("user_storage", "data"),
        )
        def update_home_acwr(pathname, session):
            if pathname != "/app":
                return no_update
            if not session or not session.get("id"):
                return ""

            user_id  = session.get("id")
            aw       = db.get_acwr(user_id)
            wk       = db.get_weekly_summary(user_id)
            acwr     = aw["acwr"]
            chronic  = aw["chronic_weekly"]
            this_m   = wk["this_metros"]
            this_s   = wk["this_sessions"]
            prev_m   = wk["prev_metros"]

            if acwr is None:
                acwr_color, acwr_label = "secondary", "Sin datos suficientes"
                rec = "Necesitas al menos 4 semanas de historial para calcular la carga."
            elif acwr > 1.5:
                acwr_color, acwr_label = "danger",  "Riesgo de Lesión"
                rec = "↓ Reduce la carga esta semana."
            elif acwr > 1.3:
                acwr_color, acwr_label = "warning", "Zona de Precaución"
                rec = "Modera la intensidad y prioriza recuperación."
            elif acwr >= 0.8:
                acwr_color, acwr_label = "success", "Zona Óptima"
                rec = "¡Carga equilibrada! Sigue así."
            else:
                acwr_color, acwr_label = "info",    "Carga Baja"
                rec = "↑ Aumenta progresivamente el volumen."

            acwr_str = str(acwr) if acwr is not None else "—"
            bar_val  = min(100, int((acwr or 0) / 2.0 * 100))

            if prev_m > 0:
                delta     = this_m - prev_m
                delta_str = f"{'▲' if delta >= 0 else '▼'} {abs(delta):,}m vs semana anterior"
                delta_col = "#22c55e" if delta >= 0 else "#ef4444"
            elif this_m > 0:
                delta_str, delta_col = "Primera semana con actividad", "var(--accent-dark)"
            else:
                delta_str, delta_col = "Sin actividad en las últimas 2 semanas", "gray"

            return dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P("⚡ ACWR · CARGA DE ENTRENAMIENTO",
                                   className="text-muted text-uppercase mb-2",
                                   style={"fontSize": ".7rem", "letterSpacing": ".07em"}),
                            dbc.Row([
                                dbc.Col([
                                    html.Span(acwr_str, style={
                                        "fontSize": "2.4rem", "fontWeight": "800",
                                        "fontFamily": "monospace",
                                        "color": f"var(--bs-{acwr_color})",
                                    }),
                                    html.Span(" ACWR", className="text-muted small ms-1"),
                                ], width="auto"),
                                dbc.Col([
                                    dbc.Badge(acwr_label, color=acwr_color,
                                              className="d-block mb-1"),
                                    html.Small(rec, className="text-muted"),
                                ], className="d-flex flex-column justify-content-center ps-2"),
                            ], className="g-1 align-items-center mb-2"),
                            dbc.Progress(value=bar_val, color=acwr_color,
                                         style={"height": "6px"}, className="mb-1"),
                            html.Div([
                                html.Small("0.0", className="text-muted",
                                           style={"fontSize": ".65rem"}),
                                html.Small("← Zona óptima 0.8 – 1.3 →",
                                           className="text-success d-block text-center",
                                           style={"fontSize": ".65rem", "flex": "1"}),
                                html.Small("2.0+", className="text-danger",
                                           style={"fontSize": ".65rem"}),
                            ], className="d-flex justify-content-between"),
                        ], width=12, md=7),

                        dbc.Col([
                            html.Hr(className="d-md-none my-2"),
                            html.P("ESTA SEMANA (7 DÍAS)",
                                   className="text-muted text-uppercase mb-1",
                                   style={"fontSize": ".7rem", "letterSpacing": ".07em"}),
                            html.H4(f"{this_m:,} m", className="fw-bold mb-0",
                                    style={"color": "var(--accent-dark)"}),
                            html.Small(
                                f"{this_s} sesión{'es' if this_s != 1 else ''} registradas",
                                className="text-muted d-block"),
                            html.Small(delta_str,
                                       style={"color": delta_col},
                                       className="fw-bold d-block mt-1"),
                            html.Hr(className="my-2", style={"borderColor": "#bae6fd"}),
                            html.Small(f"Carga crónica media: {chronic:,} m/sem (28 días)",
                                       className="text-muted"),
                        ], width=12, md=5),
                    ], align="center"),
                ], className="py-2 px-3"),
            ], className="border-0 shadow-sm")

        # 1. MODAL INTELIGENTE (Seguridad)
        @self.app.callback(
            Output("modal-missing-profile", "is_open"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def check_missing_profile(path, session):
            if path in ["/app/monitor", "/app/history"] and session and session.get("id"):
                info = db.get_user_info(session.get("id"))
                if info and (not info["age"] or not info["weight"] or not info["height"]): return True
                if not info: return True
            return False

        # 2. MONITOR EN REPOSO
        @self.app.callback(
            Output("monitor-rest-info", "children"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def update_monitor_rest(pathname, session):
            if pathname != "/app/monitor":
                return no_update
            if not session or not session.get("id"):
                return ""

            user_id   = session.get("id")
            user_info = db.get_user_info(user_id)
            age       = user_info["age"] if user_info and user_info["age"] else 0
            limit_hr  = (220 - age) if age > 0 else 170

            hist = db.get_exercise_history(user_id)
            if not hist:
                return html.Div([
                    html.Hr(className="my-3"),
                    dbc.Alert([
                        html.H6("🏔️ ¡Primera sesión!", className="fw-bold mb-1"),
                        html.P("Elige modalidad y altitud, luego pulsa INICIAR.", className="small mb-0"),
                    ], color="info", className="mb-0"),
                ])

            last = hist[0]
            # 0:date, 1:modalidad, 2:duration_sec, 3:avg_hr, 4:max_hr, 5:min_hr, 6:avg_spo2, 7:min_spo2, 8:altitud
            mins, secs = last[2] // 60, last[2] % 60
            hr_color   = "#dc2626" if last[4] > limit_hr else "#22c55e"
            spo2_color = "#dc2626" if last[7] < 90 else "#0ea5e9"
            modalidad_label = "⛷️ Esquí" if last[1] == "esqui" else "🏂 Snowboard"

            return html.Div([
                html.Hr(className="my-3"),
                html.P("Última sesión", className="small text-muted text-uppercase mb-2",
                       style={"letterSpacing": ".06em", "fontSize": ".7rem"}),
                dbc.Row([
                    dbc.Col([
                        html.P(modalidad_label, className="fw-bold mb-0 small"),
                        html.P(f"{last[8]}m altitud", className="text-muted small mb-0"),
                    ], width=6),
                    dbc.Col([
                        html.P(f"{mins}m {secs}s", className="fw-bold mb-0 small"),
                        html.P(last[0][:10], className="text-muted small mb-0"),
                    ], width=6),
                ], className="mb-2 g-1"),
                dbc.Row([
                    dbc.Col(html.P(f"❤️ FC máx: {last[4]} bpm", className="small mb-0 fw-bold",
                                   style={"color": hr_color}), width=6),
                    dbc.Col(html.P(f"🫁 SpO₂: {last[7]}%", className="small mb-0 fw-bold",
                                   style={"color": spo2_color}), width=6),
                ], className="mb-2 g-1"),
                html.Hr(className="my-2"),
                html.P("Tus límites seguros", className="small text-muted text-uppercase mb-1",
                       style={"letterSpacing": ".06em", "fontSize": ".7rem"}),
                html.P(f"FC máx teórica: {limit_hr} bpm", className="small mb-1"),
                html.P("SpO₂ alerta: < 90%", className="small mb-0"),
            ])

        # 3. HISTORIAL DEL ATLETA
        @self.app.callback(
            Output("out-quest", "children"),
            Output("table-container", "children"),
            Output("patient-chart", "figure"),
            Output("exercises-table-container", "children"),
            Output("exercises-chart", "figure"),
            Output("hr-zones-chart", "figure"),
            Input("btn-send-quest", "n_clicks"),
            Input("url", "pathname"),
            Input("manual-refresh-trigger", "data"),
            State("q-fatiga", "value"),
            State("q-rpe", "value"),
            State("q-sueno", "value"),
            State("q-altitud", "value"),
            State("user_storage", "data")
        )
        def update_history_view(n_clicks, pathname, _refresh, fatiga, rpe, sueno, altitud, session):
            _empty = go.Figure()
            if pathname != "/app/history":
                return no_update, no_update, no_update, no_update, no_update, no_update
            if not session or not session.get("id"):
                return dbc.Alert("Error"), "", go.Figure(), "", go.Figure(), _empty

            user_id = session.get("id")
            msg, ctx, trigger_id = "", callback_context, None
            if ctx.triggered: trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if trigger_id == "btn-send-quest":
                if sueno is None: msg = dbc.Alert("Introduce horas de sueño", color="warning")
                elif float(sueno) < 0: msg = dbc.Alert("⚠️ No puedes dormir tiempo negativo", color="danger")
                else:
                    db.save_quest(user_id, fatiga, rpe, sueno, altitud or 0)
                    msg = dbc.Alert("✅ Guardado", color="success")

            hist = db.get_history(user_id)
            rows = []
            if hist:
                for r in hist:
                    style = {"color": "red"} if (r[1]>=8) else {}
                    alt_text = f"{r[4]}m" if r[4] else "—"
                    rows.append(html.Tr([html.Td(r[0][:10]), html.Td(r[1], style=style), html.Td(r[2]), html.Td(r[3]), html.Td(alt_text)]))
            table_diary = dbc.Table([
                html.Thead(html.Tr([html.Th("Fecha"), html.Th("Fat"), html.Th("RPE"), html.Th("Sueño"), html.Th("Alt.")])),
                html.Tbody(rows)
            ], size="sm", bordered=True)
            
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

            # --- CAMBIO: Sustituimos las tablas antiguas por las modalidades de nieve ---
            t_esqui = self.create_table("esqui", user_id, limit_hr)
            t_snow = self.create_table("snowboard", user_id, limit_hr)
            tabs_ex = dbc.Tabs([dbc.Tab(t_esqui, label="⛷️ Esquí Alpino"), dbc.Tab(t_snow, label="🏂 Snowboard")])
            
            ex_hist = db.get_exercise_history(user_id)
            fig_ex = go.Figure()
            if ex_hist:
                ex_rev   = ex_hist[::-1]
                dates_ex = [x[0] for x in ex_rev]
                fig_ex.add_trace(go.Bar(
                    x=dates_ex, y=[x[4] for x in ex_rev],
                    name='FC Max', marker_color='#fca5a5', yaxis='y1'
                ))
                fig_ex.add_trace(go.Scatter(
                    x=dates_ex, y=[x[7] for x in ex_rev],
                    name='SpO2 Min %', line=dict(color='#0ea5e9', width=2),
                    mode='lines+markers', marker=dict(size=6), yaxis='y2'
                ))
                fig_ex.update_layout(
                    template="plotly_white", height=300,
                    margin=dict(l=40, r=50, t=10, b=40),
                    yaxis=dict(title="FC Max (bpm)", side="left"),
                    yaxis2=dict(title="SpO2 %", overlaying="y", side="right",
                                range=[80, 100], showgrid=False),
                    legend=dict(orientation="h", y=1.1),
                    autosize=True,
                )
            else:
                fig_ex.update_layout(template="plotly_white", xaxis={"visible":False}, yaxis={"visible":False})

            # ── Zonas de FC (últimas 10 sesiones) ────────────────────────────
            def _tri_cdf(x, lo, mode, hi):
                mode = max(lo + 1e-6, min(hi - 1e-6, float(mode)))
                if x <= lo: return 0.0
                if x >= hi: return 1.0
                if x <= mode:
                    return (x - lo) ** 2 / ((hi - lo) * (mode - lo))
                return 1.0 - (hi - x) ** 2 / ((hi - lo) * (hi - mode))

            fig_zones = go.Figure()
            sessions10 = (ex_hist[:10])[::-1] if ex_hist else []
            if sessions10:
                zone_names  = ["Z1 Recup.", "Z2 Base", "Z3 Aeróbico", "Z4 Umbral", "Z5 Máx"]
                zone_colors = ["#94a3b8", "#22c55e", "#a3e635", "#f59e0b", "#ef4444"]
                pct_matrix  = [[] for _ in range(5)]
                labels_z    = []

                for s in sessions10:
                    min_h = s[5] if s[5] else max(40, s[3] - 20)
                    avg_h, max_h = float(s[3]), float(s[4])
                    thresholds = [
                        (0,                   0.60 * limit_hr),
                        (0.60 * limit_hr,     0.70 * limit_hr),
                        (0.70 * limit_hr,     0.80 * limit_hr),
                        (0.80 * limit_hr,     0.90 * limit_hr),
                        (0.90 * limit_hr,     300.0),
                    ]
                    raw = []
                    for z_lo, z_hi in thresholds:
                        hi_c = _tri_cdf(min(z_hi, max_h), min_h, avg_h, max_h)
                        lo_c = _tri_cdf(max(z_lo, min_h), min_h, avg_h, max_h)
                        raw.append(max(0.0, hi_c - lo_c) * 100)
                    total = sum(raw) or 1
                    raw   = [round(v / total * 100, 1) for v in raw]
                    for i, v in enumerate(raw):
                        pct_matrix[i].append(v)
                    mod = "⛷️" if s[1] == "esqui" else "🏂"
                    labels_z.append(f"{mod} {s[0][:10]}")

                for name, color, data in zip(zone_names, zone_colors, pct_matrix):
                    fig_zones.add_trace(go.Bar(
                        name=name, x=labels_z, y=data,
                        marker_color=color,
                        text=[f"{v:.0f}%" for v in data],
                        textposition="inside",
                        textfont=dict(size=9, color="white"),
                    ))
                fig_zones.update_layout(
                    barmode="stack", template="plotly_white", height=260,
                    margin=dict(l=20, r=20, t=10, b=70),
                    legend=dict(orientation="h", y=1.08, font=dict(size=10)),
                    xaxis=dict(tickfont=dict(size=9)),
                    yaxis=dict(title="% tiempo", range=[0, 100]),
                )
            else:
                fig_zones.update_layout(
                    template="plotly_white",
                    xaxis={"visible": False}, yaxis={"visible": False},
                )

            return msg, table_diary, fig_d, tabs_ex, fig_ex, fig_zones

        # 3. PERFIL
        @self.app.callback(
            Output("out-profile", "children"),
            Output("profile-summary", "children"),
            Output("prof-age", "value"),
            Output("prof-weight", "value"),
            Output("prof-height", "value"),
            Output("onboarding-overlay", "style"),
            Output("profile-card-spotlight", "className"),
            Input("btn-save-profile", "n_clicks"),
            Input("url", "pathname"),
            State("prof-age", "value"),
            State("prof-weight", "value"),
            State("prof-height", "value"),
            State("user_storage", "data")
        )
        def update_profile_view(n_clicks, pathname, age, weight, height, session):
            _hidden  = {"display": "none"}
            _visible = {"display": "flex"}
            if pathname != "/app/profile":
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update
            if not session or not session.get("id"):
                return "", "", "", "", "", _hidden, ""
            user_id = session.get("id")
            ctx, trigger_id = callback_context, None
            if ctx.triggered: trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            msg = ""
            is_tutorial = db.is_first_login(user_id)

            if trigger_id == "btn-save-profile":
                if age and weight and height:
                    if float(age) <= 0 or float(weight) <= 0 or float(height) <= 0:
                        msg = dbc.Alert("Valores positivos por favor", color="warning")
                    elif db.update_profile(user_id, age, weight, height):
                        if is_tutorial:
                            db.mark_profile_complete(user_id)
                            is_tutorial = False
                        msg = dbc.Alert("✅ ¡Perfil completado! Ya puedes usar todas las funciones.", color="success")
                    else:
                        msg = dbc.Alert("Error al guardar", color="danger")
                else:
                    msg = dbc.Alert("Rellena todos los campos", color="warning")

            user_info = db.get_user_info(user_id)
            val_age = user_info["age"] if user_info else ""
            val_w   = user_info["weight"] if user_info else ""
            val_h   = user_info["height"] if user_info else ""
            fc_text = f"{220 - val_age} bpm" if val_age else "Pendiente"
            imc_text = "--"
            if val_w and val_h:
                imc = val_w / ((val_h / 100) ** 2)
                imc_text = f"{imc:.2f}"
            summary = [
                html.H4(f"IMC: {imc_text}", className="text-center"),
                html.Hr(),
                html.H4(f"FC Max: {fc_text}", className="text-center text-danger"),
            ]

            overlay_style    = _visible if is_tutorial else _hidden
            spotlight_class  = "spotlight-active" if is_tutorial else ""
            return msg, summary, val_age, val_w, val_h, overlay_style, spotlight_class

        # 3b. CERRAR TUTORIAL
        @self.app.callback(
            Output("onboarding-overlay", "style", allow_duplicate=True),
            Output("profile-card-spotlight", "className", allow_duplicate=True),
            Input("btn-dismiss-onboarding", "n_clicks"),
            State("user_storage", "data"),
            prevent_initial_call=True
        )
        def dismiss_onboarding(n_clicks, session):
            if session and session.get("id"):
                db.mark_profile_complete(session["id"])
            return {"display": "none"}, ""

        # 4. CALCULADORA DE RIESGO PRE-SESIÓN
        @self.app.callback(
            Output("risk-calculator", "children"),
            Input("url", "pathname"),
            Input("altitud-slider", "value"),
            State("user_storage", "data"),
        )
        def update_risk_calculator(pathname, altitud, session):
            if pathname != "/app/monitor":
                return no_update
            if not session or not session.get("id"):
                return ""

            alt = altitud if altitud else 2000
            spo2_lo, spo2_hi = get_spo2_range(alt)
            user_id = session.get("id")
            hist = db.get_history(user_id)

            fatiga = hist[0][1] if hist else 5
            sueno  = hist[0][3] if hist else 7
            sueno  = sueno if sueno is not None else 7

            score = 0
            if spo2_lo < 88:   score += 4
            elif spo2_lo < 92: score += 2
            elif spo2_lo < 95: score += 1

            if fatiga >= 8:   score += 3
            elif fatiga >= 6: score += 2
            elif fatiga >= 4: score += 1

            if sueno < 4:   score += 3
            elif sueno < 6: score += 2
            elif sueno < 7: score += 1

            if score >= 7:
                icon, level, color = "🔴", "RIESGO CRÍTICO", "danger"
                rec = "Se recomienda no salir a pista hoy."
            elif score >= 5:
                icon, level, color = "🟡", "RIESGO ALTO", "warning"
                rec = "Precaución. Monitoriza constantemente."
            elif score >= 3:
                icon, level, color = "🔵", "RIESGO MODERADO", "info"
                rec = "Aceptable. Mantén el ritmo controlado."
            else:
                icon, level, color = "🟢", "RIESGO BAJO", "success"
                rec = "¡Condiciones óptimas para descender!"

            no_data = " (sin diario)" if not hist else ""
            return dbc.Alert([
                html.Div([
                    html.Span(icon, style={"fontSize": "1.3rem"}),
                    html.Span(f"  {level}", className="fw-bold ms-1", style={"fontSize": ".88rem"}),
                ], className="d-flex align-items-center mb-1"),
                html.Small([
                    f"Altitud: {alt}m · SpO₂ {spo2_lo}–{spo2_hi}% · ",
                    f"Fatiga: {fatiga}/10 · Sueño: {sueno}h{no_data}"
                ], className="text-muted d-block"),
                html.Small(rec, className="d-block mt-1 fw-bold"),
            ], color=color, className="mt-2 mb-0 py-2 px-3 small")

        # 5. GRÁFICA DE ACLIMATACIÓN
        @self.app.callback(
            Output("aclimatacion-chart", "figure"),
            Input("url", "pathname"),
            State("user_storage", "data"),
        )
        def update_aclimatacion(pathname, session):
            if pathname != "/app/history":
                return no_update
            fig = go.Figure()
            if not session or not session.get("id"):
                return fig

            user_id = session.get("id")
            ex_hist = db.get_exercise_history(user_id)
            if not ex_hist:
                fig.update_layout(template="plotly_white",
                                  xaxis={"visible": False}, yaxis={"visible": False},
                                  annotations=[{"text": "Sin sesiones registradas", "showarrow": False,
                                                "font": {"color": "gray"}}])
                return fig

            ex_rev  = ex_hist[::-1]
            dates   = [x[0][:10] for x in ex_rev]
            spo2min = [x[7] for x in ex_rev]
            altitud = [x[8] for x in ex_rev]

            fig.add_trace(go.Scatter(
                x=dates, y=spo2min, name="SpO₂ Mín %",
                line=dict(color="#0ea5e9", width=2),
                mode="lines+markers",
                marker=dict(size=8, color=spo2min,
                            colorscale=[[0, "#ef4444"], [0.5, "#f59e0b"], [1.0, "#22c55e"]],
                            cmin=85, cmax=100, showscale=False),
                fill="tozeroy", fillcolor="rgba(14,165,233,0.07)",
                yaxis="y1",
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=altitud, name="Altitud (m)",
                line=dict(color="#94a3b8", width=1.5, dash="dot"),
                mode="lines", yaxis="y2",
            ))
            if dates:
                fig.add_shape(type="line",
                              x0=dates[0], x1=dates[-1], y0=90, y1=90,
                              line=dict(color="#ef4444", dash="dash", width=1.5), yref="y1")
                fig.add_annotation(x=dates[-1], y=90, yref="y1", xref="x",
                                   text="Umbral 90%", showarrow=False,
                                   font={"color": "#ef4444", "size": 10},
                                   xanchor="right")
            fig.update_layout(
                template="plotly_white", height=350,
                margin=dict(l=50, r=60, t=30, b=50),
                yaxis=dict(title="SpO₂ Mín (%)", range=[80, 100], side="left"),
                yaxis2=dict(title="Altitud (m)", overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", y=1.12),
            )
            return fig

        # 6. CALENDARIO DE ACTIVIDAD
        @self.app.callback(
            Output("activity-calendar", "figure"),
            Input("url", "pathname"),
            State("user_storage", "data"),
        )
        def update_activity_calendar(pathname, session):
            if pathname != "/app/history":
                return no_update
            fig = go.Figure()
            empty_layout = dict(
                template="plotly_white", height=220,
                margin=dict(l=50, r=10, t=10, b=10),
                xaxis={"visible": False}, yaxis={"visible": False},
            )
            if not session or not session.get("id"):
                fig.update_layout(**empty_layout)
                return fig

            user_id = session.get("id")
            raw = db.get_activity_by_day(user_id, 91)
            if not raw:
                fig.update_layout(**empty_layout,
                    annotations=[{"text": "Sin actividad en los últimos 90 días",
                                  "showarrow": False, "font": {"color": "gray"}}])
                return fig

            activity = {r[0]: r[1] for r in raw}
            today = datetime.now().date()
            start = today - timedelta(days=90)

            # Align start to the Monday of that week
            start -= timedelta(days=start.weekday())

            # Build week columns
            weeks = []
            d = start
            while d <= today + timedelta(days=6 - today.weekday()):
                week_col = []
                for _ in range(7):
                    week_col.append(d)
                    d += timedelta(days=1)
                weeks.append(week_col)

            day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            z = [[None] * len(weeks) for _ in range(7)]
            text = [[""] * len(weeks) for _ in range(7)]

            for wi, week in enumerate(weeks):
                for wd, day in enumerate(week):
                    if day > today:
                        continue
                    metros = activity.get(day.isoformat(), 0)
                    z[wd][wi] = metros
                    text[wd][wi] = (f"{day.strftime('%d/%m')}: {metros:,}m"
                                    if metros > 0 else day.strftime("%d/%m"))

            fig.add_trace(go.Heatmap(
                z=z, text=text,
                hovertemplate="%{text}<extra></extra>",
                colorscale=[[0, "#eaf3f9"], [0.001, "#bae6fd"], [0.3, "#38bdf8"], [1.0, "#0369a1"]],
                showscale=False,
                xgap=3, ygap=3, zmin=0,
            ))
            fig.update_layout(
                height=220,
                margin=dict(l=40, r=10, t=10, b=10),
                yaxis=dict(ticktext=day_names, tickvals=list(range(7)),
                           tickmode="array", autorange="reversed"),
                xaxis=dict(visible=False),
                template="plotly_white",
            )
            return fig

        # 7. GUARDAR SESIÓN MANUAL
        @self.app.callback(
            Output("out-manual-session", "children"),
            Output("manual-refresh-trigger", "data"),
            Input("btn-save-manual-session", "n_clicks"),
            State("manual-date",     "value"),
            State("manual-modalidad","value"),
            State("manual-altitud",  "value"),
            State("manual-duracion", "value"),
            State("manual-metros",   "value"),
            State("manual-avg-hr",   "value"),
            State("manual-max-hr",   "value"),
            State("manual-avg-spo2", "value"),
            State("manual-min-spo2", "value"),
            State("user_storage",    "data"),
            prevent_initial_call=True,
        )
        def save_manual_session(n, date, modalidad, altitud, duracion, metros,
                                avg_hr, max_hr, avg_spo2, min_spo2, session):
            if not session or not session.get("id"):
                return dbc.Alert("Error de sesión", color="danger"), no_update

            if not all([date, modalidad, altitud, duracion, avg_hr, max_hr, avg_spo2, min_spo2]):
                return dbc.Alert("Rellena todos los campos obligatorios", color="warning",
                                 duration=4000), no_update

            user_id      = session.get("id")
            duration_sec = int(float(duracion)) * 60
            metros_val   = int(float(metros)) if metros else duration_sec * 2
            min_hr       = max(40, int(float(avg_hr)) - 15)
            date_str     = f"{date} 12:00:00"

            ok = db.save_exercise_manual(
                user_id, modalidad,
                duration_sec, int(float(avg_hr)), int(float(max_hr)), min_hr,
                int(float(avg_spo2)), int(float(min_spo2)),
                int(float(altitud)), metros_val, date_str
            )
            if ok:
                return dbc.Alert("✅ Sesión registrada. Revisa la pestaña Historial de Nieve.",
                                 color="success", duration=5000), n
            return dbc.Alert("Error al guardar la sesión", color="danger"), no_update

        # 8. PDF DEL ATLETA
        @self.app.callback(
            Output("download-athlete-pdf", "data"),
            Input("btn-download-athlete-pdf", "n_clicks"),
            State("user_storage", "data"),
            prevent_initial_call=True,
        )
        def download_athlete_pdf(n_clicks, session):
            if not session or not session.get("id"):
                return no_update
            user_id   = session.get("id")
            user_info = db.get_user_info(user_id)
            name      = user_info["name"] if user_info else f"Atleta_{user_id}"
            date_str  = datetime.now().strftime("%Y-%m-%d")
            pdf_bytes = pdf_generator.create_report(user_id)
            return dcc.send_bytes(pdf_bytes, filename=f"MiInforme_{name}_{date_str}.pdf")

        # 9. TENDENCIA DE RENDIMIENTO
        @self.app.callback(
            Output("tendency-chart", "figure"),
            Input("url", "pathname"),
            Input("manual-refresh-trigger", "data"),
            State("user_storage", "data"),
        )
        def update_tendency_chart(pathname, _r, session):
            if pathname != "/app/history":
                return no_update
            fig = go.Figure()
            empty = dict(template="plotly_white", height=280,
                         margin=dict(l=40, r=20, t=10, b=40),
                         xaxis={"visible": False}, yaxis={"visible": False})
            if not session or not session.get("id"):
                fig.update_layout(**empty)
                return fig
            ex_hist = db.get_exercise_history(session.get("id"))
            if not ex_hist:
                fig.update_layout(**empty, annotations=[{
                    "text": "Sin sesiones registradas", "showarrow": False,
                    "font": {"color": "gray"}}])
                return fig

            ex_rev = ex_hist[::-1]
            bands = {
                "< 1500m":    {"range": (0,    1499), "color": "#94a3b8"},
                "1500–2000m": {"range": (1500, 1999), "color": "#22c55e"},
                "2000–2500m": {"range": (2000, 2499), "color": "#0ea5e9"},
                "2500–3000m": {"range": (2500, 2999), "color": "#f59e0b"},
                "> 3000m":    {"range": (3000, 9999), "color": "#ef4444"},
            }
            any_trace = False
            for band_name, bd in bands.items():
                lo, hi = bd["range"]
                pts = [(x[0][:10], x[3]) for x in ex_rev if lo <= x[8] <= hi]
                if len(pts) < 2:
                    continue
                fig.add_trace(go.Scatter(
                    x=[p[0] for p in pts], y=[p[1] for p in pts],
                    mode="lines+markers", name=band_name,
                    line=dict(color=bd["color"], width=2),
                    marker=dict(size=8),
                ))
                any_trace = True

            if not any_trace:
                fig.update_layout(**empty, annotations=[{
                    "text": "Se necesitan al menos 2 sesiones en la misma banda de altitud",
                    "showarrow": False, "font": {"color": "gray"}}])
                return fig

            fig.update_layout(
                template="plotly_white", height=280,
                margin=dict(l=50, r=20, t=10, b=40),
                yaxis=dict(title="FC Media (bpm)"),
                xaxis=dict(title="Fecha"),
                legend=dict(orientation="h", y=1.15, font=dict(size=10)),
            )
            return fig

        # 10. HISTORIAL DE ACWR SEMANAL
        @self.app.callback(
            Output("acwr-history-chart", "figure"),
            Input("url", "pathname"),
            Input("manual-refresh-trigger", "data"),
            State("user_storage", "data"),
        )
        def update_acwr_history(pathname, _r, session):
            if pathname != "/app/history":
                return no_update
            fig = go.Figure()
            empty = dict(template="plotly_white", height=320,
                         margin=dict(l=50, r=20, t=20, b=40),
                         xaxis={"visible": False}, yaxis={"visible": False})
            if not session or not session.get("id"):
                fig.update_layout(**empty)
                return fig

            history = db.get_acwr_history(session.get("id"))
            weeks_x = [h["week"] for h in history]
            acwrs_y = [h["acwr"] for h in history]

            if not any(a is not None for a in acwrs_y):
                fig.update_layout(**empty, annotations=[{
                    "text": "Sin datos suficientes (se necesitan sesiones en las últimas 12 semanas)",
                    "showarrow": False, "font": {"color": "gray"}}])
                return fig

            marker_colors = []
            for a in acwrs_y:
                if a is None:        marker_colors.append("gray")
                elif a > 1.5:        marker_colors.append("#ef4444")
                elif a > 1.3:        marker_colors.append("#f59e0b")
                elif a >= 0.8:       marker_colors.append("#22c55e")
                else:                marker_colors.append("#0ea5e9")

            fig.add_trace(go.Scatter(
                x=weeks_x, y=acwrs_y,
                mode="lines+markers",
                line=dict(color="#38bdf8", width=2),
                marker=dict(size=11, color=marker_colors,
                            line=dict(width=1.5, color="white")),
                name="ACWR semanal",
                connectgaps=False,
            ))

            fig.add_hrect(y0=0.8, y1=1.3,
                          fillcolor="rgba(34,197,94,0.08)", line_width=0,
                          annotation_text="Zona óptima",
                          annotation_position="top left",
                          annotation_font_size=10,
                          annotation_font_color="#22c55e")
            fig.add_hline(y=1.5, line=dict(color="#ef4444", dash="dash", width=1.2))
            fig.add_hline(y=0.8, line=dict(color="#0ea5e9", dash="dash", width=1.2))

            fig.update_layout(
                template="plotly_white", height=320,
                margin=dict(l=50, r=20, t=30, b=40),
                yaxis=dict(title="ACWR", range=[0, max(2.0, max((a for a in acwrs_y if a is not None), default=2.0))]),
                xaxis=dict(title="Semana"),
                legend=dict(orientation="h", y=1.1),
            )
            return fig

        # 11. POBLAR DROPDOWNS DE COMPARACIÓN
        @self.app.callback(
            Output("compare-sel-1", "options"),
            Output("compare-sel-2", "options"),
            Input("url", "pathname"),
            Input("manual-refresh-trigger", "data"),
            State("user_storage", "data"),
        )
        def populate_compare_dropdowns(pathname, _r, session):
            if pathname != "/app/history":
                return no_update, no_update
            if not session or not session.get("id"):
                return [], []
            ex_hist = db.get_exercise_history(session.get("id"))
            opts = []
            for i, row in enumerate(ex_hist):
                mod   = "⛷️" if row[1] == "esqui" else "🏂"
                label = f"{mod} {row[0][:10]} · {row[8]}m · FC máx {row[4]} bpm"
                opts.append({"label": label, "value": i})
            return opts, opts

        # 12. COMPARACIÓN DE SESIONES
        @self.app.callback(
            Output("compare-result", "children"),
            Input("compare-sel-1", "value"),
            Input("compare-sel-2", "value"),
            State("user_storage", "data"),
            prevent_initial_call=True,
        )
        def update_session_comparison(idx1, idx2, session):
            if idx1 is None or idx2 is None:
                return dbc.Alert("Selecciona las dos sesiones para ver la comparación.", color="info")
            if not session or not session.get("id"):
                return ""
            ex_hist = db.get_exercise_history(session.get("id"))
            if idx1 >= len(ex_hist) or idx2 >= len(ex_hist):
                return dbc.Alert("Error: sesión no encontrada.", color="warning")

            s1, s2 = ex_hist[idx1], ex_hist[idx2]

            def session_card(s, label):
                mod       = "⛷️ Esquí Alpino" if s[1] == "esqui" else "🏂 Snowboard"
                mins, sec = s[2] // 60, s[2] % 60
                return dbc.Card([
                    dbc.CardHeader(label, className="fw-bold small"),
                    dbc.CardBody([
                        html.P(f"{mod}", className="fw-bold mb-1"),
                        html.P(f"📅 {s[0][:10]}", className="small mb-1"),
                        html.P(f"⛰️ {s[8]} m altitud", className="small mb-1"),
                        html.P(f"⏱️ {mins}m {sec}s", className="small mb-2"),
                        html.Hr(className="my-2"),
                        html.P(f"❤️ FC Media: {s[3]} bpm", className="small mb-1"),
                        html.P(f"❤️ FC Máx: {s[4]} bpm", className="small fw-bold mb-1"),
                        html.P(f"❤️ FC Mín: {s[5]} bpm", className="small mb-2"),
                        html.P(f"🫁 SpO₂ Media: {s[6]} %", className="small mb-1"),
                        html.P(f"🫁 SpO₂ Mín: {s[7]} %", className="small fw-bold mb-0"),
                    ], className="py-2"),
                ], className="h-100 border-0 shadow-sm")

            metrics = ["FC Media", "FC Máx", "SpO₂ Med", "SpO₂ Mín"]
            vals1   = [s1[3], s1[4], s1[6], s1[7]]
            vals2   = [s2[3], s2[4], s2[6], s2[7]]
            fig = go.Figure()
            fig.add_trace(go.Bar(name=f"A · {s1[0][:10]}", x=metrics, y=vals1,
                                 marker_color="#0ea5e9"))
            fig.add_trace(go.Bar(name=f"B · {s2[0][:10]}", x=metrics, y=vals2,
                                 marker_color="#f97316"))
            fig.update_layout(
                barmode="group", template="plotly_white", height=260,
                margin=dict(l=20, r=20, t=10, b=20),
                legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            )
            return html.Div([
                dbc.Row([
                    dbc.Col(session_card(s1, "Sesión A"), width=6),
                    dbc.Col(session_card(s2, "Sesión B"), width=6),
                ], className="mb-3 g-2"),
                dcc.Graph(figure=fig, config={"staticPlot": True}),
            ])

        # 13. RANKING
        @self.app.callback(
            Output("ranking-my-badge", "children"),
            Output("ranking-all-badges", "children"),
            Output("ranking-table", "children"),
            Input("url", "pathname"),
            State("user_storage", "data")
        )
        def update_ranking(pathname, session):
            if pathname != "/app/ranking":
                return no_update, no_update, no_update
            if not session or not session.get("id"):
                return "", "", ""

            user_id = session.get("id")
            total = db.get_total_metros(user_id)
            current_badge, next_badge = db.get_badge_info(total)

            # --- Mi insignia ---
            if next_badge:
                progress = int((total - current_badge["metros"]) / (next_badge["metros"] - current_badge["metros"]) * 100)
                remaining = next_badge["metros"] - total
                progress_section = html.Div([
                    html.P(f"Siguiente: {next_badge['icono']} {next_badge['nombre']} ({next_badge['metros']:,}m)", className="small text-muted mb-1"),
                    dbc.Progress(value=progress, color=next_badge["color"], className="mb-1", style={"height": "12px"}),
                    html.P(f"Faltan {remaining:,}m", className="small text-muted")
                ])
            else:
                progress_section = html.P("🏆 ¡Has alcanzado el nivel máximo!", className="text-warning fw-bold")

            my_badge_content = html.Div([
                html.Div(current_badge["icono"], style={"fontSize": "72px", "lineHeight": "1"}),
                html.H4(current_badge["nombre"], className=f"text-{current_badge['color']} fw-bold mt-2"),
                html.H5(f"{total:,} metros", className="text-dark"),
                html.Hr(),
                progress_section
            ])

            # --- Lista de todas las insignias ---
            all_badges_rows = []
            for badge in BADGES:
                unlocked = total >= badge["metros"]
                style = {} if unlocked else {"opacity": "0.35", "filter": "grayscale(100%)"}
                check = "✅" if unlocked else "🔒"
                all_badges_rows.append(
                    dbc.ListGroupItem([
                        html.Span(badge["icono"], style={"fontSize": "24px", "marginRight": "10px"}),
                        html.Span(badge["nombre"], className="fw-bold"),
                        html.Span(f" — {badge['metros']:,}m", className="text-muted small"),
                        html.Span(check, className="float-end")
                    ], style=style, color=badge["color"] if unlocked and badge["metros"] > 0 else None,
                    className="d-flex align-items-center")
                )
            all_badges = dbc.ListGroup(all_badges_rows, flush=True)

            # --- Tabla de ranking global ---
            ranking_data = db.get_ranking()
            medals = ["🥇", "🥈", "🥉"]
            rows = []
            for i, entry in enumerate(ranking_data):
                pos_icon = medals[i] if i < 3 else f"#{i+1}"
                badge_for_user, _ = db.get_badge_info(entry["metros"])
                is_me = entry["id"] == user_id
                rows.append(html.Tr([
                    html.Td(pos_icon, className="text-center fw-bold fs-5"),
                    html.Td([
                        html.Span(entry["name"]),
                        html.Span(" (tú)", className="text-primary fw-bold small") if is_me else ""
                    ]),
                    html.Td(f"{badge_for_user['icono']} {badge_for_user['nombre']}"),
                    html.Td(f"{entry['metros']:,} m", className="fw-bold text-end"),
                ], className="table-primary" if is_me else ""))

            if not rows:
                table = dbc.Alert("Aún no hay atletas con sesiones registradas.", color="light")
            else:
                header = html.Thead(html.Tr([
                    html.Th("#", className="text-center"), html.Th("Atleta"),
                    html.Th("Insignia"), html.Th("Metros", className="text-end")
                ]))
                table = dbc.Table([header, html.Tbody(rows)], hover=True, bordered=False, striped=True, size="sm", className="mb-0")

            return my_badge_content, all_badges, table
