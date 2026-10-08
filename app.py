import base64
from io import BytesIO
import json
import os
import pandas as pd
import qrcode
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="S.A.T.R. - Sistema de Auditoría y Trazabilidad",
    page_icon="🏥",
    layout="wide",
)

# Archivos locales para guardar los datos de forma permanente
USER_FILE = "usuarios_satr.json"
HISTORY_FILE = "historial_satr.json"


# Funciones para cargar y guardar datos permanentemente
def cargar_usuarios():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # Usuario por defecto inicial
    return {
        "admin": {
            "password": "admin123",
            "email": "admin@clinica.com",
            "nombre": "Administrador Principal",
            "tipo": "Pasante",
        }
    }


def guardar_usuarios(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


def cargar_historial():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def guardar_historial(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


# Inicializar variables de sesión con los datos permanentes
if "users_db" not in st.session_state:
    st.session_state.users_db = cargar_usuarios()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "historial_global" not in st.session_state:
    st.session_state.historial_global = cargar_historial()

# --- DISEÑO DE LA BARRA LATERAL: AUTENTICACIÓN ---
st.sidebar.title("🔐 Panel de Acceso - S.A.T.R.")

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
        st.sidebar.subheader("📝 Nuevo Registro")
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
                # Guardar permanentemente en el archivo JSON
                guardar_usuarios(st.session_state.users_db)
                st.sidebar.success(
                    "¡Registro exitoso y guardado! Ahora inicie sesión en la pestaña anterior."
                )

    st.sidebar.info(
        "⚠️ **Sistema Protegido:** Inicie sesión para acceder al módulo."
    )

else:
    # Usuario autenticado
    user_actual = st.session_state.logged_in_user
    datos_usuario = st.session_state.users_db[user_actual]

    st.sidebar.success(
        f"Conectado como:\n**{datos_usuario['nombre']}**\n\n*{datos_usuario['tipo']}*"
    )
    st.sidebar.write(f"📧 Correo: `{datos_usuario['email']}`")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- CUERPO PRINCIPAL DE LA APLICACIÓN ---
if st.session_state.logged_in_user is None:
    st.warning(
        "🔒 **Acceso Restringido:** Por favor, inicie sesión o regístrese en la barra lateral izquierda."
    )
    st.image(
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
        use_container_width=True,
        caption="Sistema de Auditoría y Trazabilidad de Registros de Salud (S.A.T.R.)",
    )

else:
    st.title(
        "📋 S.A.T.R. - Módulo de Validación, Análisis y Trazabilidad Clínica"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🚀 Validación y Generación QR",
            "🤖 Analizador Inteligente de Archivos",
            "📊 Mi Historial de Revisiones",
        ]
    )

    # --- PESTAÑA 1 ---
    with tab1:
        st.subheader("📝 Módulo de Validación y Generación de QR en Vivo")

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
                "Especialidad / Área",
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

        if st.button("🚀 Evaluar, Bloquear Errores y Generar QR"):
            if not hc_id:
                st.error("Por favor, ingrese el código de la historia clínica.")
            elif firma and consentimiento and cie10 and lab:
                st.success(
                    f"🎉 ¡Expediente {hc_id} aprobado con éxito! Estado: 🟢 VERDE (Completo y Aprobado)"
                )

                registro_revision = {
                    "Responsable": datos_usuario["nombre"],
                    "Tipo": datos_usuario["tipo"],
                    "Correo": datos_usuario["email"],
                    "Historia_Clinica": hc_id,
                    "Especialidad": especialidad,
                    "Estado": "APROBADO (VERDE)",
                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.historial_global.append(registro_revision)
                # Guardar el historial permanentemente
                guardar_historial(st.session_state.historial_global)

                qr_data = f"SATR - HC: {hc_id} | Resp: {responsable} ({datos_usuario['tipo']}) | Área: {especialidad} | Estado: VERDE"
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
                    "❌ Expediente incompleto. Estado: 🔴 ROJO / AMARILLO (Faltan requisitos legales)."
                )

    # --- PESTAÑA 2 ---
    with tab2:
        st.subheader("🤖 Analizador Automático de Expedientes Digitales")
        archivo_subido = st.file_uploader(
            "Cargar archivo del expediente (.txt o .csv)", type=["txt", "csv"]
        )

        if archivo_subido is not None:
            texto_archivo = archivo_subido.read().decode(
                "utf-8", errors="ignore"
            )
            st.text_area(
                "Vista previa del contenido analizado:",
                texto_archivo[:500] + "...",
                height=150,
            )

            if st.button("🔍 Analizar Calidad del Archivo"):
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
                    p for p in palabras_clave if p not in texto_archivo.lower()
                ]

                st.markdown("### 📊 Resultados del Análisis:")
                st.success(f"✅ Elementos detectados: {', '.join(encontrados)}")
                if faltantes:
                    st.warning(
                        f"⚠️ Elementos ausentes: {', '.join(faltantes)}"
                    )
                else:
                    st.info("🌟 ¡El archivo cuenta con todas las menciones clave!")

    # --- PESTAÑA 3 ---
    with tab3:
        st.subheader("📊 Historial de Expedientes Revisados")
        st.write(
            f"Listado de auditorías registradas por: **{datos_usuario['nombre']}** ({datos_usuario['tipo']})"
        )

        if user_actual == "admin":
            historial_filtrado = st.session_state.historial_global
        else:
            historial_filtrado = [
                h
                for h in st.session_state.historial_global
                if h["Responsable"] == datos_usuario["nombre"]
            ]

        if historial_filtrado:
            df_historial = pd.DataFrame(historial_filtrado)
            st.dataframe(df_historial, use_container_width=True)

            csv = df_historial.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Descargar Historial en CSV",
                data=csv,
                file_name=f"historial_auditoria_{user_actual}.csv",
                mime="text/csv",
            )
        else:
            st.info("Aún no hay expedientes evaluados en esta sesión.")
        
