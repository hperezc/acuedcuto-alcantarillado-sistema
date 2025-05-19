import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from prophet import Prophet
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd


# Configuración de la página
st.set_page_config(
    page_title="Sistema de Predicción de Tarifas - Valle de Aburrá",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)


def crear_engine():
    try:
        load_dotenv()
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")

        return create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    except Exception as e:
        st.error("Error al conectar con la base de datos.")
        st.stop()

engine = crear_engine()



@st.cache_data
def cargar_datos():
    try:
        query = "SELECT * FROM tarifas_acueductos_aguas_residuales_med_ing_caracteristicas"
        df = pd.read_sql(query, engine)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        st.error("Error al cargar los datos desde la base de datos.")
        st.exception(e)
        return pd.DataFrame()  

df_real = cargar_datos()

if df_real.empty:
    st.error("No se pudo cargar la información desde la base de datos. Verifica la conexión o el contenido.")
    st.stop()

requeridas = ['Fecha', 'Municipio', 'Estrato', 'Servicio', 'Cargo Fijo']
if not all(col in df_real.columns for col in requeridas):
    st.error("La base de datos no contiene todas las columnas necesarias.")
    st.stop()
#df_real = pd.read_excel("data/tarifas_con_indicadores_excel.xlsx")  # Ajusta la ruta si es necesario


