# CLAUDE.md — SnowTrack · Guía de contexto y normas

> **Leer siempre al inicio de cada sesión antes de tocar cualquier archivo.**

---

## Qué es esta app

**SnowTrack** es un monitor de rendimiento deportivo para esquiadores y snowboarders. Simula telemetría biomédica (ECG, FC, SpO₂) durante descensos en altitud, registra el historial del atleta y ofrece un panel al entrenador con análisis avanzado.

Stack: **Python · Dash · Plotly · SQLite · Bootstrap (dbc)**

---

## Arquitectura de archivos

| Archivo | Responsabilidad |
|---------|----------------|
| `app.py` | Punto de entrada, instancia Dash, registra todos los módulos |
| `database.py` | Clase `db` (métodos de clase), define `BADGES`, crea/migra SQLite |
| `layouts.py` | Todas las vistas HTML (sin lógica). Funciones y variables globales de layout |
| `logic_auth.py` | Callbacks de login, registro y logout |
| `logic_nav.py` | Callback de routing (`render`) y redirección automática |
| `logic_athlete.py` | Clase `athlete` — todos los callbacks del atleta |
| `logic_simulation.py` | Clase `simulation` — ECG en tiempo real, timer, guardar sesión |
| `logic_physio.py` | Clase `physio` — panel del entrenador, gráficas, mapa, notas, PDF/Excel |
| `logic_pdf.py` | Generador de informes PDF individuales (para el fisio) |
| `logic_export.py` | Generador de Excel global (todos los atletas) |
| `physiological_model.py` | Modelo fisiológico: HR ramp, SpO₂ por altitud, ECG template (PhysioNet/sintético) |
| `assets/custom.css` | CSS global con variables CSS, tema mountain |

---

## Base de datos (SQLite — `users.db`)

### Tablas actuales

**`users`**: `id, user, pass, role, age, weight, height, first_login, notes`
- `role`: `"paciente"` (atleta) | `"fisio"` (entrenador)
- `first_login=1` → redirige al perfil con onboarding tutorial al hacer login
- `notes`: texto libre para anotaciones del entrenador sobre el atleta

**`quest`**: `id, user_id, fatiga, rpe, sueno, altitud_pernocta, created_at`
- Diario diario del atleta (fatiga 1-10, RPE 1-10, horas sueño, altitud donde pernoctó)

**`sesiones_nieve`**: `id, user_id, modalidad, altitud_ejercicio, duration_sec, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, metros_descenso, created_at`
- `modalidad`: **`"esqui"`** | **`"snowboard"`** — NUNCA usar tipos antiguos ("run", "bike", "squat")

### Todos los métodos de `db`

| Método | Devuelve |
|--------|----------|
| `verify(user, password)` | `{id, role}` o `None` |
| `register(user, password, role)` | `True/False` |
| `get_user_info(user_id)` | `{name, age, weight, height}` |
| `update_profile(user_id, age, weight, height)` | `True/False` |
| `is_first_login(user_id)` | `bool` |
| `mark_profile_complete(user_id)` | — |
| `save_quest(user_id, fatiga, rpe, sueno, altitud)` | `True/False` |
| `get_history(user_id)` | últimas 5 entradas del diario |
| `get_chart_data(user_id)` | todas las entradas del diario (para gráficas) |
| `save_exercise(user_id, ex_type, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud, metros)` | `True/False` — guarda sesión del monitor en directo |
| `save_exercise_manual(user_id, ex_type, duration, avg_hr, max_hr, min_hr, avg_spo2, min_spo2, altitud, metros, date_str)` | `True/False` — guarda sesión con fecha personalizada |
| `get_exercise_history(user_id)` | todas las sesiones, ORDER BY DESC |
| `get_specific_history(user_id, ex_type)` | sesiones filtradas por modalidad |
| `get_total_metros(user_id)` | `int` metros acumulados totales |
| `get_ranking()` | `[{id, name, metros}]` ORDER BY DESC |
| `get_badge_info(total_metros)` | `(current_badge, next_badge)` — badge = `{nombre, metros, icono, color}` |
| `get_last_health_status(user_id)` | `"ok"` \| `"warning"` \| `"danger"` \| `None` |
| `get_all_patients()` | `[{label, value}]` para el Dropdown del fisio |
| `get_correlation_data(user_id)` | `[{date, fatiga, hr_max, type}]` — días con diario y sesión |
| `get_heatmap_data(user_id)` | `[{altitud, metros, max_hr, modalidad}]` — para mapa geográfico |
| `get_activity_by_day(user_id, days=90)` | `[(date, metros, max_hr, count)]` — agrupado por día |
| `get_monthly_metros(user_id)` | `(metros, sessions_count)` del mes corriente |
| `get_acwr(user_id)` | `{acwr, acute, chronic_weekly}` — ratio carga aguda:crónica |
| `get_weekly_summary(user_id)` | `{this_metros, this_sessions, prev_metros, prev_sessions}` — ventanas de 7 días rodantes |
| `save_athlete_note(user_id, note)` | `True/False` — guarda notas del entrenador |
| `get_athlete_note(user_id)` | `str` — nota del entrenador |

