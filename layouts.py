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
                    dbc.Col(dbc.NavbarBrand("MedTrack 🏥", className="ms-2 fw-bold text-uppercase")),
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
            # 1. LOGO DE LA MARCA (Encima de la tarjeta)
            html.Div([
                # Asegúrate de que logo.png está en la carpeta assets
                html.Img(src="/assets/logo.png", style={"height": "120px", "marginBottom": "20px"}),
                html.H2("MedTrack", className="text-primary fw-bold"),
                html.P("Monitorización Biomédica Avanzada", className="text-muted mb-4")
            ], className="text-center"),

            # 2. TARJETA DE ACCESO
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔒 Acceso Seguro", className="text-center text-secondary mb-4"),
                    
                    html.Label("Usuario", className="small fw-bold text-muted"),
                    dbc.Input(id="in-user", placeholder="Ej: paciente1", size="lg", className="mb-3 rounded-3"),
                    
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

        ], width=12, md=6, lg=4) # Esto controla el ancho (en móviles ocupa todo, en PC solo 1/3)
    ], justify="center", className="vh-100 align-items-center") # vh-100 = Altura completa de la pantalla
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
                {"label": "Paciente", "value": "paciente"},
                {"label": "Fisioterapeuta", "value": "fisio"}
            ], value="paciente", className="mb-4"),
            dbc.Button("Crear Cuenta", id="btn-register", color="success", className="w-100"),
            html.Div(id="out-register", className="text-center mt-3"),
            dcc.Link("Volver al Login", href="/", className="d-block text-center mt-3")
        ])
    ], className="shadow-sm border-0", style={"maxWidth": "450px", "margin": "auto"})
])

# ==============================================================================
# ÁREA DEL PACIENTE
# ==============================================================================

