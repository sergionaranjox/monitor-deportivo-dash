# CLAUDE.md — SnowTrack · Guía de contexto y normas

## El contexto debe ser leido siempre que se quiera hacer un cambio para no perder el contexo ni las normas para realizar los cambios

## Qué es esta app

**SnowTrack** es un monitor de rendimiento deportivo para esquiadores y snowboarders. Simula telemetría biomédica (ECG, FC, SpO₂) durante descensos en altitud, registra el historial del atleta y ofrece un panel al entrenador con análisis avanzado. Stack: **Python · Dash · Plotly · SQLite · Bootstrap (dbc)**.

---

## Arquitectura de archivos

| Archivo | Responsabilidad |
|---------|----------------|
| `app.py` | Punto de entrada, instancia Dash, registra todos los módulos |
| `database.py` | Clase `db` (métodos de clase), define `BADGES`, crea/migra SQLite |
| `layouts.py` | Todas las vistas HTML (sin lógica). Funciones y variables globales de layout |
| `logic_auth.py` | Callbacks de login, registro y logout |
| `logic_nav.py` | Callback de routing (`render`) y redirección automática |
| `logic_athlete.py` | Clase `athlete` — todos los callbacks del atleta (home, monitor reposo, historial, perfil, ranking) |
| `logic_simulation.py` | Clase `simulation` — ECG en tiempo real, timer, guardar sesión |
| `logic_physio.py` | Clase `physio` — panel del entrenador, gráficas, mapa, descarga PDF/Excel |
| `logic_pdf.py` | Generador de informes PDF individuales |
| `logic_export.py` | Generador de Excel global (todos los atletas) |
| `physiological_model.py` | Modelo fisiológico: HR, SpO₂, ECG template (PhysioNet/sintético) |
| `assets/custom.css` | CSS global con variables CSS, tema mountain |

---

## Base de datos (SQLite — `users.db`)

### Tablas

**`users`**: `id, user, pass, role, age, weight, height, first_login`
- `role`: `"paciente"` (atleta) | `"fisio"` (entrenador)
- `first_login=1` → redirige al perfil con onboarding tutorial

**`quest`**: `id, user_id, fatiga, rpe, sueno, altitud_pernocta, created_at`
- Diario diario del atleta (fatiga 1-10, RPE 1-10, horas sueño, altitud donde durmió)

**`sesiones_nieve`**: `id, user_id, modalidad, altitud_ejercicio, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, metros_descenso, created_at`
- `modalidad`: `"esqui"` | `"snowboard"` ← IMPORTANTE: nunca usar tipos antiguos ("run", "bike", "squat")

### Métodos clave de `db`

- `get_history(user_id)` → `(date, fatiga, rpe, sueno, altitud_pernocta)` — últimas 5 entradas
- `get_exercise_history(user_id)` → `(date, modalidad, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud_ejercicio)` — todas las sesiones
- `get_specific_history(user_id, ex_type)` → igual pero filtrado por modalidad
- `get_last_health_status(user_id)` → `"ok"` | `"warning"` | `"danger"` | `None`
- `get_total_metros(user_id)` → int total acumulado
- `get_ranking()` → `[{id, name, metros}]` ordenado DESC
- `get_badge_info(total)` → `(current_badge, next_badge)` donde badge = `{nombre, metros, icono, color}`

### Índices de columnas en consultas (para no equivocarse)

`get_exercise_history`: 0=date, 1=modalidad, 2=duration_sec, 3=avg_hr, 4=max_hr, 5=min_hr, 6=avg_spo2, 7=min_spo2, 8=altitud_ejercicio

`get_specific_history`: 0=date, 1=duration_sec, 2=avg_hr, 3=max_hr, 4=min_hr, 5=avg_spo2, 6=min_spo2, 7=altitud_ejercicio

`get_history`: 0=date, 1=fatiga, 2=rpe, 3=sueno, 4=altitud_pernocta

---

## Normas de desarrollo

### Reglas críticas

1. **Verificar siempre** con `python -c "import app; print('OK')"` tras cualquier cambio.
2. **Nunca usar tipos de ejercicio antiguos** ("run", "bike", "squat") — la BD usa "esqui" y "snowboard".
3. **`allow_duplicate=True`** es obligatorio cuando dos callbacks comparten el mismo Output.
4. **Migraciones de BD**: usar siempre el patrón `try: ALTER TABLE ... except: pass` para añadir columnas.
5. **No mezclar lógica en layouts**: `layouts.py` solo define HTML/estructura, nunca hace queries a BD.

### Estilo de código

