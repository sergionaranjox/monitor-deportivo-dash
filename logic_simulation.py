from dash import Input, Output, State, html, no_update, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from database import db, BADGES
from physiological_model import (
    calculate_session_params,
    finalize_session_biometrics,
    hr_at_elapsed,
    generate_ecg_window,
    get_spo2_range,
    preload_template,
)


class simulation:
    def __init__(self, app):
        self.app = app
        # Pre-load ECG template at startup (downloads from PhysioNet or uses cache)
        preload_template()
        self.start_callbacks()

    def start_callbacks(self):

        @self.app.callback(
            # ── outputs ──────────────────────────────────────────────────────
            Output("clock-interval",          "disabled"),
            Output("clock-interval",          "n_intervals"),
            Output("btn-start-ex",            "children"),
            Output("btn-start-ex",            "color"),
            Output("is-running-store",        "data"),
            Output("save-confirmation-msg",   "children"),
            Output("locked-ex-store",         "data"),
            Output("session-biometrics-store","data"),   # ← pre-calculated HR
            # ── inputs / states ──────────────────────────────────────────────
            Input("btn-start-ex",  "n_clicks"),
            Input("ex-type",       "value"),
            State("is-running-store",         "data"),
            State("clock-interval",           "n_intervals"),
            State("user_storage",             "data"),
            State("locked-ex-store",          "data"),
            State("altitud-slider",           "value"),
            State("session-biometrics-store", "data"),   # ← stored HR at session start
            prevent_initial_call=True
        )
        def master_control(n_clicks, ex_input_value, is_running, n_intervals,
                           session, locked_ex, altitud, stored_biometrics):

            ctx        = callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            should_save = (trigger_id == "btn-start-ex" and is_running) or \
                          (trigger_id == "ex-type"      and is_running)

            # ── SESSION END: save and reset ───────────────────────────────────
            if should_save:
                duration_sec     = int(n_intervals * 0.5) if n_intervals else 0
                exercise_to_save = locked_ex if locked_ex else ex_input_value
                altitud_segura   = altitud if altitud else 1000

                if session and session.get("id"):
                    user_id   = session["id"]
                    user_info = db.get_user_info(user_id)
                    age       = user_info["age"] if user_info and user_info["age"] else 0
                    limit_hr  = (220 - age) if age > 0 else 170

                    if duration_sec > 0:
                        # Use the biometrics pre-calculated at session start so
                        # the max_hr in the summary matches the ECG peak.
                        if stored_biometrics:
                            sim_avg_hr, sim_max_hr, sim_min_hr, sim_avg_spo2, sim_min_spo2 = \
                                finalize_session_biometrics(
                                    stored_biometrics, altitud_segura, duration_sec
                                )
                        else:
                            # Fallback: recalculate (should not normally happen)
                            params = calculate_session_params(
                                exercise_to_save, altitud_segura, age
                            )
                            sim_avg_hr, sim_max_hr, sim_min_hr, sim_avg_spo2, sim_min_spo2 = \
                                finalize_session_biometrics(params, altitud_segura, duration_sec)

                        metros_factor = 2.5 if exercise_to_save == "esqui" else 2.0
                        metros_sesion = int(duration_sec * metros_factor)
                        prev_total    = db.get_total_metros(user_id)

                        if db.save_exercise(
                            user_id, exercise_to_save, duration_sec,
                            sim_avg_hr, sim_max_hr, sim_min_hr,
                            sim_avg_spo2, sim_min_spo2,
                            altitud_segura, metros_sesion
                        ):
                            mins = duration_sec // 60
                            secs = duration_sec % 60

                            if sim_min_spo2 < 90:
                                color = "warning"
                                head  = f"⚠️ RIESGO DE HIPOXIA ({sim_min_spo2}%)"
                                rec   = f"Oxigenación crítica a {altitud_segura}m. Se recomienda descender."
                            elif sim_max_hr > limit_hr:
                                color = "danger"
                                head  = f"⚠️ ALERTA CARDIACA (>{limit_hr} bpm)"
                                rec   = "Tu esfuerzo cardíaco excedió el límite seguro. Descansa."
                            else:
                                color = "success"
                                head  = "✅ Descenso Registrado"
                                rec   = f"Parámetros biométricos normales para {altitud_segura}m."

                            new_total   = prev_total + metros_sesion
                            badge_alert = None
                            for badge in BADGES[1:]:
                                if prev_total < badge["metros"] <= new_total:
                                    badge_alert = dbc.Alert([
                                        html.H5(
                                            f"🎖️ ¡Insignia Desbloqueada! "
                                            f"{badge['icono']} {badge['nombre']}",
                                            className="alert-heading mb-1"
                                        ),
                                        html.P(
                                            f"Has alcanzado {badge['metros']:,}m de descenso "
                                            f"total. ¡Felicidades!",
                                            className="mb-0 small"
                                        )
                                    ], color="warning", duration=10000)
                                    break

                            main_alert = dbc.Alert([
                                html.H5(head, className="alert-heading"),
                                html.P(
                                    f"Modalidad: {exercise_to_save.upper()} | "
                                    f"Altitud: {altitud_segura}m | "
                                    f"Tiempo: {mins}m {secs}s"
                                ),
                                html.Hr(),
                                html.B(
                                    f"❤️ Avg HR: {sim_avg_hr} | "
                                    f"Max: {sim_max_hr} bpm | "
                                    f"🫁 SpO2 Min: {sim_min_spo2}% | "
                                    f"📏 +{metros_sesion:,}m"
                                ),
                                html.P(rec, className="mb-0 small")
                            ], color=color, duration=8000)

                            msg = html.Div([badge_alert, main_alert]) if badge_alert else main_alert
                        else:
                            msg = dbc.Alert("Error BD", color="danger")
                else:
                    msg = dbc.Alert("Tiempo muy corto", color="warning", duration=3000)

                # Clear the biometrics store on session end
                return True, 0, "INICIAR DESCENSO", "success", False, msg, None, None

            # ── SESSION START: pre-calculate and lock in biometrics ───────────
            if trigger_id == "btn-start-ex" and not is_running:
                altitud_segura = altitud if altitud else 1000
                age = 0
                if session and session.get("id"):
                    info = db.get_user_info(session["id"])
                    age  = info["age"] if info and info["age"] else 0

                pre_params = calculate_session_params(ex_input_value, altitud_segura, age)
                return (False, no_update, "DETENER DESCENSO", "danger",
                        True, "", ex_input_value, pre_params)

            if trigger_id == "ex-type" and not is_running:
                return True, 0, "INICIAR DESCENSO", "success", False, "", None, no_update

            return (no_update, no_update, no_update, no_update,
                    no_update, no_update, no_update, no_update)

        # ── REAL-TIME DISPLAY (timer + ECG) ──────────────────────────────────

        @self.app.callback(
            Output("timer-display",    "children"),
            Output("ecg-graph",        "figure"),
            Output("monitor-hr-kpi",   "children"),
            Output("monitor-spo2-kpi", "children"),
            Input("clock-interval",           "n_intervals"),
            State("is-running-store",         "data"),
            State("session-biometrics-store", "data"),
            State("altitud-slider",           "value"),
            State("ex-type",                  "value"),
        )
        def update_display(n, is_running, stored_biometrics, altitud, modalidad):
            def _kpi(value, unit, label, color):
                return html.Div([
                    html.Span(value, style={
                        "fontSize": "2.4rem", "fontWeight": "800",
                        "color": color, "fontFamily": "monospace", "lineHeight": "1",
                    }),
                    html.Span(f" {unit}", style={"fontSize": ".9rem", "color": color}),
                    html.P(label, className="mb-0 mt-1",
                           style={"fontSize": ".7rem", "color": "var(--muted)",
                                  "textTransform": "uppercase", "letterSpacing": ".07em"}),
                ], className="text-center py-2 px-1",
                   style={"background": "var(--snow)", "borderRadius": "12px",
                          "border": f"1px solid {color}33"})

            _empty_kpi = html.Div()

            if n is None or n == 0:
                fig = go.Figure()
                fig.update_layout(
                    paper_bgcolor="black", plot_bgcolor="black",
                    xaxis={"visible": False}, yaxis={"visible": False},
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                return "00:00", fig, _empty_kpi, _empty_kpi

            seconds_total = n * 0.5
            time_str = f"{int(seconds_total) // 60:02d}:{int(seconds_total) % 60:02d}"

            # Use the pre-locked max_hr so the ECG peak matches the summary
            if stored_biometrics and stored_biometrics.get("max_hr"):
                target_max_hr = stored_biometrics["max_hr"]
                hr_rest       = stored_biometrics.get("hr_rest", 63)
            else:
                # Fallback estimate while store is not yet populated
                alt = altitud if altitud else 1000
                mod = modalidad if modalidad else "esqui"
                # Quick estimate without age/db lookup
                base = 145 if mod == "esqui" else 155
                alt_bonus = int((alt - 1000) / 3000 * 20)
                target_max_hr = base + alt_bonus
                hr_rest = 63

            current_hr = hr_at_elapsed(seconds_total, target_max_hr, hr_rest)

            x_vals, y_vals = generate_ecg_window(
                n_points=120,
                seconds_elapsed=seconds_total,
                hr=current_hr,
                noise=0.035,
            )

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode="lines",
                line=dict(color="#00ff00", width=2),
            ))
            fig.update_layout(
                paper_bgcolor="black", plot_bgcolor="black",
                xaxis={"visible": False, "range": [0, 120]},
                yaxis={"visible": False, "range": [-1.5, 2.0]},
                margin=dict(l=0, r=0, t=10, b=10),
                showlegend=False,
                annotations=[{
                    "text":      f"❤ {current_hr} bpm",
                    "xref":      "paper", "yref": "paper",
                    "x": 0.98,   "y": 0.95,
                    "showarrow": False,
                    "font":      {"color": "#00ff00", "size": 16},
                    "xanchor":   "right",
                }]
            )

            # HR KPI
            if stored_biometrics and stored_biometrics.get("hr_max_limit"):
                limit = stored_biometrics["hr_max_limit"]
                hr_color = "#22c55e" if current_hr < limit * 0.85 else ("#f59e0b" if current_hr < limit else "#ef4444")
            else:
                hr_color = "#22c55e" if current_hr < 150 else ("#f59e0b" if current_hr < 175 else "#ef4444")
            hr_kpi = _kpi(str(current_hr), "bpm", "Frecuencia Cardíaca", hr_color)

            # SpO2 KPI — estimate from altitude + exercise duration
            alt = altitud if altitud else 2000
            spo2_lo, spo2_hi = get_spo2_range(alt)
            time_drop = min(3, seconds_total / 180)
            current_spo2 = max(spo2_lo, int(spo2_hi - time_drop))
            spo2_color = "#22c55e" if current_spo2 >= 95 else ("#f59e0b" if current_spo2 >= 90 else "#ef4444")
            spo2_kpi = _kpi(f"{current_spo2}", "%", "SpO₂ Estimada", spo2_color)

            return time_str, fig, hr_kpi, spo2_kpi