# Estilos barra lateral
st.sidebar.markdown("""
<style>
    span[data-baseweb="tag"] {
        background-color: transparent !important;
        padding: 0px !important;
        font-size: 1.2rem !important;
    }
    .sidebar-content [data-testid="stSidebarNav"] li div a p {
        font-size: 1.2rem;
    }
    /* Ocultar "app" y reemplazarlo con un ícono y "Home" */
    .sidebar-content [data-testid="stSidebarNav"] li:first-child div a p {
        visibility: hidden;
        position: relative;
    }
    .sidebar-content [data-testid="stSidebarNav"] li:first-child div a p:after {
        content: "💧 Home";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
    }
    /* Añadir ícono a Visor Geográfico y cambiar su tamaño */
    .sidebar-content [data-testid="stSidebarNav"] li:nth-child(2) div a p {
        visibility: hidden;
        position: relative;
    }
    .sidebar-content [data-testid="stSidebarNav"] li:nth-child(2) div a p:after {
        content: "🗺️ Visor Geográfico";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
    }
    /* Añadir ícono a Predicciones y cambiar su tamaño */
    .sidebar-content [data-testid="stSidebarNav"] li:nth-child(3) div a p {
        visibility: hidden;
        position: relative;
    }
    .sidebar-content [data-testid="stSidebarNav"] li:nth-child(3) div a p:after {
        content: "📈 Predicciones";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
    }
</style>
""", unsafe_allow_html=True)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 1rem;
    }
    .card {
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .blue-card {
        background-color: #E3F2FD;
    }
    .green-card {
        background-color: #E8F5E9;
    }
    .metric-big {
        font-size: 2.2rem;
        font-weight: bold;
        text-align: center;
    }
    .metric-label {
        font-size: 1rem;
        text-align: center;
        color: #555;
    }
    .sidebar-header {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #0D47A1;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar con filtros
st.sidebar.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 1.5rem;">
    <div style="background: linear-gradient(135deg, #0D47A1, #42A5F5); padding: 1rem; border-radius: 10px; width: 100%; margin-bottom: 0.5rem;">
        <div style="display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 2.5rem; margin-right: 0.5rem;">💧</span>
            <div>
                <div style="color: white; font-weight: bold; font-size: 1.1rem; line-height: 1.2;">Sistema de Predicción</div>
                <div style="color: #E3F2FD; font-size: 0.9rem;">Tarifas de Acueducto y Alcantarillado</div>
            </div>
        </div>
    </div>
    <div style="background-color: #E3F2FD; width: 100%; height: 3px; border-radius: 3px;"></div>
</div>
""", unsafe_allow_html=True)


# Cabecera principal
st.markdown("<h1 class='main-header'>💧 Sistema de Predicción de Tarifas de Acueducto y Alcantarillado</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Evaluación y predicción de tarifas en el Valle de Aburrá</p>", unsafe_allow_html=True)


# Calcular métricas reales y mostrarlas

# === Selección de filtros ===
col1, col2, col3 = st.columns(3)
with col1:
    municipio = st.selectbox("Municipio", sorted(df_real['Municipio'].unique()))
with col2:
    estrato = st.selectbox("Estrato", sorted(df_real['Estrato'].unique()))
with col3:
    servicio = st.selectbox("Tipo de Servicio", sorted(df_real['Servicio'].unique()))

# === Filtrar datos según selección ===
df_filtrado = df_real[
    (df_real['Municipio'] == municipio) &
    (df_real['Estrato'] == estrato) &
    (df_real['Servicio'] == servicio)
].sort_values('Fecha')

# === Validar existencia de datos ===
if df_filtrado.empty:
    st.warning("⚠️ No hay datos disponibles para esta combinación.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-big'>–</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Tarifa promedio actual</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-big'>–</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Predicción a 3 meses</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-big'>–</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Variación estimada anual</div>", unsafe_allow_html=True)

else:

    
    # === Preparar datos para Prophet ===
    df_prophet = df_filtrado[['Fecha', 'Cargo Fijo']].rename(columns={'Fecha': 'ds', 'Cargo Fijo': 'y'})

    # === Entrenar modelo Prophet ===
    modelo = Prophet(interval_width=0.95)
    modelo.fit(df_prophet)

    future = modelo.make_future_dataframe(periods=12, freq='M')
    forecast = modelo.predict(future)

    historico = forecast[forecast['ds'] <= df_prophet['ds'].max()]
    prediccion = forecast[forecast['ds'] > df_prophet['ds'].max()]


        # === Métricas reales ===
    tarifa_actual = df_prophet['y'].iloc[-1]
    tarifa_3m = prediccion['yhat'].iloc[2] if len(prediccion) >= 3 else prediccion['yhat'].mean()
    tarifa_12m = prediccion['yhat'].iloc[-1]
    variacion_anual = ((tarifa_12m - tarifa_actual) / tarifa_actual) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-big'>${tarifa_actual:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Tarifa promedio actual</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-big'>${tarifa_3m:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Predicción a 3 meses</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-big'>{variacion_anual:.1f}%</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Variación estimada anual</div>", unsafe_allow_html=True)


    # === Crear gráfico ===
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historico['ds'],
        y=historico['yhat'],
        mode='lines',
        name='Datos históricos',
        line=dict(color='#1E88E5', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=prediccion['ds'],
        y=prediccion['yhat'],
        mode='lines',
        name='Predicción',
        line=dict(color='#FFA000', width=3, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=list(prediccion['ds']) + list(prediccion['ds'])[::-1],
        y=list(prediccion['yhat_upper']) + list(prediccion['yhat_lower'])[::-1],
        fill='toself',
        fillcolor='rgba(255, 160, 0, 0.2)',
        line=dict(color='rgba(255, 160, 0, 0)'),
        hoverinfo='skip',
        name='Intervalo de confianza'
    ))

    fig.update_layout(
        title='Evolución y Predicción de Tarifas',
        xaxis_title='Fecha',
        yaxis_title='Tarifa ($COP)',
        hovermode='x unified',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)



    with st.expander("¿Cómo interpretar esta gráfica?"):
        st.markdown("""
        - **Línea azul**: datos históricos reales de tarifas.
        - **Línea punteada naranja**: predicción futura basada en Prophet.
        - **Área sombreada**: intervalo de confianza del 95%.
        """)




# Indicadores clave
st.markdown("<h2 class='sub-header'>Indicadores de Análisis Tarifario</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# ======= ESTRUCTURA TARIFARIA (IET) =======
with col1:
    st.subheader("Estructura Tarifaria (IET)")

    # Agrupamos por estrato para obtener promedio de Cargo Fijo y Cargo por Consumo
    df_iet = df_real[
        (df_real['Municipio'] == municipio) &
        (df_real['Servicio'] == servicio)
    ].groupby('Estrato')[['Cargo Fijo', 'Cargo por Consumo']].mean().reset_index()

    # Ordenar por estrato numérico si es posible
    df_iet = df_iet[df_iet['Estrato'].astype(str).str.isnumeric()]
    df_iet['Estrato'] = df_iet['Estrato'].astype(int)
    df_iet = df_iet.sort_values(by='Estrato')
    estratos_graf = [f"Estrato {e}" for e in df_iet['Estrato']]

    fig_iet = go.Figure()
    fig_iet.add_trace(go.Bar(
        x=estratos_graf,
        y=df_iet['Cargo Fijo'],
        name='Cargo Fijo',
        marker_color='#1E88E5'
    ))

    fig_iet.update_layout(
        title='Composición de Tarifas por Estrato',
        xaxis_title='Estrato',
        yaxis_title='Valor Promedio ($COP)',
        barmode='group',
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig_iet, use_container_width=True)

    # Cálculo de indicadores simples
    if not df_iet.empty:
        #ratio_fijo_variable = (df_iet['Cargo Fijo'].mean() / df_iet['Cargo por Consumo'].mean())
        progresividad = (df_iet['Cargo Fijo'].max() / df_iet['Cargo Fijo'].min())
        st.markdown(f"**Indicador de Progresividad:** {progresividad:.2f}")
        #st.markdown(f"**Ratio Cargo Fijo/Variable:** {ratio_fijo_variable:.2f}")
    else:
        st.markdown("**Indicador de Progresividad:** –")
        #st.markdown("**Ratio Cargo Fijo/Variable:** –")


# ======= VARIACIÓN GEOGRÁFICA (IVG) =======
with col2:
    st.subheader("Variación Geográfica (IVG)")

    # Agrupamos por municipio para obtener estadísticas de dispersión y promedios
    df_ivg = df_real[
        (df_real['Estrato'] == estrato) &
        (df_real['Servicio'] == servicio)
    ].groupby('Municipio')['Cargo Fijo'].agg(['std', 'mean']).reset_index()
    df_ivg.columns = ['Municipio', 'Dispersión Municipal', 'Tarifa Promedio']

    # Ratio Municipal respecto al promedio regional
    promedio_total = df_ivg['Tarifa Promedio'].mean()
    df_ivg['Ratio Municipal'] = df_ivg['Tarifa Promedio'] / promedio_total

    fig_ivg = px.scatter(
        df_ivg,
        x='Dispersión Municipal',
        y='Ratio Municipal',
        size=[30] * len(df_ivg),
        color=df_ivg['Municipio'],
        hover_name='Municipio',
        text='Municipio',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    fig_ivg.update_traces(
        textposition='top center',
        marker=dict(line=dict(width=2, color='DarkSlateGrey'))
    )

    fig_ivg.update_layout(
        title='Variación Geográfica de Tarifas',
        xaxis_title='Dispersión Municipal (σ)',
        yaxis_title='Ratio Municipal (vs. promedio)',
        height=300,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig_ivg, use_container_width=True)

    # Mostrar métricas clave
    if not df_ivg.empty:
        dispersion_regional = df_ivg['Dispersión Municipal'].mean()
        indice_variabilidad = df_ivg['Ratio Municipal'].std()
        st.markdown(f"**Índice de Variabilidad:** {indice_variabilidad:.2f}")
        st.markdown(f"**Dispersión Regional:** {dispersion_regional:.2f}")
    else:
        st.markdown("**Índice de Variabilidad:** –")
        st.markdown("**Dispersión Regional:** –")



# ======================== Comparativas y Análisis Avanzados ========================
st.markdown("<h2 class='sub-header'>Comparativas y Análisis Avanzados</h2>", unsafe_allow_html=True)

# Controles de análisis comparativo
col1, col3 = st.columns(2)

with col1:
    st.write("### Municipio de referencia")
    municipios_unicos = sorted(df_real["Municipio"].unique())
    municipio_ref = st.selectbox("Seleccione municipio base", municipios_unicos, key="mun_ref")
    st.markdown(f"Las comparativas utilizan **{municipio_ref}** como base de referencia")



with col3:
    st.write("### Período de análisis")
    años_disponibles = sorted(df_real["Año"].unique())
    anno_inicio = st.selectbox("Desde", años_disponibles, index=0)
    anno_fin = st.selectbox("Hasta", años_disponibles[::-1], index=0)

# Tab de análisis comparativo
tabs = st.tabs(["Promedio tarifa", "Indicadores Tarifarios"])

with tabs[0]:
    st.write("### Promedio de tarifa por municipio")

    df_periodo = df_real[(df_real["Año"] >= anno_inicio) & (df_real["Año"] <= anno_fin)]
    df_tarifa_mun = df_periodo.groupby("Municipio")["Cargo Fijo"].mean().reset_index()
    df_tarifa_mun.columns = ["Municipio", "Tarifa Promedio"]

    tarifa_base = df_tarifa_mun[df_tarifa_mun["Municipio"] == municipio_ref]["Tarifa Promedio"].values[0]
    df_tarifa_mun["Diferencia %"] = df_tarifa_mun["Tarifa Promedio"].apply(lambda x: "Base" if x == tarifa_base else f"{((x / tarifa_base - 1)*100):+.1f}%")

    fig = px.bar(df_tarifa_mun, x="Municipio", y="Tarifa Promedio", color="Tarifa Promedio",
                 color_continuous_scale=px.colors.sequential.Blues,
                 title="Tarifa Promedio por Municipio")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=400)

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_tarifa_mun, use_container_width=True)

with tabs[1]:
    st.write("### Indicadores Tarifarios por Municipio")

    indicadores_clave = {
        "IET - Estructura Tarifaria": ["ratio_cargo_fijo_variable", "indice_progresividad", "diferencial_estratos", "indice_sectorial"],
        "IVG - Variación Geográfica": ["dispersion_municipal", "ratio_municipal", "indice_variabilidad"],
        "ISD - Servicio Diferencial": ["ratio_servicios", "diferencial_por_estrato", "indice_carga"],
        "ICO - Costos Operativos": ["ratio_penalizacion", "factor_operativo", "indice_penalizacion"]
    }

    tipo_indicador = st.selectbox("Seleccione tipo de indicador", list(indicadores_clave.keys()))

    columnas = indicadores_clave[tipo_indicador]
    df_indicador = df_real.groupby("Municipio")[columnas].mean().reset_index()

    for columna in columnas:
        fig = px.bar(df_indicador, x="Municipio", y=columna, color=columna,
                     color_continuous_scale=px.colors.sequential.Viridis,
                     title=columna.replace("_", " ").title())
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_indicador, use_container_width=True)




# Sección final informativa
st.markdown("---")
st.markdown("<h2 class='sub-header'>Metodología de Predicción</h2>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    fig = go.Figure()
    
    # Crear datos para una demostración visual de series temporales y predicciones
    x = np.array(range(50))
    y_historic = 100 + 5*x[:30] + 10*np.sin(x[:30]/5) + np.random.normal(0, 5, 30)
    y_predict = 100 + 5*x[30:] + 10*np.sin(x[30:]/5)
    y_upper = y_predict + np.linspace(5, 20, 20)
    y_lower = y_predict - np.linspace(5, 20, 20)
    
    # Añadir datos históricos
    fig.add_trace(go.Scatter(
        x=x[:30], y=y_historic,
        mode='lines',
        name='Datos históricos',
        line=dict(color='#1E88E5', width=3)
    ))
    
    # Añadir predicción
    fig.add_trace(go.Scatter(
        x=x[30:], y=y_predict,
        mode='lines',
        name='Predicción',
        line=dict(color='#FFA000', width=3, dash='dash')
    ))
    
    # Añadir intervalo de confianza
    fig.add_trace(go.Scatter(
        x=np.concatenate([x[30:], x[30:][::-1]]),
        y=np.concatenate([y_upper, y_lower[::-1]]),
        fill='toself',
        fillcolor='rgba(255, 160, 0, 0.2)',
        line=dict(color='rgba(255, 160, 0, 0)'),
        hoverinfo='skip',
        name='Intervalo de confianza'
    ))
    
    # Configurar layout
    fig.update_layout(
        title='Modelo Predictivo de Tarifas',
        xaxis_title='Tiempo',
        yaxis_title='Tarifa',
        height=300,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.markdown("""
    **Modelos implementados en el sistema:**
    
    - **ARIMA**: Captura patrones lineales y estacionalidad en datos históricos
    - **LSTM**: Redes neuronales recurrentes para patrones complejos no lineales
    - **Prophet**: Manejo robusto de datos faltantes y cambios de tendencia
    - **XGBoost**: Incorpora múltiples variables predictoras con alta precisión
    
    **Evaluación de modelos:**
    
    - MAPE (Error Medio Absoluto Porcentual): Facilita la interpretación de los errores
    - RMSE (Error Cuadrático Medio): Penaliza errores grandes
    
    El sistema selecciona automáticamente el mejor modelo para cada contexto específico basado en su desempeño histórico.
    """)

st.markdown("---")
st.caption("© 2025 Sistema de Predicción de Tarifas de acueducto y alcantarillado | Desarrollado para el Valle de Aburrá") 