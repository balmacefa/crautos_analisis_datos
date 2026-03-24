import os
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
import httpx

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
            href="#",
            className="cr-logo",
            style={"textDecoration": "none", "color": "var(--text-primary)"},
        ),
        html.Ul(className="cr-nav-links", children=[
            html.Li(html.A("Inicio", href="#")),
            html.Li(html.A("Explorar", href="#")),
            html.Li(html.A("Comparar", href="#")),
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
        html.P(
            "Miles de vehículos verificados. Busca, compara y contacta al vendedor directo.",
            className="cr-hero-sub",
        ),
        # Search box
        html.Div(className="cr-search-box", children=[
            html.Div(className="cr-search-row", children=[
                # Keyword
                html.Div(className="cr-search-field", style={"flex": "2", "minWidth": "200px"}, children=[
                    html.Label("Búsqueda", htmlFor="search-input"),
                    dcc.Input(
                        id="search-input",
                        type="text",
                        placeholder="Ej. Toyota Corolla 2020…",
                        debounce=False,
                        n_submit=0,
                    ),
                ]),
                # Marca
                html.Div(className="cr-search-field", children=[
                    html.Label("Marca"),
                    dcc.Dropdown(
                        id="filter-marca",
                        options=[{"label": m, "value": m} for m in MARCAS],
                        placeholder="Todas",
                        clearable=True,
                        style={"fontFamily": "Inter, sans-serif"},
                    ),
                ]),
                # Año
                html.Div(className="cr-search-field", children=[
                    html.Label("Año mín."),
                    dcc.Dropdown(
                        id="filter-year",
                        options=[{"label": y, "value": y} for y in YEARS],
                        placeholder="Cualquiera",
                        clearable=True,
                        style={"fontFamily": "Inter, sans-serif"},
                    ),
                ]),
                # Precio
                html.Div(className="cr-search-field", children=[
                    html.Label("Precio máx."),
                    dcc.Dropdown(
                        id="filter-price",
                        options=PRICE_RANGES,
                        placeholder="Sin límite",
                        clearable=True,
                        style={"fontFamily": "Inter, sans-serif"},
                    ),
                ]),
                # Provincia
                html.Div(className="cr-search-field", children=[
                    html.Label("Provincia"),
                    dcc.Dropdown(
                        id="filter-province",
                        options=[{"label": p, "value": p} for p in PROVINCIES],
                        placeholder="Todo CR",
                        clearable=True,
                        style={"fontFamily": "Inter, sans-serif"},
                    ),
                ]),
                # Button
                html.Button(
                    "Buscar autos",
                    id="search-button",
                    n_clicks=0,
                    className="cr-search-btn",
                ),
            ]),
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

    return html.Div(className="cr-car-card", children=[
        # Image placeholder
        html.Div(className="cr-car-img", children=[CAR_SVG], style={"fontSize": "3.5rem"}),
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
    make_navbar(),
    make_hero(),
    # Results section
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
    # Footer
    html.Footer(className="cr-footer", children=[
        html.Div([html.Span("Cr", className="gradient-text"), html.Span("Autos")], className="cr-footer-brand"),
        html.P("El marketplace de autos más completo de Costa Rica"),
        html.P("© 2025 CrAutos. Todos los derechos reservados.", className="cr-footer-copy"),
    ]),
    # Init trigger
    dcc.Interval(id="init-trigger", interval=1000, max_intervals=1),
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_query(keyword, marca, year, price, province):
    parts = []
    if keyword:  parts.append(keyword.strip())
    if marca:    parts.append(marca)
    return " ".join(parts) if parts else ""


def fetch_cars(q: str, max_price: str = "", province: str = "", year: str = ""):
    params = {"q": q, "page": 1, "limit": 24}
    try:
        resp = httpx.get(f"{API_BASE}/api/search", params=params, timeout=8)
        resp.raise_for_status()
        cars = resp.json().get("cars", [])
    except Exception as e:
        print(f"[CrAutos] API error: {e}")
        return []

    # Client-side filtering for max price / province / year (API may not support all)
    filtered = []
    for c in cars:
        if max_price:
            try:
                if (c.get("precio_usd") or 0) > float(max_price):
                    continue
            except (ValueError, TypeError):
                pass
        if province:
            car_prov = (c.get("informacion_general") or {}).get("provincia", "")
            if province.lower() not in car_prov.lower():
                continue
        if year:
            try:
                if int(c.get("año") or 0) < int(year):
                    continue
            except (ValueError, TypeError):
                pass
        filtered.append(c)
    return filtered


def empty_state(message: str, sub: str = ""):
    return html.Div(className="cr-empty-state", children=[
        html.Div("🚗", className="cr-empty-icon"),
        html.Div(message, className="cr-empty-title"),
        html.Div(sub, className="cr-empty-sub") if sub else None,
    ])


def render_cards(cars):
    if not cars:
        return empty_state("No encontramos resultados", "Prueba con otros filtros o una búsqueda diferente.")
    return html.Div(className="cr-card-grid", children=[make_car_card(c) for c in cars])


# ---------------------------------------------------------------------------
# Callback: search
# ---------------------------------------------------------------------------
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
    prevent_initial_call=True,
)
def on_search(n_clicks, n_submit, keyword, marca, year, price, province):
    q = build_query(keyword, marca, year, price, province)
    cars = fetch_cars(q, max_price=price or "", province=province or "", year=year or "")
    count_str = f"{len(cars)} resultado{'s' if len(cars) != 1 else ''} encontrado{'s' if len(cars) != 1 else ''}"
    return render_cards(cars), count_str, "Resultados de búsqueda"


# ---------------------------------------------------------------------------
# Callback: init stats + hero prompt
# ---------------------------------------------------------------------------
@app.callback(
    Output("stat-total", "children"),
    Output("stat-price", "children"),
    Input("init-trigger", "n_intervals"),
)
def on_init(n):
    try:
        resp = httpx.get(f"{API_BASE}/api/insights/summary", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        total = data.get("total_cars", 0)
        avg_usd = data.get("avg_price_usd", 0)
        
        total_str = f"{total:,}+" if total > 0 else "—"
        price_str = f"${avg_usd:,.0f}" if avg_usd > 0 else "—"
        return total_str, price_str
    except Exception as e:
        print(f"[CrAutos] Stats error: {e}")
        return "—", "—"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
