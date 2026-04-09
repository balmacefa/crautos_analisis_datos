import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, ALL
import httpx
import plotly.express as px
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def empty_fig():
    fig = px.line(title="Sin datos")
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": "No hay datos disponibles para la selección actual.",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return fig

# ---------------------------------------------------------------------------
# App init — serve Google Fonts + Bootstrap for grid utilities only
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"charset": "UTF-8"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "CrAutos — El marketplace de autos más completo de Costa Rica"},
    ],
    title="CrAutos — Autos en Costa Rica",
    suppress_callback_exceptions=True,
)
server = app.server

# ---------------------------------------------------------------------------
# Helper: car SVG icon (used in card placeholder)
# ---------------------------------------------------------------------------
CAR_SVG = html.Span("🚗", style={"fontSize": "3.5rem", "opacity": "0.3"})


# ---------------------------------------------------------------------------
# Layout helper: navbar
# ---------------------------------------------------------------------------
def make_navbar():
    return html.Nav(className="cr-navbar", children=[
        html.A(
            [html.Span("Cr", className="gradient-text"), html.Span("Autos")],
            href="/",
            className="cr-logo",
            style={"textDecoration": "none", "color": "var(--text-primary)"},
        ),
        html.Ul(className="cr-nav-links", children=[
            html.Li(html.A("Inicio", href="/")),
            html.Li(html.A("Estadísticas", href="#", id="nav-stats-link")),
            html.Li(html.A("Publicar", href="#", className="cr-nav-badge")),
        ]),
    ])


# ---------------------------------------------------------------------------
# Layout helper: hero + search box
# ---------------------------------------------------------------------------
MARCAS = [
    "Toyota", "Honda", "Hyundai", "Kia", "Suzuki", "Mazda",
    "Nissan", "Ford", "Chevrolet", "Mitsubishi", "Mercedes-Benz",
    "BMW", "Volkswagen", "Subaru", "Jeep",
]

PROVINCIES = [
    "San José", "Alajuela", "Cartago", "Heredia",
    "Guanacaste", "Puntarenas", "Limón",
]

PRICE_RANGES = [
    {"label": "Hasta $5,000",    "value": "5000"},
    {"label": "Hasta $10,000",   "value": "10000"},
    {"label": "Hasta $20,000",   "value": "20000"},
    {"label": "Hasta $30,000",   "value": "30000"},
    {"label": "Hasta $50,000",   "value": "50000"},
    {"label": "Sin límite",       "value": ""},
]

YEARS = [str(y) for y in range(2025, 1999, -1)]


def make_hero():
    return html.Section(className="cr-hero", children=[
        html.P("El marketplace #1 de Costa Rica", className="cr-hero-eyebrow"),
        html.H1([
            "Encuentra tu ",
            html.Span("auto ideal", className="gradient-text"),
            html.Br(),
            "en Costa Rica",
        ]),
        # Stats bar
        html.Div(className="cr-stats", id="stats-bar", children=[
            html.Div(className="cr-stat-item", children=[
                html.Span("—", className="cr-stat-value", id="stat-total"),
                html.Span("Autos disponibles", className="cr-stat-label"),
            ]),
            html.Div(className="cr-stat-item", children=[
                html.Span("—", className="cr-stat-value", id="stat-price"),
                html.Span("Precio promedio", className="cr-stat-label"),
            ]),
            html.Div(className="cr-stat-item", children=[
                html.Span("7", className="cr-stat-value"),
                html.Span("Provincias", className="cr-stat-label"),
            ]),
        ]),
    ])


# ---------------------------------------------------------------------------
# Layout helper: car card
# ---------------------------------------------------------------------------
def make_car_card(car: dict) -> html.Div:
    marca   = car.get("marca", "—")
    modelo  = car.get("modelo", "—")
    year    = car.get("año", "")
    price   = car.get("precio_usd")
    prov    = (car.get("informacion_general") or {}).get("provincia", "")
    car_id  = car.get("car_id", "")

    title = f"{marca} {modelo}" + (f" {year}" if year else "")
    price_str = f"${price:,.0f}" if price else "Precio a consultar"

    imagen_principal = car.get("imagen_principal")
    img_component = html.Img(src=imagen_principal, className="cr-car-img") if imagen_principal else html.Div(className="cr-car-img", children=[CAR_SVG], style={"fontSize": "3.5rem"})

    return html.Div(className="cr-car-card", children=[
        # Image placeholder
        img_component,
        # Body
        html.Div(className="cr-car-body", children=[
            html.H3(title, className="cr-car-title"),
            html.Div(className="cr-car-meta", children=[
                html.Span(prov,       className="cr-badge cr-badge-province") if prov  else None,
                html.Span(str(year),  className="cr-badge cr-badge-year")     if year  else None,
            ]),
            html.Div(price_str, className="cr-car-price"),
            html.Button(
                "Ver detalles →",
                className="cr-card-btn",
                id={"type": "card-btn", "index": str(car_id)},
                n_clicks=0,
            ),
        ]),
    ])


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    # Update banner
    html.Div(
        id="update-banner",
        style={"display": "none", "backgroundColor": "#e3f2fd", "color": "#0d47a1", "padding": "8px", "textAlign": "center", "fontSize": "0.9rem", "fontWeight": "bold"}
    ),

    make_navbar(),
    make_hero(),
    
    html.Div(className="cr-main-content", children=[
        dbc.Tabs([
            dbc.Tab(label="Búsqueda de Autos", tab_id="tab-search", label_class_name="cr-tab-label", active_label_class_name="cr-tab-active"),
            dbc.Tab(label="Estadísticas / Insights", tab_id="tab-stats", label_class_name="cr-tab-label", active_label_class_name="cr-tab-active"),
        ], id="main-tabs", active_tab="tab-stats", className="cr-tabs"),
        
        html.Div(id="tab-content", className="cr-tab-content")
    ]),

    # Modal for details
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="car-detail-title"), close_button=True),
        dbc.ModalBody(id="car-detail-body", className="cr-modal-body"),
        dbc.ModalFooter(
            html.Button("Cerrar", id="close-modal", className="cr-card-btn", style={"width": "auto", "padding": "10px 24px"})
        ),
    ], id="car-detail-modal", size="lg", is_open=False, scrollable=True, centered=True),

    # Footer
    html.Footer(className="cr-footer", children=[
        html.Div([html.Span("Cr", className="gradient-text"), html.Span("Autos")], className="cr-footer-brand"),
        html.P("El marketplace de autos más completo de Costa Rica"),
        html.P("© 2025 CrAutos. Todos los derechos reservados.", className="cr-footer-copy"),
    ]),
    
    dcc.Interval(id="init-trigger", interval=1000, max_intervals=1),
])


