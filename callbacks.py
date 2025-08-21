from dash import Output, Input, State
import plotly.express as px
import pandas as pd
from datetime import datetime
from utils.data_loader import df, model, model_columns, depreciation_data


def register_callbacks(app):
    # Dropdown modelos para predicción
    @app.callback(
        Output("modelo-dropdown", "options"), Input("marca-dropdown", "value")
    )
    def set_prediction_model_options(selected_marca):
        if not selected_marca:
            return []
        return [
            {"label": i, "value": i}
            for i in sorted(df[df["marca"] == selected_marca]["modelo"].unique())
        ]

    # Predicción
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
    def predict_price(
        n_clicks, marca, modelo, año, kilometraje, cilindrada, transmision
    ):
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
                "cantidad_extras": [df["cantidad_extras"].mean()],
                "combustible": [df["combustible"].mode()[0]],
            }
        )

        input_df_encoded = pd.get_dummies(input_df)
        input_df_aligned = input_df_encoded.reindex(columns=model_columns, fill_value=0)
        prediction = model.predict(input_df_aligned)[0]
        return f"Precio Estimado: ₡{prediction:,.0f}"

    # Dropdown modelos para depreciación
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

    # Gráfico de depreciación
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
