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
    /* Colores Corporativos SSOMA.PE */
    :root {
        --primary-blue: #0060a9; /* Azul del logo */
        --secondary-green: #28a745; /* Verde (hoja) */
        --text-black: #000000;
    }
    
    .main {
        background-color: #f8f9fa;
    }
    
    /* Botones */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: var(--primary-blue);
        color: white;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #004c87;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Tarjetas de Métricas */
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid var(--secondary-green);
    }
    
    /* Ajustes Responsivos para Móviles */
    @media (max-width: 768px) {
        .stButton>button {
            height: 3.5em; /* Botones más grandes para tocar */
        }
        h1 {
            font-size: 1.8rem !important;
        }
    }

    /* Scrollbars Visibles y Estilizados */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary-blue);
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #004c87;
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
    # Logo Corporativo
    try:
        st.image("assets/logo.png", use_container_width=True)
    except:
        st.warning("Logo no encontrado en assets/logo.png")

    st.title("🔍 Filtros")
    
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
    
    # Formatear el dataframe para mostrar (Modelo CRM)
    display_df = df[['ruc', 'razon_social', 'segmentacion', 'location', 'role_detected', 'confidence_score']]
    display_df.columns = ['RUC', 'Razón Social', 'Segmentación', 'Ubicación', 'Rol Detectado', 'Confianza']
    
    # Tabla Interactiva con Selección
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Confianza": st.column_config.ProgressColumn(
                "Confianza",
                help="Probabilidad de éxito",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
            "RUC": st.column_config.TextColumn("RUC", help="Registro Único de Contribuyentes"),
        }
    )
    
    # Detalles y Exportación
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Detalle del Prospecto (CRM)")
        
        selected_index = None
        
        # Priorizar selección de la tabla
        if len(event.selection.rows) > 0:
            selected_index = event.selection.rows[0]
        
        # Fallback a selectbox si no hay selección en tabla (o para permitir cambio manual)
        # Sincronizamos: si hay selección en tabla, el selectbox debe reflejarlo (si es posible)
        # Para simplificar, mostramos el detalle directamente si hay selección en tabla
        
        if selected_index is not None:
            prospect = df.iloc[selected_index]
            
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: var(--primary-blue); margin-top: 0;">🏢 {prospect['nombre_comercial']}</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <p><strong>🆔 RUC:</strong> {prospect['ruc'] if prospect['ruc'] else 'No detectado'}</p>
                        <p><strong>📜 Razón Social:</strong> {prospect['razon_social']}</p>
                        <p><strong>🏷️ Segmentación:</strong> <span style="background-color: #e9ecef; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{prospect['segmentacion']}</span></p>
                    </div>
                    <div>
                        <p><strong>📍 Ubicación:</strong> {prospect['location']}</p>
                        <p><strong>🔗 Fuente:</strong> <a href="{prospect['source']}" target="_blank">Enlace</a></p>
                    </div>
                </div>
                <hr style="border-top: 1px solid #eee;">
                <h4 style="color: var(--secondary-green);">👤 Contacto Detectado</h4>
                <p><strong>Nombre/Rol:</strong> {prospect['role_detected'] if prospect['role_detected'] else 'No detectado'}</p>
                <p><strong>Email/Contacto:</strong> {prospect['contact_info'] if prospect['contact_info'] else 'No disponible'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("👆 Selecciona una empresa en la tabla para ver sus detalles completos.")
            
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
