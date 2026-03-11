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
                    dbc.Col(html.Img(src="/assets/logo.png", height="40px")), 
                    dbc.Col(dbc.NavbarBrand("SnowTrack 🏔️", className="ms-2 fw-bold text-uppercase")),
                ], align="center", className="g-0"),
                href="/app",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Inicio", href="/app", active="exact")),
                    dbc.NavItem(dbc.NavLink("Perfil", href="/app/profile", active="exact")),
                    dbc.Button("Cerrar Sesión", id="btn-logout", color="danger", size="sm", className="ms-3 rounded-pill")
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
        color="white", 
        className="mb-4 shadow-sm py-3", 
    )

# --- LOGIN ---
layout_login = dbc.Container([
    dbc.Row([
        dbc.Col([
            # 1. LOGO DE LA MARCA
            html.Div([
                html.Img(src="/assets/logo.png", style={"height": "120px", "marginBottom": "20px"}),
                html.H2("SnowTrack", className="text-primary fw-bold"),
                html.P("Rendimiento y Seguridad en Altitud", className="text-muted mb-4")
            ], className="text-center"),

            # 2. TARJETA DE ACCESO
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔒 Acceso Seguro", className="text-center text-secondary mb-4"),
                    
                    html.Label("Usuario", className="small fw-bold text-muted"),
                    dbc.Input(id="in-user", placeholder="Ej: esquiador1", size="lg", className="mb-3 rounded-3"),
                    
                    html.Label("Contraseña", className="small fw-bold text-muted"),
                    dbc.Input(id="in-pass", placeholder="••••••", type="password", size="lg", className="mb-4 rounded-3"),
                    
                    dbc.Button("Entrar", id="btn-login", color="primary", size="lg", className="w-100 rounded-pill shadow-sm"),
                    
                    html.Div(id="out-login", className="text-danger text-center mt-3 fw-bold small"),
                ])
            ], className="shadow-lg border-0 p-3", style={"borderRadius": "20px"}),

            # 3. LINK DE REGISTRO
            html.Div([
                dcc.Link("¿No tienes cuenta? Regístrate aquí", href="/register", className="text-decoration-none text-muted small")
            ], className="text-center mt-4")

        ], width=12, md=6, lg=4) 
    ], justify="center", className="vh-100 align-items-center") 
], fluid=True)

# --- REGISTRO ---
layout_register = dbc.Container([
    html.Br(), html.Br(),
    dbc.Card([
        dbc.CardHeader(html.H4("📝 Nuevo Usuario", className="text-center m-0")),
        dbc.CardBody([
            dbc.Input(id="reg-user", placeholder="Elige un usuario", className="mb-3"),
            dbc.Input(id="reg-pass", placeholder="Elige una contraseña", type="password", className="mb-3"),
            html.Label("Soy:"),
            dbc.Select(id="reg-role", options=[
                {"label": "Esquiador / Atleta", "value": "paciente"},
                {"label": "Entrenador / Guía", "value": "fisio"}
            ], value="paciente", className="mb-4"),
            dbc.Button("Crear Cuenta", id="btn-register", color="success", className="w-100"),
            html.Div(id="out-register", className="text-center mt-3"),
            dcc.Link("Volver al Login", href="/", className="d-block text-center mt-3")
        ])
    ], className="shadow-sm border-0", style={"maxWidth": "450px", "margin": "auto"})
])

# ==============================================================================
# ÁREA DEL ESQUIADOR
# ==============================================================================

# 1. HOME
layout_patient_home = html.Div([
    get_navbar(),
    dbc.Container([
        html.H2("Bienvenido a tu Panel de Rendimiento", className="text-center text-secondary mb-5"),
        
        # MODAL DE ALERTA
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

        dbc.Row([
            dbc.Col(dcc.Link(
                dbc.Card([
                    dbc.CardBody([
                        html.H1("👤", className="display-3 text-center mb-3"),
                        html.H4("Mi Perfil", className="text-center text-dark"),
                        html.P("Configura tus datos físicos", className="text-center text-muted")
                    ])
                ], className="shadow-sm h-100 border-0 hover-shadow"), 
                href="/app/profile", style={"textDecoration": "none"}
            ), width=12, lg=4, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([
                    dbc.CardBody([
                        html.H1("⛷️", className="display-3 text-center mb-3"),
                        html.H4("Sesión de Nieve", className="text-center text-primary"),
                        html.P("Monitoriza tu esfuerzo y SpO2", className="text-center text-muted")
                    ])
                ], className="shadow-sm h-100 border-0 hover-shadow"), 
                href="/app/monitor", style={"textDecoration": "none"}
            ), width=12, lg=4, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([
                    dbc.CardBody([
                        html.H1("📓", className="display-3 text-center mb-3"),
                        html.H4("Diario y Fatiga", className="text-center text-info"),
                        html.P("Registra tu sueño y sensaciones", className="text-center text-muted")
                    ])
                ], className="shadow-sm h-100 border-0 hover-shadow"), 
                href="/app/history", style={"textDecoration": "none"}
            ), width=12, lg=4, className="mb-4"),
        ], justify="center")
    ])
])