### Índices de columnas en consultas (crítico — no equivocarse)

`get_exercise_history`: 0=date, 1=modalidad, 2=duration_sec, 3=avg_hr, 4=max_hr, 5=min_hr, 6=avg_spo2, 7=min_spo2, 8=altitud_ejercicio

`get_specific_history`: 0=date, 1=duration_sec, 2=avg_hr, 3=max_hr, 4=min_hr, 5=avg_spo2, 6=min_spo2, 7=altitud_ejercicio

`get_history` / `get_chart_data`: 0=date, 1=fatiga, 2=rpe, 3=sueno, 4=altitud_pernocta

---

## Estado actual de cada página

### `/app` — Home del atleta
- **Hero** + `id="home-stats-row"` (4 tarjetas: última sesión, insignia+progreso, fatiga muscular, objetivo mensual `sm=6 lg=3`)
- `id="home-acwr-section"` — tarjeta ACWR con barra 0-2.0, badge de estado, resumen semanal (metros + sesiones + comparativa semana anterior)
- **Menú** — 4 tarjetas de navegación (monitor, historial, ranking, perfil)
- Modal `id="modal-missing-profile"` si el usuario no tiene perfil completo

### `/app/monitor` — Monitor biomédico
- **Panel izquierdo**: radio de modalidad, slider altitud, `id="risk-calculator"` (semáforo pre-sesión: combina SpO₂ esperada + fatiga + sueño), timer, botón INICIAR/DETENER, `id="monitor-rest-info"` (resumen última sesión o instrucciones primera vez)
- **Panel derecho**: `id="monitor-hr-kpi"` + `id="monitor-spo2-kpi"` (KPIs en tiempo real), ECG en tiempo real (`id="ecg-graph"`), stores: `is-running-store`, `locked-ex-store`, `session-biometrics-store`
- Interval: `id="clock-interval"` cada 500ms

### `/app/history` — Historial del atleta
5 pestañas:
1. **📝 Diario de Fatiga** — sliders fatiga/RPE, input sueño, slider altitud pernocta (0-3500m), gráfica evolución, tabla últimas 5 entradas
2. **🏔️ Historial de Nieve** — tabs por modalidad (esquí/snowboard), gráfica dual-eje FC+SpO₂, `id="hr-zones-chart"` (barras apiladas Z1-Z5 últimas 10 sesiones)
3. **🫁 Aclimatación** — SpO₂ mín por sesión vs altitud, línea umbral 90%
4. **📅 Actividad** — heatmap calendario 90 días estilo GitHub
5. **➕ Añadir Sesión** — formulario registro manual (fecha, modalidad, altitud, duración, metros, FC avg/max, SpO₂ avg/min)

Store: `dcc.Store(id="manual-refresh-trigger")` — al guardar sesión manual, se incrementa y dispara refresco del historial.

### `/app/profile` — Perfil del atleta
- Formulario datos físicos (edad, peso, altura)
- Límites de seguridad calculados (FC máx teórica, IMC)
- Overlay de onboarding (`id="onboarding-overlay"`) si `first_login=1`

