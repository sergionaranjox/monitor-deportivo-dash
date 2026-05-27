from dash import html, dcc
import dash_bootstrap_components as dbc

# ==============================================================================
# NAVBAR & ESTILOS COMUNES
# ==============================================================================
def get_navbar():
    return dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Span("🏔️", style={"fontSize": "1.6rem"})),
                    dbc.Col(dbc.NavbarBrand("SnowTrack", className="ms-1")),
                ], align="center", className="g-0"),
                href="/app", style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("🏠 Inicio",   href="/app",          active="exact")),
                    dbc.NavItem(dbc.NavLink("🏆 Ranking",  href="/app/ranking",  active="exact")),
                    dbc.NavItem(dbc.NavLink("👤 Perfil",   href="/app/profile",  active="exact")),
                    dbc.NavItem(dbc.NavLink("📓 Historial",href="/app/history",  active="exact")),
                    dbc.Button("Salir", id="btn-logout", color="light", size="sm",
                               className="ms-3 rounded-pill fw-bold",
                               style={"color": "var(--accent-dark)"}),
                ], className="ms-auto", navbar=True),
                id="navbar-collapse", navbar=True,
            ),
        ]),
        className="snow-navbar mb-4",
    )

# --- LOGIN ---
_snowflakes = html.Div([
    html.Span("❄", className="snowflake", style={"left": f"{x}%", "animationDuration": f"{d}s", "animationDelay": f"{dl}s", "fontSize": f"{sz}rem", "opacity": op})
    for x, d, dl, sz, op in [
        (8,  8, 0,   1.1, .6), (18, 12, 2,  .8, .5), (29, 9,  1,  1.3, .7),
        (40, 7, 3,   .9, .4),  (52, 11, .5, 1.0, .6), (63, 8,  2,  .7, .5),
        (74, 10, 1.5,1.2, .7), (85, 6,  .8, .9, .4),  (93, 9,  2.5,1.1, .6),
    ]
], style={"position": "absolute", "inset": 0, "overflow": "hidden", "pointerEvents": "none", "zIndex": 1})

layout_login = html.Div([
    _snowflakes,
    html.Div([
        html.P("❄  SNOWTRACK  ❄", className="login-tagline"),
        html.Div([
            # Logo + título
            html.Div([
                html.Div("🏔️", style={"fontSize": "3.5rem", "lineHeight": "1"}),
                html.Div("SnowTrack", className="login-logo-text mt-1"),
                html.P("Rendimiento y Seguridad en Altitud",
                       className="text-muted small text-center mb-4 mt-1"),
            ], className="text-center mb-3"),

            html.Label("Usuario"),
            dbc.Input(id="in-user", placeholder="Ej: esquiador1", size="lg", className="mb-3"),

            html.Label("Contraseña"),
            dbc.Input(id="in-pass", placeholder="••••••", type="password", size="lg", className="mb-4"),

            dbc.Button("Entrar →", id="btn-login", color="primary", size="lg",
                       className="w-100 rounded-pill"),

            html.Div(id="out-login", className="text-danger text-center mt-3 fw-bold small"),

            html.Hr(className="my-3", style={"borderColor": "#bae6fd"}),
            html.Div(
                dcc.Link("¿No tienes cuenta? Regístrate aquí →",
                         href="/register", className="text-decoration-none small"),
                className="text-center", style={"color": "var(--muted)"}
            ),
        ], className="login-card"),
    ], style={"position": "relative", "zIndex": 2, "display": "flex",
              "flexDirection": "column", "alignItems": "center"}),
], className="login-bg")

