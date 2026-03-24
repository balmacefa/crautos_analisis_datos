import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import pandas as pd
import httpx

# Base URL for the FastAPI backend (adjust if running via Docker network)
API_BASE = "http://localhost:8000"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # expose Flask server for gunicorn if needed

app.layout = dbc.Container([
    html.H1("Crautos Car Search", className="my-4"),
    dbc.Row([
        dbc.Col(
            dcc.Input(
                id="search-input",
                type="text",
                placeholder="Enter search terms (e.g., 'Toyota', '2020')",
                debounce=True,
                style={"width": "100%"},
            ),
            width=8,
        ),
        dbc.Col(
            dbc.Button("Search", id="search-button", color="primary", className="w-100"),
            width=4,
        ),
    ], className="mb-3"),
    dbc.Spinner(html.Div(id="results-table"), size="lg", color="primary"),
])

def fetch_search_results(query: str, page: int = 1, limit: int = 20):
    """Call the FastAPI /api/search endpoint and return a DataFrame of results."""
    try:
        response = httpx.get(f"{API_BASE}/api/search", params={"q": query, "page": page, "limit": limit})
        response.raise_for_status()
        data = response.json()
        cars = data.get("cars", [])
        # Flatten nested JSON for display – we keep a few key fields
        rows = []
        for car in cars:
            rows.append({
                "id": car.get("car_id"),
                "marca": car.get("marca"),
                "modelo": car.get("modelo"),
                "año": car.get("año"),
                "precio_usd": car.get("precio_usd"),
                "provincia": car.get("informacion_general", {}).get("provincia"),
            })
        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return pd.DataFrame()

@app.callback(
    Output("results-table", "children"),
    Input("search-button", "n_clicks"),
    State("search-input", "value"),
    prevent_initial_call=True,
)
def update_results(n_clicks, query):
    if not query:
        return html.Div("Please enter a search term.")
    df = fetch_search_results(query)
    if df.empty:
        return html.Div("No results found.")
    # Use Dash DataTable for nice display
    return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
