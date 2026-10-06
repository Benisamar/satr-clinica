import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
from docx import Document

# 1. Configuración inicial de la página
st.set_page_config(page_title="S.A.T.R. - Clínica Profesional", page_icon="🏥", layout="wide")

# Inicializar base de datos temporal en la sesión
if "registros" not in st.session_state:
    st.session_state.registros = pd.DataFrame(columns=[
        "ID_Paciente", "Medico", "Especialidad", "Firma", "Consentimiento", "CIE10", "Laboratorios", "Estado", "Faltantes", "Fecha"
    ])

# --- BARRA LATERAL: SEGURIDAD Y ESTÉTICA PERSONALIZADA ---
st.sidebar.title("⚙️ Panel de Control & Ajustes")

# Seguridad por contraseña
password = st.sidebar.text_input("🔐 Contraseña de Acceso Médico:", type="password")
PASSWORD_CORRECTA = "admin123"

if password != PASSWORD_CORRECTA:
    st.warning("⚠️ **Sistema Protegido:** Por favor, ingrese la contraseña autorizada en la barra lateral para acceder al sistema clínico.")
    st.stop()

st.sidebar.success("✅ Acceso Concedido: Médico Autorizado")
st.sidebar.markdown("---")

# Selector libre de colores y estética total para el médico
st.sidebar.subheader("🎨 Personalización Visual")
modo_estetica = st.sidebar.selectbox("Elige tu Estética Base", ["Minimalista Clean (Luz)", "Modo Oscuro (Dark)", "Cyberpunk Neon"])
color_personalizado = st.sidebar.color_picker("📁 Elige el color exacto de tu carpeta y detalles", "#2E86C1")

