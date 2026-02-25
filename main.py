import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

# Importamos las clases (con nombres de archivo correctos)
from database import db
from logic_auth import auth
from logic_patient import patient
from logic_nav import router
from logic_physio import physio
from logic_simulation import simulation # <--- NUEVA IMPORTACIÓN

# Configurar App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# Iniciar DB
db.init()

# Layout Principal
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="user_storage", storage_type="session"),
    html.Div(id="page-content")
])

# Activar Lógica (todo en minúsculas)
auth(app)
patient(app)    # Lógica de base de datos del paciente
simulation(app) # Lógica de tiempo real del paciente (NUEVO)
router(app)
physio(app)

if __name__ == "__main__":
    app.run(debug=True)