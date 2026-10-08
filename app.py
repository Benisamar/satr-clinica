import base64
from io import BytesIO
import json
import os
import pandas as pd
import qrcode
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="S.A.T.R. - Sistema Integral de Salud y Estadística",
    page_icon="🏥",
    layout="wide",
)

# Archivos locales para persistencia permanente de datos
USER_FILE = "usuarios_satr.json"
HISTORY_FILE = "historial_satr.json"
TRIAGE_FILE = "triage_satr.json"


# Funciones de persistencia segura (0 errores si el archivo no existe)
def cargar_datos(archivo, por_defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return por_defecto


def guardar_datos(archivo, datos):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


# Inicializar estados y bases de datos permanentes
if "users_db" not in st.session_state:
    st.session_state.users_db = cargar_datos(
        USER_FILE,
        {
            "admin": {
                "password": "admin123",
                "email": "admin@clinica.com",
                "nombre": "Administrador Principal",
                "tipo": "Pasante",
            }
        },
    )

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "historial_global" not in st.session_state:
    st.session_state.historial_global = cargar_datos(HISTORY_FILE, [])

if "triage_global" not in st.session_state:
    st.session_state.triage_global = cargar_datos(TRIAGE_FILE, [])

# --- DISEÑO DE LA BARRA LATERAL: AUTENTICACIÓN PERSISTENTE ---
st.sidebar.title("🔐 S.A.T.R. - Acceso")

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
                usuario_input in st.session_state.users_db
                and st.session_state.users_db[usuario_input]["password"]
                == password_input
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
            elif nuevo_user in st.session_state.users_db:
                st.sidebar.error(
                    "El nombre de usuario ya existe. Elija otro."
                )
            else:
                st.session_state.users_db[nuevo_user] = {
                    "password": nuevo_pass,
                    "email": nuevo_correo,
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                }
                guardar_datos(USER_FILE, st.session_state.users_db)
                st.sidebar.success(
                    "¡Registro exitoso y guardado! Inicie sesión ahora."
                )

    st.sidebar.info("⚠️ **Sistema Protegido:** Inicie sesión para continuar.")

else:
    user_actual = st.session_state.logged_in_user
    datos_usuario = st.session_state.users_db[user_actual]

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
        "🔒 **Acceso Restringido:** Inicie sesión en la barra lateral para acceder a los módulos del S.A.T.R."
    )
    st.image(
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
        use_container_width=True,
        caption="Sistema de Auditoría y Trazabilidad de Registros de Salud (S.A.T.R.)",
    )