# ---------------------------------------------------------------------------
# Layout: Search Tab
# ---------------------------------------------------------------------------
def layout_search():
    return html.Div([
        # Search box
        html.Div(className="cr-search-box", style={"marginTop": "-40px", "position": "relative", "zIndex": "100"}, children=[
            html.Div(className="cr-search-row", children=[
                html.Div(className="cr-search-field", style={"flex": "2", "minWidth": "200px"}, children=[
                    html.Label("Búsqueda", htmlFor="search-input"),
                    dcc.Input(id="search-input", type="text", placeholder="Ej. Toyota Corolla 2020…", n_submit=0),
                ]),
                html.Div(className="cr-search-field", children=[
                    html.Label("Marca"),
                    dcc.Dropdown(id="filter-marca", options=[{"label": m, "value": m} for m in MARCAS], placeholder="Todas", clearable=True),
                ]),
                html.Div(className="cr-search-field", children=[
                    html.Label("Año mín."),
                    dcc.Dropdown(id="filter-year", options=[{"label": y, "value": y} for y in YEARS], placeholder="Cualquiera", clearable=True),
                ]),
                html.Div(className="cr-search-field", children=[
                    html.Label("Precio máx."),
                    dcc.Dropdown(id="filter-price", options=PRICE_RANGES, placeholder="Sin límite", clearable=True),
                ]),
                html.Div(className="cr-search-field", children=[
                    html.Label("Provincia"),
                    dcc.Dropdown(id="filter-province", options=[{"label": p, "value": p} for p in PROVINCIES], placeholder="Todo CR", clearable=True),
                ]),
                html.Button("Buscar autos", id="search-button", n_clicks=0, className="cr-search-btn"),
            ]),
        ]),
        # Results
        html.Section(className="cr-results-section", children=[
            html.Div(className="cr-section-header", children=[
                html.Span("Resultados", className="cr-section-title", id="result-section-title"),
                html.Span("", className="cr-result-count", id="result-count"),
            ]),
            dcc.Loading(
                id="loading-results",
                type="circle",
                color="var(--accent-1)",
                children=html.Div(id="results-container"),
            ),
        ]),
    ])


