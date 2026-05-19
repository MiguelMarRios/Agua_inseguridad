import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import random
from supabase import create_client, Client # NUEVO

# INICIALIZAR BASE DE DATOS SEGURA EN LA NUBE
@st.cache_resource
def init_connection():
    # Así se llama a la bóveda secreta, usando nombres genéricos, no la contraseña real
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Monitor HWISE México", page_icon="💧", layout="wide")

# CSS Avanzado: Estilo de cajas de ChatGPT fusionado con controles limpios y botón gigante
st.markdown("""
    <style>
    /* Fondo general del mapa y la app */
    .stApp { background: linear-gradient(135deg, #0f172a, #35c5e5); color: #f8fafc; }
    
    /* === BARRA LATERAL === */
    section[data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid #3b82f6; }
    section[data-testid="stSidebar"] label:not(div[role="radiogroup"] label):not(div[data-testid="stCheckbox"] label), 
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { 
        color: #f1f5f9 !important; 
    }
    
    /* Cajas de texto, números y dropdowns (Fondo blanco, texto NEGRO) */
    div[data-baseweb="select"] > div, textarea, input {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 6px !important;
    }
    div[role="listbox"] { background-color: #ffffff !important; }
    ul[role="listbox"] li { color: #000000 !important; }
    ul[role="listbox"] li:hover { background-color: #e2e8f0 !important; }

    /* Botones de opción de radio (Tambos/Cubetas y Filtro del mapa) */
    div[role="radiogroup"] {
        background-color: #ffffff !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1;
    }
    div[role="radiogroup"] label { 
        color: #000000 !important; 
        font-weight: 600 !important; 
        -webkit-text-fill-color: #000000 !important;
    }
    div[data-testid="stCheckbox"] label { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }

    /* === BOTÓN GIGANTE DE DIAGNÓSTICO EN SIDEBAR === */
    div.stButton > button:first-child {
        background-color: #dc2626 !important; /* Rojo vivo de alta visibilidad */
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        height: 3.2em !important;
        width: 100% !important;
        border-radius: 10px !important;
        border: 2px solid #ef4444 !important;
        box-shadow: 0px 5px 20px rgba(220, 38, 38, 0.4);
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #b91c1c !important;
        transform: scale(1.02);
    }

    /* === CUADRO EMERGENTE POP-UP ESTILO MODAL === */
    .popup-box {
        background-color: rgba(15, 23, 42, 0.95);
        border: 2px solid #60a5fa;
        border-radius: 14px;
        padding: 25px;
        margin-top: 10px;
        margin-bottom: 25px;
        box-shadow: 0px 15px 50px rgba(0,0,0,0.7);
        animation: fadeIn 0.3s ease-in-out;
    }
    .popup-title { color: #60a5fa; font-size: 22px; font-weight: bold; margin-top: 0; }
    .popup-class { color: #ffffff; background-color: rgba(96, 165, 250, 0.2); padding: 8px 12px; border-radius: 6px; display: inline-block; font-weight: bold; margin: 10px 0; }
    
    /* Tarjetas fijas e informativas */
    .stat-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; height: 100%; margin-bottom: 15px; font-size: 14.5px; }
    .stat-value { font-size: 26px; font-weight: 900; color: #60a5fa; margin-bottom: 5px; }
    .small-text { color: #cbd5e1; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CATALOGO GEOGRÁFICO DE MUNICIPIOS (Muestra adaptativa)
MUNICIPIOS_POR_ESTADO = {
    "Estado de México": ["Toluca", "Metepec", "Ecatepec", "Naucalpan", "Nezahualcóyotl", "Chimalhuacán"],
    "Ciudad de México": ["Iztapalapa", "Cuauhtémoc", "Benito Juárez", "Coyoacán", "Tlalpan", "Gustavo A. Madero"],
    "Oaxaca": ["Oaxaca de Juárez", "San Juan Bautista Tuxtepec", "Santa Cruz Xoxocotlán", "Juchitán de Zaragoza"],
    "Jalisco": ["Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá", "Puerto Vallarta"],
    "Nuevo León": ["Monterrey", "San Pedro Garza García", "San Nicolás de los Garza", "Apodaca"],
    "Baja California": ["Tijuana", "Mexicali", "Ensenada", "Tecate"]
}

ESTADOS_MEXICO = {
    "Aguascalientes": [21.8853, -102.2916], "Baja California": [30.8406, -115.2838], "Baja California Sur": [26.0444, -111.6661], 
    "Campeche": [19.5461, -90.5349], "Chiapas": [16.7569, -93.1292], "Chihuahua": [28.6330, -106.0691],
    "Ciudad de México": [19.3500, -99.1332], "Coahuila": [27.0587, -101.7068], "Colima": [19.2433, -103.7247], 
    "Durango": [24.0277, -104.6532], "Estado de México": [19.4000, -99.6420], "Guanajuato": [21.0190, -101.2574],
    "Guerrero": [17.4392, -99.5451], "Hidalgo": [20.0911, -98.7624], "Jalisco": [20.6595, -103.3494], 
    "Michoacán": [19.5665, -101.7068], "Morelos": [18.6813, -99.1013], "Nayarit": [21.7514, -104.8455],
    "Nuevo León": [25.5922, -100.0574], "Oaxaca": [17.0732, -96.7266], "Puebla": [19.0414, -98.2063], 
    "Querétaro": [20.5888, -100.3899], "Quintana Roo": [19.6802, -87.9238], "San Luis Potosí": [22.1565, -100.9855],
    "Sinaloa": [25.1721, -107.4795], "Sonora": [29.2972, -110.3309], "Tabasco": [17.8409, -92.6189], 
    "Tamaulipas": [24.2669, -98.8363], "Tlaxcala": [19.3182, -98.2375], "Veracruz": [19.1738, -96.1342],
    "Yucatán": [20.7018, -89.0943], "Zacatecas": [22.7709, -102.5832]
}

MAPA_ID_ESTADOS = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur", 4: "Campeche", 5: "Coahuila", 6: "Colima", 
    7: "Chiapas", 8: "Chihuahua", 9: "Ciudad de México", 10: "Durango", 11: "Guanajuato", 12: "Guerrero", 13: "Hidalgo", 
    14: "Jalisco", 15: "Estado de México", 16: "Michoacán", 17: "Morelos", 18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca", 
    21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí", 25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 
    28: "Tamaulipas", 29: "Tlaxcala", 30: "Veracruz", 31: "Yucatán", 32: "Zacatecas"
}

REGIMENES_ACADEMICOS = {
    1: "Exclusión Hídrica Extrema (Clase 1)", 2: "Resiliencia Forzada / Precariedad Mitigada (Clase 2)",
    3: "Seguridad Hídrica Estructural (Clase 3)", 4: "Estrés Hídrico Intermitente / Urbano (Clase 4)"
}

PALABRAS_PROHIBIDAS = ["pinche", "pendejo", "pendeja", "cabron", "cabrón", "culero", "verga", "puta", "puto", "mierda"]

def filtrar_comentario(texto):
    if not texto: return ""
    return " ".join(["*" * len(p) if p.strip(",.?!()").lower() in PALABRAS_PROHIBIDAS else p for p in texto.split()])

# 3. CARGA DE BASE DESCRIPTIVA Y JITTER GEOESPACIAL AVANZADO
@st.cache_data
def cargar_base_real():
    df = pd.read_csv('agua_proyecto_descriptiva.csv')
    df['entidad_id'] = df['upm'].apply(lambda x: int(str(x)[0]) if len(str(x)) == 12 else int(str(x)[:2]))
    df['Estado'] = df['entidad_id'].map(MAPA_ID_ESTADOS)
    
    np.random.seed(42)
    lat_centers = df['Estado'].apply(lambda x: ESTADOS_MEXICO.get(x, [23.6345, -102.5528])[0])
    lon_centers = df['Estado'].apply(lambda x: ESTADOS_MEXICO.get(x, [23.6345, -102.5528])[1])
    
    df['lat'] = lat_centers + np.random.uniform(-0.5, 0.5, len(df)) * np.random.normal(1, 0.4, len(df))
    df['lon'] = lon_centers + np.random.uniform(-0.5, 0.5, len(df)) * np.random.normal(1, 0.4, len(df))
    
    color_map = {1: [239, 68, 68, 160], 2: [16, 185, 129, 160], 3: [59, 130, 246, 160], 4: [249, 115, 22, 160]}
    df['Color'] = df['Regimen'].map(color_map)
    df['Regimen_Name'] = df['Regimen'].map(REGIMENES_ACADEMICOS)
    df['Comentario'] = "Hogar censado en modelo SEM"
    return df

df_analisis = cargar_base_real()

if 'db_ciudadana' not in st.session_state:
    st.session_state.db_ciudadana = df_analisis[['lat', 'lon', 'Estado', 'Regimen_Name', 'Comentario', 'Color']].copy()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💧 Monitor de Hogar (HWISE)")
    st.write("Ingresa los datos de tu vivienda.")
    
    estado_sel = st.selectbox("Estado de residencia:", list(ESTADOS_MEXICO.keys()))
    
    # NUEVO COMPONENTE: Ubicación por catálogo o C.P.
    tipo_ubicacion = st.radio("Método para ubicar tu hogar:", ["Catálogo de Municipio y Colonia", "Código Postal (C.P.)"], horizontal=False)
    
    if tipo_ubicacion == "Código Postal (C.P.)":
        cp_input = st.text_input("Ingresa tu C.P. (5 dígitos):", max_chars=5, placeholder="Ej. 50260")
        municipio_sel = "Zona C.P. " + cp_input if cp_input else "Desconocido"
        colonia_sel = ""
    else:
        # Resolver catálogo dinámico de municipios por estado
        municipios_disponibles = MUNICIPIOS_POR_ESTADO.get(estado_sel, ["Municipio Central", "Zona Periférica", "Sector Rural"])
        municipio_sel = st.selectbox("Selecciona tu Municipio:", municipios_disponibles)
        colonia_sel = st.text_input("Ingresa tu Colonia / Localidad:", placeholder="Ej. Capultitlán")

    st.markdown("---")
    escala_hwise = ["Nunca (0 veces)", "Rara vez (1-2 veces/mes)", "A veces (3-10 veces/mes)", "Frecuentemente (11-20 veces/mes)", "Siempre (casi diario)"]
    hwise_preocupa = st.selectbox("1. ¿Te ha preocupado no tener suficiente agua?", escala_hwise)
    hwise_planes = st.selectbox("2. ¿Has alterado tu rutina o cancelado planes esperando agua?", escala_hwise)
    hwise_lavar = st.selectbox("3. ¿Has dejado de lavar ropa o platos por escasez?", escala_hwise)
    
    cont_dias = st.slider("Días con agua corriente entubada a la semana:", 0, 7, 7)
    opcion_coping = st.radio("¿Almacenan agua en botes, cubetas o tambos?", ["No, nunca", "Solo cuando avisan de cortes", "Sí, es nuestra rutina diaria"])
    gasto_extra = st.number_input("Gasto mensual extra en agua (Pipas/Garrafones) $MXN:", 0, 5000, 200)
    tiene_cisterna = st.checkbox("Cuento con Cisterna subterránea o Tinaco fijo")
    comentario_usuario = st.text_area("Mensaje o queja ciudadana para pinchar en el mapa:", max_chars=140)

    # Lógica Inferencia SEM a Centroides LPA
    map_hwise = {escala_hwise[0]: -0.5, escala_hwise[1]: 0.3, escala_hwise[2]: 1.2, escala_hwise[3]: 2.2, escala_hwise[4]: 3.0}
    z_hwise = (map_hwise[hwise_preocupa] + map_hwise[hwise_planes] + map_hwise[hwise_lavar]) / 3
    z_cont = ((cont_dias / 7) * 3.0) - 2.178
    z_coping = {"No, nunca": -0.436, "Solo cuando avisan de cortes": 0.689, "Sí, es nuestra rutina diaria": 1.532}[opcion_coping]
    z_gasto = -0.070 if gasto_extra < 400 else (0.006 if gasto_extra < 800 else 0.135)
    
    mitigacion_activa = False
    if tiene_cisterna and z_cont < 0:
        z_hwise -= 1.0  # Atenuación del estrés hídrico subjetivo por infraestructura
        mitigacion_activa = True

    centroides = {
        1: {"name": REGIMENES_ACADEMICOS[1], "HWISE": 3.052, "CONT": -2.178, "COPING": 1.532, "GASTO": 0.135, "color": [239, 68, 68, 220]},
        2: {"name": REGIMENES_ACADEMICOS[2], "HWISE": -0.228, "CONT": -0.986, "COPING": 0.689, "GASTO": -0.070, "color": [16, 185, 129, 220]},
        3: {"name": REGIMENES_ACADEMICOS[3], "HWISE": -0.462, "CONT": 0.594, "COPING": -0.436, "GASTO": 0.006, "color": [59, 130, 246, 220]},
        4: {"name": REGIMENES_ACADEMICOS[4], "HWISE": 1.264, "CONT": -0.859, "COPING": 0.691, "GASTO": -0.001, "color": [249, 115, 22, 220]}
    }
    distancias = {c_id: np.sqrt((z_hwise-c["HWISE"])**2 + (z_cont-c["CONT"])**2 + (z_coping-c["COPING"])**2 + (z_gasto-c["GASTO"])**2) for c_id, c in centroides.items()}
    clase_asignada = min(distancias, key=distancias.get)
    regimen_final = centroides[clase_asignada]

    # ACCIÓN DEL BOTÓN GIGANTE
    if st.button("📍 Diagnosticar mi Hogar y Mapear"):
        coord_base = ESTADOS_MEXICO[estado_sel]
        comentario_final = f"Ubicación: {municipio_sel} {colonia_sel}. Reseña: " + (filtrar_comentario(comentario_usuario) if comentario_usuario else "Hogar registrado.")
        
        # 1. Guardar localmente para actualizar el mapa al instante
        nueva_lat = coord_base[0] + np.random.uniform(-0.06, 0.06)
        nueva_lon = coord_base[1] + np.random.uniform(-0.06, 0.06)
        
        nueva_entrada = pd.DataFrame({
            'lat': [nueva_lat], 'lon': [nueva_lon],
            'Estado': [estado_sel], 'Regimen_Name': [regimen_final['name']],
            'Comentario': [comentario_final], 'Color': [regimen_final['color']]
        })
        st.session_state.db_ciudadana = pd.concat([st.session_state.db_ciudadana, nueva_entrada], ignore_index=True)
        
        # 2. ENVIAR A SUPABASE (LA NUBE PERMANENTE Y SEGURA)
        try:
            supabase.table("registros_agua").insert({
                "lat": nueva_lat,
                "lon": nueva_lon,
                "estado": estado_sel,
                "regimen": regimen_final['name'],
                "comentario": comentario_final
            }).execute()
        except Exception as e:
            pass # Si falla el internet, la app no se cae
            
        # 3. Disparar interfaz
        st.session_state.ultimo_regimen = regimen_final['name']
        st.session_state.mitigacion_msg = mitigacion_activa
        st.session_state.calc_hwise = max(0, min(100, int((z_hwise + 0.5) / 3.5 * 100)))
        st.session_state.enviado = True
        st.session_state.mostrar_modal = True
        st.session_state.opcion_mapa = "Entidad Seleccionada"
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🗺️ Monitor de Desigualdad Hídrica en México")

# === CUADRO EMERGENTE POP-UP CON BOTÓN DE CIERRE (❌) ===
if st.session_state.get('mostrar_modal', False) and st.session_state.get('enviado', False):
    # Generación de la analítica descriptiva real para el pop-up en base a df_analisis
    df_f_estado = df_analisis[df_analisis['Estado'] == estado_sel]
    pct_ansiedad_real = (df_f_estado['hwise_preocupa'] >= 3).mean() * 100
    pct_tambos_real = ((df_f_estado['almacena_tambo_no_tapa'] == 1) | (df_f_estado['almacena_cubeta_no_tapa'] == 1)).mean() * 100
    promedio_estres_estado = max(0, min(100, int((df_f_estado['HWISE_fs'].mean() + 1) / 3 * 100)))
    
    # Evaluar situación de vecinos cercanos
    diferencia_contexto = st.session_state.calc_hwise - promedio_estres_estado
    if diferencia_contexto > 10:
        situacion_vecinos = f"⚠️ Tu nivel de estrés hídrico ({st.session_state.calc_hwise}%) es significativamente SUPERIOR al promedio reportado por tus vecinos en {estado_sel} ({promedio_estres_estado}%), lo que evidencia focos locales de alta vulnerabilidad o marginación de red en tu sector."
    elif diferencia_contexto < -10:
        situacion_vecinos = f"💎 Tu nivel de estrés hídrico ({st.session_state.calc_hwise}%) es INFERIOR al promedio general de tu estado ({promedio_estres_estado}%), indicando que gozas de una posición de resguardo frente a la crisis que asedia a tus vecinos cercanos."
    else:
        situacion_vecinos = f"⚖️ Tu realidad hídrica se encuentra alineada con el promedio de tus vecinos en {estado_sel} ({promedio_estres_estado}%), reflejando una problemática homogénea y compartida a nivel territorial."

    # Renderizado del Pop-up con CSS de alta calidad
    st.markdown('<div class="popup-box">', unsafe_allow_html=True)
    col_pop_title, col_pop_close = st.columns([12, 1])
    with col_pop_title:
        st.markdown('<div class="popup-title">🎯 Diagnóstico Estructural de Vulnerabilidad</div>', unsafe_allow_html=True)
    with col_pop_close:
        if st.button("❌", help="Cerrar ventana emergente"):
            st.session_state.mostrar_modal = False
            st.rerun()
            
    st.markdown(f"Tu perfil de acceso e impacto encarnado te sitúa en la clase latente:")
    st.markdown(f'<div class="popup-class">{st.session_state.ultimo_regimen}</div>', unsafe_allow_html=True)
    st.markdown(f"#### **Cociente de Inseguridad Hídrica (HWISE): {st.session_state.calc_hwise}%**")
    
    # Bloque de datos curiosos descriptivos
    st.markdown(f"#### 📊 Datos Curiosos Descriptivos de {estado_sel}:")
    st.markdown(f"* **Salud Pública:** El **{pct_tambos_real:.1f}%** de los hogares en tu entidad se ven obligados a recurrir al almacenamiento manual en botes o tambos para subsistir, alterando su dinámica espacial.")
    st.markdown(f"* **Salud Mental:** El **{pct_ansiedad_real:.1f}%** de la población en tu estado padece cuadros de ansiedad, enojo o preocupación constante debido a la incertidumbre del suministro.")
    
    # Situación de los vecinos
    st.markdown("#### 👥 Situación de tus Vecinos Cercanos:")
    st.write(situacion_vecinos)
    
    if st.session_state.mitigacion_msg:
        st.markdown("<div class='mitigacion-box'>🛠️ <b>Resiliencia Privatizada:</b> Tu inversión en cisterna/tinaco mitiga tu carga emocional diaria, cubriendo la ineficiencia de la red pública.</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# SECTOR DE MAPA DOMINANTE
st.write("---")
opcion_vista = st.radio("Enfoque del visor geográfico:", ["Entidad Seleccionada", "República Mexicana (Muestra Completa N=15,179)"], key="map_zoom_option", horizontal=True)

if opcion_vista == "Entidad Seleccionada" or st.session_state.get('opcion_mapa') == "Entidad Seleccionada":
    datos_mapa = st.session_state.db_ciudadana[st.session_state.db_ciudadana['Estado'] == estado_sel]
    coords_centro, zoom_inicial, radio_base = ESTADOS_MEXICO[estado_sel], 7.0, 3500
    # Limpiar el trigger automático de foco para permitir navegación libre posterior
    if 'opcion_mapa' in st.session_state: del st.session_state.opcion_mapa
else:
    datos_mapa = st.session_state.db_ciudadana
    coords_centro, zoom_inicial, radio_base = [23.6345, -102.5528], 4.8, 16000

st.markdown("<div style='text-align: center; margin-bottom: 12px; font-size: 14px;'>🔵 Seguridad Estructural | 🟢 Resiliencia Forzada | 🟠 Estrés Urbano | 🔴 Exclusión Extrema</div>", unsafe_allow_html=True)

# Gotas dinámicas con ajuste adaptativo de tamaño según zoom
layer = pdk.Layer(
    "ScatterplotLayer", datos_mapa, get_position="[lon, lat]", get_fill_color="Color",
    get_radius=radio_base, radius_min_pixels=2.2, radius_max_pixels=18, pickable=True
)
mapa_mexico = pdk.Deck(
    layers=[layer], initial_view_state=pdk.ViewState(latitude=coords_centro[0], longitude=coords_centro[1], zoom=zoom_inicial, pitch=25), 
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", 
    tooltip={"html": "<b>Estado:</b> {Estado}<br><b>Perfil Latente:</b> {Regimen_Name}<br><b>Detalle:</b> <i>{Comentario}</i>"}
)
st.pydeck_chart(mapa_mexico)

# BATERÍA DE TARJETAS INFORMATIVAS COMPACTAS ABAJO DEL MAPA
st.write("---")
st.header(f"📌 Radiografía Socioespacial de la Entidad")
df_estado_inf = df_analisis[df_analisis['Estado'] == estado_sel]
if len(df_estado_inf) > 0:
    pct_sin_conexion = (df_estado_inf['agua_bin'] == 0).mean() * 100
    pct_cortes_inf = (df_estado_inf['temp_sin_agua_bin'] == 1).mean() * 100
    id_pred_inf = df_estado_inf['Regimen'].mode()[0]
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="Excluidos de la red entubada", value=f"{pct_sin_conexion:.1f}%")
    with col_m2:
        st.metric(label="Sufren cortes intermitentes", value=f"{pct_cortes_inf:.1f}%")
    with col_m3:
        st.metric(label="Régimen Predominante", value=f"Clase {id_pred_inf}")