- Sin comentarios obvios; solo cuando el WHY no es evidente.
- Sin docstrings multilínea.
- Callbacks siempre dentro de `start_callbacks()` de su clase correspondiente.
- Outputs nuevos en callbacks existentes: añadir al final de la lista de Outputs para no romper orden.
- Preferir `no_update` sobre devolver valores vacíos cuando el callback no aplica a la ruta actual.

### CSS / UI

- Variables CSS disponibles: `--bg, --card, --snow, --muted, --text, --accent, --accent-dark, --pine-dark`
- Tema: gradiente azul-acero en el body, tarjetas con fondo `var(--snow)`, navbar atleta azul oscuro, navbar fisio verde-teal.
- Animaciones existentes: `page-enter` (fade-in), `spotlight-pulse` (glow azul), `bounce-arrow`, `fadeInUp`.
- Bootstrap breakpoints usados: `width=12, sm=X, lg=Y` — siempre diseñar mobile-first.

### Seguridad

- Contraseñas hasheadas con `werkzeug.security`.
- Sesión en `dcc.Store(id="user_storage")` — client-side, no cifrado.
- El logout limpia `user_storage` a `None`; el redirect callback lo manda al login.

---

## Historial de cambios

### [Sesión 1] Oscurecer UI

**Problema**: La interfaz era demasiado blanca/pálida.

**Cambios en `assets/custom.css`**:
- Body: `linear-gradient(160deg, #6a9eba 0%, #8fbdd6 45%, #afd0e4 100%)`
- Cards: `--card: #eaf3f9`, headers: `#bcd8ed`
- Form controls: `background: #daeef8`, border `#90c0da`
- Login card: `rgba(220,240,252,.88)`

---

### [Sesión 1] Onboarding tutorial primer login

**Problema**: Los atletas nuevos no completaban su perfil y el sistema no podía calcular límites.

**Solución**:

- `database.py`: Columna `first_login INTEGER DEFAULT 0` en `users`. Se pone a `1` al registrar, a `0` al completar perfil o cerrar tutorial.
- `logic_nav.py`: `redirect()` detecta `first_login=1` y manda a `/app/profile`.
- `layouts.py`: Overlay con `id="onboarding-overlay"` (fondo oscuro + tooltip flotante con botón ✕ `id="btn-dismiss-onboarding"`) y wrapper `id="profile-card-spotlight"` alrededor del formulario.
- `logic_athlete.py`: Callback de perfil devuelve `overlay_style` y `spotlight_class`; callback separado `dismiss_onboarding` con `allow_duplicate=True` cierra el overlay y llama a `db.mark_profile_complete()`.
- `assets/custom.css`: Clases `.onboarding-overlay`, `.onboarding-tooltip`, `.onboarding-close`, `.spotlight-active` (z-index 1000 sobre overlay 999), animación `spotlight-pulse`.

---

### [Sesión 2] Fix panel del fisio — tipos de ejercicio

**Problema crítico**: El panel del fisio mostraba "Sin datos" en las tabs de ejercicios porque usaba tipos obsoletos ("run", "bike", "squat") mientras la BD almacena "esqui"/"snowboard".

**Cambios en `logic_physio.py`**:
- `update_patient_view()`: sustituidas tabs `create_physio_table("run"/"bike"/"squat")` por `create_physio_table("esqui")` y `create_physio_table("snowboard")`.
- Scatter de correlación: tipos actualizados a "esqui" (azul `#0ea5e9`) y "snowboard" (naranja `#f97316`).

---

### [Sesión 2] Gráfica de ejercicios del atleta (antes vacía)

**Problema**: `exercises-chart` en la pestaña "Historial de Nieve" siempre devolvía una figura vacía.

**Cambios en `logic_athlete.py`** — `update_history_view()`:
- Usa `db.get_exercise_history(user_id)` para construir gráfica dual-eje:
  - Eje izquierdo: barras FC Max (`#fca5a5`)
  - Eje derecho: línea SpO₂ Min % (`#0ea5e9`), rango forzado 80-100

---

### [Sesión 2] Gráfica FC+SpO₂ en panel del fisio

**Cambios en `logic_physio.py`** — `update_patient_view()`:
- `fisio-ex-chart` ahora es dual-eje: barras FC Max + línea FC Media (eje izq.) + línea SpO₂ Min % (eje der.).

---

### [Sesión 3] Home dashboard con estadísticas personales

**Problema**: El home solo mostraba 4 tarjetas de navegación sin datos del atleta.

**Cambios**:
- `layouts.py`: `html.Div(id="home-stats-row")` entre el hero y el menú.
- `logic_athlete.py`: Nuevo callback `update_home_stats()` — dispara en `pathname == "/app"` — devuelve 3 tarjetas:
  1. **Semáforo de última sesión** (`db.get_last_health_status`) → verde/amarillo/rojo/gris
  2. **Mi insignia actual** (`db.get_badge_info`) + barra de progreso hacia la siguiente
  3. **Fatiga muscular** de la última entrada del diario (rojo si ≥8, naranja si ≥6)