# --- REGISTRO ---
layout_register = html.Div([
    _snowflakes,
    html.Div([
        html.P("❄  SNOWTRACK  ❄", className="login-tagline"),
        html.Div([
            html.Div([
                html.Div("🏔️", style={"fontSize": "3rem", "lineHeight": "1"}),
                html.Div("Crear Cuenta", className="login-logo-text mt-1"),
                html.P("Únete a la comunidad de montaña",
                       className="text-muted small text-center mb-4 mt-1"),
            ], className="text-center mb-3"),

            html.Label("Usuario"),
            dbc.Input(id="reg-user", placeholder="Ej: esquiador1", className="mb-3"),

            html.Label("Contraseña"),
            dbc.Input(id="reg-pass", placeholder="••••••", type="password", className="mb-3"),

            html.Label("Soy:"),
            dbc.Select(id="reg-role", options=[
                {"label": "⛷️  Esquiador / Atleta", "value": "paciente"},
                {"label": "🏋️  Entrenador / Guía",  "value": "fisio"},
            ], value="paciente", className="mb-4"),

            dbc.Button("Crear Cuenta →", id="btn-register", color="success",
                       size="lg", className="w-100 rounded-pill"),
            html.Div(id="out-register", className="text-center mt-3"),

            html.Hr(className="my-3", style={"borderColor": "#bae6fd"}),
            html.Div(
                dcc.Link("← Volver al Login", href="/",
                         className="text-decoration-none small"),
                className="text-center", style={"color": "var(--muted)"}
            ),
        ], className="login-card"),
    ], style={"position": "relative", "zIndex": 2, "display": "flex",
              "flexDirection": "column", "alignItems": "center"}),
], className="login-bg")

# ==============================================================================
# ÁREA DEL ESQUIADOR
# ==============================================================================

# 1. HOME
layout_patient_home = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Falta Configuración"), close_button=False),
            dbc.ModalBody([
                html.P("Para medir tu aclimatación y riesgos, necesitamos tus datos físicos."),
                html.P("El sistema usa tu edad para calcular tus límites seguros en altitud.", className="text-muted small")
            ]),
            dbc.ModalFooter(
                dbc.Button("Ir a Configurar Perfil", href="/app/profile", color="primary", className="ms-auto")
            ),
        ], id="modal-missing-profile", is_open=False, backdrop="static", keyboard=False),

        html.Div([
            html.H2("Panel de Rendimiento", className="fw-bold"),
            html.P("Selecciona una sección para comenzar", className="mb-0"),
        ], className="home-hero page-enter"),

        html.Div(id="home-stats-row", className="mb-2 page-enter"),
        html.Div(id="home-acwr-section", className="mb-3 page-enter"),

        dbc.Row([
            dbc.Col(dcc.Link(
                dbc.Card([dbc.CardBody([
                    html.Span("⛷️", className="menu-icon"),
                    html.H5("Sesión de Nieve", className="fw-bold text-center mb-1"),
                    html.P("Monitoriza tu ECG y SpO2 en pista", className="text-center text-muted small mb-0"),
                ])], className="menu-card card-gradient-sky h-100"),
                href="/app/monitor", style={"textDecoration": "none"}
            ), width=12, sm=6, lg=3, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([dbc.CardBody([
                    html.Span("📓", className="menu-icon"),
                    html.H5("Diario y Fatiga", className="fw-bold text-center mb-1"),
                    html.P("Registra tu sueño y sensaciones", className="text-center text-muted small mb-0"),
                ])], className="menu-card card-gradient-pine h-100"),
                href="/app/history", style={"textDecoration": "none"}
            ), width=12, sm=6, lg=3, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([dbc.CardBody([
                    html.Span("🏆", className="menu-icon"),
                    html.H5("Ranking", className="fw-bold text-center mb-1"),
                    html.P("Insignias y clasificación global", className="text-center text-muted small mb-0"),
                ])], className="menu-card card-gradient-gold h-100"),
                href="/app/ranking", style={"textDecoration": "none"}
            ), width=12, sm=6, lg=3, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([dbc.CardBody([
                    html.Span("👤", className="menu-icon"),
                    html.H5("Mi Perfil", className="fw-bold text-center mb-1"),
                    html.P("Configura tus datos físicos", className="text-center text-muted small mb-0"),
                ])], className="menu-card card-gradient-blue h-100"),
                href="/app/profile", style={"textDecoration": "none"}
            ), width=12, sm=6, lg=3, className="mb-4"),
        ], justify="center", className="page-enter"),
    ], className="py-2")
])

