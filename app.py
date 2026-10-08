import base64
from io import BytesIO
import pandas as pd
import qrcode
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="S.A.T.R. - Sistema de Auditoría y Trazabilidad",
    page_icon="🏥",
    layout="wide",
)

# Inicializar bases de datos en la memoria de la sesión si no existen
if "users_db" not in st.session_state:
    # Usuario por defecto para pruebas
    st.session_state.users_db = {
        "admin": {
            "password": "admin123",
            "email": "admin@clinica.com",
            "nombre": "Administrador Principal",
        }
    }

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "historial_global" not in st.session_state:
    st.session_state.historial_global = []

# --- DISEÑO DE LA BARRA LATERAL: AUTENTICACIÓN ---
st.sidebar.title("🔐 Panel de Acceso - S.A.T.R.")

if st.session_state.logged_in_user is None:
    opcion_auth = st.sidebar.radio(
        "Seleccione una opción:", ["Iniciar Sesión", "Registrarse como Médico"]
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
                st.sidebar.success(f"¡Bienvenido, Dr(a). {usuario_input}!")
                st.rerun()
            else:
                st.sidebar.error("Usuario o contraseña incorrectos.")

    else:
        st.sidebar.subheader("📝 Nuevo Registro Médico")
        nuevo_user = st.sidebar.text_input("Crear Nombre de Usuario")
        nuevo_pass = st.sidebar.text_input(
            "Crear Contraseña", type="password"
        )
        nuevo_correo = st.sidebar.text_input("Correo Electrónico (para reportes)")
        nuevo_nombre = st.sidebar.text_input("Nombre y Apellido Completo")

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
                }
                st.sidebar.success(
                    "¡Registro exitoso! Ahora inicie sesión en la pestaña anterior."
                )

    st.sidebar.info(
        "⚠️ **Sistema Protegido:** Inicie sesión o regístrese para acceder al módulo clínico."
    )

else:
    # Usuario autenticado
    user_actual = st.session_state.logged_in_user
    datos_medico = st.session_state.users_db[user_actual]

    st.sidebar.success(f"Conectado como:\n**{datos_medico['nombre']}**")
    st.sidebar.write(f"📧 Correo: `{datos_medico['email']}`")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in_user = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "💡 Consejo: Use su correo registrado para recibir o verificar copias de seguridad de sus expedientes."
    )

# --- CUERPO PRINCIPAL DE LA APLICACIÓN ---
if st.session_state.logged_in_user is None:
    # Pantalla de bloqueo si no ha iniciado sesión
    st.warning(
        "🔒 **Acceso Restringido:** Por favor, inicie sesión o regístrese en la barra lateral izquierda para utilizar el sistema S.A.T.R."
    )
    st.image(
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
        use_container_width=True,
        caption="Sistema de Auditoría y Trazabilidad de Registros de Salud (S.A.T.R.)",
    )

