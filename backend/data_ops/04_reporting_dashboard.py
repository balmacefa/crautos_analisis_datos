import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import joblib
import os
from datetime import datetime
import dash_bootstrap_components as dbc

# --- 1. Carga de Datos y Archivos del Modelo ---
print("Iniciando la carga de datos y modelos...")
DATA_PATH = "output/data/cleaned_cars.csv"
MODEL_PATH = "models/car_price_model.pkl"
COLUMNS_PATH = "models/model_columns.pkl"

# Verificación de la existencia de archivos necesarios
if not all(os.path.exists(p) for p in [DATA_PATH, MODEL_PATH, COLUMNS_PATH]):
    print("--- ERROR ---")
    print(
        "Faltan archivos necesarios (cleaned_cars.csv, car_price_model.pkl, o model_columns.pkl)."
    )
    print(
        "Por favor, asegúrate de ejecutar los scripts 01_data_loader.py y 03_modeling.py antes de lanzar el dashboard."
    )
    exit()

df = pd.read_csv(DATA_PATH)
model = joblib.load(MODEL_PATH)
model_columns = joblib.load(COLUMNS_PATH)
print("Datos y modelos cargados correctamente.")

# --- 2. Preparación de Datos para Análisis (Pre-cálculos) ---
print("Realizando pre-cálculos para el dashboard...")
# Estadísticas Generales
avg_price_total = df["precio_crc"].mean()
min_price_total = df["precio_crc"].min()
max_price_total = df["precio_crc"].max()

# Estadísticas por Marca
stats_by_brand = (
    df.groupby("marca")["precio_crc"].agg(["min", "max", "mean"]).round(0).reset_index()
)
stats_by_brand.columns = ["Marca", "Precio Mínimo", "Precio Máximo", "Precio Promedio"]

# Datos para el cálculo de depreciación
depreciation_data = (
    df.groupby(["marca", "modelo", "antiguedad"])["precio_crc"].mean().reset_index()
)

# Datos para el análisis geográfico
geo_counts = df["provincia"].value_counts().reset_index()
geo_counts.columns = ["Provincia", "Cantidad de Vehículos"]
geo_prices = df.groupby("provincia")["precio_crc"].mean().reset_index()
geo_prices.columns = ["Provincia", "Precio Promedio (CRC)"]
geo_prices = geo_prices.sort_values("Precio Promedio (CRC)", ascending=False)
print("Pre-cálculos completados.")

# --- 3. Inicialización de la App Dash ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Análisis de Autos Usados CR"

# --- 4. Layout de la App ---
app.layout = dbc.Container(
    [
        # Título Principal
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Dashboard de Análisis de Vehículos Usados 🚗",
                    className="text-center text-primary my-4",
                ),
                width=12,
            )
        ),
        # Sistema de Pestañas
        dbc.Tabs(
            id="tabs-principal",
            children=[
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
                                    width=12,
                                    lg=6,
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
                                    width=12,
                                    lg=6,
                                    className="mt-4",
                                ),
                            ]
                        )
                    ],
                ),
                # Pestaña 2: Análisis de Precios y Depreciación
                dbc.Tab(
                    label="💰 Análisis de Precios y Depreciación",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Precio Promedio General"),
                                            dbc.CardBody(
                                                f"₡{avg_price_total:,.0f}",
                                                className="h3 text-center text-success",
                                            ),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Precio Mínimo Registrado"),
                                            dbc.CardBody(
                                                f"₡{min_price_total:,.0f}",
                                                className="h3 text-center text-info",
                                            ),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Precio Máximo Registrado"),
                                            dbc.CardBody(
                                                f"₡{max_price_total:,.0f}",
                                                className="h3 text-center text-danger",
                                            ),
                                        ]
                                    )
                                ),
                            ],
                            className="mt-4",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Card(
                                    [
                                        html.H4(
                                            "Resumen de Precios por Marca",
                                            className="card-title text-center mt-3",
                                        ),
                                        dash_table.DataTable(
                                            columns=[
                                                {
                                                    "name": i,
                                                    "id": i,
                                                    "type": "numeric",
                                                    "format": dash_table.Format.Format(
                                                        group=","
                                                    ),
                                                }
                                                for i in stats_by_brand.columns
                                            ],
                                            data=stats_by_brand.to_dict("records"),
                                            style_cell={"textAlign": "left"},
                                            style_header={
                                                "backgroundColor": "lightgrey",
                                                "fontWeight": "bold",
                                            },
                                            page_size=10,
                                            sort_action="native",
                                            filter_action="native",
                                        ),
                                    ],
                                    body=True,
                                ),
                                className="mt-4",
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Card(
                                    [
                                        html.H4(
                                            "Calculadora de Depreciación por Modelo",
                                            className="card-title text-center mt-3",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="brand-depreciation-dropdown",
                                                        options=sorted(
                                                            df["marca"].unique()
                                                        ),
                                                        placeholder="1. Seleccione una marca...",
                                                    )
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="model-depreciation-dropdown",
                                                        placeholder="2. Seleccione un modelo...",
                                                    )
                                                ),
                                            ],
                                            className="m-3",
                                        ),
                                        dcc.Graph(id="depreciation-chart"),
                                    ],
                                    body=True,
                                ),
                                className="mt-4",
                            )
                        ),
                    ],
                ),
                # Pestaña 3: Análisis Geográfico
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
                                                text_auto=True,
                                            )
                                        )
                                    ),
                                    width=12,
                                    lg=6,
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
                                                text_auto=".2s",
                                            )
                                        )
                                    ),
                                    width=12,
                                    lg=6,
                                    className="mt-4",
                                ),
                            ]
                        )
                    ],
                ),
                # Pestaña 4: Herramienta de Predicción
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
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Marca:",
                                                        html_for="marca-dropdown",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="marca-dropdown",
                                                        options=sorted(
                                                            df["marca"].unique()
                                                        ),
                                                    ),
                                                    dbc.Label(
                                                        "Año:",
                                                        html_for="año-input",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Input(
                                                        id="año-input",
                                                        type="number",
                                                        placeholder=f"Ej: {datetime.now().year - 3}",
                                                    ),
                                                    dbc.Label(
                                                        "Cilindrada (cc):",
                                                        html_for="cilindrada-input",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Input(
                                                        id="cilindrada-input",
                                                        type="number",
                                                        placeholder="Ej: 1800",
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Modelo:",
                                                        html_for="modelo-dropdown",
                                                    ),
                                                    dcc.Dropdown(id="modelo-dropdown"),
                                                    dbc.Label(
                                                        "Kilometraje:",
                                                        html_for="kilometraje-input",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Input(
                                                        id="kilometraje-input",
                                                        type="number",
                                                        placeholder="Ej: 50000",
                                                    ),
                                                    dbc.Label(
                                                        "Tipo de Transmisión:",
                                                        html_for="transmision-dropdown",
                                                        className="mt-3",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="transmision-dropdown",
                                                        options=df[
                                                            "transmision"
                                                        ].unique(),
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
                                        className="w-100 mt-4 py-2 fs-5",
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
            ],
        ),
    ],
    fluid=True,
)


