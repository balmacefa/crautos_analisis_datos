from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime
from utils.data_loader import (
    df,
    avg_price_total,
    min_price_total,
    max_price_total,
    stats_by_brand,
    geo_counts,
    geo_prices,
)

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Dashboard de Análisis de Vehículos Usados 🚗",
                    className="text-center text-primary my-4",
                )
            )
        ),
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
                                                {"name": i, "id": i}
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
                                                    dbc.Label("Marca:"),
                                                    dcc.Dropdown(
                                                        id="marca-dropdown",
                                                        options=sorted(
                                                            df["marca"].unique()
                                                        ),
                                                    ),
                                                    dbc.Label("Año:", className="mt-3"),
                                                    dbc.Input(
                                                        id="año-input",
                                                        type="number",
                                                        placeholder=f"Ej: {datetime.now().year - 3}",
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
                                                ],
                                                md=6,
                                            ),
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
                                                        "Tipo de Transmisión:",
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