# ---------------------------------------------------------------------------
# Layout: Stats Tab
# ---------------------------------------------------------------------------
def layout_stats():
    return html.Div(className="cr-stats-dashboard", children=[

        html.H2("Extremos del Mercado", className="cr-dashboard-title", style={"marginBottom": "20px"}),
        dcc.Loading(
            id="loading-market-extremes",
            type="circle",
            color="var(--accent-1)",
            children=html.Div(id="market-extremes-container", className="cr-curiosities-grid", style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(250px, 1fr))",
                "gap": "20px",
                "marginBottom": "40px"
            })
        ),

        html.H2("Curiosidades del Mercado", className="cr-dashboard-title", style={"marginBottom": "20px"}),

        dcc.Loading(
            id="loading-curiosities",
            type="circle",
            color="var(--accent-1)",
            children=html.Div(id="curiosities-container", className="cr-curiosities-grid", style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(250px, 1fr))",
                "gap": "20px",
                "marginBottom": "40px"
            })
        ),

        html.H2("Vehículos Ganga / Oportunidades", className="cr-dashboard-title"),
        html.P("Vehículos que se encuentran por lo menos un 15% por debajo del precio promedio para su modelo y año."),
        dcc.Loading(
            id="loading-opportunities",
            type="circle",
            color="var(--accent-1)",
            children=html.Div(id="opportunities-container", className="cr-card-grid", style={"marginBottom": "40px"})
        ),

        html.H2("Top 10 Modelos por Relación Precio / Kilometraje", className="cr-dashboard-title"),
        html.P("El ratio ($ / km) muestra cuánto estás pagando por cada kilómetro de uso. Un ratio bajo suele indicar un auto muy depreciado (barato relativo a su alto desgaste), mientras que un ratio alto indica que retiene su valor o tiene muy poco kilometraje."),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Mejores Relaciones (Menor $/km)"),
                    html.P("Suelen ser autos económicos pero con alto desgaste. Ideales para presupuestos ajustados."),
                    dcc.Graph(id="chart-ratio-bottom"),
                ])
            ], lg=6),
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Relaciones Más Costosas (Mayor $/km)"),
                    html.P("Suelen ser modelos que retienen mucho su valor comercial o autos casi nuevos."),
                    dcc.Graph(id="chart-ratio-top"),
                ])
            ], lg=6),
        ]),

        html.H2("Análisis de Pérdida de Valor (Depreciación)", className="cr-dashboard-title"),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Depreciación Promedio por Año de Fabricación (Top Marcas) - USD"),
                    html.P("Muestra cómo decae el precio promedio según el año del vehículo."),
                    dcc.Dropdown(
                        id="depreciation-brands",
                        options=[{"label": m, "value": m} for m in MARCAS],
                        value=["Toyota", "Hyundai", "Nissan"],
                        multi=True,
                        placeholder="Selecciona marcas para comparar",
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="chart-depreciation"),
                ])
            ], width=12),
        ]),

        html.H2("Distribución de Combustible y Transmisión", className="cr-dashboard-title", style={"marginTop": "2rem"}),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Tipos de Combustible"),
                    dcc.Graph(id="chart-fuel"),
                ])
            ], lg=6),
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Tipos de Transmisión"),
                    dcc.Graph(id="chart-transmission"),
                ])
            ], lg=6),
        ]),


        html.H2("Distribución de Transmisión por Modelo", className="cr-dashboard-title", style={"marginTop": "2rem"}),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Top Modelos (Manual vs Automático)"),
                    html.P("Desglose de la cantidad de vehículos manuales y automáticos para los modelos más populares."),
                    dcc.Graph(id="chart-models-transmissions"),
                ])
            ], lg=7),
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Buscador Específico"),
                    html.P("Selecciona un modelo para ver su distribución exacta."),
                    dcc.Dropdown(
                        id="transmission-model-select",
                        placeholder="Cargando modelos...",
                        clearable=False,
                        style={"marginBottom": "15px"}
                    ),
                    html.Div(id="transmission-model-details", style={"marginTop": "15px", "minHeight": "150px"})
                ])
            ], lg=5),
        ]),

        html.H2("Análisis del Mercado Automotriz", className="cr-dashboard-title", style={"marginTop": "2rem"}),

        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Distribución por Provincia"),
                    dcc.Graph(id="chart-provinces"),
                ])
            ], lg=6),
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Precio Promedio por Marca (Top 10) - CRC"),
                    dcc.Graph(id="chart-brands"),
                ])
            ], lg=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Modelos más frecuentes (Treemap)"),
                    dcc.Graph(id="chart-models"),
                ])
            ], width=12),
        ]),
        html.H2("Análisis por Rango de Precio (CRC)", className="cr-dashboard-title", style={"marginTop": "2rem"}),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Distribución por Rango de Precio (Millones CRC)"),
                    dcc.Graph(id="chart-price-ranges"),
                ])
            ], width=12),
        ]),
        html.H2("Analítica por Kilometraje", className="cr-dashboard-title", style={"marginTop": "2rem"}),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Kilometraje vs Precio (CRC)"),
                    dcc.Graph(id="chart-mileage-price"),
                ])
            ], lg=6),
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Kilometraje Promedio por Marca"),
                    dcc.Graph(id="chart-mileage-brand"),
                ])
            ], lg=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(className="cr-chart-card", children=[
                    html.H4("Kilometraje vs Año"),
                    dcc.Graph(id="chart-mileage-year"),
                ])
            ], width=12),
        ]),

        html.H2("Comparativa Rápida de Marcas", className="cr-dashboard-title", style={"marginTop": "2rem"}),
        html.Div(className="cr-chart-card", children=[
            html.P("Selecciona dos marcas para comparar sus estadísticas promedio generales."),
            dbc.Row([
                dbc.Col([
                    html.Label("Marca 1"),
                    dcc.Dropdown(
                        id="compare-brand-1",
                        options=[{"label": m, "value": m} for m in MARCAS],
                        value="Toyota",
                        clearable=False
                    ),
                    html.Div(id="compare-results-1", style={"marginTop": "15px"})
                ], md=6),
                dbc.Col([
                    html.Label("Marca 2"),
                    dcc.Dropdown(
                        id="compare-brand-2",
                        options=[{"label": m, "value": m} for m in MARCAS],
                        value="Hyundai",
                        clearable=False
                    ),
                    html.Div(id="compare-results-2", style={"marginTop": "15px"})
                ], md=6),
            ])
        ]),

        html.H2("Explorador Interactivo de Datos", className="cr-dashboard-title", style={"marginTop": "3rem"}),
        html.Div(className="cr-chart-card", style={"padding": "2rem"}, children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Eje X"),
                    dcc.Dropdown(
                        id="explorer-x",
                        options=[
                            {"label": "Año", "value": "año"},
                            {"label": "Kilometraje", "value": "kilometraje_number"},
                            {"label": "Precio CRC", "value": "precio_crc"},
                            {"label": "Precio USD", "value": "precio_usd"}
                        ],
                        value="año",
                        clearable=False
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Eje Y"),
                    dcc.Dropdown(
                        id="explorer-y",
                        options=[
                            {"label": "Precio CRC", "value": "precio_crc"},
                            {"label": "Precio USD", "value": "precio_usd"},
                            {"label": "Kilometraje", "value": "kilometraje_number"},
                            {"label": "Año", "value": "año"}
                        ],
                        value="precio_usd",
                        clearable=False
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Agrupar por (Color)"),
                    dcc.Dropdown(
                        id="explorer-color",
                        options=[
                            {"label": "Marca", "value": "marca"},
                            {"label": "Transmisión", "value": "transmisión"},
                            {"label": "Combustible", "value": "combustible"},
                            {"label": "Provincia", "value": "provincia"}
                        ],
                        value="transmisión",
                        clearable=False
                    ),
                ], md=4),
            ], style={"marginBottom": "20px"}),
            dcc.Graph(id="chart-explorer")
        ])
    ])


# ---------------------------------------------------------------------------
# Callbacks: Routing / Tab switching
# ---------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "tab-stats":
        return layout_stats()
    return layout_search()