### `/app/ranking` — Ranking global
- Mi insignia actual + barra de progreso hacia la siguiente
- Lista de todas las insignias (bloqueadas/desbloqueadas)
- Tabla ranking global con medallas y metros

### `/fisio` — Panel del entrenador
Navbar propio (verde-teal) con botones PDF / Excel / Salir.
Selector de atleta (Dropdown) a la izquierda. Panel principal con 5 pestañas:
1. **👥 Vista General** — tabla todos los atletas: posición, nombre, semáforo, ACWR (badge colorizado), insignia, metros
2. **📋 Diario y Fatiga** — gráfica fatiga+RPE, tabla últimas entradas
3. **🏔️ Rendimiento en Pista** — gráfica FC Max+Media+SpO₂, tabla descensos por modalidad, **notas del entrenador** (textarea + guardar)
4. **🔬 Data Science** — scatter fatiga vs FC Max por tipo de ejercicio
5. **🗺️ Mapa de Actividad** — mapa geográfico de resorts con densidad de actividad

---

## `physiological_model.py` — Funciones clave

| Función | Uso |
|---------|-----|
| `preload_template()` | Descarga/cachea plantilla ECG de PhysioNet al arrancar |
| `calculate_session_params(ex_type, altitud, age)` | Precalcula parámetros biométricos al inicio de sesión |
| `finalize_session_biometrics(params, altitud, duration_sec)` | Devuelve (avg_hr, max_hr, min_hr, avg_spo2, min_spo2) al finalizar |
| `hr_at_elapsed(seconds, target_max_hr, hr_rest)` | HR instantánea con rampa exponencial (tau=90s) |
| `generate_ecg_window(n_points, seconds_elapsed, hr, noise)` | Genera ventana de señal ECG para el gráfico |
| `get_spo2_range(altitud)` | Devuelve `(spo2_lo, spo2_hi)` según tabla Severinghaus 1979 |

---

## Normas de desarrollo

### Reglas críticas

1. **Verificar siempre** con `python -c "import app; print('OK')"` tras cualquier cambio.
2. **Nunca usar tipos de ejercicio antiguos** ("run", "bike", "squat") — la BD usa `"esqui"` y `"snowboard"`.
3. **`allow_duplicate=True`** es obligatorio cuando dos callbacks comparten el mismo `Output`.
4. **Migraciones de BD**: siempre el patrón `try: ALTER TABLE ... except: pass` para añadir columnas.
5. **No mezclar lógica en layouts**: `layouts.py` solo define HTML/estructura, nunca hace queries a BD.
6. **`callback_context` debe importarse** explícitamente en cada archivo que lo use: `from dash import ..., callback_context`.
7. **Outputs nuevos en callbacks existentes**: añadir al final de la lista de Outputs y actualizar TODOS los `return` del callback.

### Estilo de código

- Sin comentarios obvios; solo cuando el WHY no es evidente.
- Sin docstrings multilínea.
- Callbacks siempre dentro de `start_callbacks()` de su clase correspondiente.
- Preferir `no_update` cuando el callback no aplica a la ruta actual (`pathname != "/app/..."`)
- Rutas de callbacks: comprobar siempre `pathname` con `if pathname != "/app/X": return no_update`

### CSS / UI

- Variables CSS: `--bg, --card, --snow, --muted, --text, --accent, --accent-dark, --pine-dark`
- Tema: gradiente azul-acero en el body, tarjetas con fondo `var(--snow)`, navbar atleta azul oscuro (`snow-navbar`), navbar fisio verde-teal (`physio-navbar`)
- Animaciones existentes: `page-enter` (fade-in), `spotlight-pulse` (glow azul), `bounce-arrow`, `fadeInUp`
- Bootstrap breakpoints: `width=12, sm=X, lg=Y` — siempre mobile-first

### Seguridad

- Contraseñas hasheadas con `werkzeug.security`
- Sesión en `dcc.Store(id="user_storage")` — client-side, no cifrado
- El logout limpia `user_storage` a `None`; el redirect callback lo manda al login

### ACWR — referencia rápida

