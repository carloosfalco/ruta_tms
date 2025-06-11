
import streamlit as st

def asignacion_cargas():
    st.title("🚚 Asignación de Cargas")

    # Filtros simulados
    st.sidebar.header("Filtros")
    tipo_cliente = st.sidebar.selectbox("Tipo de cliente", ["Todos", "N1 (otros)", "N2 (Mercadona)"])
    destino = st.sidebar.text_input("Destino (opcional)")
    tipo_camion = st.sidebar.multiselect("Tipo de camión", ["Lona", "Frigorífico"])

    st.markdown("### 📦 Cargas disponibles")

    # Tabla de cargas de ejemplo
    cargas = [
        {"ID": "C001", "Cliente": "Mercadona", "Destino": "Valencia", "Tipo camión": "Frigorífico", "Estado": "Pendiente"},
        {"ID": "C002", "Cliente": "Lidl", "Destino": "Madrid", "Tipo camión": "Lona", "Estado": "Pendiente"},
        {"ID": "C003", "Cliente": "Mercadona", "Destino": "Barcelona", "Tipo camión": "Frigorífico", "Estado": "Pendiente"},
        {"ID": "C004", "Cliente": "Consum", "Destino": "Sevilla", "Tipo camión": "Lona", "Estado": "Pendiente"},
    ]

    # Aplicar filtros
    if tipo_cliente != "Todos":
        cargas = [c for c in cargas if ("N2" if c["Cliente"] == "Mercadona" else "N1") == tipo_cliente.split()[0]]

    if destino:
        cargas = [c for c in cargas if destino.lower() in c["Destino"].lower()]

    if tipo_camion:
        cargas = [c for c in cargas if c["Tipo camión"] in tipo_camion]

    if not cargas:
        st.info("No hay cargas que coincidan con los filtros seleccionados.")
    else:
        for carga in cargas:
            with st.expander(f"🚛 Carga {carga['ID']} - {carga['Cliente']} ➜ {carga['Destino']}"):
                st.write(f"**Tipo de camión requerido:** {carga['Tipo camión']}")
                st.write("📝 Estado:", carga["Estado"])
                st.button(f"Asignar transporte para {carga['ID']}", key=carga['ID'])

if __name__ == "__main__":
    asignacion_cargas()