@app.callback(
    Output("main-tabs", "active_tab"),
    Input("nav-stats-link", "n_clicks"),
    prevent_initial_call=True
)
def navigate_to_stats(n):
    return "tab-stats"


# ---------------------------------------------------------------------------
# Callbacks: Search implementation
# ---------------------------------------------------------------------------
def build_query(keyword, marca, year, price, province):
    parts = []
    if keyword:  parts.append(keyword.strip())
    if marca:    parts.append(marca)
    return " ".join(parts) if parts else ""


def fetch_cars(q: str, max_price: str = "", province: str = "", year: str = ""):
    params = {"q": q, "page": 1, "limit": 48}
    try:
        resp = httpx.get(f"{API_BASE}/api/search", params=params, timeout=10)
        resp.raise_for_status()
        cars = resp.json().get("cars", [])
    except Exception as e:
        print(f"[CrAutos] API error: {e}")
        return []

    filtered = []
    for c in cars:
        if max_price:
            try:
                if (c.get("precio_usd") or 0) > float(max_price): continue
            except: pass
        if province:
            car_prov = (c.get("informacion_general") or {}).get("provincia", "")
            if province.lower() not in car_prov.lower(): continue
        if year:
            try:
                if int(c.get("año") or 0) < int(year): continue
            except: pass
        filtered.append(c)
    return filtered


@app.callback(
    Output("results-container", "children"),
    Output("result-count", "children"),
    Output("result-section-title", "children"),
    Input("search-button", "n_clicks"),
    Input("search-input", "n_submit"),
    State("search-input", "value"),
    State("filter-marca", "value"),
    State("filter-year", "value"),
    State("filter-price", "value"),
    State("filter-province", "value"),
    prevent_initial_call=False,
)
def on_search(n_clicks, n_submit, keyword, marca, year, price, province):
    q = build_query(keyword, marca, year, price, province)
    cars = fetch_cars(q, max_price=price or "", province=province or "", year=year or "")
    count_str = f"{len(cars)} autos"
    
    if not cars:
        results = html.Div(className="cr-empty-state", children=[
            html.Div("🚗", className="cr-empty-icon"),
            html.Div("No encontramos resultados", className="cr-empty-title"),
            html.Div("Prueba con otros filtros o una búsqueda diferente.", className="cr-empty-sub"),
        ])
    else:
        results = html.Div(className="cr-card-grid", children=[make_car_card(c) for c in cars])
        
    return results, count_str, "Resultados de búsqueda"


# ---------------------------------------------------------------------------
# Callbacks: Car Details Modal
# ---------------------------------------------------------------------------
@app.callback(
    Output("car-detail-modal", "is_open"),
    Output("car-detail-title", "children"),
    Output("car-detail-body", "children"),
    Input({"type": "card-btn", "index": ALL}, "n_clicks"),
    Input("close-modal", "n_clicks"),
    State("car-detail-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(n_btns, n_close, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open, "", ""
    
    trig_id = ctx.triggered[0]["prop_id"]
    
    if "close-modal" in trig_id:
        return False, "", ""
    
    if any(n_btns):
        # Find which index was clicked
        btn_index = eval(trig_id.split(".")[0])["index"]
        try:
            resp = httpx.get(f"{API_BASE}/api/cars/{btn_index}", timeout=5)
            resp.raise_for_status()
            car = resp.json()
            
            title = f"{car.get('marca')} {car.get('modelo')} {car.get('año')}"
            
            info = car.get("informacion_general", {})
            vendedor = car.get("vendedor", {})
            
            imagen_principal = car.get("imagen_principal")
            img_modal_component = html.Img(src=imagen_principal, style={"width": "100%", "borderRadius": "8px"}) if imagen_principal else CAR_SVG

            body = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div(className="cr-modal-img-placeholder", children=[img_modal_component]),
                    ], md=5),
                    dbc.Col([
                        html.Div(className="cr-modal-specs", children=[
                            html.H3(f"${car.get('precio_usd', 0):,.0f}", className="cr-modal-price"),
                            html.P([html.Strong("Provincia: "), info.get("provincia", "—")]),
                            html.P([html.Strong("Combustible: "), info.get("combustible", "—")]),
                            html.P([html.Strong("Transmisión: "), info.get("transmisión", "—")]),
                            html.P([html.Strong("Kilometraje: "), info.get("kilometraje", "—")]),
                            html.P([html.Strong("Estilo: "), info.get("estilo", "—")]),
                            html.Hr(),
                            html.H5("Vendedor"),
                            html.P([html.Strong("Nombre: "), vendedor.get("nombre", "—")]),
                            html.P([html.Strong("Teléfono: "), vendedor.get("teléfono", "—")]),
                        ])
                    ], md=7)
                ]),
                html.Div(style={"marginTop": "20px"}, children=[
                    html.H5("Comentario del vendedor"),
                    html.P(info.get("comentario_vendedor", "Sin comentarios."), style={"fontStyle": "italic"})
                ]),
                html.Hr(),
                html.Button("Mostrar Datos Crudos", id="collapse-btn", n_clicks=0, className="cr-card-btn", style={"marginBottom": "10px", "width": "auto", "padding": "5px 15px"}),
                dbc.Collapse(
                    html.Pre(json.dumps(car, indent=2, ensure_ascii=False), style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "5px", "maxHeight": "300px", "overflowY": "auto"}),
                    id="collapse-data",
                    is_open=False,
                )
            ])
            
            return True, title, body
        except Exception as e:
            print(f"Error fetching car {btn_index}: {e}")
            return True, "Error", html.P("No pudimos cargar los detalles de este vehículo.")
            
    return is_open, "", ""


