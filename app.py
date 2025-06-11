import streamlit as st
import openrouteservice
import requests
import math
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Virosque TMS", page_icon="🚛", layout="wide")

# ESTILO CORPORATIVO
st.markdown("""
    <style>
        body {
            background-color: #f5f5f5;
        }
        .stButton>button {
            background-color: #8D1B2D;
            color: white;
            border-radius: 6px;
            padding: 0.6em 1em;
            border: none;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #a7283d;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# LOGO Y TÍTULOS
st.markdown("""
    <div style="display: flex; align-items: center;">
        <div style="flex: 1;">
            <h1 style='color:#8D1B2D;'>Virosque TMS</h1>
            <h4>La excelencia es el camino — planificador de rutas para camiones</h4>
        </div>
        <div>
            <img src="logo-virosque2-01.png" alt="Logo Virosque" width="220">
        </div>
    </div>
""", unsafe_allow_html=True)

# API Key NUEVA
api_key = "5b3ce3597851110001cf6248ec3aedee3fa14ae4b1fd1b2440f2e589"
client = openrouteservice.Client(key=api_key)

# CONVERSIÓN A Hh Mm
def horas_y_minutos(valor_horas):
    horas = int(valor_horas)
    minutos = int(round((valor_horas - horas) * 60))
    return f"{horas}h {minutos:02d}min"

# GEOCODIFICACIÓN ROBUSTA
def geocode(direccion):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": api_key,
        "text": direccion,
        "boundary.country": "ES",
        "size": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" in data and data["features"]:
            coord = data["features"][0]["geometry"]["coordinates"]
            return coord
        else:
            st.error(f"❌ No se encontraron resultados para: {direccion}")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"❌ Error HTTP geocodificando '{direccion}': {http_err}")
        return None
    except Exception as e:
        st.error(f"❌ Error general geocodificando '{direccion}': {e}")
        return None

# FORMULARIO DE ENTRADA
col1, col2, col3 = st.columns(3)
with col1:
    origen = st.text_input("📍 Origen", value="Valencia, España")
with col2:
    destino = st.text_input("🏁 Destino", value="Madrid, España")
with col3:
    hora_salida_str = st.time_input("🕒 Hora de salida", value=datetime.strptime("08:00", "%H:%M")).strftime("%H:%M")

stops = st.text_area("➕ Paradas intermedias (una por línea)", placeholder="Ej: Albacete, España\nCuenca, España")

# CÁLCULO DE RUTA
if st.button("🔍 Calcular Ruta"):
    coord_origen = geocode(origen)
    coord_destino = geocode(destino)

    stops_list = []
    if stops.strip():
        for parada in stops.strip().split("\n"):
            coord = geocode(parada)
            if coord:
                stops_list.append(coord)
            else:
                st.warning(f"⚠️ No se pudo geolocalizar: {parada}")

    if not coord_origen or not coord_destino:
        st.error("❌ Error en geolocalización de origen o destino")
        st.stop()

    coords_totales = [coord_origen] + stops_list + [coord_destino]

    try:
        ruta = client.directions(
            coordinates=coords_totales,
            profile='driving-hgv',
            format='geojson'
        )
    except openrouteservice.exceptions.ApiError as e:
        st.error(f"❌ Error al calcular la ruta: {e}")
        st.stop()

    segmentos = ruta['features'][0]['properties']['segments']
    distancia_total = sum(seg["distance"] for seg in segmentos)
    duracion_total = sum(seg["duration"] for seg in segmentos)

    distancia_km = distancia_total / 1000
    duracion_horas = duracion_total / 3600
    descansos = math.floor(duracion_horas / 4.5)
    tiempo_total_h = duracion_horas + descansos * 0.75

    descanso_diario_h = 11 if tiempo_total_h > 13 else 0
    tiempo_total_real_h = tiempo_total_h + descanso_diario_h

    hora_salida = datetime.strptime(hora_salida_str, "%H:%M")
    hora_llegada = hora_salida + timedelta(hours=tiempo_total_real_h)

    tiempo_conduccion_txt = horas_y_minutos(duracion_horas)
    tiempo_total_txt = horas_y_minutos(tiempo_total_h)
    tiempo_ajustado_txt = horas_y_minutos(tiempo_total_real_h)

    # MÉTRICAS
    st.markdown("### 📊 Datos de la ruta")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🛣 Distancia", f"{distancia_km:.2f} km")
    col2.metric("🕓 Conducción", tiempo_conduccion_txt)
    col3.metric("⏱ Total (con descansos)", tiempo_total_txt)
    col4.metric("📅 Llegada estimada", hora_llegada.strftime("%H:%M"))

    if tiempo_total_h > 13:
        st.warning(f"⚠️ Se ha añadido un descanso diario obligatorio (11h).⏳ Tiempo ajustado: {tiempo_ajustado_txt}")
    else:
        st.success("🟢 El viaje puede completarse en una sola jornada de trabajo.")

    # MAPA
    st.markdown("### 🗺️ Ruta estimada:")
    linea = ruta["features"][0]["geometry"]["coordinates"]
    linea_latlon = [[p[1], p[0]] for p in linea]
    m = folium.Map(location=linea_latlon[0], zoom_start=6)
    folium.Marker(location=[coord_origen[1], coord_origen[0]], tooltip="📍 Origen").add_to(m)
    for idx, parada in enumerate(stops_list):
        folium.Marker(location=[parada[1], parada[0]], tooltip=f"Parada {idx + 1}").add_to(m)
    folium.Marker(location=[coord_destino[1], coord_destino[0]], tooltip="🏁 Destino").add_to(m)
    folium.PolyLine(linea_latlon, color="blue", weight=5).add_to(m)
    st_folium(m, width=1200, height=500)