else:
    st.title("🏥 S.A.T.R. - Plataforma Integral de Registros y Estadística")

    modulo_principal = st.selectbox(
        "📂 Seleccione el Módulo de Trabajo:",
        [
            "1. Auditoría de Expedientes y QR",
            "2. Calculadora y Analizador Estadístico Avanzado",
            "3. Tablero de Triage y Urgencias",
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

                    registro_revision = {
                        "Responsable": datos_usuario["nombre"],
                        "Tipo": datos_usuario["tipo"],
                        "Correo": datos_usuario["email"],
                        "Historia_Clinica": hc_id,
                        "Especialidad": especialidad,
                        "Estado": "APROBADO (VERDE)",
                        "Fecha": pd.Timestamp.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }
                    st.session_state.historial_global.append(registro_revision)
                    guardar_datos(
                        HISTORY_FILE, st.session_state.historial_global
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
            historial_filtrado = (
                st.session_state.historial_global
                if user_actual == "admin"
                else [
                    h
                    for h in st.session_state.historial_global
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
    # MÓDULO 2: CALCULADORA Y ANALIZADOR ESTADÍSTICO
    # ==========================================
    elif (
        modulo_principal == "2. Calculadora y Analizador Estadístico Avanzado"
    ):
        st.subheader("📊 Estadísticas de Salud, Frecuencias y Gráficos")

        sub_est = st.radio(
            "Seleccione la modalidad de análisis:",
            [
                "Calculadora de Indicadores y Frecuencias Manual",
                "Analizador Estadístico por Carga de Documento",
            ],
        )

        if sub_est == "Calculadora de Indicadores y Frecuencias Manual":
            st.markdown(
                "### 📐 Indicadores Hospitalarios Clásicos y Distribución (100% Confiable)"
            )
            st.write(
                "Ingrese los valores asistenciales correspondientes al período a evaluar:"
            )

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                total_camas = st.number_input(
                    "Camas disponibles en el servicio",
                    min_value=0,
                    value=50,
                    step=1,
                )
                dias_periodo = st.number_input(
                    "Días del período (ej. 30 o 31 días)",
                    min_value=0,
                    value=30,
                    step=1,
                )
                pacientes_ingresos = st.number_input(
                    "Total de pacientes ingresados",
                    min_value=0,
                    value=120,
                    step=1,
                )

            with col_i2:
                dias_paciente = st.number_input(
                    "Total de días-paciente (estancia acumulada)",
                    min_value=0,
                    value=1050,
                    step=1,
                )
                pacientes_egresos = st.number_input(
                    "Total de egresos (altas + defunciones)",
                    min_value=0,
                    value=118,
                    step=1,
                )

            if st.button("📈 Calcular Indicadores Seguros"):
                if (
                    total_camas <= 0
                    or dias_periodo <= 0
                    or pacientes_egresos <= 0
                ):
                    st.error(
                        "❌ **Error de validación:** El número de camas, días del período y egresos deben ser mayores a cero."
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

                    st.markdown("### 📋 Resultados Oficiales Obtenidos:")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Ocupación de Camas", f"{ocupacion:.2f}%")
                    m2.metric(
                        "Promedio de Permanencia", f"{estancia_media:.2f} días"
                    )
                    m3.metric("Giro / Rotación Cama", f"{giro_cama:.2f}")
                    m4.metric(
                        "Intervalo Sustitución",
                        f"{intervalo_sustitucion:.2f} días",
                    )

                    st.info(
                        f"📝 **Diagnóstico Ejecutivo:** Ocupación del {ocupacion:.2f}% y estancia media de {estancia_media:.2f} días evaluadas bajo parámetros OMS/OPS."
                    )

            st.markdown("---")
            st.markdown(
                "### 🔢 Análisis de Distribución de Frecuencias, Media, Mediana y Moda"
            )
            st.write(
                "Ingrese los números separados por comas (ej. 12, 15, 12, 18, 20, 15):"
            )

            input_datos = st.text_input(
                "Datos numéricos para estadística descriptiva",
                "3, 5, 2, 5, 7, 8, 5, 4, 6, 2, 5, 9",
            )

            if st.button("📊 Generar Estadísticas, Tablas y Gráficos"):
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
                            else "Sin moda clara"
                        )

                        col_m1, col_m2, col_m3 = st.columns(3)
                        col_m1.metric("Media (Promedio)", f"{media:.2f}")
                        col_m2.metric("Mediana", f"{mediana:.2f}")
                        col_m3.metric("Moda", f"{moda_str}")

                        st.markdown(
                            "#### 📋 Tabla de Distribución de Frecuencias Oficial"
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

                        st.dataframe(df_freq, use_container_width=True)

                        st.markdown("#### 📈 Gráfico Dinámico de Frecuencias")
                        st.bar_chart(
                            df_freq.set_index("Valor")["Frecuencia"]
                        )

                        csv_descarga = df_freq.to_csv(index=False).encode(
                            "utf-8"
                        )
                        st.download_button(
                            label="📥 Descargar Reporte Estadístico en CSV",
                            data=csv_descarga,
                            file_name="reporte_estadistica_hospitalaria.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning(
                            "⚠️ Ingrese datos numéricos válidos separados por comas."
                        )
                except Exception as e:
                    st.error(
                        f"❌ Error al procesar los datos ingresados: Revise el formato. ({e})"
                    )

        else:
            st.markdown(
                "### 📁 Analizador Automático de Documentos Estadísticos"
            )
            st.write(
                "Cargue un archivo (.txt o .csv) con datos numéricos. El sistema extraerá la información automáticamente, calculará media, mediana, moda y generará el gráfico."
            )

            archivo_doc = st.file_uploader(
                "Cargar documento de datos", type=["txt", "csv"]
            )
            if archivo_doc is not None:
                contenido = archivo_doc.read().decode(
                    "utf-8", errors="ignore"
                )
                st.text_area(
                    "Vista previa del documento:",
                    contenido[:400] + "...",
                    height=120,
                )

                if st.button("⚙️ Procesar Archivo Automáticamente"):
                    import re

                    numeros_extraidos = [
                        float(n) for n in re.findall(r"\b\d+\.?\d*\b", contenido)
                    ]
                    if numeros_extraidos:
                        s_doc = pd.Series(numeros_extraidos)
                        st.success(
                            f"¡Éxito! Se leyeron {len(numeros_extraidos)} valores numéricos."
                        )

                        m_med = s_doc.mean()
                        m_mediana = s_doc.median()
                        m_modas = s_doc.mode().tolist()

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Media Extraída", f"{m_med:.2f}")
                        c2.metric("Mediana Extraída", f"{m_mediana:.2f}")
                        c3.metric(
                            "Moda Extraída",
                            ", ".join(map(str, m_modas))
                            if m_modas
                            else "N/A",
                        )

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
                            label="📥 Descargar Análisis del Documento (CSV)",
                            data=csv_doc,
                            file_name="analisis_documento_salud.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning(
                            "No se detectaron valores numéricos válidos en el archivo."
                        )

    # ==========================================
    # MÓDULO 3: TABLERO DE CONTROL DE TRIAGE
    # ==========================================
    elif modulo_principal == "3. Tablero de Triage y Urgencias":
        st.subheader("🚨 Gestión y Flujo de Pacientes en Urgencias (Triage)")
        st.write(
            "Tablero dinámico de control de emergencias en tiempo real para el personal médico."
        )

        # KPIs Rápidos (Métricas de Urgencias)
        total_pacientes = len(st.session_state.triage_global)
        en_espera = len(
            [
                p
                for p in st.session_state.triage_global
                if p["Estado"] == "En Espera"
            ]
        )
        en_atencion = len(
            [
                p
                for p in st.session_state.triage_global
                if p["Estado"] == "En Atención"
            ]
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("Total en Urgencias", total_pacientes)
        k2.metric("Pacientes en Espera", en_espera)
        k3.metric("Pacientes en Atención", en_atencion)

        st.markdown("---")

        # Formulario de registro ultraseguro
        with st.form("form_triage", clear_on_submit=True):
            st.markdown("#### ➕ Registrar Ingreso Rápido de Paciente")
            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t1:
                nombre_paciente = st.text_input(
                    "Nombre o Cédula del Paciente *"
                )
            with c_t2:
                nivel_triage = st.selectbox(
                    "Clasificación Triage (Manchester/OPS)",
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
                "🚀 Registrar e Ingresar al Flujo"
            )
            if submit_triage:
                if not nombre_paciente.strip():
                    st.error(
                        "❌ **Error:** Debe ingresar el nombre o identificador del paciente."
                    )
                else:
                    nuevo_registro_triage = {
                        "Paciente": nombre_paciente.strip(),
                        "Triage": nivel_triage,
                        "Estado": estado_atencion,
                        "Hora": pd.Timestamp.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "Registrado_Por": datos_usuario["nombre"],
                    }
                    st.session_state.triage_global.append(
                        nuevo_registro_triage
                    )
                    guardar_datos(
                        TRIAGE_FILE, st.session_state.triage_global
                    )
                    st.success(
                        f"✅ ¡Paciente **{nombre_paciente}** registrado con éxito en el sistema!"
                    )
                    st.rerun()

        st.markdown("### 📋 Listado Activo de Urgencias")

        if st.session_state.triage_global:
            filtro_estado = st.selectbox(
                "🔍 Filtrar vista por estado del paciente:",
                ["Todos", "En Espera", "En Atención", "Dado de Alta"],
            )

            lista_filtrada = st.session_state.triage_global
            if filtro_estado != "Todos":
                lista_filtrada = [
                    p
                    for p in st.session_state.triage_global
                    if p["Estado"] == filtro_estado
                ]

            df_triage = pd.DataFrame(lista_filtrada)
            st.dataframe(df_triage, use_container_width=True)

            st.markdown("---")
            st.markdown("#### ⚡ Acciones de Control Médico")
            col_acc1, col_acc2 = st.columns(2)

            with col_acc1:
                nombres_en_lista = [
                    p["Paciente"] for p in st.session_state.triage_global
                ]
                if nombres_en_lista:
                    paciente_a_editar = st.selectbox(
                        "Seleccionar paciente para cambiar estado:",
                        nombres_en_lista,
                    )
                    nuevo_estado = st.selectbox(
                        "Nuevo Estado:",
                        ["En Espera", "En Atención", "Dado de Alta"],
                    )
                    if st.button("🔄 Actualizar Estado del Paciente"):
                        for p in st.session_state.triage_global:
                            if p["Paciente"] == paciente_a_editar:
                                p["Estado"] = nuevo_estado
                        guardar_datos(
                            TRIAGE_FILE, st.session_state.triage_global
                        )
                        st.success(
                            f"¡Estado de {paciente_a_editar} actualizado a '{nuevo_estado}'!"
                        )
                        st.rerun()

            with col_acc2:
                st.write("---")
                if st.button("🧹 Borrar Todos los Registros de Urgencias"):
                    st.session_state.triage_global = []
                    guardar_datos(TRIAGE_FILE, [])
                    st.rerun()

            csv_triage = pd.DataFrame(
                st.session_state.triage_global
            ).to_csv(index=False)
            st.download_button(
                label="📥 Descargar Reporte de Urgencias (CSV)",
                data=csv_triage,
                file_name="reporte_triage_urgencias.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "📭 No hay pacientes activos en el servicio de urgencias en este momento."
            )

