import base64
from io import BytesIO
import math
import sqlite3
import threading
import pandas as pd
import qrcode
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="S.A.T.R. - Plataforma Integral de Salud y Asistencia Clínica",
    page_icon="🏥",
    layout="wide",
)

# Nombre de la base de datos robusta para alta concurrencia (200+ usuarios)
DB_FILE = "satr_database.db"
db_lock = threading.Lock()


# --- INICIALIZACIÓN DE LA BASE DE DATOS SQLITE (CONCURRENTE) ---
def inicializar_bd():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Tabla de Usuarios
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        """
        )

        # Tabla de Historial de Auditorías
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                responsable TEXT,
                tipo TEXT,
                correo TEXT,
                historia_clinica TEXT,
                especialidad TEXT,
                estado TEXT,
                fecha TEXT
            )
        """
        )

        # Tabla de Triage y Urgencias
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS triage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT,
                triage TEXT,
                estado TEXT,
                hora TEXT,
                registrado_por TEXT
            )
        """
        )

        # Crear usuario administrador por defecto si no existe
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", ("admin",)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)",
                (
                    "admin",
                    "admin123",
                    "admin@clinica.com",
                    "Administrador Principal",
                    "Pasante",
                ),
            )

        conn.commit()
        conn.close()


inicializar_bd()


# --- FUNCIONES DE ACCESO SEGURO A LA BD ---
def obtener_usuarios_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM usuarios", conn)
        conn.close()
        users_dict = {}
        for _, row in df.iterrows():
            users_dict[row["usuario"]] = {
                "password": row["password"],
                "email": row["email"],
                "nombre": row["nombre"],
                "tipo": row["tipo"],
            }
        return users_dict


def registrar_usuario_db(usuario, password, email, nombre, tipo):
    with db_lock:
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)",
                (usuario, password, email, nombre, tipo),
            )
            conn.commit()
            conn.close()
            return True
        except:
            return False


def obtener_historial_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT responsable, tipo, correo, historia_clinica as Historia_Clinica, especialidad as Especialidad, estado as Estado, fecha as Fecha FROM historial",
            conn,
        )
        conn.close()
        return df.to_dict(orient="records")


def guardar_historial_db(
    responsable, tipo, correo, historia_clinica, especialidad, estado, fecha
):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historial (responsable, tipo, correo, historia_clinica, especialidad, estado, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                responsable,
                tipo,
                correo,
                historia_clinica,
                especialidad,
                estado,
                fecha,
            ),
        )
        conn.commit()
        conn.close()


def obtener_triage_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT id, paciente as Paciente, triage as Triage, estado as Estado, hora as Hora, registrado_por as Registrado_Por FROM triage",
            conn,
        )
        conn.close()
        return df.to_dict(orient="records")


def guardar_triage_db(paciente, triage, estado, hora, registrado_por):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO triage (paciente, triage, estado, hora, registrado_por) VALUES (?, ?, ?, ?, ?)",
            (paciente, triage, estado, hora, registrado_por),
        )
        conn.commit()
        conn.close()


def actualizar_estado_triage_db(paciente_id, nuevo_estado):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE triage SET estado = ? WHERE id = ?",
            (nuevo_estado, paciente_id),
        )
        conn.commit()
        conn.close()


def limpiar_triage_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM triage")
        conn.commit()
        conn.close()


# Inicializar sesión en Streamlit
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# --- DISEÑO DE LA BARRA LATERAL: AUTENTICACIÓN ---
st.sidebar.title("🔐 S.A.T.R. - Acceso Multi-Usuario")

users_db = obtener_usuarios_db()

if st.session_state.logged_in_user is None:
    opcion_auth = st.sidebar.radio(
        "Seleccione una opción:", ["Iniciar Sesión", "Registrarse"]
    )

    if opcion_auth == "Iniciar Sesión":
        st.sidebar.subheader("🔑 Iniciar Sesión")
        usuario_input = st.sidebar.text_input("Usuario")
        password_input = st.sidebar.text_input("Contraseña", type="password")

        if st.sidebar.button("Entrar al Sistema"):
            if (
                usuario_input in users_db
                and users_db[usuario_input]["password"] == password_input
            ):
                st.session_state.logged_in_user = usuario_input
                st.sidebar.success(f"¡Bienvenido(a), {usuario_input}!")
                st.rerun()
            else:
                st.sidebar.error("Usuario o contraseña incorrectos.")

    else:
        st.sidebar.subheader("📝 Nuevo Registro Permanente")
        nuevo_user = st.sidebar.text_input("Crear Nombre de Usuario")
        nuevo_pass = st.sidebar.text_input(
            "Crear Contraseña", type="password"
        )
        nuevo_correo = st.sidebar.text_input("Correo Electrónico")
        nuevo_nombre = st.sidebar.text_input("Nombre y Apellido Completo")
        nuevo_tipo = "Pasante"
        st.sidebar.info("📌 Perfil asignado: **Pasante**")

        if st.sidebar.button("Registrarse"):
            if (
                not nuevo_user
                or not nuevo_pass
                or not nuevo_correo
                or not nuevo_nombre
            ):
                st.sidebar.warning(
                    "Por favor, complete todos los campos obligatorios."
                )
            elif nuevo_user in users_db:
                st.sidebar.error(
                    "El nombre de usuario ya existe. Elija otro."
                )
            else:
                exito = registrar_usuario_db(
                    nuevo_user,
                    nuevo_pass,
                    nuevo_correo,
                    nuevo_nombre,
                    nuevo_tipo,
                )
                if exito:
                    st.sidebar.success(
                        "¡Registro exitoso y guardado! Inicie sesión ahora."
                    )
                else:
                    st.sidebar.error("Error al registrar en la base de datos.")

    st.sidebar.info(
        "⚠️ **Sistema de Alta Concurrencia:** Optimizado para +200 usuarios."
    )

else:
    user_actual = st.session_state.logged_in_user
    users_db = obtener_usuarios_db()
    datos_usuario = users_db[user_actual]

    st.sidebar.success(
        f"Conectado:\n**{datos_usuario['nombre']}**\n\n*{datos_usuario['tipo']}*"
    )
    st.sidebar.write(f"📧 Correo: `{datos_usuario['email']}`")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- CUERPO PRINCIPAL DE LA PLATAFORMA ---
if st.session_state.logged_in_user is None:
    st.warning(
        "🔒 **Acceso Restringido:** Inicie sesión en la barra lateral para acceder a los módulos."
    )
    st.image(
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
        use_container_width=True,
        caption="Sistema de Auditoría y Trazabilidad de Registros de Salud (S.A.T.R.)",
    )

else:
    st.title("🏥 S.A.T.R. - Plataforma Clínica, Bioestadística y de Guardia")

    modulo_principal = st.selectbox(
        "📂 Seleccione el Módulo de Trabajo:",
        [
            "1. Auditoría de Expedientes y QR",
            "2. Calculadora e Inteligencia Bioestadística Avanzada",
            "3. Tablero de Triage y Urgencias (Alta Resiliencia)",
            "4. Asistente Médico de Guardia (CIE-10, SOAP y Cálculos)",
        ],
    )

    st.markdown("---")

    # ==========================================
    # MÓDULO 1: AUDITORÍA Y EXPEDIENTES
    # ==========================================
    if modulo_principal == "1. Auditoría de Expedientes y QR":
        st.subheader("📋 Módulo de Validación, Análisis y Trazabilidad")

        tab_sub1, tab_sub2, tab_sub3 = st.tabs(
            [
                "🚀 Validación y QR",
                "🤖 Analizador Inteligente",
                "📊 Mi Historial",
            ]
        )

        with tab_sub1:
            col1, col2 = st.columns(2)
            with col1:
                hc_id = st.text_input(
                    "ID o Código de Historia Clínica",
                    placeholder="Ej: HC-2026-089",
                )
                responsable = st.text_input(
                    "Responsable / Auditor", value=datos_usuario["nombre"]
                )
                especialidad = st.selectbox(
                    "Área / Servicio",
                    [
                        "Registro y Estadística de la Salud",
                        "Medicina General",
                        "Pediatría",
                        "Cardiología",
                        "Ginecología",
                        "Cirugía",
                    ],
                )

            with col2:
                st.markdown("**Requisitos Obligatorios:**")
                firma = st.checkbox("¿Cuenta con firma y sello médico?")
                consentimiento = st.checkbox(
                    "¿Tiene el consentimiento informado adjunto?"
                )
                cie10 = st.checkbox("¿Tiene la codificación CIE-10 correcta?")
                lab = st.checkbox("¿Están adjuntos los resultados de laboratorio?")

            if st.button("🚀 Evaluar y Generar QR"):
                if not hc_id:
                    st.error("Ingrese el código de la historia clínica.")
                elif firma and consentimiento and cie10 and lab:
                    st.success(
                        f"🎉 ¡Expediente {hc_id} aprobado! Estado: 🟢 VERDE"
                    )

                    fecha_actual = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    guardar_historial_db(
                        datos_usuario["nombre"],
                        datos_usuario["tipo"],
                        datos_usuario["email"],
                        hc_id,
                        especialidad,
                        "APROBADO (VERDE)",
                        fecha_actual,
                    )

                    qr_data = f"SATR - HC: {hc_id} | Resp: {responsable} | Área: {especialidad} | Estado: VERDE"
                    img = qrcode.make(qr_data)
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()

                    st.markdown("### 📱 Código QR de Validación Oficial:")
                    st.markdown(
                        f'<img src="data:image/png;base64,{img_str}" width="200">',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(
                        "❌ Expediente incompleto. Estado: 🔴 ROJO / AMARILLO."
                    )

        with tab_sub2:
            st.subheader("🤖 Analizador Automático de Expedientes Digitales")
            archivo_subido = st.file_uploader(
                "Cargar archivo (.txt o .csv)", type=["txt", "csv"]
            )
            if archivo_subido is not None:
                texto_archivo = archivo_subido.read().decode(
                    "utf-8", errors="ignore"
                )
                st.text_area(
                    "Vista previa:", texto_archivo[:500] + "...", height=150
                )
                if st.button("🔍 Analizar Archivo"):
                    palabras_clave = [
                        "firma",
                        "consentimiento",
                        "cie-10",
                        "laboratorio",
                        "diagnóstico",
                    ]
                    encontrados = [
                        p for p in palabras_clave if p in texto_archivo.lower()
                    ]
                    faltantes = [
                        p
                        for p in palabras_clave
                        if p not in texto_archivo.lower()
                    ]
                    st.success(
                        f"✅ Detectados: {', '.join(encontrados) if encontrados else 'Ninguno'}"
                    )
                    if faltantes:
                        st.warning(f"⚠️ Ausentes: {', '.join(faltantes)}")
                    else:
                        st.info("🌟 ¡Cumple con todas las menciones clave!")

        with tab_sub3:
            st.subheader("📊 Historial de Revisiones")
            historial_global = obtener_historial_db()
            historial_filtrado = (
                historial_global
                if user_actual == "admin"
                else [
                    h
                    for h in historial_global
                    if h["Responsable"] == datos_usuario["nombre"]
                ]
            )
            if historial_filtrado:
                df_h = pd.DataFrame(historial_filtrado)
                st.dataframe(df_h, use_container_width=True)
                csv = df_h.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Descargar Historial CSV",
                    csv,
                    "historial.csv",
                    "text/csv",
                )
            else:
                st.info("No hay registros en esta sesión.")

    # ==========================================
    # MÓDULO 2: CALCULADORA E INTELIGENCIA BIOESTADÍSTICA (NIVEL NASA)
    # ==========================================
    elif (
        modulo_principal
        == "2. Calculadora e Inteligencia Bioestadística Avanzada"
    ):
        st.subheader("🚀 Central Bioestadística e Indicadores de Rendimiento Clínico")

        sub_est = st.radio(
            "Seleccione el motor analítico:",
            [
                "Indicadores Hospitalarios y Semáforo de Saturación",
                "Estadística Descriptiva, Frecuencias y Varianza",
                "Analizador Documental Masivo",
            ],
        )

        if sub_est == "Indicadores Hospitalarios y Semáforo de Saturación":
            st.markdown(
                "### 📐 Auditoría de Capacidad Instalada (OMS / OPS Estándar)"
            )

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                total_camas = st.number_input(
                    "Camas instaladas y habilitadas",
                    min_value=0,
                    value=60,
                    step=1,
                )
                dias_periodo = st.number_input(
                    "Días del período evaluado", min_value=0, value=30, step=1
                )
                pacientes_ingresos = st.number_input(
                    "Ingresos hospitalarios totales",
                    min_value=0,
                    value=150,
                    step=1,
                )

            with col_i2:
                dias_paciente = st.number_input(
                    "Total de días-paciente (estancia acumulada)",
                    min_value=0,
                    value=1350,
                    step=1,
                )
                pacientes_egresos = st.number_input(
                    "Total de egresos (altas + defunciones)",
                    min_value=0,
                    value=148,
                    step=1,
                )

            if st.button("⚙️ Ejecutar Motor de Cálculo de Alta Precisión"):
                if (
                    total_camas <= 0
                    or dias_periodo <= 0
                    or pacientes_egresos <= 0
                ):
                    st.error(
                        "❌ **Error Crítico de Parámetros:** Los valores de camas, días y egresos deben ser estrictamente mayores a cero."
                    )
                else:
                    ocupacion = (
                        dias_paciente / (total_camas * dias_periodo)
                    ) * 100
                    estancia_media = dias_paciente / pacientes_egresos
                    giro_cama = pacientes_egresos / total_camas
                    intervalo_sustitucion = (
                        (total_camas * dias_periodo) - dias_paciente
                    ) / pacientes_egresos

                    st.markdown("### 📊 Panel de Métricas Oficiales:")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Índice de Ocupación", f"{ocupacion:.2f}%")
                    m2.metric(
                        "Estancia Promedio", f"{estancia_media:.2f} días"
                    )
                    m3.metric("Giro de Cama", f"{giro_cama:.2f} veces")
                    m4.metric(
                        "Intervalo Sustitución",
                        f"{intervalo_sustitucion:.2f} días",
                    )

                    st.markdown("### 🚦 Diagnóstico de Carga Hospitalaria")
                    if ocupacion > 85.0:
                        st.error(
                            f"🔴 **SATURACIÓN CRÍTICA ({ocupacion:.2f}%):** El servicio supera el umbral de seguridad hospitalaria del 85%."
                        )
                    elif 75.0 <= ocupacion <= 85.0:
                        st.success(
                            f"🟢 **EFICIENCIA ÓPTIMA ({ocupacion:.2f}%):** El uso de camas se encuentra dentro de los parámetros ideales."
                        )
                    else:
                        st.warning(
                            f"🟡 **SUBUTILIZACIÓN ({ocupacion:.2f}%):** Capacidad ociosa detectada en el servicio."
                        )

        elif sub_est == "Estadística Descriptiva, Frecuencias y Varianza":
            st.markdown(
                "### 🔢 Laboratorio Bioestadístico (Media, Mediana, Moda, Varianza y Desviación)"
            )
            st.write(
                "Ingrese valores numéricos separados por comas (ej. edades, tiempos de espera, días de internación):"
            )

            input_datos = st.text_input(
                "Vector de datos analíticos",
                "12, 15, 14, 18, 20, 15, 22, 19, 15, 25, 30, 14",
            )

            if st.button("🔬 Procesar Vector Estadístico"):
                try:
                    lista_nums = [
                        float(x.strip())
                        for x in input_datos.split(",")
                        if x.strip()
                    ]
                    if lista_nums:
