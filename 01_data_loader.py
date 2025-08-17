import os
import glob
import json
import pandas as pd
from datetime import datetime


def parse_vehicle_data(file_path):
    """Lee un archivo JSON y extrae los datos a un diccionario plano."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    info_general = data.get("informacion_general", {})
    vendedor = data.get("vendedor", {})

    return {
        "marca": data.get("marca"),
        "modelo": data.get("modelo"),
        "año": data.get("año"),
        "precio_crc": data.get(
            "precio_usd"
        ),  # Corregido: el precio en CRC parece estar en la key 'precio_usd' en el JSON de ejemplo
        "precio_usd": data.get("precio_crc"),  # Corregido: viceversa
        "kilometraje": info_general.get("kilometraje_number"),
        "cilindrada": info_general.get("cilindrada_number"),
        "combustible": info_general.get("combustible"),
        "transmision": info_general.get("transmisión"),
        "estilo": info_general.get("estilo"),
        "provincia": info_general.get("provincia"),
        "cantidad_extras": len(data.get("equipamiento", [])),
        "vendedor": vendedor.get("nombre"),
    }


def main():
    """Función principal para cargar, limpiar y guardar los datos."""
    print("Iniciando el proceso de carga y limpieza...")

    # 1. Localizar los archivos JSON
    data_path = "datos_vehiculos"
    json_files = glob.glob(os.path.join(data_path, "*.json"))

    if not json_files:
        print(f"Error: No se encontraron archivos JSON en la carpeta '{data_path}'.")
        print("Asegúrate de que la carpeta exista y contenga tus archivos de datos.")
        return

    print(f"Se encontraron {len(json_files)} archivos JSON.")

    # 2. Leer y procesar cada archivo
    all_vehicles_data = [parse_vehicle_data(file) for file in json_files]
    df = pd.DataFrame(all_vehicles_data)

    # 3. Limpieza y Transformación
    print("Limpiando y transformando los datos...")

    # Convertir a numérico, los errores se convierten en NaN (Not a Number)
    numeric_cols = ["año", "precio_crc", "kilometraje", "cilindrada"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Eliminar filas donde el precio o el año son nulos, ya que son cruciales
    df.dropna(subset=["precio_crc", "año"], inplace=True)

    # Rellenar valores nulos restantes
    df["kilometraje"].fillna(df["kilometraje"].median(), inplace=True)
    df["cilindrada"].fillna(df["cilindrada"].median(), inplace=True)
    for col in ["marca", "modelo", "combustible", "transmision", "provincia"]:
        df[col].fillna("Desconocido", inplace=True)

    # Convertir 'año' a entero
    df["año"] = df["año"].astype(int)

    # 4. Feature Engineering (Crear nuevas columnas)
    current_year = datetime.now().year
    df["antiguedad"] = current_year - df["año"]
    # Asegurarse que la antiguedad no sea negativa si hay datos futuros
    df["antiguedad"] = df["antiguedad"].apply(lambda x: max(0, x))

    # 5. Guardar el resultado
    output_dir = "output/data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cleaned_cars.csv")
    df.to_csv(output_path, index=False)

    print("-" * 50)
    print(f"✅ Proceso completado. Datos limpios guardados en: {output_path}")
    print(f"Total de vehículos procesados: {len(df)}")
    print("\nVista previa de los datos:")
    print(df.head())
    print("-" * 50)


if __name__ == "__main__":
    main()