# 2. MONITOR
layout_patient_monitor = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("⬅ Volver", href="/app", color="link", className="text-decoration-none mb-3 text-muted"))),
        html.Div(id="save-confirmation-msg"),
        dbc.Card([
            dbc.CardHeader("Monitorización Biomédica en Pista", className="bg-dark text-white fw-bold"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Modalidad:", className="fw-bold text-secondary mb-2"),
                        # --- CAMBIO: BOTONES ESQUÍ Y SNOWBOARD ---
                        dbc.RadioItems(
                            id="ex-type", className="btn-group w-100 mb-4",
                            inputClassName="btn-check", labelClassName="btn btn-outline-primary fw-bold", labelCheckedClassName="active btn-primary",
                            options=[
                                {"label": "⛷️ Esquí Alpino", "value": "esqui"}, 
                                {"label": "🏂 Snowboard", "value": "snowboard"}
                            ],
                            value="esqui"
                        ),
                        
                        # --- NUEVO: SLIDER DE ALTITUD ---
                        html.Label("Altitud Actual (metros):", className="fw-bold text-secondary"),
                        html.Div([
                            dcc.Slider(
                                id="altitud-slider",
                                min=1000, max=4000, step=100,
                                marks={1000: '1000m', 2000: '2000m', 3000: '3000m', 4000: '4000m'},
                                value=2000,
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], className="px-2 mb-4 mt-2"),

                        html.Div(html.H2("00:00", id="timer-display", className="display-2 font-monospace fw-bold mb-0"), className="text-center p-4 border rounded bg-light shadow-inner my-4"),
                        dbc.Button("INICIAR DESCENSO", id="btn-start-ex", color="success", size="lg", className="w-100 shadow rounded-pill"),
                    ], width=12, lg=4, className="border-end pe-lg-4"),
                    
                    dbc.Col([
                        html.H5("Señal ECG Simulada", className="text-muted mb-3"),
                        dcc.Graph(id="ecg-graph", config={'staticPlot': True}, style={"height": "400px"}),
                        dcc.Interval(id="clock-interval", interval=500, n_intervals=0, disabled=True),
                        dcc.Store(id="is-running-store", data=False),
                        dcc.Store(id="locked-ex-store", data=None) 
                    ], width=12, lg=8, className="ps-lg-4")
                ])
            ])
        ], className="shadow border-0")
    ])
])

# 3. HISTORIAL (DIARIO DE FATIGA)
layout_patient_history = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("⬅ Volver", href="/app", color="link", className="text-decoration-none mb-3 text-muted"))),
        dbc.Card([
            dbc.CardHeader("📂 Expediente de Rendimiento", className="fw-bold"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📝 Diario de Fatiga", children=[
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.H5("Nuevo Registro Diario", className="text-primary mb-3"),
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Label("Nivel de Fatiga Muscular (1-10)"),
                                        dcc.Slider(
                                            id="q-fatiga", min=1, max=10, step=1, value=5, 
                                            marks={1:'1', 5:'5', 10:'10'},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                                        html.Br(),
                                        html.Label("Percepción de Esfuerzo (RPE)"),
                                        dcc.Slider(
                                            id="q-rpe", min=1, max=10, step=1, value=5, 
                                            marks={1:'1', 5:'5', 10:'10'},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                                        html.Br(),
                                        html.Label("Horas de Sueño Anoche"),
                                        dbc.Input(id="q-sueno", type="number", placeholder="Ej: 7.5", min=0),
                                        html.Br(),
                                        dbc.Button("Guardar en Historial", id="btn-send-quest", color="primary", className="w-100"),
                                        html.Div(id="out-quest", className="mt-2")
                                    ])
                                ], className="bg-light border-0 mb-3"),
                            ], width=12, lg=4),

                            dbc.Col([
                                html.H5("Tu Evolución", className="text-info"),
                                html.Div([dcc.Graph(id="patient-chart", style={"height": "100%", "width": "100%"})], style={"height": "300px", "overflow": "hidden"}),
                                html.Div(id="table-container", className="mt-3")
                            ], width=12, lg=8)
                        ])
                    ]),
                    dbc.Tab(label="🏔️ Historial de Nieve", children=[
                        html.Br(),
                        dbc.Row([dbc.Col([html.Div(id="exercises-table-container")], width=12)]),
                        html.Hr(),
                        dbc.Row([dbc.Col([dcc.Graph(id="exercises-chart", style={"height": "300px"})])])
                    ])
                ])
            ])
        ], className="shadow-sm border-0")
    ])
])

