import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import joblib
import os
from datetime import datetime
import dash_bootstrap_components as dbc  # Importar bootstrap

# --- Carga de Datos y Modelo ---
DATA_PATH = "output/data/cleaned_cars.csv"
MODEL_PATH = "models/car_price_model.pkl"
COLUMNS_PATH = "models/model_columns.pkl"

# Verificar que los archivos necesarios existan
if not all(os.path.exists(p) for p in [DATA_PATH, MODEL_PATH, COLUMNS_PATH]):
    print("Error: Faltan archivos necesarios (CSV, modelo o columnas).")
    print("Por favor, ejecuta los scripts 01, 02 y 03 antes de lanzar el dashboard.")
    exit()

df = pd.read_csv(DATA_PATH)
model = joblib.load(MODEL_PATH)
model_columns = joblib.load(COLUMNS_PATH)

# --- Preparación de datos para Geo-Análisis ---
# Contar vehículos por provincia
geo_counts = df["provincia"].value_counts().reset_index()
geo_counts.columns = ["Provincia", "Cantidad de Vehículos"]

# Calcular precio promedio por provincia
geo_prices = df.groupby("provincia")["precio_crc"].mean().reset_index()
geo_prices.columns = ["Provincia", "Precio Promedio (CRC)"]
geo_prices = geo_prices.sort_values("Precio Promedio (CRC)", ascending=False)


