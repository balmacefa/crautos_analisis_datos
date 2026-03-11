import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


def main():
    """Entrena un modelo de predicción de precios y guarda los resultados."""
    print("Iniciando el entrenamiento del modelo...")

    # Definir rutas
    input_path = "output/data/cleaned_cars.csv"
    model_dir = "models"
    plot_dir = "output/plots"

    if not os.path.exists(input_path):
        print(f"Error: No se encontró el archivo '{input_path}'.")
        print("Por favor, ejecuta primero el script '01_data_loader.py'.")
        return

    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)

    df = pd.read_csv(input_path)

    # 1. Preparar datos para el modelo
    features = [
        "marca",
        "modelo",
        "antiguedad",
        "kilometraje",
        "cilindrada",
        "combustible",
        "transmision",
        "cantidad_extras",
    ]
    target = "precio_crc"

    df_model = df[features + [target]].copy()

    # Convertir categóricas a numéricas (One-Hot Encoding)
    df_model = pd.get_dummies(
        df_model,
        columns=["marca", "modelo", "combustible", "transmision"],
        drop_first=True,
    )

    X = df_model.drop(target, axis=1)
    y = df_model[target]

    # Guardar las columnas del modelo para usarlas en la app
    joblib.dump(X.columns, os.path.join(model_dir, "model_columns.pkl"))

    # 2. Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 3. Entrenar el modelo
    print("Entrenando RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 4. Evaluar el modelo
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print("-" * 50)
    print("Evaluación del Modelo:")
    print(f"Error Absoluto Medio (MAE): ₡{mae:,.2f}")
    print(f"Coeficiente de Determinación (R²): {r2:.2f}")
    print("-" * 50)

    # 5. Guardar el modelo
    joblib.dump(model, os.path.join(model_dir, "car_price_model.pkl"))
    print(f"Modelo guardado en: {os.path.join(model_dir, 'car_price_model.pkl')}")

    # 6. Importancia de Características
    importances = (
        pd.Series(model.feature_importances_, index=X.columns)
        .sort_values(ascending=False)
        .nlargest(20)
    )
    plt.figure(figsize=(12, 8))
    sns.barplot(x=importances.values, y=importances.index, palette="plasma")
    plt.title("Top 20 Características más Importantes para el Precio", fontsize=16)
    plt.xlabel("Importancia Relativa", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, "feature_importance.png"))
    plt.close()
    print(f"Gráfico de importancia de características guardado en: {plot_dir}")

    print("✅ Proceso de modelado completado.")


if __name__ == "__main__":
    main()
