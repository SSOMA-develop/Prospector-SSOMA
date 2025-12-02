import streamlit as st
import pandas as pd
from backend.search_engine import SearchEngine
import time

# Configuración de la página
st.set_page_config(
    page_title="Prospector SSOMA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar motor de búsqueda
if 'engine' not in st.session_state:
    # Intentar cargar credenciales de st.secrets (Streamlit Cloud) o entorno local
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
    except:
        # Si falla (ej. local sin secrets.toml), usar variables de entorno cargadas por dotenv
        api_key = None
        cse_id = None

    st.session_state.engine = SearchEngine(api_key, cse_id)

# Sidebar
with st.sidebar:
    st.title("🔍 Filtros de Búsqueda")
    
    # Indicador de Estado de API
    if st.session_state.engine.using_real_api:
        st.success("🟢 API Google Conectada")
    else:
        st.warning("🟠 Modo Demo (Datos Simulados)")
        if st.session_state.engine.last_error:
            st.error(f"Error API: {st.session_state.engine.last_error}")
        else:
            st.info("Configura GOOGLE_API_KEY y GOOGLE_CSE_ID para datos reales.")
    
    sector = st.selectbox(
        "Sector Industrial",
        ["Construcción", "Manufactura", "Minería", "Transporte", "Servicios Generales"]
    )
    
    location = st.text_input("Ubicación / Distrito", value="Lima")
    
    st.markdown("---")
    
    deep_search = st.checkbox("Activar Deep Search", help="Intenta buscar contactos específicos (Jefes, Gerentes) en LinkedIn y webs corporativas.")
    
    search_btn = st.button("Buscar Prospectos")

# Área Principal
st.title("Prospector SSOMA - Dashboard")
st.markdown(f"**Objetivo:** Encontrar clientes potenciales en *{sector}* en *{location}*.")

if search_btn:
    with st.spinner('Buscando empresas y analizando contactos...'):
        # Simular delay para efecto de "búsqueda profunda"
        time.sleep(1.5)
        results = st.session_state.engine.search(sector, location, deep_search)
        st.session_state.results = results

if 'results' in st.session_state:
    results = st.session_state.results
    df = pd.DataFrame(results)
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Prospectos Encontrados", len(results))
    with col2:
        high_confidence = len(df[df['confidence_score'] > 0.8])
        st.metric("Alta Confianza", high_confidence)
    with col3:
        contacts_found = len(df[df['contact_info'].notna()])
        st.metric("Contactos Directos", contacts_found)
    
    st.markdown("---")
    
    # Tabla Principal
    st.subheader("Resultados")
    
    # Formatear el dataframe para mostrar
    display_df = df[['name', 'location', 'role_detected', 'confidence_score', 'source']]
    display_df.columns = ['Empresa', 'Ubicación', 'Rol Detectado', 'Confianza', 'Fuente']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Confianza": st.column_config.ProgressColumn(
                "Confianza",
                help="Probabilidad de éxito",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
        }
    )
    
    # Detalles y Exportación
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Detalle del Prospecto")
        selected_index = st.selectbox("Seleccionar Empresa para ver detalles:", df.index, format_func=lambda x: df.iloc[x]['name'])
        
        if selected_index is not None:
            prospect = df.iloc[selected_index]
            
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">
                <h3>🏢 {prospect['name']}</h3>
                <p><strong>📍 Ubicación:</strong> {prospect['location']}</p>
                <p><strong>🔗 Fuente:</strong> {prospect['source']}</p>
                <hr>
                <h4>👤 Contacto Detectado</h4>
                <p><strong>Nombre/Rol:</strong> {prospect['role_detected'] if prospect['role_detected'] else 'No detectado'}</p>
                <p><strong>Email/Contacto:</strong> {prospect['contact_info'] if prospect['contact_info'] else 'No disponible'}</p>
            </div>
            """, unsafe_allow_html=True)
            
    with col_right:
        st.subheader("Acciones")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar CSV",
            csv,
            "prospectos_ssoma.csv",
            "text/csv",
            key='download-csv'
        )

else:
    st.info("👈 Utiliza el panel lateral para iniciar una búsqueda.")