else:
    # Sistema Desbloqueado para el Médico
    st.title(
        "📋 S.A.T.R. - Módulo de Validación, Análisis y Trazabilidad Clínica"
    )

    # Pestañas de navegación interna
    tab1, tab2, tab3 = st.tabs(
        [
            "🚀 Validación y Generación QR",
            "🤖 Analizador Inteligente de Archivos",
            "📊 Mi Historial de Revisiones",
        ]
    )

    # --- PESTAÑA 1: VALIDACIÓN MANUAL Y QR ---
    with tab1:
        st.subheader("📝 Módulo de Validación y Generación de QR en Vivo")

        col1, col2 = st.columns(2)

        with col1:
            hc_id = st.text_input(
                "ID o Código de Historia Clínica",
                placeholder="Ej: HC-2026-089",
            )
            medico_tratante = st.text_input(
                "Médico Tratante", value=datos_medico["nombre"]
            )
            especialidad = st.selectbox(
                "Especialidad Médica",
                [
                    "Medicina General",
                    "Pediatría",
                    "Cardiología",
                    "Ginecología",
                    "Cirugía",
                    "Registro y Estadística",
                ],
            )

        with col2:
            st.markdown("**Requisitos Obligatorios:**")
            firma = st.checkbox("¿Cuenta con firma y sello del médico?")
            consentimiento = st.checkbox(
                "¿Tiene el consentimiento informado adjunto?"
            )
            cie10 = st.checkbox("¿Tiene la codificación CIE-10 correcta?")
            lab = st.checkbox("¿Están adjuntos los resultados de laboratorio?")

        if st.button("🚀 Evaluar, Bloquear Errores y Generar QR"):
            if not hc_id:
                st.error(
                    "Por favor, ingrese el ID o código de la historia clínica."
                )
            elif firma and consentimiento and cie10 and lab:
                st.success(
                    f"🎉 ¡Expediente {hc_id} aprobado con éxito! Estado: 🟢 VERDE (Completo y Aprobado)"
                )

                # Guardar en el historial del usuario
                registro_revision = {
                    "Medico": datos_medico["nombre"],
                    "Correo": datos_medico["email"],
                    "Historia_Clinica": hc_id,
                    "Especialidad": especialidad,
                    "Estado": "APROBADO (VERDE)",
                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.historial_global.append(registro_revision)

                # Generar Código QR
                qr_data = f"SATR - HC: {hc_id} | Medico: {medico_tratante} | Esp: {especialidad} | Estado: APROBADO (VERDE) | Correo: {datos_medico['email']}"
                img = qrcode.make(qr_data)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                st.markdown("### 📱 Código QR de Validación Oficial:")
                st.markdown(
                    f'<img src="data:image/png;base64,{img_str}" width="200">',
                    unsafe_allow_html=True,
                )
                st.info(
                    f"ℹ️ Este código QR incluye la trazabilidad digital y está vinculado al correo del médico: `{datos_medico['email']}`."
                )
            else:
                st.error(
                    "❌ Expediente incompleto. Estado: 🔴 ROJO / AMARILLO (Faltan requisitos legales obligatorios)."
                )

    # --- PESTAÑA 2: ANALIZADOR INTELIGENTE DE ARCHIVOS ---
    with tab2:
        st.subheader("🤖 Analizador Automático de Expedientes Digitales")
        st.write(
            "Sube el documento del expediente (texto, notas clínicas o informe médico) para que el sistema verifique automáticamente los elementos obligatorios."
        )

        archivo_subido = st.file_uploader(
            "Cargar archivo del expediente (.txt, .csv o notas)",
            type=["txt", "csv"],
        )

        if archivo_subido is not None:
            # Leer contenido del archivo
            contenido_bytes = archivo_subido.read()
            texto_archivo = contenido_bytes.decode("utf-8", errors="ignore")

            st.text_area(
                "Vista previa del contenido analizado:",
                texto_archivo[:500] + "...",
                height=150,
            )

            if st.button("🔍 Analizar Calidad del Archivo"):
                # Análisis automático de palabras clave
                palabras_clave = [
                    "firma",
                    "consentimiento",
                    "cie-10",
                    "laboratorio",
                    "diagnóstico",
                ]
                encontrados = []
                faltantes = []

                for palabra in palabras_clave:
                    if palabra.lower() in texto_archivo.lower():
                        encontrados.append(palabra)
                    else:
                        faltantes.append(palabra)

                st.markdown("### 📊 Resultados del Análisis:")
                st.success(f"✅ Elementos detectados: {', '.join(encontrados)}")
                if faltantes:
                    st.warning(
                        f"⚠️ Elementos ausentes en el texto: {', '.join(faltantes)}"
                    )
                else:
                    st.info(
                        "🌟 ¡El archivo cuenta con todas las menciones clave auditadas!"
                    )

    # --- PESTAÑA 3: HISTORIAL DE REVISIONES ---
    with tab3:
        st.subheader("📊 Historial de Expedientes Revisados")
        st.write(
            f"Listado de auditorías realizadas por el/la Dr(a). **{datos_medico['nombre']}**:"
        )

        # Filtrar solo el historial del médico conectado (o mostrar todo si es admin)
        if user_actual == "admin":
            historial_filtrado = st.session_state.historial_global
        else:
            historial_filtrado = [
                h
                for h in st.session_state.historial_global
                if h["Medico"] == datos_medico["nombre"]
            ]

        if historial_filtrado:
            df_historial = pd.DataFrame(historial_filtrado)
            st.dataframe(df_historial, use_container_width=True)

            # Opción para descargar reporte en CSV
            csv = df_historial.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Descargar Historial en CSV",
                data=csv,
                file_name=f"historial_auditoria_{user_actual}.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "Aún no hay expedientes evaluados en esta sesión. ¡Realiza tu primera validación en la primera pestaña!"
            )
