import streamlit as st
import openrouteservice
import requests
import math
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

# Configurar página
st.set_page_config(page_title="Virosque TMS", page_icon="🚛", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
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

# Encabezado con logo y título alineados
col_logo, col_titulo = st.columns([1, 3])
with col_logo:
    st.image("logo-virosque2-01.png", width=200)
with col_titulo:
    st.markdown("<h1 style='color:#8D1B2D;'>Virosque TMS</h1>", unsafe_allow_html=True)
    st.markdown("### La excelencia es el camino — planificador de rutas para camiones")

# API Key de OpenRouteService
api_key = "5b3ce3597851110001cf6248e38c54a14f3b4a1b85d665c9694e9874"
client = openrouteservice.Client(key=api_key)

# Función para mostrar horas y minutos
def horas_y_minutos(valor_horas):
    horas = int(valor_horas)
    minutos = int(round((valor_horas - horas) * 60))
    return f"{horas}h {minutos:02d}min"

# Función de geolocalización robusta
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


# Entradas
origen = st.text_input("📍 Ciudad de origen", "Valencia, España")
destino = st.text_input("🏁 Ciudad de destino", "Madrid, España")
hora_salida_str = st.time_input("🕒 Hora de salida", value=datetime.strptime("08:00", "%H:%M")).strftime("%H:%M")
stops = st.text_area("➕ Paradas intermedias (una por línea)", placeholder="Ej: Albacete, España\nCuenca, España")

# Botón
if st.button("🔍 Calcular Ruta"):
    coord_origen = geocode(origen)
    coord_destino = geocode(destino)
    paradas = [geocode(p.strip()) for p in stops.strip().split("\n") if p.strip()] if stops.strip() else []

    if not coord_origen or not coord_destino:
        st.error("❌ Error en geolocalización de origen o destino")
        st.stop()

    for i, p in enumerate(paradas):
        if not p:
            st.warning(f"❌ No se pudo geolocalizar la parada {i+1}")
            st.stop()

    coordenadas = [coord_origen] + paradas + [coord_destino]

    try:
        ruta = client.directions(coordinates=coordenadas, profile='driving-hgv', format='geojson')
    except openrouteservice.exceptions.ApiError as e:
        st.error(f"❌ Error al calcular la ruta: {e}")
        st.stop()

    segmentos = ruta['features'][0]['properties']['segments']
    distancia_km = sum(seg['distance'] for seg in segmentos) / 1000
    duracion_horas = sum(seg['duration'] for seg in segmentos) / 3600
    descansos = math.floor(duracion_horas / 4.5)
    tiempo_total_h = duracion_horas + descansos * 0.75
    descanso_diario_h = 11 if tiempo_total_h > 13 else 0
    tiempo_total_real = tiempo_total_h + descanso_diario_h
    hora_llegada = datetime.strptime(hora_salida_str, "%H:%M") + timedelta(hours=tiempo_total_real)

    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🛣 Distancia", f"{distancia_km:.2f} km")
    col2.metric("🕓 Conducción", horas_y_minutos(duracion_horas))
    col3.metric("⏱ Total (descansos)", horas_y_minutos(tiempo_total_h))
    col4.metric("📅 Llegada estimada", hora_llegada.strftime("%H:%M"))

    if tiempo_total_h > 13:
        st.warning(f"⚠️ Se añadió un descanso diario de 11h.\nTotal jornada: {horas_y_minutos(tiempo_total_real)}")
    else:
        st.success("🟢 Ruta realizable en una jornada de trabajo")

    # Mapa
    coords_mapa = ruta['features'][0]['geometry']['coordinates']
    coords_latlon = [[p[1], p[0]] for p in coords_mapa]
    m = folium.Map(location=coords_latlon[0], zoom_start=6)
    folium.Marker(location=[coord_origen[1], coord_origen[0]], tooltip="📍 Origen").add_to(m)
    for i, p in enumerate(paradas):
        folium.Marker(location=[p[1], p[0]], tooltip=f"Parada {i+1}").add_to(m)
    folium.Marker(location=[coord_destino[1], coord_destino[0]], tooltip="🏁 Destino").add_to(m)
    folium.PolyLine(coords_latlon, color="blue", weight=5).add_to(m)
    st_folium(m, width=1200, height=500)
