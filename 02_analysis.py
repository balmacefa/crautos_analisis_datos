import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def main():
    """Genera y guarda visualizaciones clave del mercado de autos."""
    print("Iniciando el análisis exploratorio...")

    # Definir rutas
    input_path = "output/data/cleaned_cars.csv"
    output_dir = "output/plots"

    if not os.path.exists(input_path):
        print(f"Error: No se encontró el archivo '{input_path}'.")
        print("Por favor, ejecuta primero el script '01_data_loader.py'.")
        return

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(input_path)

    # Estilo de los gráficos
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6))

    # 1. Marcas más populares (Top 15)
    print("Generando gráfico de marcas populares...")
    top_brands = df["marca"].value_counts().nlargest(15)
    sns.barplot(x=top_brands.values, y=top_brands.index, palette="viridis")
    plt.title("Top 15 Marcas de Vehículos en el Mercado", fontsize=16)
    plt.xlabel("Cantidad de Vehículos", fontsize=12)
    plt.ylabel("Marca", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "marcas_populares.png"))
    plt.close()

    # 2. Distribución de Precios
    print("Generando histograma de precios...")
    sns.histplot(df["precio_crc"], kde=True, bins=50, color="skyblue")
    plt.title("Distribución de Precios (CRC)", fontsize=16)
    plt.xlabel("Precio en Colones (CRC)", fontsize=12)
    plt.ylabel("Frecuencia", fontsize=12)
    plt.ticklabel_format(style="plain", axis="x")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "distribucion_precios.png"))
    plt.close()

    # 3. Relación Precio vs. Kilometraje
    print("Generando gráfico de dispersión Precio vs. Kilometraje...")
    sns.scatterplot(data=df, x="kilometraje", y="precio_crc", alpha=0.5)
    plt.title("Precio vs. Kilometraje", fontsize=16)
    plt.xlabel("Kilometraje", fontsize=12)
    plt.ylabel("Precio en Colones (CRC)", fontsize=12)
    plt.ticklabel_format(style="plain", axis="y")
    plt.ticklabel_format(style="plain", axis="x")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "precio_vs_kilometraje.png"))
    plt.close()

    print("-" * 50)
    print(f"✅ Análisis completado. Gráficos guardados en la carpeta: {output_dir}")
    print("-" * 50)


if __name__ == "__main__":
    main()