# 2. MONITOR
layout_patient_monitor = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("← Volver", href="/app", color="link",
                                   className="text-decoration-none mb-3 ps-0",
                                   style={"color": "var(--accent-dark)"}))),
        html.Div(id="save-confirmation-msg", className="mb-3"),
        dbc.Card([
            dbc.CardHeader("❤️ Monitorización Biomédica en Pista", className="dark-header fw-bold"),
            dbc.CardBody([
                dbc.Row([
                    # ── Panel de control ──────────────────────────────
                    dbc.Col([
                        html.Div([
                            html.Label("Modalidad:", className="mb-2"),
                            dbc.RadioItems(
                                id="ex-type", className="btn-group w-100 mb-4",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary fw-bold",
                                labelCheckedClassName="active btn-primary",
                                options=[
                                    {"label": "⛷️ Esquí Alpino",  "value": "esqui"},
                                    {"label": "🏂 Snowboard",      "value": "snowboard"},
                                ],
                                value="esqui"
                            ),
                            html.Label("Altitud Actual (metros):", className="mb-1"),
                            html.Div([
                                dcc.Slider(
                                    id="altitud-slider",
                                    min=1000, max=4000, step=100,
                                    marks={1000: "1000m", 2000: "2000m",
                                           3000: "3000m", 4000: "4000m"},
                                    value=2000,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                )
                            ], className="px-1 mb-2 mt-2"),

                            html.Div(id="risk-calculator"),

                            html.Div(
                                html.H2("00:00", id="timer-display",
                                        className="display-2 font-monospace fw-bold mb-0 text-center",
                                        style={"color": "#38bdf8"}),
                                className="timer-display text-center p-4 my-4"
                            ),
                            dbc.Button("INICIAR DESCENSO", id="btn-start-ex",
                                       color="success", size="lg",
                                       className="w-100 rounded-pill fw-bold"),
                            html.Div(id="monitor-rest-info"),
                        ], className="monitor-panel h-100")
                    ], width=12, lg=4, className="pe-lg-3 mb-3 mb-lg-0"),

                    # ── ECG ──────────────────────────────────────────
                    dbc.Col([
                        dbc.Row([
                            dbc.Col(html.Div(id="monitor-hr-kpi"),   width=6),
                            dbc.Col(html.Div(id="monitor-spo2-kpi"), width=6),
                        ], className="mb-3 g-2"),
                        html.H6("Señal ECG en Tiempo Real",
                                className="text-muted mb-2 fw-bold text-uppercase",
                                style={"letterSpacing": ".08em", "fontSize": ".75rem"}),
                        html.Div(
                            dcc.Graph(id="ecg-graph", config={"staticPlot": True},
                                      style={"height": "400px"}),
                            className="ecg-wrapper"
                        ),
                        dcc.Interval(id="clock-interval", interval=500, n_intervals=0, disabled=True),
                        dcc.Store(id="is-running-store",         data=False),
                        dcc.Store(id="locked-ex-store",          data=None),
                        dcc.Store(id="session-biometrics-store", data=None),
                    ], width=12, lg=8, className="ps-lg-3"),
                ])
            ], className="p-3 p-lg-4")
        ], className="shadow border-0 page-enter")
    ])
])