# 1. HOME
layout_patient_home = html.Div([
    get_navbar(),
    dbc.Container([
        html.H2("Bienvenido a tu Panel de Salud", className="text-center text-secondary mb-5"),
        
        # MODAL DE ALERTA (Solo saltará si intentas entrar en herramientas sin perfil)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Falta Configuración"), close_button=False),
            dbc.ModalBody([
                html.P("Para usar esta herramienta, necesitamos primero tus datos físicos."),
                html.P("El sistema necesita tu edad para calcular tus límites de seguridad.", className="text-muted small")
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
                        html.P("Configura tu edad y datos físicos", className="text-center text-muted")
                    ])
                ], className="shadow-sm h-100 border-0 hover-shadow"), 
                href="/app/profile", style={"textDecoration": "none"}
            ), width=12, lg=4, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([
                    dbc.CardBody([
                        html.H1("🏃‍♂️", className="display-3 text-center mb-3"),
                        html.H4("Iniciar Ejercicio", className="text-center text-primary"),
                        html.P("Monitorización ECG y SpO2 en vivo", className="text-center text-muted")
                    ])
                ], className="shadow-sm h-100 border-0 hover-shadow"), 
                href="/app/monitor", style={"textDecoration": "none"}
            ), width=12, lg=4, className="mb-4"),

            dbc.Col(dcc.Link(
                dbc.Card([
                    dbc.CardBody([
                        html.H1("📝", className="display-3 text-center mb-3"),
                        html.H4("Mi Diario", className="text-center text-info"),
                        html.P("Historial clínico y evolución", className="text-center text-muted")
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
            dbc.CardHeader("Monitorización Biomédica", className="bg-dark text-white fw-bold"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Selecciona Actividad:", className="lead mb-3"),
                        dbc.RadioItems(
                            id="ex-type", className="btn-group w-100",
                            inputClassName="btn-check", labelClassName="btn btn-outline-secondary", labelCheckedClassName="active btn-primary",
                            options=[{"label": "🏃 Correr", "value": "run"}, {"label": "🚲 Bici", "value": "bike"}, {"label": "🏋️ Sentadilla", "value": "squat"}],
                            value="run"
                        ),
                        html.Br(), html.Br(), html.Br(),
                        html.Div(html.H2("00:00", id="timer-display", className="display-2 font-monospace fw-bold mb-0"), className="text-center p-4 border rounded bg-light shadow-inner my-4"),
                        dbc.Button("INICIAR SESIÓN", id="btn-start-ex", color="success", size="lg", className="w-100 shadow rounded-pill"),
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

# 3. HISTORIAL (CON SLIDERS MEJORADOS)
layout_patient_history = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(dbc.Button("⬅ Volver", href="/app", color="link", className="text-decoration-none mb-3 text-muted"))),
        dbc.Card([
            dbc.CardHeader("📂 Expediente Médico Personal", className="fw-bold"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📝 Diario de Fatiga", children=[
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.H5("Nuevo Registro Diario", className="text-primary mb-3"),
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Label("Nivel de Fatiga (1-10)"),
                                        # CAMBIO: Tooltip añadido
                                        dcc.Slider(
                                            id="q-fatiga", min=1, max=10, step=1, value=5, 
                                            marks={1:'1', 5:'5', 10:'10'},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                                        html.Br(),
                                        html.Label("Percepción de Esfuerzo (RPE)"),
                                        # CAMBIO: Tooltip añadido
                                        dcc.Slider(
                                            id="q-rpe", min=1, max=10, step=1, value=5, 
                                            marks={1:'1', 5:'5', 10:'10'},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                                        html.Br(),
                                        html.Label("Horas de Sueño"),
                                        # CAMBIO: min=0 añadido
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
                    dbc.Tab(label="🏃 Historial Deportivo", children=[
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
                    dbc.CardHeader("Editar Datos Antropométricos"),
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
                    dbc.CardHeader("ℹ️ Ficha Técnica Calculada"),
                    dbc.CardBody([
                        html.Div(id="profile-summary", children="Cargando datos..."),
                        html.Hr(),
                        dbc.Alert([
                            html.H6("Información de Seguridad"),
                            html.P("Usamos tu edad para calcular tu frecuencia cardíaca máxima segura (Fórmula: 220 - edad). Si superas este límite durante el ejercicio, se generará una alerta.", className="small mb-0")
                        ], color="info")
                    ])
                ], className="shadow-sm border-0")
            ], width=12, lg=6)
        ])
    ])
])

# --- FISIO ---
layout_physio = dbc.Container([
    dbc.NavbarSimple([
        # Botón PDF (Ya existía)
        dbc.Button("📄 PDF", id="btn-download-report", color="danger", size="sm", className="me-2 fw-bold", disabled=True),
        
        # --- NUEVO: Botón EXCEL ---
        dbc.Button("📊 Excel", id="btn-download-excel", color="success", size="sm", className="me-3 fw-bold", disabled=True),
        
        dbc.Button("Salir", id="btn-logout", color="dark", size="sm", className="rounded-pill")
    ], brand="Panel Profesional 👨‍⚕️", color="primary", dark=True, className="mb-4 shadow-sm"),

    # Componentes invisibles para descarga
    dcc.Download(id="download-component"),       # Para PDF
    dcc.Download(id="download-excel-component"), # Para Excel (NUEVO)

    dbc.Row([
        # ... (El resto de la vista sigue igual) ...
        dbc.Col(dbc.Card([
            dbc.CardHeader("Gestión de Pacientes", className="fw-bold"),
            dbc.CardBody([
                html.Label("Seleccionar Paciente:"),
                dcc.Dropdown(id="fisio-patient-selector", placeholder="Buscar por nombre..."),
                html.Div(id="fisio-patient-info", className="mt-3 text-muted small border-top pt-2")
            ])
        ], className="shadow-sm h-100 border-0"), width=12, lg=3),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Expediente Clínico y Deportivo"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📋 Clínica", children=[
                        html.Br(),
                        html.H5("Fatiga y Esfuerzo Percibido", className="text-primary"),
                        dcc.Graph(id="fisio-quest-chart", style={"height": "300px"}),
                        html.Hr(),
                        html.Div(id="fisio-quest-table")
                    ]),

                    dbc.Tab(label="🏃 Rendimiento", children=[
                        html.Br(),
                        html.H5("Análisis de Sensores (FC + SpO2)", className="text-danger"),
                        dcc.Graph(id="fisio-ex-chart", style={"height": "300px"}),
                        html.Hr(),
                        html.H6("Registro de Sesiones"),
                        html.Div(id="fisio-ex-table")
                    ]),

                    dbc.Tab(label="🔬 Data Science", children=[
                        html.Br(),
                        html.H4("Correlación: Fatiga vs Esfuerzo", className="text-center"),
                        html.P("Análisis de dispersión para detectar patrones de riesgo.", className="text-muted text-center small"),
                        dcc.Graph(id="fisio-scatter-chart", style={"height": "400px"}),
                        dbc.Alert("Cada punto representa un día donde el paciente registró fatiga e hizo ejercicio.", color="info", className="mt-3 small")
                    ])
                ])
            ])
        ], className="shadow-sm h-100 border-0"), width=12, lg=9)
    ])
])