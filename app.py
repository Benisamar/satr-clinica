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
    page_title="S.A.T.R. - Plataforma Integral de Salud, Admisión y Finanzas",
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

        # Tabla de Pacientes en Admisión y Seguros
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admision_pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT NOT NULL,
                cedula TEXT,
                tipo_atencion TEXT NOT NULL,
                aseguradora TEXT,
                estado_expediente TEXT NOT NULL,
                detalles_pendientes TEXT,
                registrado_por TEXT NOT NULL,
                fecha_hora TEXT NOT NULL
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

        # Tabla de Citas Médicas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT NOT NULL,
                medico TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                motivo TEXT,
                estado TEXT NOT NULL
            )
        """
        )

        # Tabla de Contabilidad y Caja
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contabilidad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                concepto TEXT NOT NULL,
                tipo TEXT NOT NULL,
                metodo_pago TEXT NOT NULL,
                monto REAL NOT NULL,
                categoria TEXT NOT NULL,
                registrado_por TEXT NOT NULL
            )
        """
        )

        # Tabla de Insumos de Admisión
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT UNIQUE NOT NULL,
                cantidad INTEGER NOT NULL,
                minimo_requerido INTEGER NOT NULL
            )
        """
        )

        # Crear usuario administrador por defecto
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
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

        # Cargar insumos iniciales por defecto si está vacía
        cursor.execute("SELECT COUNT(*) FROM insumos")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO insumos (item, cantidad, minimo_requerido) VALUES (?, ?, ?)",
                ("Resmas de Papel Carta/Oficio", 5, 2),
            )
            cursor.execute(
                "INSERT INTO insumos (item, cantidad, minimo_requerido) VALUES (?, ?, ?)",
                ("Carpetas de Expedientes", 20, 5),
            )
            cursor.execute(
                "INSERT INTO insumos (item, cantidad, minimo_requerido) VALUES (?, ?, ?)",
                ("Planillas Seguros Miranda", 15, 10),
            )

        conn.commit()
        conn.close()


inicializar_bd()


# --- FUNCIONES DE BASE DE DATOS ---
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


def obtener_admision_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT id, paciente as Paciente, cedula as Cédula, tipo_atencion as Atención, aseguradora as Aseguradora, estado_expediente as Estado, detalles_pendientes as Pendientes, registrado_por as Registrado_Por, fecha_hora as Fecha_Hora FROM admision_pacientes",
            conn,
        )
        conn.close()
        return df.to_dict(orient="records")


def guardar_admision_db(
    paciente,
    cedula,
    tipo_atencion,
    aseguradora,
    estado_expediente,
    detalles_pendientes,
    registrado_por,
    fecha_hora,
):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admision_pacientes (paciente, cedula, tipo_atencion, aseguradora, estado_expediente, detalles_pendientes, registrado_por, fecha_hora) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                paciente,
                cedula,
                tipo_atencion,
                aseguradora,
                estado_expediente,
                detalles_pendientes,
                registrado_por,
                fecha_hora,
            ),
        )
        conn.commit()
        conn.close()


def actualizar_estado_admision_db(adm_id, nuevo_estado, detalles):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE admision_pacientes SET estado_expediente = ?, detalles_pendientes = ? WHERE id = ?",
            (nuevo_estado, detalles, adm_id),
        )
        conn.commit()
        conn.close()


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


def obtener_citas_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT id, paciente as Paciente, medico as Medico, especialidad as Especialidad, fecha_hora as Fecha_Hora, motivo as Motivo, estado as Estado FROM citas",
            conn,
        )
        conn.close()
        return df.to_dict(orient="records")


def guardar_cita_db(
    paciente, medico, especialidad, fecha_hora, motivo, estado
):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO citas (paciente, medico, especialidad, fecha_hora, motivo, estado) VALUES (?, ?, ?, ?, ?, ?)",
            (paciente, medico, especialidad, fecha_hora, motivo, estado),
        )
        conn.commit()
        conn.close()


def actualizar_estado_cita_db(cita_id, nuevo_estado):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE citas SET estado = ? WHERE id = ?",
            (nuevo_estado, cita_id),
        )
        conn.commit()
        conn.close()


def obtener_contabilidad_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT id, fecha as Fecha, concepto as Concepto, tipo as Tipo, metodo_pago as Metodo_Pago, monto as Monto, categoria as Categoria, registrado_por as Registrado_Por FROM contabilidad",
            conn,
        )
        conn.close()
        return df.to_dict(orient="records")


def guardar_transaccion_db(
    fecha, concepto, tipo, metodo_pago, monto, categoria, registrado_por
):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contabilidad (fecha, concepto, tipo, metodo_pago, monto, categoria, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                fecha,
                concepto,
                tipo,
                metodo_pago,
                monto,
                categoria,
                registrado_por,
            ),
        )
        conn.commit()
        conn.close()


def obtener_insumos_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM insumos", conn)
        conn.close()
        return df.to_dict(orient="records")


def actualizar_insumo_db(item_id, nueva_cant):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE insumos SET cantidad = ? WHERE id = ?", (nueva_cant, item_id)
        )
        conn.commit()
        conn.close()


# Inicializar sesión en Streamlit
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# --- BARRA LATERAL: AUTENTICACIÓN Y NAVEGACIÓN ---
st.sidebar.title("🔐 S.A.T.R. CLÍNICA")

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
                st.sidebar.warning("Complete todos los campos obligatorios.")
            elif nuevo_user in users_db:
                st.sidebar.error("El nombre de usuario ya existe.")
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
                        "¡Registro exitoso! Inicie sesión ahora."
                    )
                else:
                    st.sidebar.error("Error al registrar en la base de datos.")

    st.sidebar.info(
        "⚠️ **Sistema de Control de Admisión Hospitalaria:** Diseñado para alta velocidad."
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

# --- CUERPO PRINCIPAL ---
if st.session_state.logged_in_user is None:
    st.warning(
        "🔒 **Acceso Restringido:** Inicie sesión en la barra lateral para acceder al sistema."
    )
    st.image(
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
        use_container_width=True,
        caption="Sistema de Auditoría, Trazabilidad y Recepción (S.A.T.R. CLÍNICA)",
    )

else:
    st.title("🏥 S.A.T.R. CLÍNICA - Central de Admisión y Control General")

    modulo_principal = st.selectbox(
        "📂 Seleccione el Módulo de Trabajo:",
        [
            "1. Control de Admisión, Seguros y Expedientes (Semáforo)",
            "2. Coordinación Médica, Citas y Avisos de WhatsApp",
            "3. Contabilidad, Cierre de Caja y Balance Financiero",
            "4. Auditoría de Expedientes e Historia Clínica (QR)",
            "5. Central Bioestadística e Indicadores (Nivel OMS)",
            "6. Tablero de Triage y Urgencias en Tiempo Real",
            "7. Asistente Médico de Guardia (CIE-10, SOAP y Cálculos)",
            "8. Almacén e Insumos de Admisión",
        ],
    )

    st.markdown("---")

    # ==========================================
    # MÓDULO 1: ADMISIÓN, SEGUROS Y EXPEDIENTES (SEMÁFORO)
    # ==========================================
    if modulo_principal == "1. Control de Admisión, Seguros y Expedientes (Semáforo)":
        st.subheader("🗂️ Gestor de Admisión, Verificación de Seguros y Documentación")
        st.write(
            "Evita el extravío de papeles, controla las planillas obligatorias de Seguros Miranda y previene la salida de pacientes sin factura."
        )

        admisiones = obtener_admision_db()

        # Métricas de estado
        tot_adm = len(admisiones)
        rojos = len([a for a in admisiones if "🔴" in a["Estado"]])
        amarillos = len([a for a in admisiones if "🟡" in a["Estado"]])
        verdes = len([a for a in admisiones if "🟢" in a["Estado"]])

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Pacientes en Admisión", tot_adm)
        a2.metric("🔴 Documento Faltante", rojos)
        a3.metric("🟡 En Atención / Consulta", amarillos)
        a4.metric("🟢 Listo para Egreso", verdes)

        st.markdown("---")

        tab_adm1, tab_adm2 = st.tabs(
            ["📋 Tablero de Control de Admisión", "➕ Registrar Ingreso de Paciente"]
        )

        with tab_adm1:
            if admisiones:
                df_adm = pd.DataFrame(admisiones)

                filtro_est_adm = st.selectbox(
                    "Filtrar por Estado de Expediente:",
                    ["Todos", "🔴 Pendiente Documento/Firma", "🟡 En Atención (RX/Lab/Consulta)", "🟢 Listo (Factura + Récipes + Planilla)"],
                )
                if filtro_est_adm != "Todos":
                    df_adm = df_adm[df_adm["Estado"] == filtro_est_adm]

                st.dataframe(
                    df_adm.drop(columns=["id"], errors="ignore"),
                    use_container_width=True,
                )

                st.markdown("---")
                st.markdown("#### 🔄 Cambiar Estado del Expediente del Paciente")
                col_u1, col_u2 = st.columns(2)

                with col_u1:
                    dict_adm = {
                        f"{a['Paciente']} ({a['Atención']} - {a['Estado']})": a["id"]
                        for a in admisiones
                    }
                    pac_sel = st.selectbox(
                        "Seleccionar paciente a actualizar:", list(dict_adm.keys())
                    )
                    id_pac_sel = dict_adm[pac_sel]

                with col_u2:
                    nuevo_est_adm = st.selectbox(
                        "Nuevo Estado:",
                        [
                            "🔴 Pendiente Documento/Firma",
                            "🟡 En Atención (RX/Lab/Consulta)",
                            "🟢 Listo (Factura + Récipes + Planilla)",
                        ],
                    )
                    nuevos_detalles = st.text_input(
                        "Detalles / Observaciones",
                        placeholder="Ej: Entregó la planilla de Seguros Miranda firmada.",
                    )

                    if st.button("🔄 Actualizar Estado de Admisión"):
                        actualizar_estado_admision_db(
                            id_pac_sel, nuevo_est_adm, nuevos_detalles
                        )
                        st.success("¡Expediente actualizado con éxito!")
                        st.rerun()
            else:
                st.info("No hay pacientes registrados en admisión hoy.")

        with tab_adm2:
            st.markdown("#### Registrar Entrada de Paciente a Taquilla")
            with st.form("form_admision", clear_on_submit=True):
                ca1, ca2 = st.columns(2)
                with ca1:
                    ad_nombre = st.text_input("Nombre y Apellido del Paciente *")
                    ad_cedula = st.text_input("Cédula o Identificación")
                    ad_tipo = st.selectbox(
                        "Modalidad de Atención *",
                        ["Particular", "Seguros Miranda", "Caseha / Crédito", "Seguro General (Otro)"],
                    )
                with ca2:
                    ad_aseguradora = st.text_input(
                        "Nombre de la Aseguradora / Empresa",
                        placeholder="Solo si no es Particular",
                    )
                    ad_estado_ini = st.selectbox(
                        "Estado Inicial del Expediente",
                        [
                            "🔴 Pendiente Documento/Firma",
                            "🟡 En Atención (RX/Lab/Consulta)",
                            "🟢 Listo (Factura + Récipes + Planilla)",
                        ],
                    )
                    ad_obs = st.text_area(
                        "Pendientes / Documentos requeridos",
                        placeholder="Ej. Entregar planilla Miranda para firma, falta copia de cédula...",
                    )

                btn_adm = st.form_submit_button("🚀 Iniciar Admisión")
                if btn_adm:
                    if not ad_nombre.strip():
                        st.error("Ingrese el nombre del paciente.")
                    else:
                        # Alerta automatizada para Seguros Miranda
                        if ad_tipo == "Seguros Miranda":
                            st.warning(
                                "📌 **REQUISITO OBLIGATORIO:** Imprimir e incluir la Planilla Especial de Seguros Miranda para firma del paciente."
                            )

                        f_actual = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        guardar_admision_db(
                            ad_nombre.strip(),
                            ad_cedula,
                            ad_tipo,
                            ad_aseguradora,
                            ad_estado_ini,
                            ad_obs,
                            datos_usuario["nombre"],
                            f_actual,
                        )
                        st.success(f"¡Paciente {ad_nombre} registrado en admisión!")
                        st.rerun()

    # ==========================================
    # MÓDULO 2: COORDINACIÓN MÉDICA, CITAS Y WHATSAPP
    # ==========================================
    elif modulo_principal == "2. Coordinación Médica, Citas y Avisos de WhatsApp":
        st.subheader("📅 Coordinación de Agendas Médicas y Notificaciones por WhatsApp")
        st.write(
            "Avisa a los doctores si tienen pacientes, gestiona cancelaciones al instante y envía resúmenes de agenda por WhatsApp."
        )

        citas_globales = obtener_citas_db()

        tot_c = len(citas_globales)
        pend_c = len([c for c in citas_globales if c["Estado"] == "Pendiente"])
        canc_c = len([c for c in citas_globales if c["Estado"] == "Cancelada"])
        atend_c = len([c for c in citas_globales if c["Estado"] == "Atendida"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Citas Agendadas", tot_c)
        m2.metric("⏳ Pendientes", pend_c)
        m3.metric("🚨 Canceladas", canc_c)
        m4.metric("✅ Atendidas", atend_c)

        st.markdown("---")

        if canc_c > 0:
            st.error(
                f"🚨 **ALERTA PARA MÉDICOS:** Se registran **{canc_c} cita(s) cancelada(s)**. Notifique al médico por WhatsApp para evitar su traslado innecesario."
            )

        tab_cit1, tab_cit2, tab_cit3 = st.tabs(
            [
                "📋 Agenda y Estado de Citas",
                "📲 Generador de Notificación por WhatsApp",
                "➕ Agendar Cita",
            ]
        )

        with tab_cit1:
            if citas_globales:
                df_cit = pd.DataFrame(citas_globales)
                st.dataframe(
                    df_cit.drop(columns=["id"], errors="ignore"),
                    use_container_width=True,
                )

                st.markdown("#### 🔄 Cambiar Estado de Cita")
                cc1, cc2 = st.columns(2)
                with cc1:
                    dict_c = {
                        f"{c['Paciente']} - {c['Medico']} ({c['Fecha_Hora']})": c["id"]
                        for c in citas_globales
                    }
                    c_sel = st.selectbox("Seleccionar cita:", list(dict_c.keys()))
                    id_c_sel = dict_c[c_sel]
                with cc2:
                    nest_c = st.selectbox(
                        "Nuevo Estado:", ["Pendiente", "Atendida", "Cancelada"]
                    )
                    if st.button("🔄 Actualizar Cita"):
                        actualizar_estado_cita_db(id_c_sel, nest_c)
                        st.success("¡Estado de cita actualizado!")
                        st.rerun()
            else:
                st.info("No hay citas en la agenda.")

        with tab_cit2:
            st.markdown("#### 📲 Generar Mensaje de Resumen para el Médico")
            st.write(
                "Copie y envíe este reporte estandarizado por WhatsApp al médico al final de la tarde:"
            )

            medicos_unicos = list(
                set([c["Medico"] for c in citas_globales])
            ) if citas_globales else ["Dr. Pérez"]
            med_seleccionado = st.selectbox(
                "Seleccionar Médico para Notificar:", medicos_unicos
            )

            citas_medico = [
                c
                for c in citas_globales
                if c["Medico"] == med_seleccionado and c["Estado"] == "Pendiente"
            ]

            msg_whatsapp = f"""*REPORTE DE AGENDA DE ADMISIÓN - CLÍNICA*
