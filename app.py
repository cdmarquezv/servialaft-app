import streamlit as st
import pandas as pd
import unicodedata
import io
from datetime import datetime, date

try:
    from rapidfuzz import fuzz
except ImportError:
    st.error("Instala rapidfuzz: pip install rapidfuzz"); st.stop()

try:
    from generador_pdf import (
        generar_pdf_individual,
        generar_pdf_manual,
        generar_pdf_masivo,
    )
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SERVIALAFT SAS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background:#0f1b2d; }
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio > label { display:none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap:2px; }
[data-testid="stSidebar"] .stRadio label {
    display:flex !important; align-items:center; padding:10px 14px;
    border-radius:8px; margin:2px 0; cursor:pointer; font-size:15px;
    transition:background .15s;
}
[data-testid="stSidebar"] .stRadio label:hover { background:rgba(255,255,255,0.1); }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) {
    background:rgba(255,255,255,0.15);
}
.login-wrap {
    max-width:420px; margin:60px auto 0; padding:40px 36px 32px;
    background:#fff; border-radius:16px;
    box-shadow:0 4px 32px rgba(0,0,0,0.10);
}
.login-title { font-size:26px; font-weight:700; color:#0f1b2d; text-align:center; margin-bottom:4px; }
.login-sub   { font-size:13px; color:#6c757d; text-align:center; margin-bottom:24px; }
.ext-link {
    display:block; padding:18px 22px; border-radius:12px;
    border:1px solid #e2e8f0; background:#f8faff;
    text-decoration:none !important; margin-bottom:14px;
    transition:box-shadow .2s;
}
.ext-link:hover { box-shadow:0 4px 16px rgba(15,27,45,0.12); }
.ext-title { font-size:17px; font-weight:700; color:#0f1b2d; }
.ext-desc  { font-size:13px; color:#6c757d; margin-top:3px; }
.ext-url   { font-size:12px; color:#2563eb; margin-top:6px; font-family:monospace; }
.metric-box {
    background:#f8faff; border:1px solid #e2e8f0;
    border-radius:12px; padding:20px 16px; text-align:center;
}
.metric-num   { font-size:38px; font-weight:800; color:#0f1b2d; line-height:1; }
.metric-label { font-size:13px; color:#6c757d; margin-top:6px; }
footer { visibility:hidden; }
#MainMenu { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "logged_in": False,
    "user": None,
    "menu": "🌐  OFAC / ONU",
    "logs": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────────────────────────────────────
USUARIOS = {
    "admin":     {"password": "admin123",    "rol": "Administrador", "nombre": "Admin Principal"},
    "analista1": {"password": "sarlaft2024", "rol": "Analista",      "nombre": "Laura Gómez"},
    "consultor": {"password": "consulta01",  "rol": "Consultor",     "nombre": "Andrés Martínez"},
}

# ─────────────────────────────────────────────────────────────────────────────
# LISTAS VINCULANTES (DEMO EMBEBIDO)
# ─────────────────────────────────────────────────────────────────────────────
LISTA_SDN = pd.DataFrame([
    {"tipo_id":"CC",  "nro_id":"12345678",  "nombre":"JUAN CARLOS RODRIGUEZ GOMEZ",   "origen":"OFAC SDN",  "detalle":"NARCOTICS"},
    {"tipo_id":"CC",  "nro_id":"87654321",  "nombre":"MARIA FERNANDA LOPEZ HERRERA",  "origen":"OFAC SDN",  "detalle":"TERRORISM"},
    {"tipo_id":"CC",  "nro_id":"11223344",  "nombre":"CARLOS ANDRES PEREZ VILLA",     "origen":"OFAC SDN",  "detalle":"SDGT"},
    {"tipo_id":"CC",  "nro_id":"55667788",  "nombre":"ANA LUCIA MARTINEZ CASTRO",     "origen":"OFAC SDN",  "detalle":"NARCOTICS"},
    {"tipo_id":"NIT", "nro_id":"900123456", "nombre":"INVERSIONES DELTA SAS",          "origen":"OFAC SDN",  "detalle":"SDGT"},
    {"tipo_id":"NIT", "nro_id":"800987654", "nombre":"COMERCIALIZADORA OMEGA LTDA",    "origen":"OFAC SDN",  "detalle":"NARCOTICS"},
    {"tipo_id":"CC",  "nro_id":"44556677",  "nombre":"LUIS MIGUEL VARGAS OSPINA",     "origen":"ONU",       "detalle":"RES. 1267"},
    {"tipo_id":"CC",  "nro_id":"99001122",  "nombre":"DIANA CAROLINA RESTREPO MESA",  "origen":"ONU",       "detalle":"RES. 1988"},
    {"tipo_id":"NIT", "nro_id":"901111222", "nombre":"GRUPO FINANCIERO ANDINO SA",     "origen":"ONU",       "detalle":"RES. 1267"},
])

LISTA_PEPS = pd.DataFrame([
    {"tipo_id":"CC",  "nro_id":"99887766",  "nombre":"PEDRO ANTONIO SUAREZ MORA",    "origen":"PEP",           "detalle":"Alcalde Municipal — Alcaldía de Bogotá"},
    {"tipo_id":"CC",  "nro_id":"44332211",  "nombre":"SANDRA MILENA TORRES RUIZ",    "origen":"PEP",           "detalle":"Senadora de la República — Senado"},
    {"tipo_id":"CC",  "nro_id":"66778899",  "nombre":"JORGE LUIS VARGAS MENDOZA",    "origen":"PEP",           "detalle":"Director General DIAN"},
    {"tipo_id":"CC",  "nro_id":"33221100",  "nombre":"LUCIA ESPERANZA DIAZ PARRA",   "origen":"PEP",           "detalle":"Magistrada Corte Suprema de Justicia"},
    {"tipo_id":"NIT", "nro_id":"901234567", "nombre":"FUNDACION PROGRESO Y PAZ",      "origen":"PEP",           "detalle":"Entidad sin ánimo de lucro"},
    {"tipo_id":"CC",  "nro_id":"77665544",  "nombre":"ROBERTO CARLOS ARANGO SILVA",  "origen":"DECLARADO PEP", "detalle":"Ex-Gobernador — Gobernación Antioquia"},
    {"tipo_id":"CC",  "nro_id":"22334455",  "nombre":"CLAUDIA VIVIANA MUNOZ REYES",  "origen":"DECLARADO PEP", "detalle":"Ex-Ministra de Salud"},
])

TODAS = pd.concat([LISTA_SDN, LISTA_PEPS], ignore_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────
def norm(s):
    if not isinstance(s, str): return ""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").upper().strip()

def buscar(tipo_id, nro_id, nombre, umbral):
    res = []
    nombre_n = norm(nombre)
    for _, row in TODAS.iterrows():
        if row["tipo_id"] != tipo_id:
            continue
        doc_exacto  = str(row["nro_id"]) == str(nro_id)
        doc_cercano = fuzz.ratio(str(row["nro_id"]), str(nro_id)) >= 85
        sim = fuzz.token_sort_ratio(norm(str(row["nombre"])), nombre_n) / 100

        if doc_exacto and sim >= umbral:
            nivel = "EXACTA"
        elif doc_cercano and sim >= umbral:
            nivel = "APROXIMADA"
        elif sim >= umbral:
            nivel = "SOLO NOMBRE"
        else:
            continue

        r = row.to_dict()
        r["sim_%"] = round(sim * 100, 1)
        r["nivel"] = nivel
        res.append(r)
    return pd.DataFrame(res) if res else pd.DataFrame()

def log_q(modulo, tipo_id, nro_id, nombre, resultado):
    st.session_state.logs.append({
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": st.session_state.user,
        "modulo": modulo,
        "tipo_id": tipo_id,
        "nro_id": str(nro_id),
        "nombre": nombre,
        "resultado": resultado,
    })

def a_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Datos")
        ws = w.sheets["Datos"]
        from openpyxl.styles import Font, PatternFill, Alignment
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="0F1B2D")
            cell.alignment = Alignment(horizontal="center")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                len(str(col[0].value or "")), 10) + 4
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# PANTALLA DE LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def pantalla_login():
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
        <div class="login-wrap">
          <div class="login-title">🛡️ SERVIALAFT SAS</div>
          <div class="login-sub">Sistema de Consulta Listas Vinculantes<br>
          OFAC · ONU · PEPs · Policía · Procuraduría</div>
        </div>
        """, unsafe_allow_html=True)
        usuario  = st.text_input("Usuario", placeholder="usuario")
        password = st.text_input("Contraseña", type="password", placeholder="contraseña")
        st.caption("Demo rápido → **admin** / **admin123**")
        if st.button("Iniciar sesión →", type="primary", use_container_width=True):
            if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
MENU_ITEMS = [
    "🌐  OFAC / ONU",
    "👮  Policía Nacional",
    "⚖️  Procuraduría",
    "📋  Registros consultados",
    "📊  Estadísticas de uso",
    "🚪  Cerrar sesión",
]

def sidebar():
    with st.sidebar:
        st.markdown("### 🛡️ SERVIALAFT SAS")
        st.markdown("---")
        info = USUARIOS[st.session_state.user]
        st.markdown(f"**{info['nombre']}**")
        st.caption(f"Rol: {info['rol']}")
        st.markdown("---")
        sel = st.radio("Menú", MENU_ITEMS, index=MENU_ITEMS.index(st.session_state.menu)
                       if st.session_state.menu in MENU_ITEMS else 0,
                       label_visibility="collapsed")
        if sel == "🚪  Cerrar sesión":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.menu = "🌐  OFAC / ONU"
            st.rerun()
        else:
            st.session_state.menu = sel

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO OFAC / ONU
# ─────────────────────────────────────────────────────────────────────────────
def mod_ofac():
    st.markdown("## 🌐 Consultar Listas Vinculantes — OFAC · ONU · PEPs")
    st.caption(f"Fuentes: OFAC SDN · ONU Resoluciones · PEPs Colombia | Actualización: {date.today():%d/%m/%Y}")

    tab_ind, tab_mas = st.tabs(["🔎 Consulta individual", "📂 Carga masiva (Excel)"])

    # ── Individual ──────────────────────────────────────────────────────────
    with tab_ind:
        c1, c2 = st.columns([1, 2])
        with c1:
            tipo_id  = st.selectbox("Tipo ID", ["CC", "NIT", "CE", "PAS"])
            nro_id   = st.text_input("Número de identificación")
            nombre   = st.text_input("Nombre completo")
            umbral   = st.slider("SimiliScore™ (%)", 50, 100, 85,
                                  help="Porcentaje mínimo de similitud para considerar coincidencia")
            consultar = st.button("🔍 Consultar", type="primary", use_container_width=True)

        with c2:
            if consultar:
                if not nro_id.strip() or not nombre.strip():
                    st.warning("Completa todos los campos.")
                else:
                    df = buscar(tipo_id, nro_id.strip(), nombre.strip(), umbral / 100)
                    if df.empty:
                        st.success("✅ Sin coincidencias — no figura en listas vinculantes.")
                        log_q("OFAC/ONU", tipo_id, nro_id, nombre, "NO ENCONTRADO")
                        if PDF_DISPONIBLE:
                            pdf_b = generar_pdf_individual(
                                tipo_id, nro_id.strip(), nombre.strip(), None,
                                usuario=st.session_state.user)
                            st.download_button("📄 Certificado PDF (resultado limpio)",
                                               data=pdf_b,
                                               file_name=f"certificado_{nro_id}_{date.today()}.pdf",
                                               mime="application/pdf")
                    else:
                        st.error(f"🚨 {len(df)} coincidencia(s) encontrada(s)")
                        log_q("OFAC/ONU", tipo_id, nro_id, nombre, df["nivel"].iloc[0])
                        for _, row in df.iterrows():
                            emoji = "🔴" if row["nivel"] == "EXACTA" else "🟡"
                            with st.expander(f"{emoji} {row['nombre']}  —  {row['origen']}", expanded=True):
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Lista",        row["origen"])
                                col2.metric("SimiliScore™", f"{row['sim_%']}%")
                                col3.metric("Nivel",        row["nivel"])
                                st.write(f"**Tipo ID:** {row['tipo_id']}  |  **Número:** {row['nro_id']}")
                                if row.get("detalle"):
                                    st.write(f"**Detalle:** {row['detalle']}")
                        cx, cy = st.columns(2)
                        cx.download_button("📥 Excel",
                                           data=a_excel(df),
                                           file_name=f"resultado_{date.today()}.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True)
                        if PDF_DISPONIBLE:
                            pdf_b = generar_pdf_individual(
                                tipo_id, nro_id.strip(), nombre.strip(), df,
                                usuario=st.session_state.user)
                            cy.download_button("📄 Certificado PDF",
                                               data=pdf_b,
                                               file_name=f"certificado_{nro_id}_{date.today()}.pdf",
                                               mime="application/pdf",
                                               use_container_width=True)
            else:
                st.info("Completa el formulario y presiona **Consultar**.")

    # ── Masiva ───────────────────────────────────────────────────────────────
    with tab_mas:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("**Formato requerido:**")
            st.code("tipo_id | nro_id | nombre")
            plantilla = pd.DataFrame({
                "tipo_id": ["CC","NIT","CE"],
                "nro_id":  ["12345678","900123456","87654321"],
                "nombre":  ["JUAN PEREZ GOMEZ","EMPRESA ABC SAS","CARLOS LOPEZ"],
            })
            st.download_button("📄 Descargar plantilla",
                               data=a_excel(plantilla),
                               file_name="plantilla.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            archivo  = st.file_uploader("Subir archivo .xlsx", type=["xlsx"])
            umbral_m = st.slider("SimiliScore™ masivo (%)", 50, 100, 85)
            procesar = st.button("⚙️ Procesar", type="primary", use_container_width=True)

        with c2:
            if procesar and archivo:
                df_in = pd.read_excel(archivo)
                df_in.columns = [c.lower().strip() for c in df_in.columns]
                if not {"tipo_id","nro_id","nombre"}.issubset(df_in.columns):
                    st.error("El archivo debe tener columnas: tipo_id, nro_id, nombre")
                else:
                    resultados = []
                    prog = st.progress(0)
                    for i, row in df_in.iterrows():
                        prog.progress((i+1)/len(df_in), f"Procesando {i+1}/{len(df_in)}…")
                        df_r = buscar(str(row["tipo_id"]).upper().strip(),
                                      str(row["nro_id"]).strip(),
                                      str(row["nombre"]).strip(),
                                      umbral_m / 100)
                        if df_r.empty:
                            resultados.append({"tipo_id":row["tipo_id"],"nro_id":row["nro_id"],
                                               "nombre":row["nombre"],"resultado":"SIN COINCIDENCIA",
                                               "origen":"—","nivel":"—","sim_%":"—"})
                            log_q("MASIVO", row["tipo_id"], row["nro_id"], row["nombre"], "NO ENCONTRADO")
                        else:
                            for _, r in df_r.iterrows():
                                rd = r.to_dict(); rd["resultado"] = "ENCONTRADO EN LISTA"
                                resultados.append(rd)
                            log_q("MASIVO", row["tipo_id"], row["nro_id"], row["nombre"], df_r["nivel"].iloc[0])
                    prog.empty()
                    df_out = pd.DataFrame(resultados)
                    enc = (df_out["resultado"] == "ENCONTRADO EN LISTA").sum()
                    co1,co2,co3 = st.columns(3)
                    co1.metric("Total",             len(df_in))
                    co2.metric("🚨 Con coincidencia", enc)
                    co3.metric("✅ Sin coincidencia", len(df_in)-enc)
                    st.dataframe(df_out, use_container_width=True, height=280)
                    bx, by = st.columns(2)
                    bx.download_button("📥 Excel completo",
                                       data=a_excel(df_out),
                                       file_name=f"masivo_{date.today()}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
                    if PDF_DISPONIBLE:
                        pdf_m = generar_pdf_masivo(
                            df_out, umbral_m / 100,
                            usuario=st.session_state.user)
                        by.download_button("📄 Reporte PDF ejecutivo",
                                           data=pdf_m,
                                           file_name=f"reporte_masivo_{date.today()}.pdf",
                                           mime="application/pdf",
                                           use_container_width=True)
            elif procesar:
                st.warning("Sube primero un archivo .xlsx")
            else:
                st.info("Sube un archivo y presiona **Procesar**.")

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO POLICÍA
# ─────────────────────────────────────────────────────────────────────────────
def mod_policia():
    st.markdown("## 👮 Antecedentes Judiciales — Policía Nacional")
    st.info("Esta fuente usa CAPTCHA. Accede al portal oficial y registra el resultado aquí.", icon="ℹ️")

    st.markdown("""
    <a class="ext-link" href="https://antecedentes.policia.gov.co:7005/WebJudicial/" target="_blank">
      <div class="ext-title">🔗 Policía Nacional — Certificado Judicial</div>
      <div class="ext-desc">Consulta y descarga del certificado judicial de personas naturales en Colombia.</div>
      <div class="ext-url">https://antecedentes.policia.gov.co:7005/WebJudicial/</div>
    </a>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 Registrar resultado de consulta manual")
    with st.form("frm_policia", clear_on_submit=True):
        c1, c2 = st.columns(2)
        tipo_id = c1.selectbox("Tipo ID", ["CC","NIT","CE","PAS"])
        nro_id  = c2.text_input("Número de identificación")
        nombre  = st.text_input("Nombre completo")
        resultado = st.radio("Resultado obtenido",
                             ["SIN ANTECEDENTES","CON ANTECEDENTES","NO SE PUDO VERIFICAR"],
                             horizontal=True)
        obs = st.text_area("Observaciones (opcional)", height=80)
        ok  = st.form_submit_button("💾 Guardar registro", type="primary")
    if ok:
        if not nro_id or not nombre:
            st.warning("Completa tipo ID, número y nombre.")
        else:
            log_q("POLICÍA", tipo_id, nro_id, nombre, resultado)
            if resultado == "SIN ANTECEDENTES":
                st.success("✅ Registro guardado — Sin antecedentes.")
            elif resultado == "CON ANTECEDENTES":
                st.error("🚨 Registro guardado — Con antecedentes registrados.")
            else:
                st.warning("⚠️ Registro guardado — Verificación pendiente.")
            if PDF_DISPONIBLE:
                pdf_p = generar_pdf_manual(
                    tipo_id, nro_id, nombre, "POLICÍA", resultado,
                    observacion=obs, usuario=st.session_state.user)
                st.download_button("📄 Descargar certificado PDF",
                                   data=pdf_p,
                                   file_name=f"certificado_policia_{nro_id}_{date.today()}.pdf",
                                   mime="application/pdf")

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO PROCURADURÍA
# ─────────────────────────────────────────────────────────────────────────────
def mod_procuraduria():
    st.markdown("## ⚖️ Antecedentes Disciplinarios — Procuraduría General")
    st.info("Esta fuente usa CAPTCHA. Accede al portal oficial y registra el resultado aquí.", icon="ℹ️")

    st.markdown("""
    <a class="ext-link" href="https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx" target="_blank">
      <div class="ext-title">🔗 Procuraduría General de la Nación — Antecedentes Disciplinarios</div>
      <div class="ext-desc">Consulta de antecedentes disciplinarios de servidores públicos y particulares sancionados en Colombia.</div>
      <div class="ext-url">https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx</div>
    </a>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 Registrar resultado de consulta manual")
    with st.form("frm_procu", clear_on_submit=True):
        c1, c2 = st.columns(2)
        tipo_id = c1.selectbox("Tipo ID", ["CC","NIT","CE","PAS"])
        nro_id  = c2.text_input("Número de identificación")
        nombre  = st.text_input("Nombre completo")
        resultado = st.radio("Resultado obtenido",
                             ["SIN SANCIONES DISCIPLINARIAS","CON SANCIONES DISCIPLINARIAS","NO SE PUDO VERIFICAR"],
                             horizontal=True)
        obs = st.text_area("Observaciones (opcional)", height=80)
        ok  = st.form_submit_button("💾 Guardar registro", type="primary")
    if ok:
        if not nro_id or not nombre:
            st.warning("Completa tipo ID, número y nombre.")
        else:
            log_q("PROCURADURÍA", tipo_id, nro_id, nombre, resultado)
            if "SIN" in resultado:
                st.success("✅ Registro guardado — Sin sanciones.")
            elif "CON" in resultado:
                st.error("🚨 Registro guardado — Con sanciones disciplinarias.")
            else:
                st.warning("⚠️ Registro guardado — Verificación pendiente.")
            if PDF_DISPONIBLE:
                pdf_pr = generar_pdf_manual(
                    tipo_id, nro_id, nombre, "PROCURADURÍA", resultado,
                    observacion=obs, usuario=st.session_state.user)
                st.download_button("📄 Descargar certificado PDF",
                                   data=pdf_pr,
                                   file_name=f"certificado_procuraduria_{nro_id}_{date.today()}.pdf",
                                   mime="application/pdf")

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO LOGS
# ─────────────────────────────────────────────────────────────────────────────
LOGS_DEMO = [
    {"fecha_hora":"2024-06-10 08:14:22","usuario":"analista1","modulo":"OFAC/ONU",
     "tipo_id":"CC","nro_id":"12345678","nombre":"JUAN CARLOS RODRIGUEZ GOMEZ","resultado":"EXACTA"},
    {"fecha_hora":"2024-06-10 09:02:55","usuario":"consultor","modulo":"POLICÍA",
     "tipo_id":"CC","nro_id":"98765432","nombre":"MARIA JOSE ALVAREZ RUIZ","resultado":"SIN ANTECEDENTES"},
    {"fecha_hora":"2024-06-10 09:48:10","usuario":"analista1","modulo":"MASIVO",
     "tipo_id":"NIT","nro_id":"900123456","nombre":"INVERSIONES DELTA SAS","resultado":"EXACTA"},
    {"fecha_hora":"2024-06-10 10:15:33","usuario":"admin","modulo":"PROCURADURÍA",
     "tipo_id":"CC","nro_id":"55443322","nombre":"LUCIA PATRICIA MORA VARGAS","resultado":"SIN SANCIONES DISCIPLINARIAS"},
    {"fecha_hora":"2024-06-10 10:58:01","usuario":"analista1","modulo":"OFAC/ONU",
     "tipo_id":"CC","nro_id":"11223344","nombre":"CARLOS ANDRES PEREZ","resultado":"APROXIMADA"},
    {"fecha_hora":"2024-06-10 11:22:44","usuario":"consultor","modulo":"POLICÍA",
     "tipo_id":"CC","nro_id":"87654321","nombre":"ANDRES FELIPE LOPEZ","resultado":"NO SE PUDO VERIFICAR"},
    {"fecha_hora":"2024-06-10 12:05:18","usuario":"admin","modulo":"OFAC/ONU",
     "tipo_id":"NIT","nro_id":"800987654","nombre":"COMERCIALIZADORA OMEGA LTDA","resultado":"EXACTA"},
    {"fecha_hora":"2024-06-10 13:30:44","usuario":"analista1","modulo":"MASIVO",
     "tipo_id":"CC","nro_id":"55667788","nombre":"ANA LUCIA MARTINEZ","resultado":"APROXIMADA"},
]

def mod_logs():
    st.markdown("## 📋 Registros de consultas")
    todos = LOGS_DEMO + st.session_state.logs
    df = pd.DataFrame(todos)

    if df.empty:
        st.info("No hay registros aún.")
        return

    c1, c2, c3 = st.columns(3)
    mods  = ["Todos"] + sorted(df["modulo"].unique().tolist())
    users = ["Todos"] + sorted(df["usuario"].unique().tolist())
    f_mod  = c1.selectbox("Módulo",  mods)
    f_usr  = c2.selectbox("Usuario", users)
    f_txt  = c3.text_input("Buscar nombre o número")

    df_f = df.copy()
    if f_mod  != "Todos": df_f = df_f[df_f["modulo"]  == f_mod]
    if f_usr  != "Todos": df_f = df_f[df_f["usuario"] == f_usr]
    if f_txt:
        q = f_txt.upper()
        df_f = df_f[df_f["nombre"].str.upper().str.contains(q, na=False) |
                    df_f["nro_id"].str.contains(q, na=False)]

    df_f = df_f.sort_values("fecha_hora", ascending=False).reset_index(drop=True)
    st.caption(f"Mostrando {len(df_f)} de {len(df)} registros")
    st.dataframe(df_f, use_container_width=True, height=400)
    st.download_button("📥 Exportar registros",
                       data=a_excel(df_f),
                       file_name=f"logs_{date.today()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO ESTADÍSTICAS
# ─────────────────────────────────────────────────────────────────────────────
def mod_stats():
    st.markdown("## 📊 Estadísticas de uso")

    # Métricas principales
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="metric-box"><div class="metric-num">172</div><div class="metric-label">Consultas este mes</div></div>', unsafe_allow_html=True)
    c2.markdown('<div class="metric-box"><div class="metric-num">38</div><div class="metric-label">🚨 Alertas generadas</div></div>', unsafe_allow_html=True)
    c3.markdown('<div class="metric-box"><div class="metric-num">3</div><div class="metric-label">Usuarios activos</div></div>', unsafe_allow_html=True)
    c4.markdown('<div class="metric-box"><div class="metric-num">16</div><div class="metric-label">Cargas masivas</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Gráficas
    consultas_dia = pd.DataFrame({
        "Fecha":         pd.date_range("2024-06-01", periods=10, freq="D"),
        "OFAC/ONU":      [12,18,9,22,15,30,8,25,19,14],
        "Policía":       [5,8,4,9,6,12,3,10,7,6],
        "Procuraduría":  [3,5,2,6,4,8,2,7,5,4],
    }).set_index("Fecha")

    resultados = pd.DataFrame({
        "Resultado":  ["Sin coincidencia","Coincidencia exacta","Coincidencia aproximada","Con antecedentes"],
        "Cantidad":   [134, 18, 12, 8],
    }).set_index("Resultado")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Consultas diarias por módulo")
        st.line_chart(consultas_dia, height=220)
    with col2:
        st.markdown("#### Distribución de resultados")
        st.bar_chart(resultados, height=220)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Actividad por usuario")
        st.dataframe(pd.DataFrame({
            "Usuario": ["analista1","consultor","admin"],
            "Consultas": [87, 42, 23],
            "Alertas":   [21,  9,  8],
        }), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### Listas con más alertas")
        st.dataframe(pd.DataFrame({
            "Lista":   ["OFAC SDN","ONU","PEP","DECLARADO PEP"],
            "Alertas": [22, 8, 5, 3],
        }), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.download_button("📥 Exportar reporte",
                       data=a_excel(consultas_dia.reset_index()),
                       file_name=f"estadisticas_{date.today()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    pantalla_login()
else:
    sidebar()
    m = st.session_state.menu
    if   "OFAC"          in m: mod_ofac()
    elif "Policía"       in m: mod_policia()
    elif "Procuraduría"  in m: mod_procuraduria()
    elif "Registros"     in m: mod_logs()
    elif "Estadísticas"  in m: mod_stats()
