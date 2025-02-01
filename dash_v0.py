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


# Cargar configuraciones desde config.toml
config = toml.load("config.toml")

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
data_path = config.get("data_path", "data_filt.xlsx")
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
    options=config.get("sectors", ["Mining", "Manufacturing"])
)



# Filtrar actividades basadas en el sector seleccionado
activity_options = df[df["Sector"] == sector]["activityName"].unique()
activity = st.sidebar.selectbox(
    "SELECT ACTIVITY NAME",
    options=activity_options
)


variable = st.sidebar.selectbox(
    "SELECT VARIABLE",
    options=df["variableName"].unique()
)


# Filtrar el DataFrame según las selecciones
df_selection = df.query(
    "country in @country & year >= @year_range[0] & year <= @year_range[1] & activityName in @activity & variableName == @variable"
)

# Mostrar los datos filtrados
with st.expander("VIEW DATA"):
    st.dataframe(df_selection, use_container_width=True)


y_axis_label = df_selection["unidadMedida"].iloc[0] if not df_selection.empty else "Value"

# Gráfico de serie de tiempo y gráfico de barras
if not df_selection.empty:
    st.subheader("Data Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_time_series = px.line(
            df_selection,
            x="year",
            y="valueUSD",
            color="country",
            line_group="activityName",
            title=f"{variable} Over Time by Activity and Country",
            markers=True,
            template="plotly"
        )
        fig_time_series.update_layout(
            xaxis_title="Year",
            yaxis_title=f"{y_axis_label}",
            legend_title="Country / Activity",
            #plot_bgcolor=config['theme']['secondaryBackgroundColor'],
            #paper_bgcolor=config['theme']['secondaryBackgroundColor'],
            font=dict(color=config['theme']['textColor'])
        )
        st.plotly_chart(fig_time_series, use_container_width=True)
    
    with col2:
        df_latest = df_selection.loc[df_selection.groupby('country')['year'].idxmax()]
        df_latest["country_label"] = df_latest.apply(lambda row: f"{row['country']} ({row['year']})", axis=1)
        
        fig_bar = px.bar(
            df_latest,
            x="country_label",
            y="valueUSD",
            color="country",
            title=f"Latest {variable} Data by Country",
            text_auto=True,
            template="plotly"
        )
        fig_bar.update_layout(
            xaxis_title="Country (Latest Year)",
            yaxis_title=f"{y_axis_label}",
            #plot_bgcolor=config['theme']['secondaryBackgroundColor'],
            #paper_bgcolor=config['theme']['secondaryBackgroundColor'],
            font=dict(color=config['theme']['textColor']),
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")
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
