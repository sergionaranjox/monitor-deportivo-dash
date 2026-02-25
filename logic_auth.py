from dash import Input, Output, State, no_update
import dash_bootstrap_components as dbc
from database import db

class auth:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def start_callbacks(self):
        # --- LOGIN ---
        @self.app.callback(
            Output("user_storage", "data"),
            Output("out-login", "children"),
            Input("btn-login", "n_clicks"),
            State("in-user", "value"),
            State("in-pass", "value"),
            prevent_initial_call=True
        )
        def login(n, user, pwd):
            # Si no se ha pulsado el botón, limpiamos el mensaje
            if not n: 
                return no_update, ""
            
            # Si faltan campos
            if not user or not pwd: 
                return no_update, "⚠️ Introduce usuario y contraseña"
            
            # Verificamos en DB
            data = db.verify(user, pwd)
            print(f"LOGIN INTENTO: {user} -> {data}")
            
            if data: 
                return data, "" # Éxito, borramos mensaje de error
            
            return no_update, "❌ Usuario o contraseña incorrectos"

        # --- REGISTRO ---
        @self.app.callback(
            Output("out-register", "children"),
            Input("btn-register", "n_clicks"),
            State("reg-user", "value"),
            State("reg-pass", "value"),
            State("reg-role", "value"),
            prevent_initial_call=True
        )
        def register(n, user, pwd, role):
            if not n: return ""
            
            if not user or not pwd: 
                return dbc.Alert("Rellena todos los campos", color="warning")
            
            if db.register(user, pwd, role):
                return dbc.Alert("✅ Usuario creado. ¡Ahora inicia sesión!", color="success")
            
            return dbc.Alert("❌ Error: El usuario ya existe", color="danger")

        # --- LOGOUT ---
        @self.app.callback(
            Output("user_storage", "data", allow_duplicate=True),
            Input("btn-logout", "n_clicks"),
            prevent_initial_call=True
        )
        def logout(n):
            if not n: return no_update
            print("Cerrando sesión...")
            return None # Esto limpia el user_storage