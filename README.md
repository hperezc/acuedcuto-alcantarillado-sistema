# Sistema de Predicción de Tarifas para Servicios de Acueducto y Alcantarillado - Valle de Aburrá

Este es el Sistema de Predicción de Tarifas para Servicios de Acueducto y Alcantarillado en el Valle de Aburrá, desarrollado con Streamlit. Este sistema permite visualizar, analizar y predecir las tarifas de servicios públicos para facilitar la planificación financiera de usuarios y entidades.

## Descripción del Sistema

El sistema ofrece una plataforma interactiva que permite:

- Visualización de tendencias históricas de tarifas por municipio y estrato
- Predicciones de tarifas futuras utilizando múltiples modelos de inteligencia artificial
- Análisis de indicadores tarifarios por categorías (IET, IVG, ISD, ICO)
- Comparativas geográficas mediante visualización en mapas interactivos
- Evaluación del desempeño de diferentes modelos predictivos

## Estructura del Proyecto

La aplicación está organizada en módulos:

1. **Home (`home.py`)**: Dashboard principal con visión general del sistema, métricas clave y gráficos de tendencias
2. **Visor Geográfico (`pages/1_Visor_Geografico.py`)**: Visualización espacial de indicadores y tarifas en el Valle de Aburrá
3. **Predicciones (`pages/2_Predicciones.py`)**: Módulo de análisis predictivo con comparativa de modelos y métricas de evaluación

## Tecnologías Implementadas

- **Framework Frontend**: Streamlit v1.30.0
- **Visualización de Datos**: 
  - Plotly v5.18.0 para gráficos interactivos
  - Folium v0.19.0 para visualizaciones geoespaciales
- **Análisis y Procesamiento**:
  - Pandas v2.1.4 para manipulación de datos
  - NumPy v1.26.3 para operaciones numéricas
  - Scikit-learn v1.3.2 para implementación de modelos
- **Modelos Predictivos**:
  - ARIMA: Para predicción de series temporales con patrones lineales
  - Prophet: Para manejo de estacionalidad y datos faltantes
  - XGBoost: Para modelado con múltiples variables
- **Bases de datos**:
  - Postgresql 16

## Instalación y Ejecución
1. restaurar base de datos en postgresql:
   ```
    El archivo con el backup esta en data/backup_db_aguas_residuales_med.sql
   ```
2. Clona o descarga el repositorio del aplicativo:
   ```
   git clone https://github.com/Acueducto-aguas-residuales-Medellin/code
   ```
3. Dirígete a la carpeta del proyecto:
   ```
   cd ruta/del/proyecto/python
   ```

4. Crea y activa un entorno virtual:
   - En Windows:
     ```
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

5. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
6. Crear archivo .env con las siguientes variables:
   ```
    DB_USER=usuario
    DB_PASSWORD=clave
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=db_aguas_residuales_med
   ```
7. Ejecuta el servidor:
   ```
   streamlit run home.py
   ```



## Funcionalidades Principales

### Dashboard Principal
- Métricas clave de tarifas actuales y proyectadas
- Gráfico de evolución histórica y predicción de tarifas
- Análisis de indicadores tarifarios
- Filtros por municipio, estrato y tipo de servicio

### Visor Geográfico
- Mapa interactivo del Valle de Aburrá
- Visualización de indicadores por municipio
- Comparativas geográficas de tarifas
- Análisis de dispersión y variabilidad tarifaria

### Módulo de Predicciones
- Selección de múltiples modelos predictivos
- Configuración de horizontes temporales
- Visualización de intervalos de confianza
- Métricas de evaluación (MAPE, RMSE)
- Análisis comparativo de desempeño de modelos

## Autores

Desarrollado por:
- Héctor Camilo Pérez Contreras
- Esteban Zuluaga Montes
- Camilo Andrés Navarro Narváez

Como parte del proyecto de la materia Gestión y Calidad de Software (Semestre 2025-1). 