| Ratio | Estado | Color |
|-------|--------|-------|
| `None` | Sin datos (<28 días historial) | secondary |
| < 0.8 | Carga baja / desentrenamiento | info |
| 0.8 – 1.3 | **Zona óptima** | success |
| 1.3 – 1.5 | Precaución | warning |
| > 1.5 | Riesgo de lesión | danger |

Fórmula: `ACWR = metros_últimos_7_días / (metros_últimos_28_días / 4)`

### Zonas de FC — referencia rápida

| Zona | % FC máx | Color |
|------|----------|-------|
| Z1 Recuperación | < 60% | `#94a3b8` gris |
| Z2 Base aeróbica | 60-70% | `#22c55e` verde |
| Z3 Aeróbico | 70-80% | `#a3e635` verde-lima |
| Z4 Umbral | 80-90% | `#f59e0b` naranja |
| Z5 Máximo | > 90% | `#ef4444` rojo |

Estimación por sesión: distribución triangular con `min_hr` (mínimo), `avg_hr` (moda), `max_hr` (máximo).

---

## Historial de cambios

### [Sesión 1] Oscurecer UI + Onboarding tutorial

**UI**: Gradiente del body a azul-acero, cards más oscuras, form controls con fondo `#daeef8`.

**Onboarding**: Columna `first_login` en `users`. Al registrarse → `first_login=1`. `logic_nav.py` redirige a `/app/profile`. Overlay `id="onboarding-overlay"` con tooltip flotante y botón ✕ `id="btn-dismiss-onboarding"`. Al guardar perfil o cerrar → `db.mark_profile_complete()` → `first_login=0`.

---

### [Sesión 2] Fixes críticos + gráficas

**Fix panel fisio**: `create_physio_table()` usaba tipos obsoletos ("run"/"bike"/"squat"). Cambiado a "esqui"/"snowboard".

**Gráfica ejercicios atleta**: `exercises-chart` siempre devolvía figura vacía. Ahora usa `db.get_exercise_history()` con dual-eje (FC Max barras + SpO₂ Min línea).

**Gráfica fisio**: `fisio-ex-chart` es dual-eje: FC Max barras + FC Media línea (eje izq.) + SpO₂ Min % (eje der.).

---

### [Sesión 3] Home dashboard + KPIs tiempo real

**Home**: `id="home-stats-row"` con 3 tarjetas (→ ampliado a 4 en sesión 5): semáforo última sesión, insignia+progreso, fatiga muscular.

**KPIs monitor**: `id="monitor-hr-kpi"` + `id="monitor-spo2-kpi"` encima del ECG. Se actualizan cada 500ms con color según % del límite personal.

---

### [Sesión 4] Altitud de pernocta + Monitor en reposo + Vista General fisio

**Altitud pernocta**: Slider `id="q-altitud"` en diario. Tabla del diario añade columna "Alt."

**Monitor en reposo**: `id="monitor-rest-info"` muestra resumen de última sesión o instrucciones primera vez.

**Vista General fisio**: Primera pestaña del panel con tabla de todos los atletas (ranking, semáforo, insignia, metros).

---

### [Sesión 5] 6 nuevas features

1. **Calculadora de riesgo pre-sesión** (`id="risk-calculator"`): score 0-10 combinando SpO₂ esperada + fatiga + sueño → alerta coloreada con recomendación. Se actualiza al mover el slider de altitud.

2. **Gráfica de aclimatación** (pestaña "🫁 Aclimatación"): SpO₂ mín por sesión + altitud (dual-eje) + línea umbral 90%.

3. **Calendario de actividad** (pestaña "📅 Actividad"): `go.Heatmap` 7×N semanas, últimos 90 días, colorscale azul por metros.

4. **Objetivo mensual** (4.ª tarjeta home): metros del mes + barra de progreso hacia 10.000m. `db.get_monthly_metros()` → `(metros, count)`.

5. **Registro manual** (pestaña "➕ Añadir Sesión"): formulario completo, `db.save_exercise_manual()` con `date_str` personalizado, `dcc.Store(id="manual-refresh-trigger")` para refresco automático del historial.