# --- 5. Callbacks de la App (Lógica Interactiva) ---


# Callback para actualizar el dropdown de modelos en la pestaña de predicción
@app.callback(Output("modelo-dropdown", "options"), Input("marca-dropdown", "value"))
def set_prediction_model_options(selected_marca):
    if not selected_marca:
        return []
    return [
        {"label": i, "value": i}
        for i in sorted(df[df["marca"] == selected_marca]["modelo"].unique())
    ]


# Callback para la predicción de precios
@app.callback(
    Output("prediction-output", "children"),
    Input("predict-button", "n_clicks"),
    [
        State("marca-dropdown", "value"),
        State("modelo-dropdown", "value"),
        State("año-input", "value"),
        State("kilometraje-input", "value"),
        State("cilindrada-input", "value"),
        State("transmision-dropdown", "value"),
    ],
)
def predict_price(n_clicks, marca, modelo, año, kilometraje, cilindrada, transmision):
    if n_clicks == 0:
        return "Ingrese los datos del vehículo para obtener una estimación."
    if not all([marca, modelo, año, kilometraje, cilindrada, transmision]):
        return "⚠️ Por favor, complete todos los campos."

    antiguedad = max(0, datetime.now().year - año)
    input_df = pd.DataFrame(
        {
            "antiguedad": [antiguedad],
            "kilometraje": [kilometraje],
            "cilindrada": [cilindrada],
            "marca": [marca],
            "modelo": [modelo],
            "transmision": [transmision],
            "cantidad_extras": [
                df["cantidad_extras"].mean()
            ],  # Usamos un promedio para simplificar
            "combustible": [
                df["combustible"].mode()[0]
            ],  # Usamos el más común para simplificar
        }
    )

    input_df_encoded = pd.get_dummies(input_df)
    input_df_aligned = input_df_encoded.reindex(columns=model_columns, fill_value=0)

    prediction = model.predict(input_df_aligned)[0]
    return f"Precio Estimado: ₡{prediction:,.0f}"


# Callback para actualizar el dropdown de modelos en la pestaña de depreciación
@app.callback(
    Output("model-depreciation-dropdown", "options"),
    Input("brand-depreciation-dropdown", "value"),
)
def set_depreciation_model_options(selected_marca):
    if not selected_marca:
        return []
    return [
        {"label": i, "value": i}
        for i in sorted(df[df["marca"] == selected_marca]["modelo"].unique())
    ]


# Callback para actualizar el gráfico de depreciación
@app.callback(
    Output("depreciation-chart", "figure"),
    Input("model-depreciation-dropdown", "value"),
    State("brand-depreciation-dropdown", "value"),
)
def update_depreciation_chart(selected_model, selected_brand):
    if not selected_model or not selected_brand:
        return px.line(
            title="Seleccione una marca y modelo para ver su curva de depreciación",
            template="plotly_white",
        )

    filtered_data = depreciation_data[
        (depreciation_data["marca"] == selected_brand)
        & (depreciation_data["modelo"] == selected_model)
    ]

    if len(filtered_data) < 2:
        return px.line(
            title=f"No hay suficientes datos para graficar la depreciación de {selected_model}",
            template="plotly_white",
        )

    fig = px.line(
        filtered_data,
        x="antiguedad",
        y="precio_crc",
        title=f"Curva de Depreciación para {selected_brand} {selected_model}",
        labels={
            "antiguedad": "Antigüedad (Años)",
            "precio_crc": "Precio Promedio (CRC)",
        },
        markers=True,
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_title="Precio Promedio (CRC)",
        xaxis_title="Antigüedad (Años)",
    )
    return fig


# --- 6. Ejecución del Servidor ---
if __name__ == "__main__":
    print("Iniciando servidor de Dash...")
    print("Accede al dashboard en http://127.0.0.1:8050")
    app.run(debug=False)