# --- Inicialización de la App Dash con Tema Bootstrap ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# --- Layout de la App ---
app.layout = dbc.Container(
    [
        # Título Principal
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Dashboard Avanzado de Vehículos Usados 🚗",
                    className="text-center text-primary my-4",
                ),
                width=12,
            )
        ),
        # Sistema de Pestañas
        dbc.Tabs(
            [
                # Pestaña 1: Análisis General
                dbc.Tab(
                    label="📊 Análisis General",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        dcc.Graph(
                                            figure=px.histogram(
                                                df,
                                                x="precio_crc",
                                                title="Distribución de Precios (CRC)",
                                            )
                                        )
                                    ),
                                    width=6,
                                    className="mt-4",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dcc.Graph(
                                            figure=px.scatter(
                                                df,
                                                x="kilometraje",
                                                y="precio_crc",
                                                hover_data=["marca", "modelo"],
                                                title="Precio vs. Kilometraje",
                                            )
                                        )
                                    ),
                                    width=6,
                                    className="mt-4",
                                ),
                            ]
                        )
                    ],
                ),
                # Pestaña 2: Análisis Geográfico
                dbc.Tab(
                    label="🗺️ Análisis Geográfico",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        dcc.Graph(
                                            figure=px.bar(
                                                geo_counts,
                                                x="Provincia",
                                                y="Cantidad de Vehículos",
                                                title="Cantidad de Vehículos por Provincia",
                                            )
                                        )
                                    ),
                                    width=6,
                                    className="mt-4",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dcc.Graph(
                                            figure=px.bar(
                                                geo_prices,
                                                x="Provincia",
                                                y="Precio Promedio (CRC)",
                                                title="Precio Promedio por Provincia",
                                            )
                                        )
                                    ),
                                    width=6,
                                    className="mt-4",
                                ),
                            ]
                        )
                    ],
                ),
                # Pestaña 3: Herramienta de Predicción
                dbc.Tab(
                    label="🔮 Herramienta de Predicción",
                    children=[
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3(
                                        "Estima el valor de un vehículo",
                                        className="card-title text-center",
                                    ),
                                    html.Hr(),
                                    dbc.Row(
                                        [
                                            # Columna Izquierda de Inputs
                                            dbc.Col(
                                                [
                                                    dbc.Label("Marca:"),
                                                    dcc.Dropdown(
                                                        id="marca-dropdown",
                                                        options=[
                                                            {"label": i, "value": i}
                                                            for i in sorted(
                                                                df["marca"].unique()
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Label("Año:", className="mt-3"),
                                                    dbc.Input(
                                                        id="año-input",
                                                        type="number",
                                                        placeholder="Ej: 2020",
                                                    ),
                                                    dbc.Label(
                                                        "Cilindrada (cc):",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Input(
                                                        id="cilindrada-input",
                                                        type="number",
                                                        placeholder="Ej: 1800",
                                                    ),
                                                    dbc.Label(
                                                        "Tipo de Transmisión:",
                                                        className="mt-3",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="transmision-dropdown",
                                                        options=[
                                                            {"label": i, "value": i}
                                                            for i in df[
                                                                "transmision"
                                                            ].unique()
                                                        ],
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                            # Columna Derecha de Inputs
                                            dbc.Col(
                                                [
                                                    dbc.Label("Modelo:"),
                                                    dcc.Dropdown(id="modelo-dropdown"),
                                                    dbc.Label(
                                                        "Kilometraje:", className="mt-3"
                                                    ),
                                                    dbc.Input(
                                                        id="kilometraje-input",
                                                        type="number",
                                                        placeholder="Ej: 50000",
                                                    ),
                                                    dbc.Label(
                                                        "Tipo de Combustible:",
                                                        className="mt-3",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="combustible-dropdown",
                                                        options=[
                                                            {"label": i, "value": i}
                                                            for i in df[
                                                                "combustible"
                                                            ].unique()
                                                        ],
                                                    ),
                                                    dbc.Label(
                                                        "Cantidad de Extras:",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Input(
                                                        id="extras-input",
                                                        type="number",
                                                        placeholder="Ej: 10",
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                        ]
                                    ),
                                    dbc.Button(
                                        "Predecir Precio",
                                        id="predict-button",
                                        n_clicks=0,
                                        color="primary",
                                        className="w-100 mt-4",
                                    ),
                                    html.Div(
                                        id="prediction-output",
                                        className="text-center h3 mt-4 p-3 border rounded",
                                    ),
                                ]
                            ),
                            className="mt-4",
                        )
                    ],
                ),
            ]
        ),
    ],
    fluid=True,
)

# --- Callbacks (Lógica de la App) ---


# Callback para actualizar modelos según la marca
@app.callback(Output("modelo-dropdown", "options"), Input("marca-dropdown", "value"))
def set_modelo_options(selected_marca):
    if not selected_marca:
        return []
    modelos = df[df["marca"] == selected_marca]["modelo"].unique()
    return [{"label": i, "value": i} for i in sorted(modelos)]


# Callback para la predicción
@app.callback(
    Output("prediction-output", "children"),
    Input("predict-button", "n_clicks"),
    [
        State("marca-dropdown", "value"),
        State("modelo-dropdown", "value"),
        State("año-input", "value"),
        State("kilometraje-input", "value"),
        State("cilindrada-input", "value"),
        State("combustible-dropdown", "value"),
        State("transmision-dropdown", "value"),
        State("extras-input", "value"),
    ],
)
def predict_price(
    n_clicks,
    marca,
    modelo,
    año,
    kilometraje,
    cilindrada,
    combustible,
    transmision,
    extras,
):
    if n_clicks == 0:
        return "Ingrese los datos para obtener una estimación."
    if not all(
        [marca, modelo, año, kilometraje, cilindrada, combustible, transmision, extras]
    ):
        return "⚠️ Por favor, complete todos los campos."

    current_year = datetime.now().year
    antiguedad = max(0, current_year - año)
    input_df = pd.DataFrame(
        {
            "antiguedad": [antiguedad],
            "kilometraje": [kilometraje],
            "cilindrada": [cilindrada],
            "cantidad_extras": [extras],
            "marca": [marca],
            "modelo": [modelo],
            "combustible": [combustible],
            "transmision": [transmision],
        }
    )

    input_df_encoded = pd.get_dummies(input_df)
    input_df_aligned = input_df_encoded.reindex(columns=model_columns, fill_value=0)

    prediction = model.predict(input_df_aligned)[0]
    return f"Precio Estimado: ₡{prediction:,.2f}"


# --- Ejecutar la App ---
if __name__ == "__main__":
    app.run_server(debug=True)