Estimado(a) *{med_seleccionado}*, le saludamos de Admisión.
Le informamos sus pacientes confirmados para su próxima consulta:

"""
            if citas_medico:
                for idx, cm in enumerate(citas_medico, 1):
                    msg_whatsapp += f"{idx}. {cm['Paciente']} | Hora: {cm['Fecha_Hora']} | Motivo: {cm['Motivo']}\n"
                msg_whatsapp += f"\nTotal de pacientes: *{len(citas_medico)}*."
            else:
                msg_whatsapp += "Por el momento no registra pacientes agendados."

            st.code(msg_whatsapp, language="text")
            st.info(
                "💡 **Consejo:** Copie este texto y péguelo directamente en el chat de WhatsApp del especialista."
            )

        with tab_cit3:
            st.markdown("#### Agendar Nueva Cita")
            with st.form("form_cita_nueva", clear_on_submit=True):
                cn_pac = st.text_input("Paciente *")
                cn_med = st.text_input("Médico Especialista *")
                cn_esp = st.selectbox(
                    "Especialidad",
                    [
                        "Medicina General",
                        "Pediatría",
                        "Cardiología",
                        "Ginecología",
                        "Cirugía",
                        "Traumatología",
                    ],
                )
                cn_fec = st.text_input(
                    "Fecha y Hora",
                    value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                )
                cn_mot = st.text_area("Motivo")

                if st.form_submit_button("📅 Guardar Cita"):
                    if not cn_pac or not cn_med:
                        st.error("Complete el paciente y médico.")
                    else:
                        guardar_cita_db(
                            cn_pac, cn_med, cn_esp, cn_fec, cn_mot, "Pendiente"
                        )
                        st.success("¡Cita agendada con éxito!")
                        st.rerun()

    # ==========================================
    # MÓDULO 3: CONTABILIDAD Y CAJA
    # ==========================================
    elif modulo_principal == "3. Contabilidad, Cierre de Caja y Balance Financiero":
        st.subheader("💰 Control de Caja Diaria, Facturación y Balance Contable")
        st.write(
            "Registra pagos en efectivo, punto de venta, pago móvil y transferencias, asegurando un cuadre perfecto al final del turno."
        )

        transacciones = obtener_contabilidad_db()

        ingresos = sum([t["Monto"] for t in transacciones if t["Tipo"] == "Ingreso"])
        egresos = sum([t["Monto"] for t in transacciones if t["Tipo"] == "Egreso"])
        balance = ingresos - egresos

        f1, f2, f3 = st.columns(3)
        f1.metric("🟢 Ingresos Totales ($)", f"${ingresos:,.2f}")
        f2.metric("🔴 Egresos Totales ($)", f"${egresos:,.2f}")
        f3.metric("💵 Balance Neto ($)", f"${balance:,.2f}", delta=f"${balance:,.2f}")

        st.markdown("---")

        tab_f1, tab_f2 = st.tabs(
            ["📊 Historial de Transacciones y Cierre", "➕ Registrar Cobro / Pago"]
        )

        with tab_f1:
            if transacciones:
                df_fin = pd.DataFrame(transacciones)
                st.dataframe(
                    df_fin.drop(columns=["id"], errors="ignore"),
                    use_container_width=True,
                )

                st.markdown("#### 💳 Desglose por Método de Pago en Caja")
                df_metodos = (
                    df_fin[df_fin["Tipo"] == "Ingreso"]
                    .groupby("Metodo_Pago")["Monto"]
                    .sum()
                    .reset_index()
                )
                st.dataframe(df_metodos, use_container_width=True)

                csv_f = df_fin.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Descargar Balance de Caja (CSV)",
                    csv_f,
                    "caja_admision.csv",
                    "text/csv",
                )
            else:
                st.info("No hay transacciones registradas.")

        with tab_f2:
            st.markdown("#### Registrar Transacción en Caja")
            with st.form("form_fin", clear_on_submit=True):
                cf1, cf2 = st.columns(2)
                with cf1:
                    fn_con = st.text_input("Concepto / Factura N° *")
                    fn_mon = st.number_input(
                        "Monto ($) *", min_value=0.01, value=50.0, step=5.0
                    )
                    fn_tip = st.selectbox("Tipo", ["Ingreso", "Egreso"])
                with cf2:
                    fn_met = st.selectbox(
                        "Método de Pago *",
                        [
                            "Efectivo ($ / Bs)",
                            "Punto de Venta (Débito)",
                            "Punto de Venta (Crédito)",
                            "Pago Móvil",
                            "Transferencia Bancaria",
                            "Caseha / Crédito Institucional",
                        ],
                    )
                    fn_cat = st.selectbox(
                        "Categoría",
                        [
                            "Consulta Médica",
                            "Estudio RX / Imagen",
                            "Exámenes de Laboratorio",
                            "Procedimiento / Cirugía",
                            "Insumos / Varios",
                        ],
                    )

                fn_fec = st.text_input(
                    "Fecha y Hora",
                    value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                )

                if st.form_submit_button("💾 Guardar en Caja"):
                    if not fn_con.strip():
                        st.error("Ingrese el concepto.")
                    else:
                        guardar_transaccion_db(
                            fn_fec,
                            fn_con.strip(),
                            fn_tip,
                            fn_met,
                            fn_mon,
                            fn_cat,
                            datos_usuario["nombre"],
                        )
                        st.success("¡Transacción registrada en caja!")
                        st.rerun()

    # ==========================================
    # MÓDULO 4: AUDITORÍA DE EXPEDIENTES Y QR
    # ==========================================
    elif modulo_principal == "4. Auditoría de Expedientes e Historia Clínica (QR)":
        st.subheader("📋 Módulo de Auditoría y Verificación de Expedientes")

        col1, col2 = st.columns(2)
        with col1:
            hc_id = st.text_input("ID o Código de Historia Clínica", placeholder="Ej: HC-2026-089")
            responsable = st.text_input("Responsable / Auditor", value=datos_usuario["nombre"])
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
            consentimiento = st.checkbox("¿Tiene consentimiento informado adjunto?")
            cie10 = st.checkbox("¿Tiene codificación CIE-10 correcta?")
            lab = st.checkbox("¿Resultados de laboratorio adjuntos?")

        if st.button("🚀 Evaluar y Generar QR"):
            if not hc_id:
                st.error("Ingrese el código de la historia clínica.")
            elif firma and consentimiento and cie10 and lab:
                st.success(f"🎉 ¡Expediente {hc_id} aprobado! Estado: 🟢 VERDE")

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
                st.error("❌ Expediente incompleto. Estado: 🔴 ROJO / AMARILLO.")

    # ==========================================
    # MÓDULO 5: BIOESTADÍSTICA (OMS)
    # ==========================================
    elif modulo_principal == "5. Central Bioestadística e Indicadores (Nivel OMS)":
        st.subheader("🚀 Central Bioestadística e Indicadores de Rendimiento Clínico")

        sub_est = st.radio(
            "Seleccione la función:",
            [
                "Indicadores Hospitalarios y Semáforo de Saturación",
                "Estadística Descriptiva, Frecuencias y Varianza",
            ],
        )

        if sub_est == "Indicadores Hospitalarios y Semáforo de Saturación":
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                total_camas = st.number_input("Camas instaladas", min_value=0, value=60, step=1)
                dias_periodo = st.number_input("Días del período", min_value=0, value=30, step=1)
            with col_i2:
                dias_paciente = st.number_input("Días-paciente acumulados", min_value=0, value=1350, step=1)
                pacientes_egresos = st.number_input("Total egresos", min_value=0, value=148, step=1)

            if st.button("⚙️ Calcular Indicadores"):
                if total_camas <= 0 or dias_periodo <= 0 or pacientes_egresos <= 0:
                    st.error("Valores deben ser mayores a cero.")
                else:
                    ocupacion = (dias_paciente / (total_camas * dias_periodo)) * 100
                    estancia_media = dias_paciente / pacientes_egresos
                    giro_cama = pacientes_egresos / total_camas

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Ocupación de Camas", f"{ocupacion:.2f}%")
                    m2.metric("Estancia Promedio", f"{estancia_media:.2f} días")
                    m3.metric("Giro de Cama", f"{giro_cama:.2f} veces")

                    if ocupacion > 85.0:
                        st.error("🔴 SATURACIÓN CRÍTICA (>85%)")
                    elif 75.0 <= ocupacion <= 85.0:
                        st.success("🟢 EFICIENCIA ÓPTIMA (75%-85%)")
                    else:
                        st.warning("🟡 SUBUTILIZACIÓN (<75%)")

        else:
            input_datos = st.text_input(
                "Ingrese datos numéricos separados por comas",
                "12, 15, 14, 18, 20, 15, 22, 19, 15",
            )
            if st.button("🔬 Procesar Estadísticas"):
                lista_nums = [float(x.strip()) for x in input_datos.split(",") if x.strip()]
                if lista_nums:
                    s_datos = pd.Series(lista_nums)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Media", f"{s_datos.mean():.2f}")
                    c2.metric("Mediana", f"{s_datos.median():.2f}")
                    c3.metric("Varianza", f"{s_datos.var(ddof=0):.2f}")
                    c4.metric("Desviación Std", f"{s_datos.std(ddof=0):.2f}")

    # ==========================================
    # MÓDULO 6: TRIAGE Y URGENCIAS
    # ==========================================
    elif modulo_principal == "6. Tablero de Triage y Urgencias en Tiempo Real":
        st.subheader("🚨 Gestión y Control de Flujo de Urgencias")

        triage_global = obtener_triage_db()

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Pacientes", len(triage_global))
        k2.metric("En Espera", len([p for p in triage_global if p["Estado"] == "En Espera"]))
        k3.metric("En Atención", len([p for p in triage_global if p["Estado"] == "En Atención"]))

        with st.form("form_tri", clear_on_submit=True):
            npac = st.text_input("Nombre del Paciente *")
            ntri = st.selectbox(
                "Nivel Triage",
                [
                    "Nivel 1 - Resucitación (Rojo)",
                    "Nivel 2 - Emergencia (Naranja)",
                    "Nivel 3 - Urgencia (Amarillo)",
                    "Nivel 4 - Menor Urgencia (Verde)",
                    "Nivel 5 - No Urgente (Azul)",
                ],
            )
            nest = st.selectbox("Estado Inicial", ["En Espera", "En Atención"])

            if st.form_submit_button("🚀 Registrar en Triage"):
                if npac:
                    guardar_triage_db(
                        npac,
                        ntri,
                        nest,
                        pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        datos_usuario["nombre"],
                    )
                    st.success("¡Paciente registrado en Triage!")
                    st.rerun()

        if triage_global:
            st.dataframe(pd.DataFrame(triage_global), use_container_width=True)

    # ==========================================
    # MÓDULO 7: ASISTENTE MÉDICO DE GUARDIA
    # ==========================================
    elif modulo_principal == "7. Asistente Médico de Guardia (CIE-10, SOAP y Cálculos)":
        st.subheader("🩺 Utilidades Médicas de Guardia")

        sub_g = st.selectbox(
            "Herramienta:",
            ["📖 Buscador CIE-10", "📝 Redactor Nota SOAP", "🧮 Calculadora IMC y Goteo"],
        )

        if sub_g == "📖 Buscador CIE-10":
            st.write("Buscador rápido de códigos de diagnóstico frecuentes.")
            b_cie = [
                {"Código": "J02.9", "Diagnóstico": "Faringitis aguda"},
                {"Código": "I10", "Diagnóstico": "Hipertensión esencial"},
                {"Código": "A90", "Diagnóstico": "Fiebre del dengue"},
                {"Código": "E11.9", "Diagnóstico": "Diabetes mellitus tipo 2"},
            ]
            st.dataframe(pd.DataFrame(b_cie), use_container_width=True)

        elif sub_g == "📝 Redactor Nota SOAP":
            st.write("Generador de nota clínica estructurada.")
            p_n = st.text_input("Nombre Paciente")
            p_s = st.text_area("Subjetivo (S)")
            p_o = st.text_area("Objetivo (O)")
            p_a = st.text_area("Análisis (A)")
            p_p = st.text_area("Plan (P)")

            if st.button("📄 Generar Nota"):
                nota_txt = f"PATIENT: {p_n}\nS: {p_s}\nO: {p_o}\nA: {p_a}\nP: {p_p}"
                st.code(nota_txt)

        else:
            p_kg = st.number_input("Peso (kg)", value=70.0)
            t_m = st.number_input("Talla (m)", value=1.70)
            if st.button("⚖️ Calcular IMC"):
                imc_v = p_kg / (t_m**2)
                st.metric("IMC", f"{imc_v:.2f}")

    # ==========================================
    # MÓDULO 8: ALMACÉN E INSUMOS DE ADMISIÓN
    # ==========================================
    elif modulo_principal == "8. Almacén e Insumos de Admisión":
        st.subheader("📦 Control de Insumos del Área de Admisión")
        st.write("Evita quedarte sin resmas de papel o planillas de Seguros Miranda a mitad del turno.")

        insumos_data = obtener_insumos_db()

        for ins in insumos_data:
            if ins["cantidad"] <= ins["minimo_requerido"]:
                st.error(
                    f"⚠️ **ALERTA DE ALMACÉN:** Quedan solo **{ins['cantidad']} {ins['item']}**. ¡Ir al almacén a reponer!"
                )

        if insumos_data:
            df_ins = pd.DataFrame(insumos_data)
            st.dataframe(df_ins, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 🔄 Actualizar Inventario de Admisión")
            ci1, ci2 = st.columns(2)
            with ci1:
                dict_ins = {ins["item"]: ins["id"] for ins in insumos_data}
                item_sel = st.selectbox("Seleccionar Insumo:", list(dict_ins.keys()))
                id_item_sel = dict_ins[item_sel]
            with ci2:
                nueva_cant_ins = st.number_input("Nueva Cantidad Disponible", min_value=0, value=5, step=1)
                if st.button("💾 Actualizar Stock"):
                    actualizar_insumo_db(id_item_sel, nueva_cant_ins)
                    st.success("¡Stock actualizado!")
                    st.rerun()