# Aplicar estilos CSS dinámicos según el color y modo elegido por el usuario
if modo_estetica == "Modo Oscuro (Dark)":
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #121212; color: #E0E0E0; }}
        div.stButton > button {{ background-color: {color_personalizado}; color: white; border-radius: 8px; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)
elif modo_estetica == "Cyberpunk Neon":
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #05050a; color: {color_personalizado}; }}
        div.stButton > button {{ background-color: {color_personalizado}; color: #000000; border-radius: 8px; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)
else: # Minimalista Clean
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #F8F9FA; color: #212529; }}
        div.stButton > button {{ background-color: {color_personalizado}; color: white; border-radius: 8px; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

# --- INTERFAZ PRINCIPAL ---
st.title("🏥 S.A.T.R. - Sistema de Trazabilidad y Calidad Clínica")
st.markdown(f"**Gestión Inteligente de Historias Clínicas** | *Color Activo:* `{color_personalizado}`")
st.markdown("---")

menu = st.sidebar.selectbox("📂 Menú de Navegación", ["Registrar / Auditar Expediente", "📁 Carpeta Central de Registros"])

if menu == "Registrar / Auditar Expediente":
    st.subheader("📝 Módulo de Validación y Generación de QR en Vivo")
    
    with st.form("form_expediente"):
        col1, col2 = st.columns(2)
        with col1:
            id_paciente = st.text_input("ID o Código de Historia Clínica (Ej: HC-2026-089)")
            medico_resp = st.text_input("Médico Tratante")
            especialidad = st.selectbox("Especialidad Médica", ["Medicina General", "Pediatría", "Cardiología", "Traumatología", "Ginecología"])
        with col2:
            st.markdown("**Requisitos Obligatorios:**")
            tiene_firma = st.checkbox("¿Cuenta con firma y sello del médico?")
            tiene_consentimiento = st.checkbox("¿Tiene el consentimiento informado adjunto?")
            tiene_cie10 = st.checkbox("¿Tiene la codificación CIE-10 correcta?")
            tiene_labs = st.checkbox("¿Están adjuntos los resultados de laboratorio?")
            
        submitted = st.form_submit_button("🚀 Evaluar, Bloquear Errores y Generar QR")
        
        if submitted:
            faltantes = []
            if not id_paciente:
                faltantes.append("El ID del Paciente está vacío.")
            if not medico_resp:
                faltantes.append("El nombre del Médico Tratante está vacío.")
            if not tiene_firma:
                faltantes.append("Falta la firma y sello médico.")
            if not tiene_consentimiento:
                faltantes.append("Falta el consentimiento informado.")
            if not tiene_cie10:
                faltantes.append("Falta la codificación CIE-10.")
            if not tiene_labs:
                faltantes.append("Faltan los resultados de laboratorio.")
                
            if not id_paciente or not medico_resp:
                st.error("❌ **Error Crítico:** Debe rellenar el ID del Paciente y el Médico Tratante obligatoriamente.")
            elif len(faltantes) > 0:
                # Alerta rápida no intrusiva con lo que falta
                st.toast("⚠️ Expediente incompleto. Revisa los faltantes.", icon="🚨")
                st.error("❌ **Expediente Incompleto - Registro Bloqueado**")
                st.warning("⚠️ **Elementos que hacen falta para completar el expediente:**")
                for f in faltantes:
                    st.markdown(f"- 🔴 {f}")
            else:
                estado = "🟢 VERDE (Completo y Aprobado)"
                detalle_faltantes = "Ninguno (100% Completo)"
                
                # Guardar en la base de datos de la sesión
                nuevo_registro = pd.DataFrame([{
                    "ID_Paciente": id_paciente,
                    "Medico": medico_resp,
                    "Especialidad": especialidad,
                    "Firma": "Sí",
                    "Consentimiento": "Sí",
                    "CIE10": "Sí",
                    "Laboratorios": "Sí",
                    "Estado": estado,
                    "Faltantes": detalle_faltantes,
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                
                st.session_state.registros = pd.concat([st.session_state.registros, nuevo_registro], ignore_index=True)
                
                # Notificación rápida flotante de éxito
                st.toast("🎉 ¡Expediente evaluado y guardado con éxito!", icon="✅")
                st.success(f"🎉 ¡Expediente {id_paciente} aprobado con éxito! Estado: **{estado}**")

                # --- GENERADOR DE CÓDIGO QR EN VIVO ---
                st.markdown("---")
                st.subheader("📱 Código QR Generado para el Expediente")
                qr_data = f"SATR-CLINICA | Paciente: {id_paciente} | Medico: {medico_resp} | Estado: APROBADO"
                
                # Crear imagen QR en memoria
                img = qrcode.make(qr_data)
                buf = BytesIO()
                img.save(buf)
                byte_im = buf.getvalue()
                
                col_qr1, col_qr2 = st.columns([1, 2])
                with col_qr1:
                    st.image(byte_im, width=200, caption=f"QR: {id_paciente}")
                with col_qr2:
                    st.info("ℹ️ **Escaneo Rápido:** El personal de enfermería o archivo puede escanear este código QR directamente desde la pantalla para verificar la validez y trazabilidad inmediata del expediente en la clínica.")

elif menu == "📁 Carpeta Central de Registros":
    st.subheader("📁 Archivo Digital Centralizado de Pacientes")
    st.markdown("Aquí se encuentran todos los registros históricos auditados por los médicos de la clínica.")
    
    if len(st.session_state.registros) == 0:
        st.info("Aún no hay registros guardados en la sesión actual.")
    else:
        st.dataframe(st.session_state.registros, use_container_width=True)
        
        # Opción para exportar a Word (DOCX)
        st.markdown("---")
        st.subheader("📄 Exportar Reporte Institucional")
        
        if st.button("📥 Generar y Descargar Reporte en Word (.docx)"):
            doc = Document()
            doc.add_heading("S.A.T.R. - Reporte Oficial de Auditoría Clínica", 0)
            doc.add_paragraph(f"Fecha de emisión: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            doc.add_paragraph("Registros auditados en el sistema central:")
            
            for index, row in st.session_state.registros.iterrows():
                doc.add_paragraph(f"• ID: {row['ID_Paciente']} | Médico: {row['Medico']} | Especialidad: {row['Especialidad']} | Estado: {row['Estado']}")
            
            # Guardar en archivo temporal en memoria
            word_file = "Reporte_Auditoria_SATR.docx"
            doc.save(word_file)
            
            with open(word_file, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Archivo Word Ahora",
                    data=f,
                    file_name="Reporte_Clinica_SATR.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
