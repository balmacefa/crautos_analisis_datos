import dash
import dash_bootstrap_components as dbc
from layout import layout
from callbacks import register_callbacks

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Análisis de Autos Usados CR"

# Layout y callbacks
app.layout = layout
register_callbacks(app)

if __name__ == "__main__":
    print("Iniciando servidor de Dash...")
    print("Accede al dashboard en http://127.0.0.1:8050")
    app.run(debug=False)
