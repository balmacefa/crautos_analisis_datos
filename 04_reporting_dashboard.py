import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import joblib
import os
from datetime import datetime

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

# --- Inicialización de la App Dash ---
app = dash.Dash(__name__)
server = app.server

# --- Layout de la App ---
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
    children=[
        html.H1(
            "Dashboard de Análisis de Vehículos Usados",
            style={"textAlign": "center", "color": "#333"},
        ),
        html.Hr(),
        # --- Sección de Análisis Exploratorio ---
        html.H2("Análisis Exploratorio del Mercado", style={"color": "#555"}),
        dcc.Graph(
            figure=px.histogram(
                df,
                x="precio_crc",
                title="Distribución de Precios (CRC)",
                labels={"precio_crc": "Precio en Colones"},
            )
        ),
        dcc.Graph(
            figure=px.scatter(
                df,
                x="kilometraje",
                y="precio_crc",
                hover_data=["marca", "modelo", "año"],
                title="Precio vs. Kilometraje",
                labels={
                    "kilometraje": "Kilometraje",
                    "precio_crc": "Precio en Colones",
                },
            )
        ),
        html.Hr(),
        # --- Sección de Predicción de Precio ---
        html.H2("Herramienta de Predicción de Precios 🔮", style={"color": "#555"}),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "20px",
                "padding": "20px",
                "border": "1px solid #ddd",
                "borderRadius": "5px",
            },
            children=[
                # Columna de Inputs
                html.Div(
                    [
                        html.Label("Marca:"),
                        dcc.Dropdown(
                            id="marca-dropdown",
                            options=[
                                {"label": i, "value": i}
                                for i in sorted(df["marca"].unique())
                            ],
                            placeholder="Seleccione una marca...",
                        ),
                        html.Br(),
                        html.Label("Modelo:"),
                        dcc.Dropdown(
                            id="modelo-dropdown", placeholder="Seleccione un modelo..."
                        ),
                        html.Br(),
                        html.Label("Año del vehículo:"),
                        dcc.Input(
                            id="año-input",
                            type="number",
                            placeholder="Ej: 2020",
                            style={"width": "100%"},
                        ),
                        html.Br(),
                        html.Br(),
                        html.Label("Kilometraje:"),
                        dcc.Input(
                            id="kilometraje-input",
                            type="number",
                            placeholder="Ej: 50000",
                            style={"width": "100%"},
                        ),
                    ]
                ),
                # Columna de Inputs
                html.Div(
                    [
                        html.Label("Cilindrada (cc):"),
                        dcc.Input(
                            id="cilindrada-input",
                            type="number",
                            placeholder="Ej: 1800",
                            style={"width": "100%"},
                        ),
                        html.Br(),
                        html.Br(),
                        html.Label("Tipo de Combustible:"),
                        dcc.Dropdown(
                            id="combustible-dropdown",
                            options=[
                                {"label": i, "value": i}
                                for i in df["combustible"].unique()
                            ],
                        ),
                        html.Br(),
                        html.Label("Tipo de Transmisión:"),
                        dcc.Dropdown(
                            id="transmision-dropdown",
                            options=[
                                {"label": i, "value": i}
                                for i in df["transmision"].unique()
                            ],
                        ),
                        html.Br(),
                        html.Label("Cantidad de Extras:"),
                        dcc.Input(
                            id="extras-input",
                            type="number",
                            placeholder="Ej: 10",
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ],
        ),
        html.Button(
            "Predecir Precio",
            id="predict-button",
            n_clicks=0,
            style={
                "marginTop": "20px",
                "width": "100%",
                "padding": "15px",
                "fontSize": "18px",
                "backgroundColor": "#007BFF",
                "color": "white",
                "border": "none",
                "borderRadius": "5px",
            },
        ),
        html.Div(
            id="prediction-output",
            style={
                "marginTop": "20px",
                "fontSize": "24px",
                "fontWeight": "bold",
                "textAlign": "center",
                "padding": "20px",
                "border": "2px dashed #007BFF",
                "borderRadius": "5px",
            },
        ),
    ],
)

# --- Callbacks ---


# Callback para actualizar modelos según la marca seleccionada
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
        return "Ingrese los datos del vehículo para obtener una estimación."

    if not all(
        [marca, modelo, año, kilometraje, cilindrada, combustible, transmision, extras]
    ):
        return "⚠️ Por favor, complete todos los campos."

    # Crear un DataFrame con los datos del usuario
    current_year = datetime.now().year
    antiguedad = current_year - año
    antiguedad = max(0, antiguedad)

    input_data = {
        "antiguedad": [antiguedad],
        "kilometraje": [kilometraje],
        "cilindrada": [cilindrada],
        "cantidad_extras": [extras],
        "marca": [marca],
        "modelo": [modelo],
        "combustible": [combustible],
        "transmision": [transmision],
    }
    input_df = pd.DataFrame(input_data)

    # Preprocesamiento igual al del entrenamiento
    input_df_encoded = pd.get_dummies(input_df)
    input_df_aligned = input_df_encoded.reindex(columns=model_columns, fill_value=0)

    # Realizar la predicción
    prediction = model.predict(input_df_aligned)[0]

    return f"Precio Estimado: ₡{prediction:,.2f}"


# --- Ejecutar la App ---
if __name__ == "__main__":
    app.run_server(debug=True)
