import os
import pandas as pd
import joblib
from datetime import datetime

# Rutas de archivos
DATA_PATH = "output/data/cleaned_cars.csv"
MODEL_PATH = "models/car_price_model.pkl"
COLUMNS_PATH = "models/model_columns.pkl"

# Verificación
if not all(os.path.exists(p) for p in [DATA_PATH, MODEL_PATH, COLUMNS_PATH]):
    raise FileNotFoundError(
        "Faltan archivos necesarios: cleaned_cars.csv, car_price_model.pkl o model_columns.pkl"
    )

# Carga de datos y modelo
df = pd.read_csv(DATA_PATH)
model = joblib.load(MODEL_PATH)
model_columns = joblib.load(COLUMNS_PATH)

# Pre-cálculos
avg_price_total = df["precio_crc"].mean()
min_price_total = df["precio_crc"].min()
max_price_total = df["precio_crc"].max()

stats_by_brand = (
    df.groupby("marca")["precio_crc"].agg(["min", "max", "mean"]).round(0).reset_index()
)
stats_by_brand.columns = ["Marca", "Precio Mínimo", "Precio Máximo", "Precio Promedio"]

depreciation_data = (
    df.groupby(["marca", "modelo", "antiguedad"])["precio_crc"].mean().reset_index()
)

geo_counts = df["provincia"].value_counts().reset_index()
geo_counts.columns = ["Provincia", "Cantidad de Vehículos"]

geo_prices = df.groupby("provincia")["precio_crc"].mean().reset_index()
geo_prices.columns = ["Provincia", "Precio Promedio (CRC)"]
geo_prices = geo_prices.sort_values("Precio Promedio (CRC)", ascending=False)