# 3. HISTORIAL
layout_patient_history = html.Div([
    get_navbar(),
    dcc.Store(id="manual-refresh-trigger", data=0),
    dcc.Download(id="download-athlete-pdf"),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("← Volver", href="/app", color="link",
                                   className="text-decoration-none mb-3 ps-0",
                                   style={"color": "var(--accent-dark)"}))),
        dbc.Card([
            dbc.CardHeader([
                html.Span("📂 Expediente de Rendimiento"),
                dbc.Button("📄 Mi Informe PDF", id="btn-download-athlete-pdf",
                           color="outline-primary", size="sm", className="fw-bold"),
            ], className="fw-bold d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📝 Diario de Fatiga", children=[
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.H6("Nuevo Registro", className="fw-bold text-uppercase mb-3",
                                        style={"color": "var(--accent-dark)", "letterSpacing": ".06em"}),
                                dbc.Card([dbc.CardBody([
                                    html.Label("Fatiga Muscular (1-10)"),
                                    dcc.Slider(id="q-fatiga", min=1, max=10, step=1, value=5,
                                               marks={1:"1", 5:"5", 10:"10"},
                                               tooltip={"placement": "bottom", "always_visible": True}),
                                    html.Br(),
                                    html.Label("Percepción de Esfuerzo (RPE)"),
                                    dcc.Slider(id="q-rpe", min=1, max=10, step=1, value=5,
                                               marks={1:"1", 5:"5", 10:"10"},
                                               tooltip={"placement": "bottom", "always_visible": True}),
                                    html.Br(),
                                    html.Label("Horas de Sueño"),
                                    dbc.Input(id="q-sueno", type="number", placeholder="Ej: 7.5", min=0, className="mb-3"),
                                    html.Label("Altitud de Pernocta (m)"),
                                    dcc.Slider(id="q-altitud", min=0, max=3500, step=100, value=0,
                                               marks={0: "0m", 1000: "1000m", 2000: "2000m", 3500: "3500m"},
                                               tooltip={"placement": "bottom", "always_visible": True},
                                               className="mb-4"),
                                    dbc.Button("💾 Guardar Registro", id="btn-send-quest",
                                               color="primary", className="w-100 rounded-pill"),
                                    html.Div(id="out-quest", className="mt-2"),
                                ])], className="border-0", style={"background": "var(--snow)"}),
                            ], width=12, lg=4),
                            dbc.Col([
                                html.H6("Tu Evolución", className="fw-bold text-uppercase mb-3",
                                        style={"color": "var(--accent-dark)", "letterSpacing": ".06em"}),
                                html.Div([dcc.Graph(id="patient-chart",
                                                    style={"height": "100%", "width": "100%"})],
                                         style={"height": "300px", "overflow": "hidden"}),
                                html.Div(id="table-container", className="mt-3"),
                            ], width=12, lg=8),
                        ])
                    ]),
                    dbc.Tab(label="🏔️ Historial de Nieve", children=[
                        html.Br(),
                        html.Div(id="exercises-table-container"),
                        html.Hr(),
                        dcc.Graph(id="exercises-chart", style={"height": "300px"}),
                        html.Hr(),
                        html.H6("Distribución de Zonas de FC (últimas 10 sesiones)",
                                className="fw-bold text-uppercase mb-2",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem",
                                       "letterSpacing": ".06em"}),
                        dcc.Graph(id="hr-zones-chart", style={"height": "260px"}),
                        html.Hr(),
                        html.H6("📈 Tendencia de Rendimiento · FC Media por Altitud",
                                className="fw-bold text-uppercase mb-2",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem",
                                       "letterSpacing": ".06em"}),
                        html.P("Si la FC media baja con el tiempo a la misma altitud, tu corazón es más eficiente.",
                               className="text-muted small mb-2"),
                        dcc.Graph(id="tendency-chart", style={"height": "280px"}),
                    ]),

                    dbc.Tab(label="🫁 Aclimatación", children=[
                        html.Br(),
                        html.H6("SpO₂ Mínima por Sesión vs Altitud de Ejercicio",
                                className="fw-bold text-uppercase mb-3",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                        dcc.Graph(id="aclimatacion-chart", style={"height": "350px"}),
                    ]),

                    dbc.Tab(label="📅 Actividad", children=[
                        html.Br(),
                        html.H6("Calendario de Actividad — últimos 90 días",
                                className="fw-bold text-uppercase mb-3",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                        dcc.Graph(id="activity-calendar", style={"height": "220px"}),
                    ]),

                    dbc.Tab(label="📊 ACWR Semanal", children=[
                        html.Br(),
                        html.H6("Historial de Carga de Entrenamiento — últimas 12 semanas",
                                className="fw-bold text-uppercase mb-1",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem",
                                       "letterSpacing": ".06em"}),
                        html.P("Los puntos coloreados indican la zona ACWR de cada semana. "
                               "Zona verde óptima: 0.8 – 1.3.",
                               className="text-muted small mb-3"),
                        dcc.Graph(id="acwr-history-chart", style={"height": "320px"}),
                    ]),

                    dbc.Tab(label="🔀 Comparar Sesiones", children=[
                        html.Br(),
                        html.H6("Comparación de Dos Sesiones",
                                className="fw-bold text-uppercase mb-3",
                                style={"color": "var(--accent-dark)", "fontSize": ".78rem",
                                       "letterSpacing": ".06em"}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Sesión A:"),
                                dcc.Dropdown(id="compare-sel-1",
                                             placeholder="Selecciona una sesión...",
                                             className="mb-3"),
                            ], width=12, md=6),
                            dbc.Col([
                                html.Label("Sesión B:"),
                                dcc.Dropdown(id="compare-sel-2",
                                             placeholder="Selecciona otra sesión...",
                                             className="mb-3"),
                            ], width=12, md=6),
                        ]),
                        html.Div("Selecciona las dos sesiones para ver la comparación detallada.",
                                 id="compare-result",
                                 className="text-muted text-center p-4 small"),
                    ]),

                    dbc.Tab(label="➕ Añadir Sesión", children=[
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.H6("Registrar Sesión Pasada", className="fw-bold text-uppercase mb-3",
                                        style={"color": "var(--accent-dark)", "letterSpacing": ".06em", "fontSize": ".78rem"}),
                                dbc.Card([dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("Fecha"),
                                            dbc.Input(id="manual-date", type="date", className="mb-3"),
                                        ], width=12, sm=6),
                                        dbc.Col([
                                            html.Label("Modalidad"),
                                            dbc.Select(id="manual-modalidad", options=[
                                                {"label": "⛷️ Esquí Alpino", "value": "esqui"},
                                                {"label": "🏂 Snowboard",    "value": "snowboard"},
                                            ], value="esqui", className="mb-3"),
                                        ], width=12, sm=6),
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("Altitud (m)"),
                                            dbc.Input(id="manual-altitud", type="number",
                                                      placeholder="Ej: 2500", min=0, max=5000, className="mb-3"),
                                        ], width=12, sm=4),
                                        dbc.Col([
                                            html.Label("Duración (min)"),
                                            dbc.Input(id="manual-duracion", type="number",
                                                      placeholder="Ej: 45", min=1, className="mb-3"),
                                        ], width=12, sm=4),
                                        dbc.Col([
                                            html.Label("Metros Descenso"),
                                            dbc.Input(id="manual-metros", type="number",
                                                      placeholder="Ej: 5000", min=0, className="mb-3"),
                                        ], width=12, sm=4),
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("FC Media (bpm)"),
                                            dbc.Input(id="manual-avg-hr", type="number",
                                                      placeholder="Ej: 145", min=40, max=220, className="mb-3"),
                                        ], width=12, sm=3),
                                        dbc.Col([
                                            html.Label("FC Máx (bpm)"),
                                            dbc.Input(id="manual-max-hr", type="number",
                                                      placeholder="Ej: 175", min=40, max=220, className="mb-3"),
                                        ], width=12, sm=3),
                                        dbc.Col([
                                            html.Label("SpO₂ Med (%)"),
                                            dbc.Input(id="manual-avg-spo2", type="number",
                                                      placeholder="Ej: 95", min=50, max=100, className="mb-3"),
                                        ], width=12, sm=3),
                                        dbc.Col([
                                            html.Label("SpO₂ Mín (%)"),
                                            dbc.Input(id="manual-min-spo2", type="number",
                                                      placeholder="Ej: 91", min=50, max=100, className="mb-3"),
                                        ], width=12, sm=3),
                                    ]),
                                    dbc.Button("💾 Registrar Sesión", id="btn-save-manual-session",
                                               color="primary", className="w-100 rounded-pill"),
                                    html.Div(id="out-manual-session", className="mt-2"),
                                ])], className="border-0", style={"background": "var(--snow)"}),
                            ], width=12, lg=8),
                            dbc.Col([
                                dbc.Alert([
                                    html.H6("📋 Instrucciones", className="fw-bold"),
                                    html.P("Registra sesiones anteriores sin haber usado el monitor en directo.", className="small mb-2"),
                                    html.P("Los datos se integrarán en tu historial, gráficas y ranking.", className="small mb-0"),
                                ], color="info"),
                            ], width=12, lg=4),
                        ]),
                    ]),
                ])
            ])
        ], className="shadow-sm border-0 page-enter")
    ])
])