# ---------------------------------------------------------------------------
# Callbacks: Statistics Graphs & Explorer & Curiosities
# ---------------------------------------------------------------------------
def make_curiosity_card(title, curiosity_data):
    if not curiosity_data:
        return html.Div(className="cr-chart-card", children=[html.H4(title), html.P("Sin datos")])

    img_src = curiosity_data.get("imagen_principal")
    img_component = html.Img(src=img_src, style={"width": "100%", "height": "150px", "objectFit": "cover", "borderRadius": "8px"}) if img_src else CAR_SVG

    return html.Div(className="cr-chart-card", style={"padding": "1rem", "textAlign": "center"}, children=[
        html.H4(title, style={"fontSize": "1.1rem", "color": "var(--text-secondary)"}),
        html.Div(img_component, style={"margin": "10px 0"}),
        html.H3(curiosity_data.get("title"), style={"fontSize": "1.2rem", "margin": "10px 0"}),
        html.P(curiosity_data.get("description"), style={"fontWeight": "bold", "color": "var(--accent-1)"}),
        html.Button(
            "Ver Auto",
            className="cr-card-btn",
            id={"type": "card-btn", "index": str(curiosity_data.get("car_id"))},
            n_clicks=0,
            style={"marginTop": "10px", "padding": "5px 15px", "fontSize": "0.9rem", "width": "auto"}
        )
    ])


def make_opportunity_card(car: dict) -> html.Div:
    marca   = car.get("marca", "—")
    modelo  = car.get("modelo", "—")
    year    = car.get("año", "")
    price   = car.get("precio_usd")
    avg_price = car.get("avg_price_usd", 0)
    dev_percent = car.get("deviation_percent", 0)
    car_id  = car.get("car_id", "")

    title = f"{marca} {modelo}" + (f" {year}" if year else "")
    price_str = f"${price:,.0f}" if price else "Precio a consultar"

    imagen_principal = car.get("imagen_principal")
    img_component = html.Img(src=imagen_principal, className="cr-car-img") if imagen_principal else html.Div(className="cr-car-img", children=[CAR_SVG], style={"fontSize": "3.5rem"})

    return html.Div(className="cr-car-card", style={"border": "2px solid var(--accent-1)"}, children=[
        # Image placeholder
        img_component,
        html.Div(f"¡{dev_percent:.0f}% más barato!", style={"position": "absolute", "top": "10px", "right": "10px", "background": "var(--accent-1)", "color": "white", "padding": "5px 10px", "borderRadius": "4px", "fontWeight": "bold", "fontSize": "0.8rem", "zIndex": "10"}),
        # Body
        html.Div(className="cr-car-body", children=[
            html.H3(title, className="cr-car-title"),
            html.Div(className="cr-car-meta", children=[
                html.Span(f"Promedio: ${avg_price:,.0f}", className="cr-badge cr-badge-year", style={"background": "#f0f0f0", "color": "#666"}),
            ]),
            html.Div(price_str, className="cr-car-price", style={"color": "var(--accent-1)"}),
            html.Button(
                "Ver detalles →",
                className="cr-card-btn",
                id={"type": "card-btn", "index": str(car_id)},
                n_clicks=0,
            ),
        ]),
    ])

