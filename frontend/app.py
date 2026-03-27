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

        html.H2("Análisis del Mercado Automotriz", className="cr-dashboard-title"),
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