# 4. PERFIL
layout_patient_profile = html.Div([
    get_navbar(),

    # ── Onboarding overlay ─────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Button("✕", id="btn-dismiss-onboarding", className="onboarding-close"),
            html.Div("🏔️", style={"fontSize": "3rem", "lineHeight": "1", "marginBottom": ".4rem"}),
            html.H4("¡Bienvenido a SnowTrack!", className="fw-bold mb-2",
                    style={"color": "var(--text)"}),
            html.P(
                "Para calcular tus límites seguros en altitud necesitamos "
                "tus datos físicos. Completa el formulario y pulsa guardar.",
                className="text-muted small mb-3",
            ),
            html.Div("↓", className="onboarding-arrow"),
            html.P("El formulario está resaltado abajo", className="text-muted small mb-0"),
        ], className="onboarding-tooltip"),
    ], id="onboarding-overlay", className="onboarding-overlay", style={"display": "none"}),

    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("← Volver", href="/app", color="link",
                                   className="text-decoration-none mb-3 ps-0",
                                   style={"color": "var(--accent-dark)"}))),
        html.H4("👤 Mi Perfil", className="fw-bold mb-4 page-enter"),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Card([
                        dbc.CardHeader("✏️ Datos Físicos"),
                        dbc.CardBody([
                            html.Label("Edad (años)"),
                            dbc.Input(id="prof-age",    type="number", placeholder="Ej: 25",  min=0, className="mb-3"),
                            html.Label("Peso (kg)"),
                            dbc.Input(id="prof-weight", type="number", placeholder="Ej: 70.5", min=0, className="mb-3"),
                            html.Label("Altura (cm)"),
                            dbc.Input(id="prof-height", type="number", placeholder="Ej: 175", min=0, className="mb-4"),
                            dbc.Button("💾 Guardar y Comenzar", id="btn-save-profile",
                                       color="dark", className="w-100 rounded-pill"),
                            html.Div(id="out-profile", className="mt-3"),
                        ])
                    ], className="shadow-sm border-0 mb-4"),
                ], id="profile-card-spotlight"),
                width=12, lg=6,
            ),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🛡️ Límites de Seguridad"),
                    dbc.CardBody([
                        html.Div(id="profile-summary", children="Cargando datos..."),
                        html.Hr(style={"borderColor": "#bae6fd"}),
                        dbc.Alert([
                            html.H6("⛰️ Protección en Altitud", className="fw-bold"),
                            html.P("Calculamos tu FC máxima teórica para alertarte de riesgo cardíaco combinado con hipoxia en la montaña.", className="small mb-0")
                        ], color="info", className="mb-0"),
                    ])
                ], className="shadow-sm border-0")
            ], width=12, lg=6),
        ], className="page-enter")
    ])
])