@app.callback(
    Output("opportunities-container", "children"),
    Input("main-tabs", "active_tab"),
)
def update_opportunities(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/opportunities", timeout=10).json()
        if not r:
            return html.Div("No se encontraron oportunidades destacadas.", className="cr-empty-state")
        return [make_opportunity_card(c) for c in r[:8]] # Show top 8
    except Exception as e:
        print(f"Opportunities error: {e}")
        return html.Div("No se pudieron cargar las oportunidades.")

@app.callback(
    Output("chart-ratio-bottom", "figure"),
    Output("chart-ratio-top", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_price_mileage_chart(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update, dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/ratios/top", timeout=10).json()
        df = pd.DataFrame(r)

        if df.empty:
            return empty_fig(), empty_fig()

        df["modelo_completo"] = df["marca"] + " " + df["modelo"]
        df_bottom = df.sort_values("ratio_usd", ascending=True).head(10)
        df_top = df.sort_values("ratio_usd", ascending=False).head(10)

        fig_bottom = px.bar(
            df_bottom, x="ratio_usd", y="modelo_completo", orientation="h",
            color="ratio_usd", template="plotly_white",
            labels={"ratio_usd": "Ratio ($ / km)", "modelo_completo": "Modelo"}
        )
        fig_bottom.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, yaxis={'categoryorder':'total descending'})

        fig_top = px.bar(
            df_top, x="ratio_usd", y="modelo_completo", orientation="h",
            color="ratio_usd", template="plotly_white",
            labels={"ratio_usd": "Ratio ($ / km)", "modelo_completo": "Modelo"}
        )
        fig_top.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, yaxis={'categoryorder':'total ascending'})

        return fig_bottom, fig_top
    except Exception as e:
        print(f"Ratios error: {e}")
        return empty_fig(), empty_fig()

@app.callback(
    Output("compare-results-1", "children"),
    Output("compare-results-2", "children"),
    Input("compare-brand-1", "value"),
    Input("compare-brand-2", "value"),
    Input("main-tabs", "active_tab"),
)
def update_brand_comparison(brand1, brand2, active_tab):
    if active_tab != "tab-stats" or not brand1 or not brand2:
        return dash.no_update, dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/brands/compare", params={"brands": f"{brand1},{brand2}"}, timeout=10).json()

        res1, res2 = html.Div("Sin datos suficientes para la marca."), html.Div("Sin datos suficientes para la marca.")

        for item in r:
            body = html.Div([
                html.P([html.Strong("Autos analizados: "), f"{item.get('count', 0)}"]),
                html.P([html.Strong("Precio Promedio: "), f"${item.get('avg_price_usd', 0):,.0f} USD"]),
                html.P([html.Strong("Kilometraje Promedio: "), f"{item.get('avg_mileage', 0):,.0f} km"]),
                html.P([html.Strong("Año Promedio: "), f"{item.get('avg_year', 0):.0f}"]),
            ], style={"padding": "10px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"})

            if item["marca"] == brand1:
                res1 = body
            elif item["marca"] == brand2:
                res2 = body

        return res1, res2
    except Exception as e:
        print(f"Compare error: {e}")
        return html.Div("Error"), html.Div("Error")


@app.callback(
    Output("chart-fuel", "figure"),
    Output("chart-transmission", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_distribution_charts(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update, dash.no_update

    try:
        r_f = httpx.get(f"{API_BASE}/api/insights/distribution/fuel", timeout=5).json()
        df_f = pd.DataFrame(r_f)
        fig_f = px.pie(df_f, names="combustible", values="count", title="Combustible", template="plotly_white", hole=0.3) if not df_f.empty else empty_fig()
        if not df_f.empty: fig_f.update_traces(textposition='inside', textinfo='percent+label')

        r_t = httpx.get(f"{API_BASE}/api/insights/distribution/transmission", timeout=5).json()
        df_t = pd.DataFrame(r_t)
        fig_t = px.pie(df_t, names="transmisión", values="count", title="Transmisión", template="plotly_white", hole=0.3) if not df_t.empty else empty_fig()
        if not df_t.empty: fig_t.update_traces(textposition='inside', textinfo='percent+label')

        return fig_f, fig_t
    except Exception as e:
        print(f"Distribution error: {e}")
        return empty_fig(), empty_fig()


@app.callback(
    Output("chart-depreciation", "figure"),
    Input("main-tabs", "active_tab"),
    Input("depreciation-brands", "value")
)
def update_depreciation_chart(active_tab, selected_brands):
    if active_tab != "tab-stats":
        return dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/depreciation", timeout=10).json()
        df = pd.DataFrame(r)

        if df.empty or not selected_brands:
            return {}

        df_filtered = df[df["marca"].isin(selected_brands)]

        # Agrupar solo por marca y año para el gráfico de líneas (promediando los modelos)
        df_grouped = df_filtered.groupby(["marca", "año"])["avg_price_usd"].mean().reset_index()
        df_grouped = df_grouped[df_grouped["año"] >= 2005] # Filtrar para una gráfica más limpia
        df_grouped = df_grouped.sort_values("año")

        fig = px.line(
            df_grouped,
            x="año",
            y="avg_price_usd",
            color="marca",
            markers=True,
            labels={"año": "Año de Fabricación", "avg_price_usd": "Precio Promedio (USD)", "marca": "Marca"},
            template="plotly_white"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400)
        return fig
    except Exception as e:
        print(f"Depreciation error: {e}")
        return {}

@app.callback(
    Output("curiosities-container", "children"),
    Input("main-tabs", "active_tab"),
)
def update_curiosities(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/curiosities", timeout=5).json()
        cards = [
            make_curiosity_card("El Más Caro", r.get("most_expensive")),
            make_curiosity_card("El Más Económico", r.get("cheapest")),
            make_curiosity_card("El Más Antiguo", r.get("oldest")),
            make_curiosity_card("Mayor Kilometraje", r.get("highest_mileage"))
        ]
        return cards
    except Exception as e:
        print(f"Curiosities error: {e}")
        return html.Div("No se pudieron cargar las curiosidades.")


@app.callback(
    Output("chart-explorer", "figure"),
    Input("main-tabs", "active_tab"),
    Input("explorer-x", "value"),
    Input("explorer-y", "value"),
    Input("explorer-color", "value")
)
def update_explorer(active_tab, x_col, y_col, color_col):
    if active_tab != "tab-stats":
        return dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/explorer", timeout=10).json()
        df = pd.DataFrame(r)

        if df.empty:
            return {}

        # Clean NaNs depending on selections
        df = df.dropna(subset=[x_col, y_col])

        labels_map = {
            "año": "Año",
            "kilometraje_number": "Kilometraje",
            "precio_crc": "Precio (CRC)",
            "precio_usd": "Precio (USD)",
            "marca": "Marca",
            "transmisión": "Transmisión",
            "combustible": "Combustible",
            "provincia": "Provincia"
        }

        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            hover_data=["marca", "modelo", "año"],
            labels=labels_map,
            template="plotly_white",
            opacity=0.7
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=500)
        return fig
    except Exception as e:
        print(f"Explorer error: {e}")
        return {}


@app.callback(
    Output("chart-provinces", "figure"),
    Output("chart-brands", "figure"),
    Output("chart-models", "figure"),
    Output("chart-price-ranges", "figure"),
    Output("chart-mileage-price", "figure"),
    Output("chart-mileage-brand", "figure"),
    Output("chart-mileage-year", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_charts(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Provinces
        r_p = httpx.get(f"{API_BASE}/api/insights/provinces", timeout=5).json()
        df_p = pd.DataFrame(r_p)
        if not df_p.empty:
            fig_p = px.bar(df_p, x="provincia", y="count", color="avg_price_crc",
                           labels={"count": "Cantidad", "provincia": "Provincia", "avg_price_crc": "Precio Avg (CRC)"},
                           color_continuous_scale="Viridis", template="plotly_white")
            fig_p.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        else:
            fig_p = {}

        # Brands
        r_b = httpx.get(f"{API_BASE}/api/insights/brands", timeout=5).json()
        df_b = pd.DataFrame(r_b).head(10)
        if not df_b.empty:
            fig_b = px.bar(df_b, x="marca", y="avg_price_crc", color="count",
                           labels={"count": "Cantidad", "marca": "Marca", "avg_price_crc": "Precio Avg (CRC)"},
                           color_continuous_scale="Bluered", template="plotly_white")
            fig_b.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        else:
            fig_b = {}

        # Models (Treemap)
        r_m = httpx.get(f"{API_BASE}/api/insights/models", timeout=5).json()
        df_m = pd.DataFrame(r_m)
        if not df_m.empty:
            fig_m = px.treemap(df_m, path=["marca", "modelo"], values="count", color="avg_price_crc",
                               color_continuous_scale="RdBu_r", template="plotly_white")
            fig_m.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=500)
        else:
            fig_m = {}

        # Price Ranges CRC
        r_pr = httpx.get(f"{API_BASE}/api/insights/price-ranges-crc", timeout=5).json()
        df_pr = pd.DataFrame(r_pr)
        # Create a formatted label like "0.5 M", "1.0 M", etc.
        if not df_pr.empty:
            df_pr = df_pr.sort_values("rango_m_crc")
            df_pr["Rango"] = df_pr["rango_m_crc"].apply(lambda x: f"{x:.1f} M")

            # Use treemap or sunburst to visualize ranges, brands, and models
            df_pr_grouped = df_pr.groupby(["Rango", "marca", "modelo"]).size().reset_index(name="count")
            fig_pr = px.treemap(df_pr_grouped, path=["Rango", "marca", "modelo"], values="count",
                                  labels={"Rango": "Rango de Precio (CRC)", "count": "Cantidad", "marca": "Marca", "modelo": "Modelo"},
                                  template="plotly_white")

            fig_pr.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=500)
        else:
            fig_pr = {}

        # Mileage Analytics
        r_mil = httpx.get(f"{API_BASE}/api/insights/mileage", timeout=5).json()
        df_mil = pd.DataFrame(r_mil)

        if not df_mil.empty:
            # Mileage vs Price
            fig_mil_price = px.scatter(df_mil, x="kilometraje_number", y="precio_crc", color="marca",
                                       labels={"kilometraje_number": "Kilometraje", "precio_crc": "Precio (CRC)", "marca": "Marca"},
                                       template="plotly_white", opacity=0.7)
            fig_mil_price.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)

            # Average Mileage by Brand
            df_mil_brand = df_mil.groupby("marca")["kilometraje_number"].mean().reset_index().sort_values("kilometraje_number", ascending=False).head(15)
            fig_mil_brand = px.bar(df_mil_brand, x="marca", y="kilometraje_number", color="kilometraje_number",
                                   labels={"marca": "Marca", "kilometraje_number": "Kilometraje Avg"},
                                   color_continuous_scale="Oranges", template="plotly_white")
            fig_mil_brand.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)

            # Mileage vs Year
            fig_mil_year = px.box(df_mil, x="año", y="kilometraje_number",
                                  labels={"año": "Año", "kilometraje_number": "Kilometraje"},
                                  template="plotly_white")
            fig_mil_year.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        else:
            fig_mil_price = {}
            fig_mil_brand = {}
            fig_mil_year = {}

        return fig_p, fig_b, fig_m, fig_pr, fig_mil_price, fig_mil_brand, fig_mil_year
    except Exception as e:
        print(f"Stats error: {e}")
        return {}, {}, {}, {}, {}, {}, {}


# ---------------------------------------------------------------------------
# Callback: Hero stats
# ---------------------------------------------------------------------------
@app.callback(
    Output("stat-total", "children"),
    Output("stat-price", "children"),
    Output("update-banner", "children"),
    Output("update-banner", "style"),
    Input("init-trigger", "n_intervals"),
    State("update-banner", "style"),
)
def on_init(n, current_style):
    if current_style is None:
        current_style = {}

    try:
        resp = httpx.get(f"{API_BASE}/api/insights/summary", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        total = data.get("total_cars", 0)
        avg_usd = data.get("avg_price_usd", 0)
        last_updated = data.get("last_updated")
        
        total_str = f"{total:,}+" if total > 0 else "—"
        price_str = f"${avg_usd:,.0f}" if avg_usd > 0 else "—"

        banner_text = ""
        banner_style = dict(current_style)

        if last_updated:
            # last_updated is an ISO timestamp, e.g., '2023-10-27T14:30:00Z'
            try:
                # Basic extraction of date and time
                date_time_part = str(last_updated).replace("T", " ").split(".")[0].replace("Z", "")
                banner_text = f"Última actualización de la base de datos: {date_time_part}"
                banner_style["display"] = "block"
            except:
                banner_style["display"] = "none"
        else:
            banner_style["display"] = "none"

        return total_str, price_str, banner_text, banner_style
    except Exception as e:
        print(f"on_init error: {e}")
        banner_style = dict(current_style)
        banner_style["display"] = "none"
        return "—", "—", "", banner_style


# ---------------------------------------------------------------------------
# Callback: Toggle Raw Data Collapse
# ---------------------------------------------------------------------------
@app.callback(
    Output("collapse-data", "is_open"),
    Input("collapse-btn", "n_clicks"),
    State("collapse-data", "is_open"),
    prevent_initial_call=True
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)

# ---------------------------------------------------------------------------
# Callbacks: Market Extremes and Transmissions
# ---------------------------------------------------------------------------
@app.callback(
    Output("market-extremes-container", "children"),
    Input("main-tabs", "active_tab"),
)
def update_market_extremes(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/market-extremes", timeout=5).json()

        def make_extreme_card(title, desc_label, data, is_price=False):
            if not data:
                return html.Div(className="cr-chart-card", children=[html.H4(title), html.P("Sin datos")])

            main_text = data.get("marca")
            if "modelo" in data:
                main_text = f"{data['marca']} {data['modelo']}"

            val_text = ""
            if is_price:
                val_text = f"₡{data.get('avg_price_crc', 0):,.0f}"
            else:
                val_text = f"{data.get('count', 0):,} anuncios"

            return html.Div(className="cr-chart-card", style={"padding": "1.5rem", "textAlign": "center", "border": "1px solid var(--accent-1)"}, children=[
                html.H4(title, style={"fontSize": "1rem", "color": "var(--text-secondary)", "textTransform": "uppercase", "letterSpacing": "1px"}),
                html.H3(main_text, style={"fontSize": "1.5rem", "margin": "15px 0", "color": "var(--text-primary)"}),
                html.Div([
                    html.Span(desc_label, style={"fontSize": "0.9rem", "color": "#666", "display": "block"}),
                    html.Strong(val_text, style={"fontSize": "1.2rem", "color": "var(--accent-1)"})
                ])
            ])

        cards = [
            make_extreme_card("Marca Más Común", "Volumen:", r.get("most_popular_brand")),
            make_extreme_card("Marca Menos Común", "Volumen:", r.get("least_popular_brand")),
            make_extreme_card("Modelo Mayor Valor", "Precio Promedio:", r.get("highest_value_model"), is_price=True),
            make_extreme_card("Modelo Menor Valor", "Precio Promedio:", r.get("lowest_value_model"), is_price=True)
        ]
        return cards
    except Exception as e:
        print(f"Market Extremes error: {e}")
        return html.Div("No se pudieron cargar los extremos del mercado.")

@app.callback(
    Output("chart-models-transmissions", "figure"),
    Output("transmission-model-select", "options"),
    Output("transmission-model-select", "value"),
    Input("main-tabs", "active_tab"),
)
def update_transmissions_chart(active_tab):
    if active_tab != "tab-stats":
        return dash.no_update, dash.no_update, dash.no_update

    try:
        r = httpx.get(f"{API_BASE}/api/insights/models/transmissions", timeout=5).json()
        df = pd.DataFrame(r)

        if df.empty:
            return empty_fig(), [], None

        df["modelo_completo"] = df["marca"] + " " + df["modelo"]

        # Options for dropdown
        models_unique = df["modelo_completo"].unique().tolist()
        options = [{"label": m, "value": m} for m in sorted(models_unique)]

        # Calculate total counts to find top models for chart
        top_models = df.groupby("modelo_completo")["count"].sum().nlargest(15).index
        df_top = df[df["modelo_completo"].isin(top_models)]

        # Group similar transmissions to simplify (Automática vs Manual)
        def simplify_trans(t):
            t_lower = t.lower() if t else ""
            if "manual" in t_lower: return "Manual"
            if "automática" in t_lower or "automatica" in t_lower: return "Automática"
            return "Otra/No Especifica"

        df_top["trans_simple"] = df_top["transmisión"].apply(simplify_trans)
        df_chart = df_top.groupby(["modelo_completo", "trans_simple"])["count"].sum().reset_index()

        fig = px.bar(
            df_chart,
            x="modelo_completo",
            y="count",
            color="trans_simple",
            title="Distribución en Top 15 Modelos",
            labels={"modelo_completo": "Modelo", "count": "Cantidad", "trans_simple": "Transmisión"},
            template="plotly_white",
            barmode="stack"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=80), height=400, xaxis={'categoryorder':'total descending'}, xaxis_tickangle=-45)

        default_val = options[0]["value"] if options else None
        return fig, options, default_val
    except Exception as e:
        print(f"Transmissions chart error: {e}")
        return empty_fig(), [], None

@app.callback(
    Output("transmission-model-details", "children"),
    Input("transmission-model-select", "value"),
    State("main-tabs", "active_tab"),
)
def update_transmission_details(selected_model, active_tab):
    if active_tab != "tab-stats" or not selected_model:
        return dash.no_update

    try:
        # Fetch all transmission data to filter by selected
        # In a real large scale app, this might be a dedicated endpoint like /api/insights/models/transmissions?model=...
        # For our purposes, we'll fetch all and filter in memory or we can query the backend.
        # Since it's cached, fetching all is fine.
        r = httpx.get(f"{API_BASE}/api/insights/models/transmissions", timeout=5).json()
        df = pd.DataFrame(r)

        if df.empty:
            return html.Div("Sin datos")

        df["modelo_completo"] = df["marca"] + " " + df["modelo"]
        df_model = df[df["modelo_completo"] == selected_model]

        if df_model.empty:
            return html.Div("No se encontraron registros para este modelo.")

        total = df_model["count"].sum()

        # Create visual breakdown
        bars = []
        for _, row in df_model.iterrows():
            pct = (row["count"] / total) * 100
            t_name = row["transmisión"].capitalize() if row["transmisión"] else "Desconocida"

            bars.append(html.Div(style={"marginBottom": "10px"}, children=[
                html.Div([
                    html.Span(t_name, style={"fontWeight": "bold"}),
                    html.Span(f" {row['count']} ({pct:.1f}%)", style={"float": "right", "color": "#666"})
                ]),
                html.Div(style={"width": "100%", "backgroundColor": "#e9ecef", "height": "10px", "borderRadius": "5px", "marginTop": "5px"}, children=[
                    html.Div(style={"width": f"{pct}%", "backgroundColor": "var(--accent-1)", "height": "100%", "borderRadius": "5px"})
                ])
            ]))

        return html.Div([
            html.H5(f"Total publicados: {total}", style={"marginBottom": "20px"}),
            html.Div(bars)
        ])
    except Exception as e:
        print(f"Transmission details error: {e}")
        return html.Div("Error cargando detalles.")
