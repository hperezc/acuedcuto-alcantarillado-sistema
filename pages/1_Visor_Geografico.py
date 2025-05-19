import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import geopandas as gpd
import os
import unidecode


# Configuración de la página
st.set_page_config(
    page_title="Visor Geográfico - Sistema de Predicción de Tarifas",
    page_icon="🗺️",
    layout="wide"
)

if 'last_indicador' not in st.session_state:
    st.session_state.last_indicador = None
if 'map_container' not in st.session_state:
    st.session_state.map_container = None

# Estilos CSS personalizados
st.markdown("""
<style>
    .header-style {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .subheader-style {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 1rem;
    }
    .card {
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .map-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        overflow: hidden;
    }
    .info-box {
        background-color: #e1f5fe;
        border-left: 4px solid #03a9f4;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título de la página
st.markdown("<h1 class='header-style'>🗺️ Visor Geográfico de Indicadores de Acueducto y Alcantarillado</h1>", unsafe_allow_html=True)
st.markdown("Visualización por municipio del Valle de Aburrá y del Oriente cercano de los diferentes indicadores de acueducto y alcantarillado")

# Coordenadas centrales del Valle de Aburrá (Medellín)
CENTRO_VALLE_ABURRA = [6.25184, -75.56359]

INDICADORES = {
    "Diferencial por Estrato": "diferencial_por_estrato",
    "Índice de Carga": "indice_carga",
    "Ratio de Penalización": "ratio_penalizacion",
    "Factor Operativo": "factor_operativo",
    "Índice de Penalización": "indice_penalizacion",
    "Dispersión Municipal": "dispersion_municipal",
    "Ratio Municipal": "ratio_municipal",
    "Índice de Variabilidad": "indice_variabilidad"
}

ESCALAS_COLORES = {
    "Diferencial por Estrato": ['#e5f5e0', '#a1d99b', '#31a354', '#006d2c', '#00441b'],  # Verde
    "Índice de Carga": ['#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#2171b5'],  # Azul
    "Ratio de Penalización": ['#fee6ce', '#fdd0a2', '#fdae6b', '#f16913', '#d94801'],  # Naranja
    "Factor Operativo": ['#f2f0f7', '#dadaeb', '#bcbddc', '#9e9ac8', '#6a51a3'],  # Púrpura
    "Índice de Penalización": ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],  # Rojo
    "Dispersión Municipal": ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#4292c6'],  # Azul claro
    "Ratio Municipal": ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#41ab5d'],  # Verde claro
    "Índice de Variabilidad": ['#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84', '#fc8d59']  # Amarillo-Naranja
}

# Función para normalizar nombres de municipios
def normalizar_nombre(texto):
    if pd.isna(texto):
        return texto
    texto = str(texto).lower()
    texto = unidecode.unidecode(texto)
    texto = texto.replace(' ', '')
    return texto

# Cargar datos
@st.cache_data
def cargar_datos():
    try:
        # Cargar shapefile de municipios
        gdf_municipios = gpd.read_file('../data/shp/municipios.shp')
        
        # Cargar datos de tarifas e indicadores
        df_tarifas = pd.read_csv('../data/tarifas_con_indicadores.csv')
        
        # Normalizar nombres de municipios
        gdf_municipios['MpNombre_norm'] = gdf_municipios['MpNombre'].apply(normalizar_nombre)
        df_tarifas['Municipio_norm'] = df_tarifas['Municipio'].apply(normalizar_nombre)
        
        return gdf_municipios, df_tarifas
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return None, None

gdf_municipios, df_tarifas = cargar_datos()

if gdf_municipios is None or df_tarifas is None:
    st.error("No se pudieron cargar los datos necesarios. Por favor, verifica que los archivos existan y sean accesibles.")
    st.stop()

try:
    if gdf_municipios.crs is None:
        gdf_municipios.set_crs(epsg=4326, inplace=True)
    elif gdf_municipios.crs.to_string() != "EPSG:4326":
        gdf_municipios = gdf_municipios.to_crs("EPSG:4326")
except Exception as e:
    st.error(f"Error al configurar el CRS: {str(e)}")
    st.stop()

# Panel lateral para controles
st.sidebar.markdown("## Configuración del Visor")

# Selección de tipo de mapa base
mapa_base = st.sidebar.selectbox(
    "Mapa base",
    ["Satélite", "OpenStreetMap", "Cartografía", "Terreno"],
    index=0  # Satélite por defecto
)

# Capas disponibles
st.sidebar.markdown("### Capas disponibles")
mostrar_municipios = st.sidebar.checkbox("Mostrar Municipios", value=True)

# Filtros adicionales
st.sidebar.markdown("### Filtros")

# Obtener lista de municipios con datos disponibles
municipios_con_datos = sorted(df_tarifas['Municipio'].unique().tolist())
municipio_seleccionado = st.sidebar.selectbox(
    "Municipio",
    ["Todos"] + municipios_con_datos,
    help="Seleccione un municipio para ver sus indicadores específicos"
)

# Obtener el rango de años disponible en los datos
año_min = int(df_tarifas['Año'].min())
año_max = int(df_tarifas['Año'].max())
año_seleccionado = st.sidebar.slider(
    "Rango de años",
    min_value=año_min,
    max_value=año_max,
    value=(año_min, año_max),
    help="Seleccione el rango de años para calcular los promedios de los indicadores"
)

# Filtrar datos por el rango de años seleccionado
df_tarifas_filtrado = df_tarifas[
    (df_tarifas['Año'] >= año_seleccionado[0]) & 
    (df_tarifas['Año'] <= año_seleccionado[1])
]

# Función para obtener el mapa base según la selección
def get_base_map(selection):
    if selection == "OpenStreetMap":
        return "OpenStreetMap"
    elif selection == "Cartografía":
        return "CartoDB positron"
    elif selection == "Satélite":
        return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    elif selection == "Terreno":
        return "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg"
    else:
        return "OpenStreetMap"

# Función para obtener la atribución según el mapa base
def get_attribution(selection):
    if selection == "Satélite":
        return "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    elif selection == "Terreno":
        return "Map tiles by <a href='http://stamen.com'>Stamen Design</a>, <a href='http://creativecommons.org/licenses/by/3.0'>CC BY 3.0</a> &mdash; Map data &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
    else:
        return "© OpenStreetMap contributors"

# Función para crear el mapa
def crear_mapa(geojson_data, columna_indicador, indicador_seleccionado, mapa_base, vmin, vmax, municipio_seleccionado=None):
    m = folium.Map(
        location=CENTRO_VALLE_ABURRA,
        zoom_start=10,
        tiles=None
    )
    
    # Añadir capa base
    folium.TileLayer(
        tiles=get_base_map(mapa_base),
        attr=get_attribution(mapa_base),
        name=mapa_base
    ).add_to(m)
    
    # Definir la escala de colores
    colormap = folium.LinearColormap(
        colors=ESCALAS_COLORES[indicador_seleccionado],
        vmin=vmin,
        vmax=vmax,
        caption=f'Valor de {indicador_seleccionado}'
    )
    
    # Crear el estilo base
    base_style = {
        'color': '#0D47A1',
        'fillOpacity': 0.7,
        'weight': 1
    }
    
    # Función para el estilo de cada polígono
    def style_function(feature):
        valor = feature['properties'].get(columna_indicador)
        nombre = feature['properties'].get('MpNombre')
        
        # Si hay un municipio seleccionado, resaltarlo
        if municipio_seleccionado and nombre == municipio_seleccionado:
            return {
                'fillColor': colormap(valor) if not pd.isna(valor) else '#808080',
                'color': '#FF0000',  # Borde rojo para el municipio seleccionado
                'fillOpacity': 0.9,
                'weight': 3
            }
        
        return {
            'fillColor': '#808080' if pd.isna(valor) else colormap(valor),
            'color': '#0D47A1',
            'fillOpacity': 0.7,
            'weight': 1
        }
    
    # Añadir capa de municipios al mapa
    folium.GeoJson(
        geojson_data,
        name='Municipios',
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['MpNombre', columna_indicador],
            aliases=['Municipio:', f'{indicador_seleccionado}:'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    ).add_to(m)
    
    # Añadir la leyenda de colores
    colormap.add_to(m)
    
    # Añadir control de capas
    folium.LayerControl().add_to(m)
    
    return m

# Disposición principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<h2 class='subheader-style'>Visualización Geográfica</h2>", unsafe_allow_html=True)
    
    # Selector de indicador para el mapa coroplético
    indicador_seleccionado = st.selectbox(
        "Seleccione indicador",
        list(INDICADORES.keys()),
        key="selector_indicador"
    )
    
    try:
        # Calcular promedio del indicador por municipio para el rango de años
        columna_indicador = INDICADORES[indicador_seleccionado]
        promedios_municipio = df_tarifas_filtrado.groupby('Municipio_norm')[columna_indicador].mean().reset_index()
        
        # Unir los datos con el GeoDataFrame
        gdf_municipios_temp = gdf_municipios.copy()
        gdf_municipios_temp = gdf_municipios_temp.merge(
            promedios_municipio,
            left_on='MpNombre_norm',
            right_on='Municipio_norm',
            how='left'
        )
        
        # Calcular vmin y vmax
        vmin = gdf_municipios_temp[columna_indicador].min()
        vmax = gdf_municipios_temp[columna_indicador].max()
        
        # Convertir GeoDataFrame a GeoJSON
        geojson_data = gdf_municipios_temp.to_json()
        
        # Crear el mapa
        m = crear_mapa(
            geojson_data, 
            columna_indicador, 
            indicador_seleccionado, 
            mapa_base, 
            vmin, 
            vmax,
            municipio_seleccionado if municipio_seleccionado != "Todos" else None
        )
        
        # Crear un contenedor fijo para el mapa
        map_container = st.container()
        
        with map_container:
            st.markdown("<div class='map-container'>", unsafe_allow_html=True)
            st_folium(
                m,
                width=1000,
                height=600,
                key=f"mapa_{indicador_seleccionado}_{st.session_state.last_indicador}"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Actualizar el último indicador
        st.session_state.last_indicador = indicador_seleccionado
        
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.markdown(f"""
        **Nota:** Este mapa muestra la distribución del indicador {indicador_seleccionado} por municipio para el período {año_seleccionado[0]}-{año_seleccionado[1]}. Los municipios en gris no tienen datos disponibles.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error al generar el mapa: {str(e)}")
        st.stop()

with col2:
    st.markdown("<h2 class='subheader-style'>Indicadores por Zona</h2>", unsafe_allow_html=True)
    
    try:
        # Calcular promedio del indicador por municipio para el rango de años
        columna_indicador = INDICADORES[indicador_seleccionado]
        df_promedios = df_tarifas_filtrado.groupby('Municipio')[columna_indicador].mean().reset_index()

        if municipio_seleccionado != "Todos":
            df_promedios = df_promedios[df_promedios['Municipio'] == municipio_seleccionado]
        
        # Ordenar los municipios por el valor del indicador
        df_promedios = df_promedios.sort_values(by=columna_indicador, ascending=False)
        
        # Generar gráfico de barras con los promedios
        fig = px.bar(
            df_promedios,
            x='Municipio',
            y=columna_indicador,
            labels={
                "Municipio": "Municipio",
                columna_indicador: f"Promedio de {indicador_seleccionado}"
            },
            title=f"Promedio de {indicador_seleccionado} por Municipio ({año_seleccionado[0]}-{año_seleccionado[1]})",
            color=columna_indicador,
            color_continuous_scale=ESCALAS_COLORES[indicador_seleccionado]
        )
        
        # Personalizar el diseño del gráfico
        fig.update_layout(
            xaxis_title="Municipio",
            yaxis_title=f"Promedio de {indicador_seleccionado}",
            showlegend=False,
            height=500,
            coloraxis_showscale=True,
            coloraxis_colorbar=dict(
                title=f"Valor de {indicador_seleccionado}",
                thicknessmode="pixels",
                thickness=20,
                lenmode="pixels",
                len=300,
                yanchor="middle",
                y=0.5
            )
        )
        
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar estadísticas adicionales
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.markdown(f"""
        **Estadísticas del indicador {indicador_seleccionado} para el período {año_seleccionado[0]}-{año_seleccionado[1]}:**
        - Valor máximo: **{df_promedios[columna_indicador].max():.2f}**
        - Valor mínimo: **{df_promedios[columna_indicador].min():.2f}**
        - Promedio general: **{df_promedios[columna_indicador].mean():.2f}**
        - Desviación estándar: **{df_promedios[columna_indicador].std():.2f}**
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error al generar el gráfico: {str(e)}")
        st.stop()

# Resumen y conclusiones
st.markdown("<h2 class='subheader-style'>Análisis de Indicadores</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Usar los datos filtrados por año y municipio para los resúmenes
df_resumen = df_tarifas_filtrado.copy()
if municipio_seleccionado != "Todos":
    df_resumen = df_resumen[df_resumen['Municipio'] == municipio_seleccionado]

with col1:
    st.markdown("<h3>Resumen de Indicadores</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    - Diferencial por Estrato promedio: **{df_resumen['diferencial_por_estrato'].mean():.2f}**
    - Índice de Carga promedio: **{df_resumen['indice_carga'].mean():.2f}**
    - Ratio de Penalización promedio: **{df_resumen['ratio_penalizacion'].mean():.2f}**
    - Factor Operativo promedio: **{df_resumen['factor_operativo'].mean():.2f}**
    """)

with col2:
    st.markdown("<h3>Análisis de Variabilidad</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    - Índice de Penalización promedio: **{df_resumen['indice_penalizacion'].mean():.2f}**
    - Dispersión Municipal promedio: **{df_resumen['dispersion_municipal'].mean():.2f}**
    - Ratio Municipal promedio: **{df_resumen['ratio_municipal'].mean():.2f}**
    - Índice de Variabilidad promedio: **{df_resumen['indice_variabilidad'].mean():.2f}**
    """)

st.markdown("---")
st.caption("© 2025 Sistema de Predicción de Tarifas de acueducto y alcantarillado | Módulo de Análisis Geográfico") 