# 5. RANKING
layout_patient_ranking = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("← Volver", href="/app", color="link",
                                   className="text-decoration-none mb-3 ps-0",
                                   style={"color": "var(--accent-dark)"}))),
        html.Div([
            html.H3("🏆 Ranking de Descensos", className="fw-bold mb-1"),
            html.P("Acumula metros bajando pistas para desbloquear insignias", className="text-muted mb-0"),
        ], className="text-center mb-4 page-enter"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎖️ Mi Insignia Actual", className="dark-header"),
                    dbc.CardBody([
                        html.Div(id="ranking-my-badge", className="text-center py-2 badge-display")
                    ])
                ], className="shadow border-0 mb-4"),
                dbc.Card([
                    dbc.CardHeader("📜 Todas las Insignias"),
                    dbc.CardBody([html.Div(id="ranking-all-badges")])
                ], className="shadow-sm border-0"),
            ], width=12, lg=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🥇 Clasificación Global", className="dark-header"),
                    dbc.CardBody([html.Div(id="ranking-table")])
                ], className="shadow border-0"),
            ], width=12, lg=8),
        ], className="page-enter")
    ])
])

# --- PANEL DEL ENTRENADOR ---
layout_physio = html.Div([
    dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Span("🏂", style={"fontSize": "1.5rem"})),
                    dbc.Col(dbc.NavbarBrand("Panel del Entrenador", className="ms-1")),
                ], align="center", className="g-0"),
                href="#", style={"textDecoration": "none"},
            ),
            dbc.Nav([
                dbc.Button("📄 PDF",   id="btn-download-report", color="light", size="sm",
                           className="me-2 fw-bold", disabled=True,
                           style={"color": "var(--accent-dark)"}),
                dbc.Button("📊 Excel", id="btn-download-excel",  color="light", size="sm",
                           className="me-3 fw-bold", disabled=True,
                           style={"color": "var(--pine-dark)"}),
                dbc.Button("Salir", id="btn-logout", color="light", size="sm",
                           className="rounded-pill fw-bold",
                           style={"color": "var(--accent-dark)"}),
            ], navbar=True, className="ms-auto"),
        ]),
        className="physio-navbar mb-4",
    ),

    dcc.Download(id="download-component"),
    dcc.Download(id="download-excel-component"),

    dbc.Container([
        dbc.Row([
            # ── Selector lateral ─────────────────────────────────────
            dbc.Col(dbc.Card([
                dbc.CardHeader("🧑‍🤝‍🧑 Gestión de Atletas"),
                dbc.CardBody([
                    html.Label("Seleccionar Atleta:"),
                    dcc.Dropdown(id="fisio-patient-selector",
                                 placeholder="Buscar por nombre...",
                                 style={"borderRadius": "8px"}),
                    html.Div(id="fisio-patient-info",
                             className="mt-3 small border-top pt-2",
                             style={"color": "var(--muted)"}),
                ])
            ], className="shadow-sm h-100 border-0"),
            width=12, lg=3, className="mb-3 mb-lg-0",
            style={"position": "relative", "zIndex": 10}),

            # ── Panel principal ───────────────────────────────────────
            dbc.Col(dbc.Card([
                dbc.CardHeader("📊 Expediente de Rendimiento"),
                dbc.CardBody([
                    dbc.Tabs([
                        dbc.Tab(label="👥 Vista General", children=[
                            html.Br(),
                            html.Div(id="fisio-overview"),
                        ]),

                        dbc.Tab(label="📋 Diario y Fatiga", children=[
                            html.Br(),
                            html.H6("Fatiga Acumulada y Esfuerzo Percibido",
                                    className="fw-bold text-uppercase mb-3",
                                    style={"color": "var(--accent-dark)", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                            dcc.Graph(id="fisio-quest-chart", style={"height": "300px"}),
                            html.Hr(style={"borderColor": "#bae6fd"}),
                            html.Div(id="fisio-quest-table"),
                        ]),

                        dbc.Tab(label="🏔️ Rendimiento en Pista", children=[
                            html.Br(),
                            html.H6("Análisis de Riesgo · FC + SpO2",
                                    className="fw-bold text-uppercase mb-3",
                                    style={"color": "#dc2626", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                            dcc.Graph(id="fisio-ex-chart", style={"height": "300px"}),
                            html.Hr(style={"borderColor": "#bae6fd"}),
                            html.H6("Registro de Descensos", className="fw-bold mb-2"),
                            html.Div(id="fisio-ex-table"),
                            html.Hr(style={"borderColor": "#bae6fd"}),
                            html.H6("📝 Notas del Entrenador", className="fw-bold mb-2"),
                            dbc.Textarea(id="physio-note-input",
                                         placeholder="Escribe observaciones sobre el atleta...",
                                         rows=3, className="mb-2",
                                         style={"background": "var(--snow)", "borderColor": "#90c0da"}),
                            dbc.Button("💾 Guardar Nota", id="btn-save-physio-note",
                                       color="outline-primary", size="sm", className="rounded-pill"),
                            html.Div(id="physio-note-msg", className="mt-2"),
                        ]),

                        dbc.Tab(label="🔬 Data Science", children=[
                            html.Br(),
                            html.H6("Correlación: Fatiga vs Esfuerzo en Altitud",
                                    className="text-center fw-bold text-uppercase mb-1",
                                    style={"color": "var(--accent-dark)", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                            html.P("Detecta si el atleta fuerza demasiado con fatiga elevada.",
                                   className="text-muted text-center small mb-3"),
                            dcc.Graph(id="fisio-scatter-chart", style={"height": "400px"}),
                            dbc.Alert("Cada punto = un día con fatiga registrada y descensos realizados.",
                                      color="info", className="mt-3 small mb-0"),
                        ]),

                        dbc.Tab(label="🗺️ Mapa de Actividad", children=[
                            html.Br(),
                            html.H6("Distribución Geográfica de Actividad",
                                    className="fw-bold text-uppercase mb-1",
                                    style={"color": "var(--accent-dark)", "fontSize": ".78rem", "letterSpacing": ".06em"}),
                            html.P("Resorts asignados por altitud de sesión · Tamaño = metros · Calor = metros × FC.",
                                   className="text-muted small mb-3"),
                            dcc.Graph(id="fisio-heatmap"),
                        ]),
                    ])
                ])
            ], className="shadow-sm h-100 border-0"), width=12, lg=9),
        ], className="page-enter"),
    ], fluid=True, className="px-3 px-lg-4"),
])
