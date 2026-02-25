from dash import Input, Output, State, no_update
# Importamos TODAS las vistas (incluida profile)
from layouts import layout_login, layout_register, layout_patient_home, layout_patient_monitor, layout_patient_history, layout_patient_profile, layout_physio

class router:
    def __init__(self, app):
        self.app = app
        self.start_callbacks()

    def start_callbacks(self):
        # 1. RENDERIZADO DE PÁGINA (Controlador de Vistas)
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname"),
            State("user_storage", "data") 
        )
        def render(path, session):
            session = session or {}
            role = session.get("role")
            
            # Rutas públicas
            if path == "/register": return layout_register
            if path == "/" or path is None: return layout_login

            # Seguridad: Si no hay rol, al login
            if not role:
                return layout_login

            # --- RUTA FISIO ---
            if role == "fisio":
                return layout_physio

            # --- RUTAS PACIENTE ---
            if role == "paciente":
                if path == "/app/monitor":
                    return layout_patient_monitor
                elif path == "/app/history":
                    return layout_patient_history
                elif path == "/app/profile":  # <--- NUEVA RUTA
                    return layout_patient_profile
                else:
                    # Por defecto al menú
                    return layout_patient_home
            
            return layout_login

        # 2. REDIRECCIÓN AUTOMÁTICA
        @self.app.callback(
            Output("url", "pathname"),
            Input("user_storage", "data"),
            State("url", "pathname"),
            prevent_initial_call=True
        )
        def redirect(session, path):
            # Si entras login/registro y ya tienes sesión -> Home
            if session and (path == "/" or path == "/register"):
                return "/app"
            
            # Si intentas entrar a /app sin sesión -> Login
            if not session and path and "/app" in path:
                return "/"
            
            return no_update