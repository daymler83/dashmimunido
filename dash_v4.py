import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
import time
from streamlit_extras.metric_cards import style_metric_cards
import toml
#st.set_option('deprecation.showPyplotGlobalUse', False)
import plotly.graph_objs as go
import os


# Cargar configuraciones desde config.toml
#config = toml.load("config.toml")

# Get the absolute path to the config file
base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, ".streamlit", "config.toml")

# Load the config file
config = toml.load(config_path)


# Get the base URL path from config
base_url_path = config.get("server", {}).get("baseUrlPath", "/")

# Configuración inicial del dashboard
st.set_page_config(
    page_title=config.get("page_title", "Dashboard"),
    page_icon=config.get("page_icon", "🌍"),
    layout=config.get("layout", "wide")
)



st.header(config.get("header", "INDICATORS: trends and predictions"))


#all graphs we use custom css not streamlit 
theme_plotly = None 


# load Style css
with open('style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

# Cargar el archivo Excel
data_path = config.get("data_path", "data_dash_final.xlsx")
df = pd.read_excel(data_path ,sheet_name="Sheet1")
print(df.columns)

# Filtros laterales
country = st.sidebar.multiselect(
    "SELECT COUNTRY",
    options=df["country"].unique(),
    default=df["country"].unique()
)

year_range = st.sidebar.slider(
    "SELECT YEAR RANGE",
    min_value=int(df["year"].min()),
    max_value=int(df["year"].max()),
    value=(int(df["year"].min()), int(df["year"].max())),
    step=1
)

sector = st.sidebar.selectbox(
    "SELECT SECTOR",
    options=config.get("sectors", ["Mining", "Manufacturing"]),
    index=1
)

# Filtrar actividades basadas en el sector seleccionado
activity_options = df[df["Sector"] == sector]["activityName"].unique()
activity = st.sidebar.selectbox(
    "SELECT ACTIVITY NAME",
    options=activity_options
)

# Establecer la selección por defecto a las 4 dimensiones y 4 indicadores
default_dimensions = ["Strategic", "Output", "Exports", "Investment"]  # Las 4 dimensiones por defecto


# Definir los indicadores por defecto según el sector
sector_indicators = {
    "Manufacturing": [
        "Manufacturing value added (MVA) per capita",
        "MVA annual growth rate",
        "Manufactured exports per employee",
        "Total investment as a percentage of GDP"
    ],
    "Mining": [
        "Total investment as a percentage of GDP",
        "Index of industrial production"
    ]
}

# Obtener los indicadores predeterminados según el sector seleccionado
default_indicators = sector_indicators.get(sector, [])

# Selección de dimensiones con valores por defecto
dimension = st.sidebar.multiselect(
    "SELECT UP TO FOUR DIMENSIONS",
    options=df["Dimension"].unique(),
    default=default_dimensions,
    max_selections=4
)

# Verificar si hay dimensiones seleccionadas antes de mostrar los indicadores
if dimension:
    # Filtrar variables en función de las dimensiones seleccionadas
    variable_options = df[df["Dimension"].isin(dimension)]["variableName"].unique()

    # Obtener indicadores por defecto según el sector seleccionado
    default_indicators = sector_indicators.get(sector, [])

    # Selección de hasta 4 indicadores con valores por defecto
    variable = st.sidebar.multiselect(
        "SELECT UP TO FOUR INDICATORS",
        options=variable_options,
        default=[ind for ind in default_indicators if ind in variable_options],  # Filtrar solo los que existen en los datos
        max_selections=4
    )
else:
    variable = []


# Filtrar solo si hay dimensiones e indicadores seleccionados
if dimension and variable:
    df_selection = df.query(
        "country in @country & year >= @year_range[0] & year <= @year_range[1] & activityName in @activity & variableName in @variable"
    )
else:
    df_selection = pd.DataFrame()  # Si no se selecciona nada, dataframe vacío


# Mostrar los datos filtrados
with st.expander("VIEW DATA"):
    st.dataframe(df_selection, use_container_width=True)



# Crear un diccionario que relacione cada variable con su unidad de medida
unit_mapping = df_selection.groupby("variableName")["unidadMedida"].first().to_dict()

# Diccionario para renombrar indicadores en los gráficos
variable_rename_map = {
    "MVA (Manufacturing Value Added), constant 2015 USD": "Manufacturing value added(MVA), constant 2015 USD",
    "MVA Growth Rate": "MVA annual growth rate (%)",
    "Manufactured Exports per Employee": "Exports per employee",
    "Total investment as a percentage of output": "Total investment as a percentage of output"
}

# Reemplazar nombres en la selección por defecto
default_indicators = list(variable_rename_map.keys())



# Define different marker styles for each graph
marker_styles = ["circle", "square", "triangle-up", "cross"]

# Function to create line charts with different markers and highlight Saudi Arabia
def plot_line_graph(variable_name, col, marker_style):
    """Generates line charts with different markers, highlighting Saudi Arabia."""
    y_axis_label = unit_mapping.get(variable_name, "Unknown")

    # Ensure data exists for the selected variable
    df_filtered = df_selection[df_selection["variableName"] == variable_name]
    if df_filtered.empty:
        st.warning(f"No data available for {variable_name}")
        return

    fig = px.line(
        df_filtered,
        x="year",
        y="value",
        color="country",
        title=f"{variable_rename_map.get(variable_name, variable_name)}",
        markers=True
    )

    # Apply thickness and color to Saudi Arabia's line, and set different markers
    for trace in fig.data:
        if trace.name == "Saudi Arabia":
            trace.line.width = 4  # Thicker line
            trace.line.color = "green"  # Highlight color
        else:
            trace.line.width = 1.5  # Normal lines
        
        # Apply different marker styles for each graph
        trace.marker.symbol = marker_style

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=y_axis_label,
        legend_title="Country / Activity",
        font=dict(color=config['theme']['textColor'])
    )

    with col:
        st.plotly_chart(fig, use_container_width=True)

# Generate graphs with the correct layout
if len(variable) > 0:
    st.subheader("Data Analysis")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # Generate line charts with different marker styles
    if len(variable) > 0:
        plot_line_graph(variable[0], col1, marker_styles[0])  # Circle markers
    if len(variable) > 1:
        plot_line_graph(variable[1], col2, marker_styles[1])  # Square markers
    if len(variable) > 2:
        plot_line_graph(variable[2], col3, marker_styles[2])  # Triangle markers
    if len(variable) > 3:
        plot_line_graph(variable[3], col4, marker_styles[3])  # Cross markers



# Pie de página o notas adicionales
#st.sidebar.image(config.get("logo_path", "data/logo1.png"), caption="")

hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)