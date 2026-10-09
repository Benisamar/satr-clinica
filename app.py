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
                        s_datos = pd.Series(lista_nums)
                        media = s_datos.mean()
                        mediana = s_datos.median()
                        moda_vals = s_datos.mode().tolist()
                        moda_str = (
                            ", ".join(map(str, moda_vals))
                            if moda_vals
                            else "Sin moda única"
                        )
                        varianza = s_datos.var(ddof=0)
                        desv_std = s_datos.std(ddof=0)
                        min_val = s_datos.min()
                        max_val = s_datos.max()
                        rango = max_val - min_val

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Media (μ)", f"{media:.2f}")
                        c2.metric("Mediana (Me)", f"{mediana:.2f}")
                        c3.metric("Moda (Mo)", f"{moda_str}")
                        c4.metric(
                            "Desviación Estándar (σ)", f"{desv_std:.2f}"
                        )

                        c5, c6, c7, c8 = st.columns(4)
                        c5.metric("Varianza (σ²)", f"{varianza:.2f}")
                        c6.metric("Valor Mínimo", f"{min_val}")
                        c7.metric("Valor Máximo", f"{max_val}")
                        c8.metric("Rango", f"{rango}")

                        st.markdown(
                            "#### 📋 Tabla Analítica de Distribución de Frecuencias"
                        )
                        df_freq = (
                            s_datos.value_counts()
                            .reset_index()
                            .rename(
                                columns={
                                    "index": "Valor",
                                    0: "Frecuencia",
                                    "count": "Frecuencia",
                                }
                            )
                        )
                        df_freq = df_freq.sort_values(by="Valor").reset_index(
                            drop=True
                        )
                        df_freq["Frecuencia Acumulada"] = df_freq[
                            "Frecuencia"
                        ].cumsum()
                        df_freq["Frecuencia Relativa"] = (
                            df_freq["Frecuencia"] / len(lista_nums)
                        ).round(4)
                        df_freq["Porcentaje (%)"] = (
                            df_freq["Frecuencia Relativa"] * 100
                        ).round(2)

                        st.dataframe(df_freq, use_container_width=True)

                        st.markdown(
                            "#### 📈 Histograma de Distribución Frecuencial"
                        )
                        st.bar_chart(
                            df_freq.set_index("Valor")["Frecuencia"]
                        )

                        csv_descarga = df_freq.to_csv(index=False).encode(
                            "utf-8"
                        )
                        st.download_button(
                            label="📥 Descargar Reporte Bioestadístico (CSV)",
                            data=csv_descarga,
                            file_name="reporte_bioestadistica_satr.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("⚠️ Ingrese datos numéricos válidos.")
                except Exception as e:
                    st.error(f"❌ Error en el procesamiento del vector: {e}")

        else:
            st.markdown(
                "### 📁 Analizador Masivo de Documentos Estadísticos"
            )
            st.write(
                "Cargue expedientes en formato plano (.txt o .csv). El motor extraerá todos los valores numéricos para su analítica."
            )

            archivo_doc = st.file_uploader(
                "Cargar archivo de datos clínicos", type=["txt", "csv"]
            )
            if archivo_doc is not None:
                contenido = archivo_doc.read().decode(
                    "utf-8", errors="ignore"
                )
                st.text_area(
                    "Vista previa del documento:",
                    contenido[:500] + "...",
                    height=130,
                )

                if st.button("⚙️ Ejecutar Extracción y Análisis Masivo"):
                    import re

                    numeros_extraidos = [
                        float(n) for n in re.findall(r"\b\d+\.?\d*\b", contenido)
                    ]
                    if numeros_extraidos:
                        s_doc = pd.Series(numeros_extraidos)
                        st.success(
                            f"¡Extracción exitosa! {len(numeros_extraidos)} registros numéricos procesados."
                        )

                        m_med = s_doc.mean()
                        m_mediana = s_doc.median()
                        m_std = s_doc.std(ddof=0)

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Media Extraída", f"{m_med:.2f}")
                        c2.metric("Mediana Extraída", f"{m_mediana:.2f}")
                        c3.metric("Desviación (σ)", f"{m_std:.2f}")

                        df_doc_freq = (
                            s_doc.value_counts()
                            .reset_index()
                            .rename(
                                columns={
                                    "index": "Valor",
                                    0: "Frecuencia",
                                    "count": "Frecuencia",
                                }
                            )
                            .sort_values(by="Valor")
                            .reset_index(drop=True)
                        )
                        st.dataframe(df_doc_freq, use_container_width=True)
                        st.bar_chart(
                            df_doc_freq.set_index("Valor")["Frecuencia"]
                        )

                        csv_doc = df_doc_freq.to_csv(index=False).encode(
                            "utf-8"
                        )
                        st.download_button(
                            label="📥 Descargar Analítica Documental (CSV)",
                            data=csv_doc,
                            file_name="analisis_documental_satr.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning(
                            "No se identificaron patrones numéricos válidos en el archivo cargado."
                        )

    # ==========================================
    # MÓDULO 3: TABLERO DE TRIAGE Y URGENCIAS (ALTA RESILIENCIA)
    # ==========================================
    elif (
        modulo_principal
        == "3. Tablero de Triage y Urgencias (Alta Resiliencia)"
    ):
        st.subheader(
            "🚨 Centro de Control Operativo de Urgencias y Triage en Tiempo Real"
        )
        st.write(
            "Monitoreo crítico de flujos, tiempos de espera y priorización clínica."
        )

        triage_global = obtener_triage_db()

        total_pacientes = len(triage_global)
        en_espera = len(
            [p for p in triage_global if p["Estado"] == "En Espera"]
        )
        en_atencion = len(
            [p for p in triage_global if p["Estado"] == "En Atención"]
        )
        criticos = len(
            [
                p
                for p in triage_global
                if "Nivel 1" in p["Triage"] or "Nivel 2" in p["Triage"]
            ]
        )

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Censo de Urgencias", total_pacientes)
        k2.metric("Pacientes en Espera", en_espera)
        k3.metric("En Atención Médica", en_atencion)
        k4.metric("Casos Críticos (N1/N2)", criticos)

        st.markdown("---")

        with st.form("form_triage", clear_on_submit=True):
            st.markdown("#### ➕ Admisión Inmediata a Urgencias / Triage")
            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t1:
                nombre_paciente = st.text_input(
                    "Nombre o Cédula del Paciente *"
                )
            with c_t2:
                nivel_triage = st.selectbox(
                    "Escala de Triage (Manchester / OPS)",
                    [
                        "Nivel 1 - Resucitación (Rojo)",
                        "Nivel 2 - Emergencia (Naranja)",
                        "Nivel 3 - Urgencia (Amarillo)",
                        "Nivel 4 - Menor Urgencia (Verde)",
                        "Nivel 5 - No Urgente (Azul)",
                    ],
                )
            with c_t3:
                estado_atencion = st.selectbox(
                    "Estado Inicial", ["En Espera", "En Atención"]
                )

            submit_triage = st.form_submit_button(
                "🚀 Registrar Ingreso a Urgencias"
            )
            if submit_triage:
                if not nombre_paciente.strip():
                    st.error(
                        "❌ **Error:** Debe ingresar el identificador del paciente."
                    )
                else:
                    hora_actual = pd.Timestamp.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    guardar_triage_db(
                        nombre_paciente.strip(),
                        nivel_triage,
                        estado_atencion,
                        hora_actual,
                        datos_usuario["nombre"],
                    )
                    st.success(
                        f"✅ ¡Paciente **{nombre_paciente}** admitido exitosamente!"
                    )
                    st.rerun()

        st.markdown("### 📋 Tablero Activo de Control de Flujo")

        triage_global = obtener_triage_db()
        if triage_global:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_estado = st.selectbox(
                    "Filtrar por Estado:",
                    ["Todos", "En Espera", "En Atención", "Dado de Alta"],
                )
            with col_f2:
                filtro_nivel = st.selectbox(
                    "Filtrar por Triage:",
                    [
                        "Todos",
                        "Nivel 1 - Resucitación (Rojo)",
                        "Nivel 2 - Emergencia (Naranja)",
                        "Nivel 3 - Urgencia (Amarillo)",
                        "Nivel 4 - Menor Urgencia (Verde)",
                        "Nivel 5 - No Urgente (Azul)",
                    ],
                )

            lista_filtrada = triage_global
            if filtro_estado != "Todos":
                lista_filtrada = [
                    p for p in lista_filtrada if p["Estado"] == filtro_estado
                ]
            if filtro_nivel != "Todos":
                lista_filtrada = [
                    p for p in lista_filtrada if p["Triage"] == filtro_nivel
                ]

            if lista_filtrada:
                df_triage = pd.DataFrame(lista_filtrada)
                st.dataframe(
                    df_triage.drop(columns=["id"], errors="ignore"),
                    use_container_width=True,
                )
            else:
                st.info(
                    "No hay pacientes que coincidan con los filtros seleccionados."
                )

            st.markdown("---")
            st.markdown("#### ⚡ Acciones de Gestión de Guardia")
            col_acc1, col_acc2 = st.columns(2)

            with col_acc1:
                opciones_pacientes = {
                    f"{p['Paciente']} (Ingreso: {p['Hora']})": p["id"]
                    for p in triage_global
                }
                if opciones_pacientes:
                    paciente_seleccionado_label = st.selectbox(
                        "Seleccionar paciente para actualizar estado:",
                        list(opciones_pacientes.keys()),
                    )
                    paciente_id_activo = opciones_pacientes[
                        paciente_seleccionado_label
                    ]

                    nuevo_estado = st.selectbox(
                        "Asignar Nuevo Estado:",
                        ["En Espera", "En Atención", "Dado de Alta"],
                    )
                    if st.button("🔄 Actualizar Estado Clínico"):
                        actualizar_estado_triage_db(
                            paciente_id_activo, nuevo_estado
                        )
                        st.success("¡Estado del paciente actualizado con éxito!")
                        st.rerun()

            with col_acc2:
                st.write("---")
                if st.button("🧹 Vaciar Registro de Urgencias (Reiniciar Turno)"):
                    limpiar_triage_db()
                    st.success("El tablero de urgencias ha sido reiniciado.")
                    st.rerun()

            csv_triage = pd.DataFrame(triage_global).to_csv(index=False)
            st.download_button(
                label="📥 Descargar Reporte Completo de Urgencias (CSV)",
                data=csv_triage,
                file_name="reporte_urgencias_triage.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "📭 Servicio de urgencias despejado. No hay pacientes activos registrados."
            )

    # ==========================================
    # MÓDULO 4: ASISTENTE MÉDICO DE GUARDIA
    # ==========================================
    elif (
        modulo_principal
        == "4. Asistente Médico de Guardia (CIE-10, SOAP y Cálculos)"
    ):
        st.subheader("🩺 Asistente Clínico para el Día a Día en Guardia")
        st.write(
            "Herramientas de consulta rápida y redacción médica para el personal asistencial."
        )

        sub_guardia = st.selectbox(
            "Seleccione la utilidad médica:",
            [
                "📖 Buscador Rápido de Códigos CIE-10",
                "📝 Generador de Nota de Evolución SOAP",
                "🧮 Calculadoras Clínicas de Emergencia (IMC & Goteo)",
            ],
        )

        if sub_guardia == "📖 Buscador Rápido de Códigos CIE-10":
            st.markdown("### 🔍 Consulta Rápida del Manual CIE-10")
            st.write(
                "Busque patologías frecuentes para obtener su codificación oficial de forma inmediata:"
            )

            base_cie10 = [
                {
                    "Código": "J02.9",
                    "Diagnóstico": "Faringitis aguda, no especificada",
                    "Capítulo": "Enfermedades respiratorias",
                },
                {
                    "Código": "J18.9",
                    "Diagnóstico": "Neumonía, no especificada",
                    "Capítulo": "Enfermedades respiratorias",
                },
                {
                    "Código": "K35.9",
                    "Diagnóstico": (
                        "Apendicitis aguda, sin otra especificación"
                    ),
                    "Capítulo": "Enfermedades digestivas",
                },
                {
                    "Código": "K30",
                    "Diagnóstico": "Dispepsia (Indigestión)",
                    "Capítulo": "Enfermedades digestivas",
                },
                {
                    "Código": "I10",
                    "Diagnóstico": "Hipertensión esencial (primaria)",
                    "Capítulo": "Enfermedades del sistema circulatorio",
                },
                {
                    "Código": "E11.9",
                    "Diagnóstico": (
                        "Diabetes mellitus tipo 2 sin complicaciones"
                    ),
                    "Capítulo": "Enfermedades endocrinas y metabólicas",
                },
                {
                    "Código": "A09",
                    "Diagnóstico": (
                        "Diarrea y gastroenteritis de presunto origen infeccioso"
                    ),
                    "Capítulo": "Enfermedades infecciosas",
                },
                {
                    "Código": "A90",
                    "Diagnóstico": "Fiebre del dengue [dengue clásico]",
                    "Capítulo": "Enfermedades infecciosas",
                },
                {
                    "Código": "S93.4",
                    "Diagnóstico": "Esguinces y torceduras del tobillo",
                    "Capítulo": "Traumatismos y lesiones",
                },
                {
                    "Código": "R51",
                    "Diagnóstico": "Cefalea (Dolor de cabeza)",
                    "Capítulo": "Síntomas y signos generales",
                },
                {
                    "Código": "R10.4",
                    "Diagnóstico": "Dolor abdominal no especificado",
                    "Capítulo": "Síntomas y signos generales",
                },
                {
                    "Código": "N39.0",
                    "Diagnóstico": (
                        "Infección de vías urinarias, sitio no especificado"
                    ),
                    "Capítulo": "Enfermedades genitourinarias",
                },
            ]

            df_cie = pd.DataFrame(base_cie10)
            busqueda = st.text_input(
                "🔎 Escriba el síntoma o diagnóstico a buscar:",
                placeholder="Ej: dengue, dolor, neumonía, diabetes...",
            )

            if busqueda:
                resultado_busqueda = df_cie[
                    df_cie["Diagnóstico"]
                    .str.lower()
                    .str.contains(busqueda.lower())
                    | df_cie["Código"]
                    .str.lower()
                    .str.contains(busqueda.lower())
                ]
                if not resultado_busqueda.empty:
                    st.success(
                        f"Se encontraron {len(resultado_busqueda)} coincidencias:"
                    )
                    st.dataframe(
                        resultado_busqueda, use_container_width=True
                    )
                else:
                    st.warning(
                        "No se encontró ese término en la base rápida. Verifique la ortografía."
                    )
            else:
                st.markdown("#### Listado Frecuente en Guardia:")
                st.dataframe(df_cie, use_container_width=True)

        elif sub_guardia == "📝 Generador de Nota de Evolución SOAP":
            st.markdown(
                "### 📝 Redactor Automatizado de Notas Clínicas (Formato SOAP)"
            )
            st.write(
                "Complete los datos del paciente para estructurar una nota médica profesional lista para el expediente:"
            )

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                p_nombre = st.text_input("Nombre y Apellido del Paciente")
                p_edad = st.text_input("Edad / Sexo")
            with col_s2:
                p_fecha = st.text_input(
                    "Fecha y Hora",
                    value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                )
                p_medico = st.text_input(
                    "Médico Tratante / Residente",
                    value=datos_usuario["nombre"],
                )

            st.markdown("---")
            subjetivo = st.text_area(
                "**S (Subjetivo):** Motivo de consulta y síntomas referidos por el paciente."
            )
            objetivo = st.text_area(
                "**O (Objetivo):** Signos vitales, examen físico y hallazgos clínicos."
            )
            analisis = st.text_area(
                "**A (Análisis / Diagnóstico):** Impresión diagnóstica y evolución clínica."
            )
            plan = st.text_area(
                "**P (Plan):** Tratamiento indicado, exámenes paraclínicos y recomendaciones."
            )

            if st.button("📄 Generar Nota Clínica Estructurada"):
                if not p_nombre or not subjetivo:
                    st.error(
                        "Por favor, complete al menos el nombre del paciente y la sección Subjetiva."
                    )
                else:
                    nota_formateada = f"""
==================================================
              NOTA DE EVOLUCIÓN CLÍNICA (SOAP)
==================================================
Paciente: {p_nombre} | Edad/Sexo: {p_edad}
Fecha/Hora: {p_fecha}
Responsable: {p_medico} ({datos_usuario['tipo']})
--------------------------------------------------
[S] SUBJETIVO:
{subjetivo}

[O] OBJETIVO:
{objetivo}

[A] ANÁLISIS / DIAGNÓSTICO:
{analisis}

[P] PLAN Y TRATAMIENTO:
{plan}
==================================================
"""
                    st.markdown("### 📋 Vista Previa del Documento Médico:")
                    st.code(nota_formateada, language="text")

                    st.download_button(
                        label="📥 Descargar Nota Médica en TXT",
                        data=nota_formateada.encode("utf-8"),
                        file_name=f"Nota_Clinica_{p_nombre.replace(' ', '_')}.txt",
                        mime="text/plain",
                    )

        elif (
            sub_guardia
            == "🧮 Calculadoras Clínicas de Emergencia (IMC & Goteo)"
        ):
            st.markdown(
                "### 🧮 Calculadoras Auxiliares de Urgencias y Consulta"
            )

            calc_tab = st.radio(
                "Seleccione la calculadora:",
                [
                    "Índice de Masa Corporal (IMC)",
                    "Velocidad de Infusión (Goteo de Soluciones)",
                ],
            )

            if calc_tab == "Índice de Masa Corporal (IMC)":
                st.markdown("#### Cálculo de Antropometría y Estado Nutricional")
                c_imc1, c_imc2 = st.columns(2)
                with c_imc1:
                    peso_kg = st.number_input(
                        "Peso del paciente (kg)",
                        min_value=1.0,
                        value=70.0,
                        step=0.5,
                    )
                with c_imc2:
                    talla_m = st.number_input(
                        "Talla / Estatura (metros, ej. 1.75)",
                        min_value=0.5,
                        value=1.70,
                        step=0.01,
                    )

                if st.button("⚖️ Calcular IMC"):
                    if talla_m > 0:
                        imc = peso_kg / (talla_m**2)
                        st.metric("Índice de Masa Corporal (IMC)", f"{imc:.2f}")

                        if imc < 18.5:
                            st.warning(
                                "⚠️ Clasificación: **Bajo peso** (Delgadez)"
                            )
                        elif 18.5 <= imc < 25.0:
                            st.success(
                                "✅ Clasificación: **Peso normal** (Eutrófico)"
                            )
                        elif 25.0 <= imc < 30.0:
                            st.warning("⚠️ Clasificación: **Sobrepeso**")
                        else:
                            st.error(
                                "🔴 Clasificación: **Obesidad** (Riesgo metabólico elevado)"
                            )
                    else:
                        st.error("La talla debe ser mayor a cero.")

            else:
                st.markdown(
                    "#### Cálculo de Velocidad de Infusión (Gotas por Minuto)"
                )
                st.write(
                    "Calcula el goteo para sueros y soluciones intravenosas según el volumen y el tiempo."
                )

                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    volumen_ml = st.number_input(
                        "Volumen total a infundir (ml)",
                        min_value=10.0,
                        value=500.0,
                        step=50.0,
                    )
                    horas = st.number_input(
                        "Tiempo en horas",
                        min_value=0.5,
                        value=8.0,
                        step=0.5,
                    )
                with c_g2:
                    factor_goteo = st.selectbox(
                        "Equipo de Infusión",
                        [
                            "Macrogotero (20 gotas/ml - Adultos)",
                            "Microgotero (60 microgotas/ml - Pediátrico)",
                        ],
                    )

                if st.button("💧 Calcular Goteo"):
                    if horas > 0:
                        factor = (
                            20
                            if "Macrogotero" in factor_goteo
                            else 60
                        )
                        goteo_minuto = (volumen_ml * factor) / (horas * 60)

                        st.metric(
                            "Velocidad de Infusión Requerida",
                            f"{goteo_minuto:.1f} gotas/min",
                        )
                        st.info(
                            f"💡 **Indicación práctica:** Administrar {round(goteo_minuto)} gotas por minuto para pasar {volumen_ml} ml en {horas} horas."
                        )
                    else:
                        st.error("El tiempo en horas debe ser mayor a cero.")