6. **Notas del entrenador**: textarea en pestaña "Rendimiento en Pista" del fisio. `db.save_athlete_note()` / `db.get_athlete_note()`. Columna `notes TEXT` en tabla `users`.

---

### [Sesión 6] ACWR + Zonas de FC + Fix callback_context

**ACWR + Resumen Semanal**: `id="home-acwr-section"` en home. Tarjeta con valor ACWR colorizado, barra 0-2.0 (zona óptima 0.8-1.3), metros de la semana y comparativa vs semana anterior. Columna ACWR también en Vista General del fisio. `db.get_acwr()` y `db.get_weekly_summary()`.

**Zonas de FC**: `id="hr-zones-chart"` al pie del Historial de Nieve. Barras apiladas (Z1-Z5) para las últimas 10 sesiones. Función auxiliar `_tri_cdf()` implementa CDF de distribución triangular para estimar % tiempo en cada zona.

**Fix**: `callback_context` no estaba importado en `logic_physio.py` → `NameError` al entrar al panel del fisio. Corregido añadiéndolo al import de `dash`.

---

## Pendiente / Ideas futuras (ordenado por importancia)

| # | Cambio | Área | Descripción |
|---|--------|------|-------------|
| 1 | **Alertas automáticas al fisio** | Fisio | Banner rojo en Vista General para atletas con ACWR > 1.5 + fatiga ≥ 8 simultáneamente, o sin sesión en los últimos 7 días |
| 2 | **Comparación de dos sesiones** | Atleta | Selecciona dos fechas y compara FC, SpO₂, altitud y metros en columnas paralelas |
| 3 | **Tendencia de rendimiento** | Atleta | Gráfica de FC media a la misma altitud a lo largo del tiempo — proxy de mejora cardiovascular |
| 4 | **PDF personal del atleta** | Atleta | El atleta descarga un informe de sus últimas N sesiones desde su historial, sin necesitar al fisio |
| 5 | **Historial de ACWR** | Atleta | Línea temporal del ratio semana a semana para ver periodos de sobreentrenamiento |
| 6 | **Objetivos personalizables** | Atleta | El atleta fija su propia meta mensual de metros desde el perfil (ahora está fija en 10.000m) |
| 7 | **Predictor de aclimatación** | Atleta | Basado en la curva de SpO₂ histórica, estima cuántas sesiones más necesita para aclimatarse a una altitud objetivo |
| 8 | **Recordatorio de diario** | Atleta | Aviso visual en el home si el diario de hoy no está rellenado — sin datos de diario el risk calculator y el ACWR pierden precisión |
| 9 | **Añadir sesión por el fisio** | Fisio | El entrenador registra una sesión manualmente para cualquier atleta de su lista |
| 10 | **Filtros en Vista General** | Fisio | Filtrar tabla de atletas por estado (🔴/🟡/🟢), ACWR o días sin actividad |
| 11 | **Registro de hidratación y nutrición** | Atleta | Dos sliders extra en el diario (litros de agua, calidad dieta 1-10) correlacionables con fatiga y rendimiento |
| 12 | **Registro de lesiones** | Atleta | Campo en el diario para marcar día de recuperación con zona corporal afectada; aparece en el calendario de actividad en otro color |
| 13 | **Comparar dos atletas** | Fisio | Panel de comparación directa con las curvas de dos atletas seleccionados en la misma gráfica |
| 14 | **Historial de notas del fisio** | Fisio | En lugar de sobrescribir la nota, guardar un historial con fecha de cada anotación del entrenador |
| 15 | **Exportar CSV** | Atleta | Botón en historial del atleta para descargar sus datos en bruto (complementa el Excel global del fisio) |
| 16 | **Expiración de sesión** | Técnico | `storage_type="session"` en `dcc.Store` para que el login caduque al cerrar el navegador |
| 17 | **Modo demostración** | Técnico | Opción al registrarse de cargar datos de ejemplo para ver el dashboard lleno antes de tener sesiones reales |
| 18 | **Soporte multi-idioma** | Técnico | Diccionario de textos ES/EN con toggle en el perfil |