# 4. PERFIL
layout_patient_profile = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("⬅ Volver", href="/app", color="link", className="text-decoration-none mb-3 text-muted"))),
        html.H3("Configuración de Perfil", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Editar Datos Físicos"),
                    dbc.CardBody([
                        html.Label("Edad (años)"),
                        dbc.Input(id="prof-age", type="number", placeholder="Ej: 25", min=0),
                        html.Br(),
                        html.Label("Peso (kg)"),
                        dbc.Input(id="prof-weight", type="number", placeholder="Ej: 70.5", min=0),
                        html.Br(),
                        html.Label("Altura (cm)"),
                        dbc.Input(id="prof-height", type="number", placeholder="Ej: 175", min=0),
                        html.Br(),
                        dbc.Button("💾 Guardar Cambios", id="btn-save-profile", color="dark", className="w-100"),
                        html.Div(id="out-profile", className="mt-3")
                    ])
                ], className="shadow-sm border-0 mb-4")
            ], width=12, lg=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("ℹ️ Límites de Seguridad"),
                    dbc.CardBody([
                        html.Div(id="profile-summary", children="Cargando datos..."),
                        html.Hr(),
                        dbc.Alert([
                            html.H6("Protección en Altitud"),
                            html.P("Calculamos tu frecuencia cardíaca máxima teórica para protegerte de taquicardias severas combinadas con la hipoxia (falta de oxígeno) en la montaña.", className="small mb-0")
                        ], color="info")
                    ])
                ], className="shadow-sm border-0")
            ], width=12, lg=6)
        ])
    ])
])

# --- PANEL DEL ENTRENADOR ---
layout_physio = dbc.Container([
    dbc.NavbarSimple([
        dbc.Button("📄 PDF", id="btn-download-report", color="danger", size="sm", className="me-2 fw-bold", disabled=True),
        dbc.Button("📊 Excel", id="btn-download-excel", color="success", size="sm", className="me-3 fw-bold", disabled=True),
        dbc.Button("Salir", id="btn-logout", color="dark", size="sm", className="rounded-pill")
    ], brand="Panel del Entrenador 🏂", color="primary", dark=True, className="mb-4 shadow-sm"),

    dcc.Download(id="download-component"),       
    dcc.Download(id="download-excel-component"), 

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Gestión de Atletas", className="fw-bold"),
            dbc.CardBody([
                html.Label("Seleccionar Atleta:"),
                dcc.Dropdown(id="fisio-patient-selector", placeholder="Buscar por nombre..."),
                html.Div(id="fisio-patient-info", className="mt-3 text-muted small border-top pt-2")
            ])
        ], className="shadow-sm h-100 border-0"), width=12, lg=3),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Expediente de Rendimiento"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📋 Diario y Fatiga", children=[
                        html.Br(),
                        html.H5("Fatiga Acumulada y Esfuerzo Percibido", className="text-primary"),
                        dcc.Graph(id="fisio-quest-chart", style={"height": "300px"}),
                        html.Hr(),
                        html.Div(id="fisio-quest-table")
                    ]),

                    dbc.Tab(label="🏔️ Rendimiento en Pista", children=[
                        html.Br(),
                        html.H5("Análisis de Riesgo (FC + SpO2)", className="text-danger"),
                        dcc.Graph(id="fisio-ex-chart", style={"height": "300px"}),
                        html.Hr(),
                        html.H6("Registro de Descensos"),
                        html.Div(id="fisio-ex-table")
                    ]),

                    dbc.Tab(label="🔬 Data Science", children=[
                        html.Br(),
                        html.H4("Correlación: Fatiga vs Esfuerzo en Altitud", className="text-center"),
                        html.P("Detecta si el atleta está forzando demasiado cuando sus niveles de fatiga ya son altos.", className="text-muted text-center small"),
                        dcc.Graph(id="fisio-scatter-chart", style={"height": "400px"}),
                        dbc.Alert("Cada punto representa un día donde el atleta registró fatiga y realizó descensos.", color="info", className="mt-3 small")
                    ])
                ])
            ])
        ], className="shadow-sm h-100 border-0"), width=12, lg=9)
    ])
])
