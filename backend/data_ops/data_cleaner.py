import os
import glob
import json
from datetime import datetime


def corregir_json(file_path):
    """Corrige un archivo JSON según las reglas definidas y lo sobrescribe."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Intercambiar precios si están invertidos
    precio_crc = data.get("precio_usd")
    precio_usd = data.get("precio_crc")
    data["precio_crc"] = precio_crc
    data["precio_usd"] = precio_usd

    # 2. Normalizar información general
    info_general = data.get("informacion_general", {})
    if "kilometraje_number" in info_general:
        try:
            info_general["kilometraje_number"] = int(info_general["kilometraje_number"])
        except:
            info_general["kilometraje_number"] = None
    if "cilindrada_number" in info_general:
        try:
            info_general["cilindrada_number"] = int(info_general["cilindrada_number"])
        except:
            info_general["cilindrada_number"] = None

    # 3. Normalizar año
    try:
        data["año"] = int(data.get("año", 0))
    except:
        data["año"] = None

    # 4. Calcular antigüedad (opcional)
    if data["año"]:
        current_year = datetime.now().year
        antiguedad = current_year - data["año"]
        if antiguedad < 0:
            antiguedad = 0
        data["antiguedad"] = antiguedad

    # 5. Sobrescribir el JSON con las correcciones
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ Corregido: {file_path}")


def main():
    data_path = "datos_vehiculos"
    json_files = glob.glob(os.path.join(data_path, "*.json"))

    if not json_files:
        print(f"Error: No se encontraron archivos JSON en '{data_path}'.")
        return

    print(f"Se encontraron {len(json_files)} archivos JSON para corregir...")

    for file in json_files:
        corregir_json(file)

    print("-" * 50)
    print("✅ Proceso completado. Todos los archivos fueron corregidos.")
    print("-" * 50)


if __name__ == "__main__":
    main()