---

### [Sesión 3] KPIs en tiempo real en el monitor

**Problema**: Durante una sesión solo se veía el ECG y el cronómetro; sin valores numéricos de FC ni SpO₂.

**Cambios**:
- `layouts.py`: `dbc.Row` con `id="monitor-hr-kpi"` y `id="monitor-spo2-kpi"` encima del ECG.
- `logic_simulation.py`:
  - Importa `get_spo2_range` de `physiological_model`.
  - `update_display()` devuelve 4 valores: timer, figura ECG, HR KPI, SpO₂ KPI.
  - HR: color verde/naranja/rojo según % del límite personal (`hr_max_limit` del store).
  - SpO₂: estimada con `get_spo2_range(altitud)` decrementando hasta 3 puntos por penalización de ejercicio según tiempo transcurrido.

---

### [Sesión 4] Altitud de pernocta en el diario de fatiga

**Problema**: La BD tenía la columna `altitud_pernocta` pero no había UI para introducirla.

**Cambios**:
- `layouts.py`: Slider `id="q-altitud"` (0-3500m, step 100) entre "Horas de Sueño" y el botón guardar.
- `logic_athlete.py`: `update_history_view()` añade `State("q-altitud", "value")` y pasa el valor a `db.save_quest(..., altitud or 0)`. Tabla del diario añade columna "Alt." mostrando `altitud_pernocta`.

---

### [Sesión 4] Monitor en reposo informativo

**Problema**: Al entrar al monitor sin sesión activa, el panel izquierdo estaba casi vacío.

**Cambios**:
- `layouts.py`: `html.Div(id="monitor-rest-info")` debajo del botón INICIAR en el panel de control.
- `logic_athlete.py`: Nuevo callback `update_monitor_rest()` — dispara en `pathname == "/app/monitor"` — muestra:
  - Si sin historial: alerta "Primera sesión" con instrucciones.
  - Si hay historial: resumen de última sesión (modalidad, altitud, duración, FC máx en rojo/verde, SpO₂ en rojo/azul) + límites de seguridad personales del atleta.

---

### [Sesión 4] Vista General en panel del fisio

**Problema**: El entrenador tenía que seleccionar atleta por atleta para ver su estado.

