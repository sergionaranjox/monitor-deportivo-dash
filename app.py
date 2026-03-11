import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from database import db
from logic_auth import auth
# --- CAMBIO AQUÍ ---
from logic_athlete import athlete 
from logic_nav import router
from logic_physio import physio
from logic_simulation import simulation

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

db.init()

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="user_storage", storage_type="session"),
    html.Div(id="page-content")
])

auth(app)
# --- Y CAMBIO AQUÍ ---
athlete(app)    
simulation(app) 
router(app)
physio(app)

if __name__ == "__main__":
    app.run(debug=True)