**Cambios**:
- `layouts.py`: Nueva primera pestaña `"👥 Vista General"` con `html.Div(id="fisio-overview")` en el panel del entrenador.
- `logic_physio.py`: `load_list()` añade `Output("fisio-overview", "children")` — construye tabla con todos los atletas: posición ranking (🥇🥈🥉/#N), nombre, semáforo (🔴🟡🟢⚪), insignia actual, metros totales. Filas coloreadas en rojo/amarillo según estado de salud.

---

---

### [Sesión 5] Calculadora de riesgo pre-sesión

**Problema**: No había ningún indicador antes de iniciar una sesión que combinara fatiga, sueño y altitud.

**Cambios**:
- `layouts.py`: `html.Div(id="risk-calculator")` entre el slider de altitud y el timer en el monitor.
- `logic_athlete.py`: Nuevo callback `update_risk_calculator()` — se dispara en `pathname == "/app/monitor"` y en cambios de `altitud-slider`. Calcula un `score` (0-10) sumando penalizaciones por SpO₂ esperada (<88%: +4, <92%: +2), fatiga (≥8: +3, ≥6: +2) y sueño (<4h: +3, <6h: +2). Muestra alerta coloreada (danger/warning/info/success) con nivel, factores y recomendación.
- Importa `get_spo2_range` de `physiological_model`.

---

### [Sesión 5] Gráfica de aclimatación

**Cambios**:
- `layouts.py`: Nueva pestaña `"🫁 Aclimatación"` en Historial con `dcc.Graph(id="aclimatacion-chart")`.
- `logic_athlete.py`: Nuevo callback `update_aclimatacion()` — gráfica dual-eje: SpO₂ mín (línea azul + fill, puntos coloreados verde/naranja/rojo según valor) + Altitud de ejercicio (línea gris punteada). Línea horizontal roja a 90% como umbral de hipoxia.

---

### [Sesión 5] Calendario de actividad tipo heatmap

**Cambios**:
- `layouts.py`: Nueva pestaña `"📅 Actividad"` en Historial con `dcc.Graph(id="activity-calendar")`.
- `logic_athlete.py`: Nuevo callback `update_activity_calendar()` — construye grid 7×N semanas (últimos 90 días), usa `go.Heatmap` con colorscale azul (blanco=0, azul intenso=máximo metros). Eje Y = días de la semana (Lun-Dom), eje X = semanas.
- `database.py`: Nuevo método `get_activity_by_day(user_id, days=90)` — agrupa por fecha: metros, max_hr, nº sesiones.

---

### [Sesión 5] Objetivo mensual de metros en el home

**Cambios**:
- `logic_athlete.py`: `update_home_stats()` ahora devuelve 4 tarjetas (antes 3). Nueva tarjeta "🎯 Objetivo Mensual" muestra metros del mes actual + barra de progreso hacia meta de 10.000m. Layout cambia a `sm=6, lg=3`.
- `database.py`: Nuevo método `get_monthly_metros(user_id)` → `(metros, sessions_count)` del mes corriente.

---

### [Sesión 5] Registro manual de sesión pasada

**Cambios**:
- `layouts.py`: Nueva pestaña `"➕ Añadir Sesión"` en Historial con formulario: fecha, modalidad, altitud, duración (min), metros, FC avg/max, SpO₂ avg/min. Instrucciones en columna lateral. `dcc.Store(id="manual-refresh-trigger", data=0)` en la página.
- `logic_athlete.py`: Nuevo callback `save_manual_session()` — valida campos, calcula `min_hr = avg_hr - 15`, guarda con `db.save_exercise_manual()`, actualiza `manual-refresh-trigger` para forzar recarga de tablas.
- `update_history_view()` añade `Input("manual-refresh-trigger", "data")` para refrescar automáticamente al guardar.
- `database.py`: Nuevo método `save_exercise_manual(...)` — igual que `save_exercise` pero acepta `date_str` para `created_at`.

---

### [Sesión 5] Notas del entrenador por atleta

**Cambios**:
- `layouts.py`: En la pestaña "🏔️ Rendimiento en Pista" del panel del fisio, bajo la tabla de descensos: `dbc.Textarea(id="physio-note-input")`, `dbc.Button(id="btn-save-physio-note")`, `html.Div(id="physio-note-msg")`.
- `logic_physio.py`: Nuevo callback `manage_physio_notes()` — al cambiar de atleta carga su nota (`db.get_athlete_note()`); al guardar la persiste (`db.save_athlete_note()`).
- `database.py`: Nuevos métodos `save_athlete_note(user_id, note)` y `get_athlete_note(user_id)`. Migración `ALTER TABLE users ADD COLUMN notes TEXT DEFAULT ''`.

---

---

### [Sesión 6] ACWR y Resumen Semanal

**Problema**: No había ningún indicador de carga de entrenamiento acumulada; el atleta no sabía si estaba sobreentrenando o infraentrenando.

**Cambios**:
- `database.py`: Nuevo método `get_acwr(user_id)` → `{acwr, acute, chronic_weekly}`. ACWR = metros últimos 7 días / (metros últimos 28 días / 4). Nuevo método `get_weekly_summary(user_id)` → `{this_metros, this_sessions, prev_metros, prev_sessions}` usando ventanas de 7 días rodantes.
- `layouts.py`: `html.Div(id="home-acwr-section")` entre las 4 tarjetas y el menú de navegación en el home.
- `logic_athlete.py`: Nuevo callback `update_home_acwr()` — dispara en `pathname == "/app"`. Construye una tarjeta con: valor ACWR (colorizado danger/warning/success/info), badge de etiqueta, barra de progreso 0-2.0 con zona óptima 0.8-1.3 indicada, resumen semanal (metros + sesiones + comparativa vs semana anterior).
- `logic_physio.py`: `load_list()` añade columna "ACWR" en la Vista General del fisio, con `db.get_acwr()` por atleta y badge colorizado.

---

### [Sesión 6] Zonas de Frecuencia Cardíaca

**Problema**: No había análisis de intensidad de entrenamiento; saber que la FC máx fue 175 bpm no indica si el atleta pasó más tiempo en zona aeróbica o anaeróbica.

**Cambios**:
- `layouts.py`: `dcc.Graph(id="hr-zones-chart")` al pie de la pestaña "🏔️ Historial de Nieve".
- `logic_athlete.py`: `update_history_view()` añade 6.º output `hr-zones-chart`. Función auxiliar `_tri_cdf()` implementa la CDF de distribución triangular para estimar % tiempo en cada zona usando `min_hr`, `avg_hr`, `max_hr`. Zonas: Z1 (<60% FCmax), Z2 (60-70%), Z3 (70-80%), Z4 (80-90%), Z5 (>90%). Gráfico de barras apiladas para las últimas 10 sesiones, colores: gris/verde/verde-lima/naranja/rojo.

---

## Pendiente / Ideas futuras

- Comparación lado a lado de dos sesiones
- Exportar sesión individual como PDF desde el panel del atleta
